#!/usr/bin/env python3
"""
clean_adapt.py — 从 ELF 重新生成所有 hex 文件，正确适配 mcycle 测量。

流程:
  1. 从 ELF 重定位地址 (0x80000000 → 0x0)
  2. 转换为 hex（保留所有原始指令，不损坏 BNE）
  3. 查找全部 3 个 ECALL 并应用补丁
  4. 添加 mcycle 测量启动/终止代码
"""

import struct
import sys
import os
import glob
import subprocess
import argparse

RISCV_TOOLS = "/home/yifengxin/riscv/bin"
OBJCOPY     = f"{RISCV_TOOLS}/riscv32-unknown-elf-objcopy"
OBJDUMP     = f"{RISCV_TOOLS}/riscv32-unknown-elf-objdump"
TEST_SRC_DIR = "/home/yifengxin/riscv-tests/isa"

# mcycle 测量代码
# 启动代码: 读 mcycle → 存 0x3F0 → 跳转 test_entry
STARTUP_CODE = [
    0xB00022F3,  # csrrs x5, mcycle, x0    (read mcycle CSR)
    0x3E502823,  # sw    x5, 0x3F0(x0)     (store startup value to 0x3F0)
    # JAL x0, test_entry will be appended dynamically
]
# 终止代码: 读 mcycle → 存 0x3F4 → 死循环
FINALIZER_CODE = [
    0xB00022F3,  # csrrs x5, mcycle, x0
    0x3E502A23,  # sw    x5, 0x3F4(x0)     (store end value to 0x3F4)
    0x0000006F,  # J_SELF
]

def elf_to_hex_lines(elf_path):
    """将 ELF 转换为 hex 行列表（不做 ecall 补丁）。"""
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

    lines = []
    for i in range(0, len(data), 4):
        word = data[i] | (data[i+1] << 8) | (data[i+2] << 16) | (data[i+3] << 24)
        lines.append(f"{word:08X}")

    os.remove(bin_path)
    return lines


def relocate_elf(src_path, dst_path):
    """重定位 ELF: 0x80000000 → 0x00000000。"""
    delta = -0x80000000
    subprocess.run(
        [OBJCOPY, f"--change-addresses={delta}", src_path, dst_path],
        check=True, capture_output=True
    )


def find_ecalls(hex_lines):
    """查找所有 ECALL 位置（0x00000073）。"""
    positions = []
    for i, line in enumerate(hex_lines):
        if line == "00000073":
            positions.append(i)
    return positions


def decode_branch_target(instr, current_line):
    """解码 B-type 指令的分支目标行号。返回 None 如果不是 B-type。"""
    opcode = instr & 0x7F
    if opcode != 0x63:
        return None
    imm12 = (instr >> 31) & 1
    imm10_5 = (instr >> 25) & 0x3F
    imm4_1 = (instr >> 8) & 0xF
    imm11 = (instr >> 7) & 1
    imm = (imm12 << 12) | (imm11 << 11) | (imm10_5 << 5) | (imm4_1 << 1)
    if imm & (1 << 12):
        imm |= ~((1 << 13) - 1)  # sign extend 13-bit
    return current_line + imm // 4


def decode_jal_target(instr, current_line):
    """解码 JAL 指令的目标行号。返回 None 如果不是 JAL。"""
    opcode = instr & 0x7F
    if opcode != 0x6F:
        return None
    imm20 = (instr >> 31) & 1
    imm10_1 = (instr >> 21) & 0x3FF
    imm11 = (instr >> 20) & 1
    imm19_12 = (instr >> 12) & 0xFF
    imm = (imm20 << 20) | (imm19_12 << 12) | (imm11 << 11) | (imm10_1 << 1)
    if imm & (1 << 20):
        imm |= ~((1 << 21) - 1)  # sign extend 21-bit
    return current_line + imm // 4


def classify_ecalls(hex_lines, ecall_positions):
    """
    将 ECALL 分类为 trap_vector, pass_handler, fail_handler.

    RISC-V 测试框架约定:
    - 第1个 ECALL 总是 trap_vector (用于初始化测试数据)
    - PASS handler: 被 JAL (无条件跳转) 到达，或 x10=0
    - FAIL handler: 被条件分支 (BNE/BEQ等) 到达，或 x10!=0

    返回: (pass_pos, fail_pos) 两个 ECALL 位置，或 (None, None)
    """
    if len(ecall_positions) < 2:
        return None, None

    # 第1个 ECALL 总是 trap_vector (环境检查/测试数据设置)
    remaining = ecall_positions[1:]  # 剩下的 ECALL

    if len(remaining) == 1:
        # 只有1个非-trap ECALL → 就是 PASS handler
        return remaining[0], None
    elif len(remaining) == 2:
        pos_a, pos_b = remaining[0], remaining[1]
    else:
        # 多于3个 ECALL: 第1个=trap, 最后2个处理
        pos_a, pos_b = remaining[-2], remaining[-1]

    # 分析每个非-trap ECALL: 检查哪些指令跳转到它们
    branch_targets = {}  # ecall_pos → count of conditional branches targeting it
    jal_targets = {}     # ecall_pos → count of JALs targeting it

    for pos in remaining:
        branch_targets[pos] = 0
        jal_targets[pos] = 0

    for i, line in enumerate(hex_lines):
        instr = int(line, 16)
        target = decode_branch_target(instr, i)
        if target is not None and target in branch_targets:
            branch_targets[target] += 1
        target = decode_jal_target(instr, i)
        if target is not None and target in jal_targets:
            jal_targets[target] += 1

    # 分类逻辑:
    # PASS handler: 被 JAL 跳转到的，且/或没有条件分支跳转到它
    # FAIL handler: 被条件分支跳转到的

    pos_a_branches = branch_targets.get(pos_a, 0)
    pos_b_branches = branch_targets.get(pos_b, 0)
    pos_a_jals = jal_targets.get(pos_a, 0)
    pos_b_jals = jal_targets.get(pos_b, 0)

    # 如果只有其中一个被条件分支跳转 → 那就是 FAIL handler
    if pos_a_branches > 0 and pos_b_branches == 0:
        return pos_b, pos_a  # (pass=pos_b, fail=pos_a)
    elif pos_b_branches > 0 and pos_a_branches == 0:
        return pos_a, pos_b  # (pass=pos_a, fail=pos_b)
    elif pos_a_jals > 0 and pos_b_jals == 0:
        return pos_a, pos_b  # (pass=pos_a, fail=pos_b)
    elif pos_b_jals > 0 and pos_a_jals == 0:
        return pos_b, pos_a  # (pass=pos_b, fail=pos_a)

    # Fallback: 假设最后一个 ECALL 是 PASS, 倒数第二个是 FAIL
    return pos_b, pos_a


def get_reset_vector_line(hex_lines):
    """
    从原始 hex 的 line 0 (原 _start 的 JAL 指令) 解析 reset_vector 位置。

    ELF 中 _start 位于 0x80000000，第一条指令是 `j reset_vector`。
    重定位后地址=0，通过解码 JAL 立即数得到 reset_vector 的 hex 行号。

    示例: 0x0500006f → offset=0x50 → line 20
    """
    if not hex_lines:
        return 1  # fallback

    instr = int(hex_lines[0], 16)
    opcode = instr & 0x7F

    if opcode == 0x6F:  # JAL
        imm_20    = (instr >> 31) & 1
        imm_10_1  = (instr >> 21) & 0x3FF
        imm_11    = (instr >> 20) & 1
        imm_19_12 = (instr >> 12) & 0xFF

        imm = (imm_20 << 20) | (imm_10_1 << 1) | (imm_11 << 11) | (imm_19_12 << 12)
        # Sign-extend 21-bit to 32-bit
        if imm & (1 << 20):
            imm = imm - (1 << 21)

        # 指令在地址 0，target = offset
        target_line = imm // 4
        if target_line > 0 and target_line < len(hex_lines):
            return target_line

    # fallback: 大多数测试 reset_vector 在 line 20 (addr 0x50)
    print(f"  WARNING: Could not parse reset_vector from JAL, using fallback line=20")
    return 20


def encode_jal(rd, target_line, current_line):
    """编码 JAL 指令。target_line 和 current_line 是 hex 行号（每行 4 字节）。"""
    target_addr = target_line * 4
    current_addr = current_line * 4
    offset = target_addr - current_addr

    if offset < -1048576 or offset >= 1048576:
        raise ValueError(f"JAL offset {offset} out of range")

    # Encode 21-bit signed immediate
    imm = offset & 0x1FFFFF  # 21-bit unsigned
    if offset < 0:
        imm = (1 << 21) + offset  # signed to unsigned

    # JAL encoding: imm[20|10:1|11|19:12] | rd | opcode
    imm_20    = (imm >> 20) & 1
    imm_10_1  = (imm >> 1) & 0x3FF
    imm_11    = (imm >> 11) & 1
    imm_19_12 = (imm >> 12) & 0xFF

    instr = (imm_20 << 31) | (imm_10_1 << 21) | (imm_11 << 20) | \
            (imm_19_12 << 12) | (rd << 7) | 0x6F

    return f"{instr:08X}"


def adapt_hex(hex_lines, test_entry_line=None):
    """
    适配 hex 用于 mcycle 测量:
    1. 将 line 0 改为 JAL → startup
    2. ECALL #1 → NOP (env check)
    3. ECALL #2 → J_SELF (FAIL)
    4. ECALL #3 → JAL → finalizer (PASS)
    5. 末尾附加启动代码 + 终止代码

    test_entry_line: 测试入口行号。None=自动从 line 0 的 JAL 解析。
    """

    # 复制 hex，避免修改原列表
    lines = list(hex_lines)

    # 自动检测 reset_vector 位置（从原始 _start JAL 解析）
    if test_entry_line is None:
        test_entry_line = get_reset_vector_line(lines)
    print(f"  test_entry_line = {test_entry_line} (addr 0x{test_entry_line*4:08X})")

    # 查找 ECALL
    ecall_positions = find_ecalls(lines)
    if len(ecall_positions) < 2:
        print(f"  WARNING: Only {len(ecall_positions)} ECALL(s) found, expected >= 2")
    print(f"  ECALL positions: {ecall_positions}")

    # 分类 ECALL: trap_vector (第1个), pass_handler, fail_handler
    pass_ecall, fail_ecall = classify_ecalls(lines, ecall_positions)
    print(f"  PASS={pass_ecall}, FAIL={fail_ecall}")

    # 补丁 1: ECALL #1 (trap_vector) → NOP (环境检查)
    if len(ecall_positions) >= 1:
        lines[ecall_positions[0]] = "00000013"  # NOP

    # 补丁 2: PASS handler → JAL → finalizer
    finalizer_line = len(lines) + 3  # startup = 3 words (csrrs + sw + JAL)
    if pass_ecall is not None:
        lines[pass_ecall] = encode_jal(0, finalizer_line, pass_ecall)

    # 补丁 3: FAIL handler → J_SELF (如果存在独立 FAIL handler)
    if fail_ecall is not None:
        lines[fail_ecall] = "0000006F"  # J_SELF

    # 构建新 hex：
    # [0]: JAL → startup
    # [1:N]: 原 hex (lines 1 to N-1，但 line 0 被替换)
    # [startup]: 启动代码 (csrrs mcycle, sw 0x3F0, JAL test_entry)
    # [finalizer]: 终止代码 (csrrs mcycle, sw 0x3F4, J_SELF)

    new_lines = []

    # Line 0: JAL → startup (在末尾)
    # 新 hex 结构: [0]=JAL, [1..N-1]=原hex[1:], [N..N+2]=startup, [N+3..]=finalizer
    startup_line = len(lines)  # startup 代码在 new_lines 中的起始行号
    new_lines.append(encode_jal(0, startup_line, 0))

    # Lines 1 to N-1: 原始 hex（省略原 line 0）
    new_lines.extend(lines[1:])

    # 启动代码：读 mcycle, 存 0x3F0, JAL test_entry
    # 先添加 csrrs 和 sw
    for word in STARTUP_CODE:
        new_lines.append(f"{word:08X}")

    # 然后动态计算 JAL 到 test_entry
    startup_jal_line = len(new_lines)  # 新加 JAL 的位置
    new_lines.append(encode_jal(0, test_entry_line, startup_jal_line))

    # 终止代码
    for word in FINALIZER_CODE:
        new_lines.append(f"{word:08X}")

    return new_lines


def process_one_test(test_name, output_dir):
    """处理单个测试。"""
    src_elf = f"{TEST_SRC_DIR}/{test_name}"
    tmp_elf = f"/tmp/{test_name}_clean.elf"

    if not os.path.exists(src_elf):
        print(f"  ERROR: Source ELF not found: {src_elf}")
        return False

    print(f"Processing {test_name}...")

    # Step 1: 重定位
    relocate_elf(src_elf, tmp_elf)

    # Step 2: 转换为 hex
    hex_lines = elf_to_hex_lines(tmp_elf)
    print(f"  ELF → {len(hex_lines)} hex words")

    # Step 3: 适配 mcycle
    hex_lines = adapt_hex(hex_lines)
    print(f"  Adapted → {len(hex_lines)} hex words")

    # Step 4: 写入输出
    hex_name = test_name.replace("rv32ui-p-", "") + ".hex"
    hex_path = os.path.join(output_dir, hex_name)
    with open(hex_path, "w") as f:
        for line in hex_lines:
            f.write(line + "\n")

    # 清理
    os.remove(tmp_elf)
    print(f"  → {hex_path}")
    return True


def process_all(output_dir):
    """批量处理所有 rv32ui-p 测试。"""
    pattern = f"{TEST_SRC_DIR}/rv32ui-p-*"
    tests = sorted(glob.glob(pattern))

    tests = [t for t in tests if os.path.isfile(t)
             and not t.endswith('.dump')
             and not t.endswith('.bin')
             and not t.endswith('.hex')
             and 'fence_i' not in os.path.basename(t)]  # skip fence_i (not supported)

    print(f"Found {len(tests)} tests to process\n")

    success = 0
    for test_path in tests:
        test_name = os.path.basename(test_path)
        if process_one_test(test_name, output_dir):
            success += 1
        print()

    print(f"Done: {success}/{len(tests)} tests processed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate clean hex files")
    parser.add_argument("--output-dir", default="/home/yifengxin/FX-RV32_RemoveM_Custom/riscv_tests/hex")
    parser.add_argument("--test", help="Single test name (e.g. rv32ui-p-add)")
    args = parser.parse_args()

    if args.test:
        process_one_test(args.test, args.output_dir)
    else:
        process_all(args.output_dir)
