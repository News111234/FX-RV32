# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

FX-RV32 is a 5-stage pipelined RISC-V CPU implementing RV32IM (base integer + M extension) with interrupt support and peripherals (UART, GPIO, Timer, SPI, I2C). It targets Xilinx FPGA (200 MHz) and is verified via Verilator simulation.

## Architecture

**Pipeline**: IF → ID → EX → MEM → WB, with full forwarding (MEM→EX, WB→EX) and hazard detection (stall on load-use, flush on branch/jump/interrupt).

**Harvard memory**: Instruction fetch goes to `inst_rom` (16KB at `0x00000000`). Load/store goes through `bus_arbiter` to `data_ram` (64KB at `0x00000000`) and MMIO peripherals. The overlapping address ranges are safe — they use physically separate buses.

**Reset vector**: PC starts at `0x00000000` (`pc_reg.v:29`). This must match the linker script's `_start` location.

**Bus arbiter address decode** (see `soc/bus/bus_arbiter.v` for full table):
- RAM: `0x0000_0000`
- UART: `0x1000_0000`, GPIO: `0x1000_1000`, Timer: `0x1000_2000`, SPI: `0x1000_3000`, I2C: `0x1000_4000`
- TOHOST: `0x8000_1000` (RISC-V test pass/fail reporting)

**Interrupt pipeline** (`core/interrupt/interrupt_pipeline.v`): Waits for all in-flight instructions to complete before taking an interrupt. Saves mepc/mcause/mstatus via CSR writes during the interrupt injection cycle. `interrupt_controller.v` prioritizes and encodes interrupt sources.

**CSR dual-write**: `csr_instructions.v` handles explicit CSR instructions. `interrupt_pipeline.v` writes mepc/mcause/mstatus during interrupt entry. Both feed into `csr_regfile.v` which arbitrates the two write sources.

**Two top-level modules exist**:
- `soc_top.v` — simulation/ASIC, single-ended clock, debug/perf ports, tohost debug outputs
- `soc_top_fpga.v` — FPGA target, differential clock (LVDS), LED outputs, different port list

## Build and test commands

### Verilator simulation (primary flow)

```bash
# Run a riscv-test
cp mytests/test_hex/rv32ui-p-add.hex sim/program.hex
cd sim/
make clean
make run RVTEST=1       # RVTEST=1 enables $readmemh in inst_rom
```

The `RVTEST` make variable passes `-DRVTEST` to Verilator, which gates `$readmemh("program.hex", rom)` in `inst_rom.v`. Without it, the ROM fills with NOPs.

### Compile and run official riscv-tests

```bash
cd mytests/
python3 run_riscv_tests.py         # compiles all rv32ui-p + rv32um-p tests
cd test_hex/
./run_test.sh rv32ui-p-add         # run a single test
```

The script requires `riscv32-unknown-elf-gcc` (falls back to `riscv64-`). It auto-clones `riscv-tests` if the directory is absent.

### Simulation flow for riscv-tests

`sim_main.cpp` instantiates `core_top_sim` which wraps `soc_top`. When a test writes to `0x80001000`:
- Value `1` → `$display("PASSED")` + `$finish`
- Other value → `$display("FAILED code=...")` + `$finish`

A 10M-cycle timeout catches hangs.

### Python assembler

```bash
cd python/
python riscv_arm.py    # interactive assembly-to-hex converter
```

### FPGA build (Vivado)

Project at `vivado/RISCV_TEST/RISCV_TEST.xpr`. Top module: `soc_top_fpga`.

## Key files for common tasks

| Task | Files |
|------|-------|
| Add instruction | `core/id/decoder.v`, `core/exu/alu.v`, `core/exu/branch.v` |
| Add CSR | `core/csr/csr_regfile.v` (register), `core/csr/csr_instructions.v` (read/write logic) |
| Add peripheral | `soc/periph/`, `soc/bus/bus_arbiter.v` (address decode) |
| Pipeline control | `core/hazard/hazard_unit.v` (stall/flush), `core/hazard/forwarding_unit.v` |
| Interrupt routing | `core/interrupt/interrupt_controller.v`, `core/interrupt/interrupt_pipeline.v` |
| Testbench | `tb/tb_soc_top.v` (Modelsim), `sim/core_top_sim.v` + `sim/sim_main.cpp` (Verilator) |

## Linker script and memory layout for tests

`mytests/test.ld` defines:
- `.text` / `.text.init` → `0x00000000` (inst_rom, instruction fetch bus)
- `.data` / `.bss` → `0x00000100` (data_ram, load/store bus)
- `tohost = 0x80001000`, `fromhost = 0x80001004` (MMIO symbols)

Tests are compiled with `-nostdlib -nostartfiles`. Each riscv-test `.S` file defines its own `_start` via the `RVTEST_CODE_BEGIN` macro.

Two include paths are required when compiling riscv-tests:
- `riscv-tests/env/p/` — `riscv_test.h`, `encoding.h`
- `riscv-tests/isa/macros/scalar/` — `test_macros.h`

## Important gotchas

- **Perf counters in `core_top.v` are hardcoded to `32'b0`**. CoreMark simulation works through `tb_core_top.v` reading data_ram directly (`uut.u_data_ram.mem[253]`), not through the perf ports. The `core_top_sim` Verilator flow won't detect CoreMark completion.
- **soc_top vs soc_top_fpga**: When modifying SoC-level features, check both files. They have different port lists and clocking.
- **inst_rom size**: 4096 x 32-bit = 16KB. Tests exceeding this will silently truncate.
- **data_ram** prepopulates `mem[0]` and `mem[1]` with test values in its initial block. This is simulation-only; FPGA synthesis ignores initial blocks.
- **UART write in bus_arbiter** uses a latched + timeout mechanism (5 cycles), not a direct pass-through. This is to handle the UART's flow-control ready signal.
