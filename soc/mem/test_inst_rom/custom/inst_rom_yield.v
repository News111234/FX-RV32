// rtl/ifu/inst_rom_hello.v - I2C测试程序
`timescale 1ns/1ps
(* DONT_TOUCH = "true" *)
module inst_rom (
    input  wire [31:0] addr_i,
    output reg  [31:0] data_o
);

reg [31:0] rom [0:511];
integer i;

initial begin
    // 初始化所有指令为nop
    for (i = 0; i <= 511; i = i + 1) begin
        rom[i] = 32'h00000013; // nop: addi x0, x0, 0
    end

$readmemh("program.hex", rom);


end

always @(*) begin
    if (addr_i[31:2] <= 511) begin
        data_o = rom[addr_i[31:2]];
    end else begin
        data_o = 32'h00000013; // nop
    end
end

// ============================================================================
// YIELD 指令 (RTOS 任务让出)
// ============================================================================
// 编码格式: custom-0 类 R-type
//   [31:25]=funct7=7'b0000001, [24:20]=rs2=5'b0, [19:15]=rs1=5'b0,
//   [14:12]=funct3=3'b000, [11:7]=rd=5'b0, [6:0]=opcode=7'b0001011
//   机器码: 32'h0200000B
//
// 功能: 触发软件中断 (MSI)，用于 RTOS 任务切换

// ============================================================================
// RTOS 任务切换测试程序 (程序入口: 0x0000_0000)
// ============================================================================
// 说明: 使用 YIELD 指令主动让出CPU，触发软件中断进行任务切换。
//       任务0和任务1各自运行，通过 YIELD 互相切换。
//
// 内存布局:
//   0x0000_0000 - 0x0000_00FF: 启动代码和任务0
//   0x0000_0100 - 0x0000_01FF: 任务1
//   0x0000_0200 - 0x0000_02FF: 中断/异常向量表 (mtvec)
//
// 任务0 (约 0x0000_0000):
//   lui   sp, 0x00010        # 栈指针指向 0x00010000
//   lui   t0, 0x00002        # mtvec = 0x00000200 (中断向量表)
//   csrw  mtvec, t0
//   lui   t0, 0x00000        # 初始化计数器
//   addi  s0, x0, 10         # 循环10次
// loop0:
//   addi  t0, t0, 1          # 任务0: 计数器加1
//   addi  s0, s0, -1         # 递减
//   bne   s0, x0, loop0      # 循环
//   yield                    # 让出CPU -> 切换到任务1 (0x0200000B)
//   j     loop0
//
// 任务1 (约 0x0000_0100):
//   addi  s1, x0, 10         # 循环10次
// loop1:
//   addi  t1, t1, 1          # 任务1: 计数器加1
//   addi  s1, s1, -1         # 递减
//   bne   s1, x0, loop1      # 循环
//   yield                    # 让出CPU -> 切换到任务0 (0x0200000B)
//   j     loop1
//
// 中断向量表 (mtvec = 0x0000_0200):
//   csrrw  sp, mscratch, sp   # 交换 sp 和 mscratch
//   ... 保存上下文 ...
//   ... 切换任务 ...
//   mret
//
// ============================================================================
// YIELD 指令在汇编中的使用:
//   汇编: yield
//   机器码: 0x0200000B (可直接写入 program.hex)
// ============================================================================
// 示例: 直接编写 program.hex 内容 (小端格式):
//   0200000B   # yield 指令

endmodule


//TCL
// add wave -position end  sim:/tb_soc_top/clk
// add wave -position end  sim:/tb_soc_top/debug_if_instr
// add wave -position end  sim:/tb_soc_top/debug_if_pc
// add wave -position end  sim:/tb_soc_top/u_soc_top/u_core/u_id_top/debug_x15_o
// add wave -position 3  sim:/tb_soc_top/u_soc_top/u_core/u_id_top/debug_x10_o
// add wave -position end  sim:/tb_soc_top/u_soc_top/u_data_ram/mem

// sp	x2	栈指针 (Stack Pointer)
// ra	x1	返回地址 (Return Address)
// a0 ~ a7	x10 ~ x17	函数参数 / 返回值 (Arguments/Return values)
// s0 / fp	x8	帧指针 (Frame Pointer) 或保存寄存器
// s1	x9	保存寄存器 (Callee-saved)
// a4	x14	第 5 个参数（通用）
// a5	x15	第 6 个参数（通用）
