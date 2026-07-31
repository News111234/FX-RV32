# test2_fib.S ¨C µÝ¹éì³²¨ÄÇÆõ£¬ÖØ¸´20´Î
.section .text
.globl _start

_start:
    li sp, 0x200 
    li   x5, 20
    li   x6, 0x140             # results

fib_loop:
    csrr x22, mcycle
    li   a0, 8
    call fib
    csrr x23, mcycle
    sub  x24, x23, x22
    sw   x24, 0(x6)
    addi x6, x6, 4
    addi x5, x5, -1
    bnez x5, fib_loop

    li   x10, 0xFC
    sw   x0, 0(x10)
    j    .

# µÝ¹éº¯Êý fib
fib:
    addi sp, sp, -16
    sw   ra, 12(sp)
    sw   a0, 8(sp)
    li   t0, 2
    bge  a0, t0, recurse
    li   a0, 1
    addi sp, sp, 16
    ret

recurse:
    addi a0, a0, -1
    call fib
    sw   a0, 4(sp)
    lw   a0, 8(sp)
    addi a0, a0, -2
    call fib
    lw   t0, 4(sp)
    add  a0, a0, t0
    lw   ra, 12(sp)
    addi sp, sp, 16
    ret