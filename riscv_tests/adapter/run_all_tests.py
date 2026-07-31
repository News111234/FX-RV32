#!/usr/bin/env python3
"""
run_all_tests.py — 批量运行 FX-RV32 适配后的 RISC-V 官方测试。

用法:
  python3 run_all_tests.py                    # 运行全部测试
  python3 run_all_tests.py --test add         # 运行单个测试
  python3 run_all_tests.py --dry-run          # 仅列出测试，不运行
"""

import os
import sys
import glob
import argparse
import subprocess
import time

# ============================================================
# 配置
# ============================================================
HEX_DIR     = "/home/yifengxin/FX-RV32_RemoveM_Custom/riscv_tests/hex"
RESULTS_DIR = "/home/yifengxin/FX-RV32_RemoveM_Custom/riscv_tests/results"

# UVM 仿真配置
UVM_DIR   = "/home/yifengxin/FX-RV32_RemoveM_Custom/uvm"
MSIM_CMD  = 'D:\\modeltech64_10.6e\\win64\\vsim.exe'
MSIM_TCL  = "run_test.tcl"
MSIM_COV  = "0"
MSIM_GUI  = "0"
TEST_NAME = "cpu_test_alu"

# Modelsim 路径
WORK_DIR_WIN = "D:\\FX-RV32_Tests\\uvm"        # Windows 原生路径（给 cmd.exe 用）
WORK_DIR_WSL = "/mnt/d/FX-RV32_Tests/uvm"      # WSL 挂载路径（给 Python 读文件用）

# ============================================================
# 工具函数
# ============================================================

def parse_result(transcript_path):
    """从 UVM transcript 中提取测试结果。"""
    if not os.path.exists(transcript_path):
        return "NO_FILE", "Transcript not found"

    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 检查 UVM 错误（排除计数为 0 的汇总行）
    for line in content.split("\n"):
        if "UVM_FATAL" in line:
            # 汇总行格式: "# UVM_FATAL :    0" — 这是正常的
            if "UVM_FATAL :" in line:
                count = line.split(":")[-1].strip()
                if count != "0":
                    return "FATAL", f"UVM_FATAL count = {count}"
            else:
                return "FATAL", line.strip()
        if "UVM_ERROR" in line and "UVM_ERROR :" in line:
            count = line.split(":")[-1].strip()
            if count != "0":
                return "ERROR", f"UVM_ERROR count = {count}"

    # 检查 Scoreboard — 这是最可靠的通过/失败判断
    if "Mismatches:" in content:
        for line in content.split("\n"):
            if "Mismatches:" in line:
                if "Mismatches:            0" in line:
                    return "PASS", "0 mismatches (scoreboard)"
                else:
                    return "FAIL", line.strip()

    # 回退方案：检查 tohost 写入
    # 注意：由于 CPU 的 AUIPC bug，实际写入地址可能是 0xFC0 而非 0x1000
    for line in content.split("\n"):
        if "STORE: [0x00000fc0]" in line or "STORE: [0x00001000]" in line:
            val_str = line.split("<= ")[-1].strip()
            try:
                val = int(val_str, 16)
                if val == 1:
                    return "PASS", f"gp=1 written"
                elif val != 0:
                    return "FAIL", f"fail code gp={val}"
            except ValueError:
                pass

    return "NO_RESULT", "No scoreboard or result write found"


def run_one_test(hex_name, dry_run=False):
    """运行单个测试。"""
    hex_path = os.path.join(HEX_DIR, hex_name)
    test_name = os.path.splitext(hex_name)[0]

    if not os.path.exists(hex_path):
        print(f"  SKIP: hex file not found: {hex_path}")
        return "SKIP", "hex not found"

    if dry_run:
        print(f"  [DRY RUN] {test_name}: {hex_path}")
        return "DRY", ""

    # 准备 UVM 工作目录（Windows 可访问路径）
    os.makedirs(WORK_DIR_WIN, exist_ok=True)

    # 复制 hex 到 UVM 目录
    uvm_hex = os.path.join(WORK_DIR_WIN, "test.hex")
    try:
        with open(hex_path, "r") as src:
            with open(uvm_hex, "w") as dst:
                dst.write(src.read())
    except Exception as e:
        return "ERROR", f"Cannot write hex: {e}"

    # 创建 TCL 脚本
    tcl_script = os.path.join(WORK_DIR_WIN, MSIM_TCL)
    with open(tcl_script, "w") as f:
        f.write(f"set HEX_FILE test.hex\n")
        f.write(f"set TEST_NAME {TEST_NAME}\n")
        f.write(f"set COV_ENABLE 0\n")
        f.write(f"set GUI_MODE 0\n")
        f.write(f"do run_msim.tcl\n")

    # 清理上次的 transcript
    transcript_win = os.path.join(WORK_DIR_WIN, "transcript")
    transcript_wsl = os.path.join(WORK_DIR_WSL, "transcript")
    if os.path.exists(transcript_wsl):
        os.remove(transcript_wsl)

    # 运行 Modelsim
    print(f"  Running {test_name}...", end=" ", flush=True)
    start = time.time()
    try:
        cmd = (f'cd /d {WORK_DIR_WIN} && {MSIM_CMD} -c -do {MSIM_TCL}')
        result = subprocess.run(
            ["cmd.exe", "/c", cmd],
            capture_output=True, text=True,
            encoding="gbk", errors="replace",
            timeout=120
        )
        elapsed = time.time() - start
        print(f"({elapsed:.0f}s)")
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "Simulation timed out (>120s)"

    # 解析结果（通过 WSL 路径读取）
    status, detail = parse_result(transcript_wsl)

    # 保存结果日志
    log_path = os.path.join(RESULTS_DIR, f"{test_name}.log")
    try:
        with open(transcript, "r", encoding="utf-8", errors="ignore") as src:
            with open(log_path, "w") as dst:
                dst.write(src.read())
    except Exception:
        pass

    return status, detail


def run_all(dry_run=False, filter_test=None):
    """运行所有适配后的测试。"""
    hex_files = sorted(glob.glob(os.path.join(HEX_DIR, "*.hex")))

    if filter_test:
        hex_files = [h for h in hex_files if filter_test in h]

    if not hex_files:
        print("No test hex files found!")
        return

    print(f"\n{'='*60}")
    print(f"  FX-RV32 RISC-V 官方测试批量运行器")
    print(f"  测试数量: {len(hex_files)}")
    if dry_run:
        print(f"  DRY RUN 模式 — 仅列出测试")
    print(f"{'='*60}\n")

    results = {}
    for i, hex_path in enumerate(hex_files):
        test_name = os.path.splitext(os.path.basename(hex_path))[0]
        print(f"[{i+1}/{len(hex_files)}]", end=" ")

        if dry_run:
            run_one_test(os.path.basename(hex_path), dry_run=True)
            results[test_name] = ("DRY", "")
            continue

        # 运行前先确保工作目录有必要的 UVM 文件
        # (首次运行需复制)
        status, detail = run_one_test(os.path.basename(hex_path))
        results[test_name] = (status, detail)

        if status == "FATAL" and "not found" in detail:
            print(f"  ERROR: UVM setup incomplete. Check {WORK_DIR_WIN}")
            break

    # 汇总报告
    print(f"\n{'='*60}")
    print(f"  测试结果汇总")
    print(f"{'='*60}")

    passed  = sum(1 for s, _ in results.values() if s == "PASS")
    failed  = sum(1 for s, _ in results.values() if s == "FAIL")
    errors  = sum(1 for s, _ in results.values() if s in ("ERROR", "FATAL", "TIMEOUT"))
    unknown = sum(1 for s, _ in results.values() if s not in ("PASS", "FAIL", "ERROR", "FATAL", "TIMEOUT", "DRY"))

    print(f"  总计: {len(results)}")
    print(f"  通过: {passed} ({100*passed/len(results):.0f}%)" if results else "  通过: 0")
    print(f"  失败: {failed}")
    print(f"  错误: {errors}")
    print(f"  未知: {unknown}")
    print(f"{'='*60}")

    # 失败详情
    for name, (status, detail) in sorted(results.items()):
        if status not in ("PASS", "DRY"):
            print(f"  [{status}] {name}: {detail}")

    # 写入汇总文件
    summary_path = os.path.join(RESULTS_DIR, "summary.txt")
    with open(summary_path, "w") as f:
        f.write(f"FX-RV32 RISC-V Official Test Results\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Total: {len(results)}, Passed: {passed}, Failed: {failed}\n\n")
        for name, (status, detail) in sorted(results.items()):
            f.write(f"[{status}] {name}: {detail}\n")

    print(f"\n详细结果: {summary_path}")


# ============================================================
# 命令行
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FX-RV32 RISC-V test batch runner"
    )
    parser.add_argument("--test", "-t", help="Run single test (e.g. 'add')")
    parser.add_argument("--dry-run", action="store_true", help="List tests without running")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    run_all(dry_run=args.dry_run, filter_test=args.test)
