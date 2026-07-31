// soc/periph/tohost.v - RISC-V 测试套件 tohost 接口
`timescale 1ns/1ps

// ============================================================================
// 模块: tohost
// 功能: 提供 tohost 寄存器用于 RISC-V 官方测试套件的结果输出
// 描述:
//   该模块实现了一个简单的寄存器外设，用于捕获 CPU 写入 tohost 地址的数据。
//   RISC-V 官方测试套件通过向 tohost 写入结果值来报告测试状态:
//     - 写入 1:   测试通过 (PASS)
//     写入其他值: 测试失败 (FAIL)，值为失败代码
//   testbench 监控 tohost_reg 的值来判断测试结果。
//
// 地址映射: 0x8000_1000 (tohost)
//           0x8000_1004 (fromhost) - 仅用于占位，暂无实际用途
// ============================================================================
module tohost (
    // ========== 系统接口 ==========
    input  wire        clk_i,          // 时钟信号
    input  wire        rst_n_i,        // 复位信号 (低电平有效)

    // ========== 总线接口 ==========
    input  wire        we_i,           // 写使能
    input  wire        re_i,           // 读使能
    input  wire [31:0] addr_i,         // 访问地址
    input  wire [31:0] wdata_i,        // 写数据
    output reg  [31:0] rdata_o         // 读数据
);

// tohost 寄存器
reg [31:0] tohost_reg;
reg [31:0] fromhost_reg;

// 写操作
always @(posedge clk_i) begin
    if (!rst_n_i) begin
        tohost_reg    <= 32'b0;
        fromhost_reg  <= 32'b0;
    end else if (we_i) begin
        if (addr_i[3:2] == 2'b00) begin
            tohost_reg <= wdata_i;
        end else if (addr_i[3:2] == 2'b01) begin
            fromhost_reg <= wdata_i;
        end
    end
end

// 读操作
always @(*) begin
    rdata_o = 32'b0;
    if (re_i) begin
        if (addr_i[3:2] == 2'b00) begin
            rdata_o = tohost_reg;
        end else if (addr_i[3:2] == 2'b01) begin
            rdata_o = fromhost_reg;
        end
    end
end

endmodule