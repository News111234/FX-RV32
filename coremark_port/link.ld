/*
 * FX-RV32 CoreMark Linker Script
 *
 * Harvard architecture: inst_rom and data_ram share address space
 * but are separate physical memories.
 *
 * .text and .rodata go to inst_rom (loaded from program.hex).
 * .data/.sdata are placed after .rodata — their LMA is in ROM
 * (for initial values), VMA is at the same address but writes
 * go to data_ram.  Since .bss startup zeroing overwrites the
 * data_ram region anyway, we rely on the fact that data_ram
 * at simulation init is X (unknown), and .bss zeroing handles
 * zero-init data.  Runtime-initialized globals use portable_init().
 *
 * Memory layout:
 *   0x00000000 ─┬── .text (code)
 *               ├── .rodata
 *               ├── .sdata / .data (initial values in ROM; VMA overlay)
 *   0x00005000 ─┼── .bss  (zeroed by startup)
 *   0x00010000 ─┴── stack top
 */

ENTRY(_start)

MEMORY
{
    MEM (rwx) : ORIGIN = 0x00000000, LENGTH = 64K
}

SECTIONS
{
    .text : {
        *(.text._start)
        *(.text*)
        *(.init)
        *(.fini)
    } > MEM

    .rodata : {
        *(.rodata*)
        *(.srodata*)
    } > MEM

    /* Small data: keep it (don't discard) */
    .sdata : {
        *(.sdata*)
    } > MEM

    .data : {
        *(.data*)
    } > MEM

    /* .bss placed at 0x5000 (above ROM image, within data_ram area) */
    .bss 0x5000 (NOLOAD) : {
        _bss_start = .;
        *(.sbss*)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _bss_end = .;
    } > MEM

    _stack_end = 0x00010000;

    /DISCARD/ : {
        *(.comment)
        *(.riscv.attributes)
        *(.eh_frame)
    }
}
