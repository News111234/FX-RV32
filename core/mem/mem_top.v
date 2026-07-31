// core/mem/mem_top.v — 访存阶段顶层模块 (FPGA 专用, 带总线接口)
`timescale 1ns/1ps

// ============================================================================
// 模块: mem_top
// 功能: 访存阶段顶层模块 (FPGA 专用)，连接系统总线仲裁器
// 描述:
//   本模块是流水线访存阶段的核心，功能包括:
//   1. 接收来自 EX/MEM 流水线寄存器的内存访问请求
//   2. 将请求直接转发给系统总线仲裁器 (bus_arbiter)
//   3. 接收总线返回的读取数据
//   4. 将 PC+4 和写回控制信号透传给 MEM/WB 流水线寄存器
//   本模块不包含实际的 RAM，内存访问通过总线进行。
// ============================================================================
module mem_top (
    // ========== 系统接口 ==========
    input  wire        clk_i,              // 时钟信号
    input  wire        rst_n_i,            // 复位信号 (低电平有效)

    // ========== 来自 EX/MEM 流水线寄存器的输入 ==========
    input  wire [31:0] alu_result_i,       // ALU 结果 (内存地址)
    input  wire [31:0] wdata_i,            // 写数据
    input  wire        mem_we_i,           // 内存写使能
    input  wire        mem_re_i,           // 内存读使能
    input  wire [2:0]  mem_width_i,        // 访问宽度
    input  wire [31:0] pc_plus4_i,         // PC+4 (用于 JAL 返回地址)
    input  wire        reg_we_i,           // 寄存器写使能
    input  wire [1:0]  wb_sel_i,           // 写回选择
    input  wire [4:0]  rd_addr_i,          // 目标寄存器地址

    // ========== 送入 MEM/WB 流水线寄存器 ==========
    output wire [31:0] pc_plus4_o,         // PC+4 (透传)
    output wire        reg_we_o,           // 寄存器写使能 (透传)
    output wire [1:0]  wb_sel_o,           // 写回选择 (透传)
    output wire [4:0]  rd_addr_o,          // 目标寄存器地址 (透传)

    // ========== 总线接口 (连接到 bus_arbiter) ==========
    output wire        bus_re_o,           // 总线读请求
    output wire        bus_we_o,           // 总线写请求
    output wire [31:0] bus_addr_o,         // 总线地址
    output wire [31:0] bus_wdata_o,        // 总线写数据
    output wire [2:0]  bus_width_o,        // 总线访问宽度
    input  wire [31:0] bus_rdata_i,        // 总线读数据
    input  wire        bus_ready_i,        // 总线就绪信号

    // ========== 异常输出 ==========
    output wire        mem_exception_o,        // 内存异常标志 (misalign || error)
    output wire [31:0] mem_exception_addr_o,   // 异常地址 (= alu_result, 用于 mtval)
    output wire        mem_misalign_flag_o,    // 未对齐异常 (mcause=4/6)
    output wire        mem_range_err_o,        // 范围越界 (mcause=5/7)
    output wire        mem_exception_we_o      // 是否为 store 指令 (区分 mcause)
);

// ========== mem_ctrl 实例化 — 地址对齐检查 + 地址范围检查 ==========
wire [31:0] mem_addr;
wire [31:0] mem_wdata;
wire        mem_we_checked;
wire        mem_re_checked;
wire [2:0]  mem_width;
wire        mem_misalign;
wire        mem_error;

mem_ctrl u_mem_ctrl (
    .alu_result_i  (alu_result_i),
    .wdata_i       (wdata_i),
    .mem_we_i      (mem_we_i),
    .mem_re_i      (mem_re_i),
    .mem_width_i   (mem_width_i),
    .mem_addr_o    (mem_addr),
    .mem_wdata_o   (mem_wdata),
    .mem_we_o      (mem_we_checked),
    .mem_re_o      (mem_re_checked),
    .mem_width_o   (mem_width),
    .mem_misalign_o(mem_misalign),
    .mem_error_o   (mem_error)
);

// 总线信号 — 经过 mem_ctrl 对齐/范围检查后发出
assign bus_re_o    = mem_re_checked || mem_we_checked;
assign bus_we_o    = mem_we_checked;
assign bus_addr_o  = mem_addr;
assign bus_wdata_o = mem_wdata;
assign bus_width_o = mem_width;

// 控制信号透传到下一阶段
assign pc_plus4_o      = pc_plus4_i;
assign reg_we_o        = reg_we_i;
assign wb_sel_o        = wb_sel_i;
assign rd_addr_o       = rd_addr_i;
assign mem_exception_o      = mem_misalign || mem_error;
assign mem_exception_addr_o = alu_result_i;        // 异常地址 → mtval
assign mem_misalign_flag_o  = mem_misalign;        // mcause=4(load)/6(store)
assign mem_range_err_o      = mem_error;            // mcause=5(load)/7(store)
assign mem_exception_we_o   = mem_we_i;             // 1=store, 0=load

endmodule
