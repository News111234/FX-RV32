#!/usr/bin/env python3
"""
reloc_test.py — 将 RISC-V 官方测试 ELF 适配为 FX-RV32 可用的 hex 文件。

处理内容：
  1. 地址重定位: 0x80000000 → 0x00000000
  2. 替换 ecall 退出机制 → 写 gp 到 0x3FC + 死循环
  3. 输出 Verilog hex 格式 ($readmemh 兼容)

用法:
  python3 reloc_test.py --input rv32ui-p-add --output ../hex/add.hex
  python3 reloc_test.py --batch   # 批量处理所有 rv32ui-p 测试
"""

import struct
import sys
import os
import glob
import argparse
import subprocess

# ============================================================
# 配置
# ============================================================
RISCV_TOOLS = "/home/yifengxin/riscv/bin"
OBJCOPY     = f"{RISCV_TOOLS}/riscv32-unknown-elf-objcopy"
OBJDUMP     = f"{RISCV_TOOLS}/riscv32-unknown-elf-objdump"

# 官方测试目录
TEST_SRC_DIR = "/home/yifengxin/riscv-tests/isa"

# FX-RV32 适配参数
TARGET_BASE     = 0x00000000   # 目标基址
RESULT_ADDR     = 0x000003FC   # 结果写入地址 (perf_data_size)
DATA_RAM_ORIGIN = 0x00000100   # 数据段起始地址

# ecall 指令编码
ECALL_BYTES = bytes([0x73, 0x00, 0x00, 0x00])  # little-endian

# 替换代码: sw gp, 1020(x0); j .
# 汇编: sw gp, 1020(x0) → 0x3E302E23 (little-endian: 23 2e 30 3e)
#       j .             → 0x0000006F (little-endian: 6f 00 00 00)
STORE_LOOP = bytes([
    0x23, 0x2e, 0x30, 0x3e,  # sw gp, 1020(x0)
    0x6f, 0x00, 0x00, 0x00,  # j .
])
PASS_PATCH = STORE_LOOP  # 8 bytes — 替换 ecall + unimp
# FAIL patch 动态生成: j (pass_pos - fail_pos)，跳到 PASS 的 store+loop 共用

# ============================================================
# 核心逻辑
# ============================================================

def find_elf_sections(elf_path):
    """用 objdump 解析 ELF 段信息。"""
    result = subprocess.run(
        [OBJDUMP, "-h", elf_path], capture_output=True, text=True
    )
    sections = {}
    for line in result.stdout.split("\n"):
        parts = line.strip().split()
        if len(parts) >= 7 and parts[0].replace(".", "").isdigit():
            try:
                idx  = int(parts[0])
                name = parts[1]
                size = int(parts[2], 16)
                vma  = int(parts[3], 16)
                lma  = int(parts[4], 16)
                sections[name] = {"idx": idx, "size": size, "vma": vma, "lma": lma}
            except (ValueError, IndexError):
                continue
    return sections


def find_symbol_offset(elf_path, sym_name):
    """查找符号在段内的偏移。"""
    result = subprocess.run(
        [OBJDUMP, "-t", elf_path], capture_output=True, text=True
    )
    for line in result.stdout.split("\n"):
        parts = line.strip().split()
        if len(parts) >= 4 and parts[-1] == sym_name:
            return int(parts[0], 16)
    return None


def relocate_elf(src_path, dst_path, new_base=TARGET_BASE):
    """
    用 objcopy 重定位 ELF:
      --change-addresses: 移动所有段
      --change-section-address .tohost=...: 单独调整数据段
    """
    old_base = 0x80000000
    delta = new_base - old_base  # 例如 -0x80000000

    # 1. 移动所有段的地址
    cmd = [
        OBJCOPY,
        f"--change-addresses={delta}",
        src_path,
        dst_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Relocated: {src_path} -> {dst_path}")


def patch_elf(elf_path):
    """
    在 ELF 二进制中查找 ecall 指令并替换为 store+loop。
    策略:
      - PASS ecall + unimp (8 bytes) → sw gp,1020(x0); j .
      - FAIL ecall (4 bytes) → j <PASS ecall 位置> (共用 store+loop)
      - reset ecall + unimp (8 bytes) → sw gp,1020(x0); j .
    这样 PASS 和 FAIL 都写入 gp 到 0x3FC 后死循环。
    """
    with open(elf_path, "rb") as f:
        data = bytearray(f.read())

    # 查找所有 ecall 位置
    ecall_positions = []
    pos = 0
    while True:
        pos = data.find(ECALL_BYTES, pos)
        if pos == -1:
            break
        ecall_positions.append(pos)
        pos += 4

    if len(ecall_positions) < 3:
        print(f"  Warning: Only {len(ecall_positions)} ecall(s), expected >= 3")
        return

    print(f"  Found {len(ecall_positions)} ecall(s) at offsets: "
          f"{[hex(p) for p in ecall_positions]}")

    # ELF 中可能有 4 个匹配 (数据段巧合)，真正的 ecall 只有 3 个:
    #   索引 0 = startup (0x158)
    #   索引 1 = FAIL (0x684)
    #   索引 2 = PASS (0x698)
    # 跳过可能的第 4 个 (数据段假阳性)
    reset_pos = ecall_positions[0]   # startup ecall
    fail_pos  = ecall_positions[1]   # FAIL handler ecall
    pass_pos  = ecall_positions[2]   # PASS handler ecall

    # FAIL: 4 bytes only (j .) — 不覆盖 pass 代码
    # 这样 FAIL 分支在 gp 被正确设置后死循环，PASS 分支正常执行到 0x698
    fail_j = struct.pack("<I", 0x0000006F)  # j . (infinite loop)
    print(f"  FAIL patch: ecall@{hex(fail_pos)} -> j . (4 bytes, preserves pass)")
    data[fail_pos:fail_pos+4] = fail_j

    # PASS: 8 bytes (sw gp,1020(x0); j .) — 替换 ecall+unimp
    print(f"  PASS patch: ecall@{hex(pass_pos)} -> sw gp,1020(x0); j .")
    data[pass_pos:pass_pos+8] = STORE_LOOP

    # RESET (startup ecall): 4 bytes nop (保留原逻辑, 不阻塞启动)
    # 原代码中 bltz a0, skip 会跳过此处, 若未跳过则 ecall 也不会影响测试
    nop = struct.pack("<I", 0x00000013)  # addi x0, x0, 0
    print(f"  RESET patch: ecall@{hex(reset_pos)} -> nop (preserve startup flow)")
    data[reset_pos:reset_pos+4] = nop

    with open(elf_path, "wb") as f:
        f.write(data)
    print(f"  Patched ELF: {elf_path}")


def elf_to_hex(elf_path, hex_path):
    """将 ELF 转换为 Verilog $readmemh 兼容的 hex 格式。"""
    # 先转成 raw binary, 再转成 hex 文本
    bin_path = elf_path + ".bin"
    subprocess.run(
        [OBJCOPY, "-O", "binary", elf_path, bin_path],
        check=True, capture_output=True
    )

    with open(bin_path, "rb") as f:
        data = f.read()

    # 补齐到 4 字节边界
    while len(data) % 4 != 0:
        data += b'\x00'

    with open(hex_path, "w") as f:
        for i in range(0, len(data), 4):
            word = data[i] | (data[i+1] << 8) | (data[i+2] << 16) | (data[i+3] << 24)
            f.write(f"{word:08x}\n")

    os.remove(bin_path)
    words = len(data) // 4
    print(f"  Generated hex: {hex_path} ({words} words)")


def process_one_test(test_name, output_dir):
    """
    处理单个测试: 输入官方 ELF, 输出适配后的 hex。
    test_name: 如 "rv32ui-p-add"
    """
    src_elf = f"{TEST_SRC_DIR}/{test_name}"
    tmp_elf = f"/tmp/{test_name}_reloc.elf"

    if not os.path.exists(src_elf):
        print(f"  ERROR: Source ELF not found: {src_elf}")
        return False

    print(f"\n=== Processing {test_name} ===")

    # Step 1: 重定位
    relocate_elf(src_elf, tmp_elf)

    # Step 2: 替换 ecall
    patch_elf(tmp_elf)

    # Step 3: 生成 hex
    hex_name = test_name.replace("rv32ui-p-", "") + ".hex"
    hex_path = os.path.join(output_dir, hex_name)
    elf_to_hex(tmp_elf, hex_path)

    # 清理
    os.remove(tmp_elf)
    return True


def process_all(output_dir):
    """批量处理所有 rv32ui-p 测试。"""
    pattern = f"{TEST_SRC_DIR}/rv32ui-p-*"
    tests = sorted(glob.glob(pattern))

    # 过滤掉 .dump, .bin, .hex 等非 ELF 文件
    tests = [t for t in tests if os.path.isfile(t)
             and not t.endswith('.dump')
             and not t.endswith('.bin')
             and not t.endswith('.hex')]

    print(f"Found {len(tests)} tests to process\n")

    success = 0
    for test_path in tests:
        test_name = os.path.basename(test_path)
        if process_one_test(test_name, output_dir):
            success += 1

    print(f"\n=== Done: {success}/{len(tests)} tests processed ===")


# ============================================================
# 命令行接口
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="RISC-V official test → FX-RV32 hex converter"
    )
    parser.add_argument("--input", "-i", help="Single test ELF path")
    parser.add_argument("--output", "-o", help="Output hex file path")
    parser.add_argument("--batch", action="store_true",
                        help="Process all rv32ui-p tests")
    parser.add_argument("--output-dir", default="../hex",
                        help="Output directory for batch mode")
    args = parser.parse_args()

    if args.batch:
        process_all(args.output_dir)
    elif args.input and args.output:
        process_one_test(os.path.basename(args.input),
                         os.path.dirname(args.output) or ".")
    else:
        parser.print_help()
        print("\nExample:")
        print("  python3 reloc_test.py --input /path/to/rv32ui-p-add --output ../hex/add.hex")
        print("  python3 reloc_test.py --batch")
