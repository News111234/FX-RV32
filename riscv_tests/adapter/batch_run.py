#!/usr/bin/env python3
"""
Batch runner for deterministic RISC-V tests (FX-RV32).
Runs each test 5 times, measures cycle count via mcycle CSR.
"""
import os, subprocess, glob, time, statistics

HEX_DIR = '/home/yifengxin/FX-RV32_RemoveM_Custom/riscv_tests/hex'
UVM_WIN = r'D:\FX-RV32_Tests\uvm'
UVM_WSL = '/mnt/d/FX-RV32_Tests/uvm'
MSIM = r'D:\modeltech64_10.6e\win64\vsim.exe'
RUN_TCL = 'run_test_fast.tcl'
N_RUNS = 5

def run_one_test(hex_path):
    """Run a single simulation, return cycle count or None."""
    test_hex = os.path.join(UVM_WSL, 'test.hex')
    transcript = os.path.join(UVM_WSL, 'transcript')

    # Copy hex (force overwrite)
    subprocess.run(['cp', '-f', hex_path, test_hex], check=True)

    # Truncate transcript (don't delete—avoids permission issues on WSL mounts)
    try:
        with open(transcript, 'w') as f:
            pass  # truncate
    except:
        pass

    # Run Modelsim via cmd.exe with pre-compiled work library (fast path).
    # Use DEVNULL to avoid pipe buffer deadlocks; transcript is the real output.
    try:
        subprocess.run(
            ['cmd.exe', '/c', f'cd /d {UVM_WIN} && {MSIM} -c -do {RUN_TCL}'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120
        )
    except subprocess.TimeoutExpired:
        return None

    # Small delay to ensure filesystem sync on WSL/DrvFS mounts
    time.sleep(0.1)

    # Parse transcript
    if not os.path.exists(transcript):
        return None

    with open(transcript, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    sv = None  # startup mcycle value (from first store to 0x3F0)
    ev = None  # end mcycle value (from first store to 0x3F4)

    for line in content.split('\n'):
        if 'STORE: [0x000003f0]' in line and sv is None:
            sv = int(line.split('<= ')[-1].strip(), 16)
        if 'STORE: [0x000003f4]' in line and ev is None:
            ev = int(line.split('<= ')[-1].strip(), 16)

    if sv is not None and ev is not None:
        return ev - sv
    return None

def main():
    os.makedirs(os.path.join(HEX_DIR, '..', 'results'), exist_ok=True)

    hex_files = sorted(glob.glob(f'{HEX_DIR}/*.hex'))
    print(f"Running {len(hex_files)} tests x {N_RUNS} iterations each")
    print(f"Start: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}
    start_time = time.time()

    for idx, hex_path in enumerate(hex_files):
        name = os.path.splitext(os.path.basename(hex_path))[0]
        print(f"[{idx+1:2d}/{len(hex_files)}] {name:<12}: ", end='', flush=True)

        cycles_list = []
        for run in range(1, N_RUNS + 1):
            cycles = run_one_test(hex_path)
            if cycles is not None:
                cycles_list.append(cycles)

        if len(cycles_list) == N_RUNS:
            avg = statistics.mean(cycles_list)
            is_det = len(set(cycles_list)) == 1
            stdev = statistics.stdev(cycles_list) if len(cycles_list) > 1 else 0
            results[name] = {
                'cycles': cycles_list[0],
                'avg': avg,
                'stdev': stdev,
                'det': is_det,
                'all_values': cycles_list
            }
            print(f"{cycles_list[0]} cycles (det={'YES' if is_det else 'NO'}, σ={stdev:.1f})")
        else:
            results[name] = None
            print(f"FAILED ({len(cycles_list)}/{N_RUNS})")

    elapsed = time.time() - start_time

    # Summary
    print(f"\n{'='*70}")
    print(f"  FX-RV32 RV32I Deterministic Test Results ({N_RUNS} runs/test)")
    print(f"  Elapsed: {elapsed/60:.1f} min")
    print(f"{'='*70}")
    print(f"  {'Test':<20} {'Cycles':>10} {'Det':>6}")
    print(f"  {'-'*20} {'-'*10} {'-'*6}")

    for name in sorted(results.keys()):
        r = results[name]
        if r:
            print(f"  {name:<20} {r['cycles']:>10} {'YES' if r['det'] else 'NO':>6}")
        else:
            print(f"  {name:<20} {'FAIL':>10}")

    # Save results
    rf = os.path.join(HEX_DIR, '..', 'results', 'deterministic_test_results.txt')
    with open(rf, 'w') as f:
        f.write(f"FX-RV32 RV32I Deterministic Test Results ({N_RUNS} runs/test)\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"AUIPC: not fixed | ECALL1: NOP | ECALL2: J_SELF | ECALL3 (PASS): preserved\n\n")
        f.write(f"{'Test':<25} {'Cycles':>10} {'Avg':>10} {'Stdev':>10} {'Det':>5}\n")
        f.write(f"{'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*5}\n")
        for name in sorted(results.keys()):
            r = results[name]
            if r:
                f.write(f"{name:<25} {r['cycles']:>10} {r['avg']:>10.1f} {r['stdev']:>10.1f} {'YES' if r['det'] else 'NO':>5}\n")
            else:
                f.write(f"{name:<25} {'FAIL':>10}\n")

    print(f"\nResults saved to {rf}")

    # Distinct cycle counts
    counts = {}
    for name, r in results.items():
        if r:
            c = r['cycles']
            counts.setdefault(c, []).append(name)

    print(f"\nDistinct cycle counts: {len(counts)}")
    for c in sorted(counts.keys()):
        print(f"  {c} cycles: {', '.join(counts[c][:6])}{'...' if len(counts[c]) > 6 else ''}")

if __name__ == '__main__':
    main()
