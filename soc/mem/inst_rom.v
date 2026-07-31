// soc/mem/inst_rom.v — 指令 ROM (组合读, 零延迟)
//
// 程序加载: 由 testbench 在 time=0 通过层次化后门写入加载到 rom[] 数组。
// 不设 initial NOP 填充——避免与 testbench 后门写入的执行顺序冲突。
// 仿真中 ROM 输出在 testbench 写入后立即生效, CPU 复位释放前数据已就绪。
//
// 注意: 论文 (bare_jrnl_new_sample4.tex, Table I) 标称默认 INST_DEPTH = 1024 (4KB)。
//       本文件默认值取 512 以加速综合/仿真; 综合报告取 core_top 面积, 不含本 ROM,
//       故调小不影响论文面积数据。
`timescale 1ns/1ps
(* DONT_TOUCH = "true" *)
module inst_rom #(
    parameter INST_DEPTH = 512            // 512 × 32-bit words = 2KB (论文标称默认 1024/4KB)
) (
    input  wire [31:0] addr_i,           // PC 地址 (字节地址)
    output wire [31:0] data_o             // 组合逻辑输出 (零延迟)
);

reg [31:0] rom [0:INST_DEPTH-1];

integer i;

initial begin
    // 初始化所有指令为nop
    for (i = 0; i <= 511; i = i + 1) begin
        rom[i] = 32'h00000013; // nop: addi x0, x0, 0
    end
rom[   0] = 32'h100010b7;  // lui    x1, 0x10001000
rom[   1] = 32'h00100193;  // li     x3, 1
rom[   2] = 32'h0030a223;  // sw     x3, 4(x1)
rom[   3] = 32'hfff00113;  // addi   x2, x0, -1
rom[   4] = 32'h0020a023;  // sw     x2, 0(x1)
rom[   5] = 32'h0000a023;  // sw     x0, 0(x1)
rom[   6] = 32'h0020a023;  // sw     x2, 0(x1)
rom[   7] = 32'h0000a023;  // sw     x0, 0(x1)
rom[   8] = 32'h0020a023;  // sw     x2, 0(x1)
rom[   9] = 32'h0000a023;  // sw     x0, 0(x1)
rom[   10] = 32'h0020a023;  // sw     x2, 0(x1)
rom[   11] = 32'h0000a023;  // sw     x0, 0(x1)
rom[   12] = 32'h0020a023;  // sw     x2, 0(x1)
rom[   13] = 32'h0000a023;  // sw     x0, 0(x1)
rom[   14] = 32'h0020a023;  // sw     x2, 0(x1)
rom[   15] = 32'h0000a023;  // sw     x0, 0(x1)
rom[   16] = 32'h0020a023;  // sw     x2, 0(x1)
rom[   17] = 32'h0000a023;  // sw     x0, 0(x1)
rom[   18] = 32'h0020a023;  // sw     x2, 0(x1)
rom[   19] = 32'h0000a023;  // sw     x0, 0(x1)
end

// 组合读 — 零延迟, 地址变化立即反映到输出
assign data_o = (addr_i[31:2] < INST_DEPTH) ? rom[addr_i[31:2]] : 32'h00000013;

endmodule
