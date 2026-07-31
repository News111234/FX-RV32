# FX-RV32 CoreMark Startup Code (crt0.S)
# Bare-metal initialization for RISC-V RV32I
#
# 1. Set up stack pointer
# 2. Zero .bss section
# 3. Call main()
# 4. After main returns, call write_results() to signal completion

.section .text._start
.globl _start

_start:
    # 1. Initialize stack pointer
    la   sp, _stack_end

    # 2. Zero .bss section
    la   t0, _bss_start
    la   t2, _bss_end
    beq  t0, t2, 2f
1:
    sw   zero, 0(t0)
    addi t0, t0, 4
    bltu t0, t2, 1b
2:

    # 3. Call main(argc=0, argv=0)
    li   a0, 0
    li   a1, 0
    call main

    # 4. Write results to memory-mapped addresses (detected by core_top_sim)
    call write_results

    # 5. Loop forever
    j    .

.globl _exit
_exit:
    j    .
