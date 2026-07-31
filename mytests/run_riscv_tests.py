#!/usr/bin/env python3
"""
RISC-V official test suite compiler for FX-RV32

Usage:
  1. Install RISC-V GCC toolchain (riscv32-unknown-elf-gcc or riscv64-unknown-elf-gcc)
  2. Run this script: python run_riscv_tests.py
  3. Run individual tests: ./test_hex/run_test.sh <test_name>

Requirements:
  - riscv32-unknown-elf-gcc (or riscv64-unknown-elf-gcc with -march=rv32im)
  - Python 3
"""

import subprocess
import os
import sys
import glob
import shutil
import platform

# ========== Configuration ==========
RISCV_PREFIX = "riscv32-unknown-elf"
RISCV64_FALLBACK = "riscv64-unknown-elf"

# riscv-tests source path (auto-clone if empty)
RISCV_TESTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "riscv-tests")

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_hex")

# Linker script
LINKER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.ld")

# Test categories to compile (rv32ui = RV32I user, rv32um = RV32M)
TEST_CATEGORIES = ["rv32ui-p", "rv32um-p"]

# Architecture settings
MARCH = "rv32im"
MABI = "ilp32"


def find_toolchain():
    """Find available RISC-V GCC toolchain."""
    # try riscv32 first
    for prefix in [RISCV_PREFIX, RISCV64_FALLBACK]:
        try:
            result = subprocess.run(
                [f"{prefix}-gcc", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print(f"[OK] Found {prefix}-gcc")
                return prefix
        except FileNotFoundError:
            continue

    print("[ERROR] RISC-V GCC toolchain not found!")
    print("Install riscv-gnu-toolchain:")
    print("  Ubuntu: sudo apt install gcc-riscv64-unknown-elf")
    print("  macOS:  brew install riscv64-unknown-elf-gcc")
    print("  https://github.com/riscv-collab/riscv-gnu-toolchain/releases")
    return None


def check_riscv_tests():
    """Ensure riscv-tests source is available."""
    if os.path.exists(RISCV_TESTS_DIR):
        print(f"[OK] riscv-tests directory exists: {RISCV_TESTS_DIR}")
        return True

    print("[INFO] Cloning riscv-tests...")
    try:
        subprocess.run(
            ["git", "clone", "https://github.com/riscv-software-src/riscv-tests",
             RISCV_TESTS_DIR],
            check=True, timeout=300
        )
        print("[OK] riscv-tests cloned successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Clone failed: {e}")
        print("Manually clone: git clone https://github.com/riscv-software-src/riscv-tests")
        return False


def compile_test(prefix, test_name, asm_file, include_dirs):
    """Compile a single test assembly file to hex."""
    output_elf = os.path.join(OUTPUT_DIR, f"{test_name}.elf")
    output_bin = os.path.join(OUTPUT_DIR, f"{test_name}.bin")
    output_hex = os.path.join(OUTPUT_DIR, f"{test_name}.hex")

    # build include flags
    inc_flags = []
    for d in include_dirs:
        inc_flags += ["-I", d]

    # compile: asm -> elf
    cmd = [
        f"{prefix}-gcc",
        "-march=" + MARCH,
        "-mabi=" + MABI,
        "-nostdlib",
        "-nostartfiles",
    ] + inc_flags + [
        "-T", LINKER_SCRIPT,
        "-o", output_elf,
        asm_file
    ]

    print(f"  Compiling: {test_name}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        print(f"  [ERROR] Compilation failed:")
        # show last lines of error
        for line in result.stderr.strip().split('\n')[-5:]:
            print(f"    {line}")
        return False

    if not os.path.exists(output_elf):
        print(f"  [ERROR] ELF file not generated")
        return False

    # convert: elf -> binary
    cmd = [
        f"{prefix}-objcopy",
        "-O", "binary",
        output_elf,
        output_bin
    ]
    subprocess.run(cmd, check=True, timeout=10)

    # convert: binary -> hex (little-endian, 32-bit words)
    with open(output_bin, "rb") as f:
        data = f.read()

    # pad to 4-byte alignment
    if len(data) % 4 != 0:
        data += b'\x00' * (4 - len(data) % 4)

    with open(output_hex, "w") as f:
        for i in range(0, len(data), 4):
            word = int.from_bytes(data[i:i+4], 'little')
            f.write(f"{word:08x}\n")

    size = len(data)
    print(f"  [OK] {test_name}: {size} bytes -> {output_hex}")
    return True


def generate_run_script():
    """Generate a shell script to run individual tests with Verilator."""
    script_path = os.path.join(OUTPUT_DIR, "run_test.sh")

    with open(script_path, "w", encoding='utf-8') as f:
        f.write("""#!/bin/bash
# Run a single RISC-V test on FX-RV32 via Verilator
# Usage: ./run_test.sh <test_name>
# Example: ./run_test.sh rv32ui-p-add

set -e

TEST_NAME="$1"
if [ -z "$TEST_NAME" ]; then
    echo "Usage: ./run_test.sh <test_name>"
    echo "Available tests:"
    for f in *.hex; do
        echo "  $(basename "$f" .hex)"
    done
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HEX_FILE="${SCRIPT_DIR}/${TEST_NAME}.hex"

if [ ! -f "$HEX_FILE" ]; then
    echo "Error: $HEX_FILE not found"
    exit 1
fi

# copy hex to sim directory as program.hex
cp "$HEX_FILE" "${SCRIPT_DIR}/../../sim/program.hex"

# build and run
cd "${SCRIPT_DIR}/../../sim"
make clean
make run RVTEST=1
""")
    os.chmod(script_path, 0o755)

    print(f"[INFO] Run script generated: {script_path}")


def main():
    print("=" * 60)
    print("RISC-V Official Test Compiler for FX-RV32")
    print("=" * 60)

    # find toolchain
    prefix = find_toolchain()
    if not prefix:
        sys.exit(1)

    # check riscv-tests
    if not check_riscv_tests():
        sys.exit(1)

    # include paths for riscv-tests headers
    include_dirs = [
        os.path.join(RISCV_TESTS_DIR, "env", "p"),
        os.path.join(RISCV_TESTS_DIR, "isa", "macros", "scalar"),
    ]
    for d in include_dirs:
        if not os.path.isdir(d):
            print(f"[ERROR] riscv-tests include directory not found: {d}")
            sys.exit(1)

    # create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # find all test files
    all_tests = []
    for category in TEST_CATEGORIES:
        pattern = os.path.join(RISCV_TESTS_DIR, "isa", f"{category}*.S")
        found = sorted(glob.glob(pattern))
        all_tests.extend(found)
        print(f"[INFO] {category}: found {len(found)} tests")

    if not all_tests:
        print("[ERROR] No test files found!")
        print(f"  Looked in: {os.path.join(RISCV_TESTS_DIR, 'isa')}")
        sys.exit(1)

    # compile each test
    success = 0
    failed = 0
    for asm_file in all_tests:
        test_name = os.path.splitext(os.path.basename(asm_file))[0]
        print()
        if compile_test(prefix, test_name, asm_file, include_dirs):
            success += 1
        else:
            failed += 1

    # summary
    print("\n" + "=" * 60)
    print(f"Compilation complete: {success} succeeded, {failed} failed")
    print(f"Hex files directory: {OUTPUT_DIR}")
    print("=" * 60)

    # generate run script
    generate_run_script()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    main()
