// rtl/id/regfile.v (单Bank版, TVLSI基线)
`timescale 1ns/1ps

// ============================================================================
// 模块: regfile
// 功能: 通用寄存器堆，包含32个32位寄存器 (x0-x31) + 单组影子寄存器
// 特性:
//   1. 两个读端口，一个写端口
//   2. x0寄存器硬连线为0，写入无效
//   3. 写数据内部转发(读地址等于写地址且写使能有效时，直接返回写入数据)
//   4. 单Bank影子寄存器: 中断时自动保存x1-x31, MRET时自动恢复
//
// 注意: 本文件为 TVLSI 论文基线版本 (FX-RV32, 单Bank, 不支持中断嵌套)。
//       多Bank嵌套版本 (FX-RV32-X) 在 FX-RV32_Custom 目录维护。
// ============================================================================
module regfile #(
    parameter SHADOW_EN    = 1      // 影子寄存器使能: 1=开启, 0=关闭
) (
    // ========== 系统接口 ==========
    input  wire        clk,           // 时钟信号
    input  wire        rst_n,         // 复位信号 (低电平有效)

    // ========== 读端口1 ==========
    input  wire [4:0]  raddr1_i,      // 读地址1
    output reg  [31:0] rdata1_o,      // 读数据1

    // ========== 读端口2 ==========
    input  wire [4:0]  raddr2_i,      // 读地址2
    output reg  [31:0] rdata2_o,      // 读数据2

    // ========== 写端口 ==========
    input  wire        we_i,          // 写使能
    input  wire [4:0]  waddr_i,       // 写地址
    input  wire [31:0] wdata_i,       // 写数据

    // ========== 影子寄存器控制 (单Bank) ==========
    input  wire        shadow_save_i,     // 保存x1-x31到影子寄存器
    input  wire        shadow_restore_i   // 从影子寄存器恢复x1-x31

);

reg [31:0] registers [0:31];
// 单Bank影子寄存器: shadow[reg_index]
reg [31:0] shadow_registers [1:31];
integer i;

// 读逻辑 - 组合电路
always @(*) begin
    // 读端口1
    if (raddr1_i == 5'b0) begin
        rdata1_o = 32'b0;  // x0始终为0
    end else if (we_i && (raddr1_i == waddr_i)) begin
        rdata1_o = wdata_i;  // 转发:直接返回当前写入的数据值
    end else begin
        rdata1_o = registers[raddr1_i];
    end

    // 读端口2
    if (raddr2_i == 5'b0) begin
        rdata2_o = 32'b0;
    end else if (we_i && (raddr2_i == waddr_i)) begin
        rdata2_o = wdata_i;  // 转发:直接返回当前写入的数据值
    end else begin
        rdata2_o = registers[raddr2_i];
    end
end

// 写逻辑 (含影子寄存器操作)
always @(posedge clk) begin
    if (!rst_n) begin
        for (i = 0; i < 32; i = i + 1) begin
            registers[i] <= 32'b0;
        end
        for (i = 1; i < 32; i = i + 1) begin
            shadow_registers[i] <= 32'b0;
        end
    end else begin
        // 影子恢复 (最高优先级): 从影子寄存器恢复x1-x31
        if (SHADOW_EN && shadow_restore_i) begin
            for (i = 1; i < 32; i = i + 1) begin
                registers[i] <= shadow_registers[i];
            end
        end else begin
            // 正常写操作 (优先级高于影子保存,确保WB写入先完成)
            if (we_i && waddr_i != 5'b0) begin
                registers[waddr_i] <= wdata_i;
            end

            // 影子保存 (最低优先级): 将当前x1-x31保存到影子寄存器
            if (SHADOW_EN && shadow_save_i) begin
                for (i = 1; i < 32; i = i + 1) begin
                    shadow_registers[i] <= registers[i];
                end
            end
        end
    end
end

endmodule
