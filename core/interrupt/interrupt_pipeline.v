// rtl/interrupt/interrupt_pipeline.v - 中断流水线控制器 (单Bank版, TVLSI基线)
`timescale 1ns/1ps

// ============================================================================
// 模块: interrupt_pipeline
// 功能: 中断流水线控制器 + 单Bank影子寄存器管理
//
// 本模块负责:
//   1. 中断检测与接受 (恒定2周期延迟)
//   2. PC选择与CSR更新 (mepc, mcause, mstatus)
//   3. 流水线冲刷控制
//   4. shadow_save / shadow_restore 脉冲生成 (单Bank, 无嵌套)
//
// 注意: 本文件为 TVLSI 论文基线版本 (FX-RV32, 单Bank影子寄存器, 不支持中断嵌套)。
//       多Bank嵌套版本 (FX-RV32-X) 在 FX-RV32_Custom 目录维护。
// ============================================================================
module interrupt_pipeline #(
    parameter SHADOW_EN    = 1      // 影子寄存器使能
) (
    // ========== 系统接口 ==========
    input  wire        clk_i,
    input  wire        rst_n_i,

    // ========== 来自各级流水线的PC和状态信息 ==========
    input  wire [31:0] if_pc_i,
    input  wire        id_valid_i,
    input  wire [31:0] id_pc_i,
    input  wire        ex_valid_i,
    input  wire [31:0] ex_pc_i,
    input  wire        ex_branch_taken_i,
    input  wire        ex_jump_taken_i,
    input  wire        mem_valid_i,
    input  wire [31:0] mem_pc_i,
    input  wire        mem_mem_re_i,
    input  wire        mem_mem_we_i,
    input  wire        bus_ready_i,
    input  wire        wb_valid_i,
    input  wire [4:0]  wb_rd_addr_i,
    input  wire        wb_reg_we_i,
    input  wire        id_ex_mret,

    // ========== 中断请求 ==========
    input  wire        intr_pending_i,
    input  wire [31:0] intr_cause_i,

    // ========== CSR当前值 ==========
    input  wire [31:0] mstatus_i,

    // ========== 对CSR的更新信号 ==========
    output reg         csr_mepc_we_o,
    output reg  [31:0] csr_mepc_data_o,
    output reg         csr_mcause_we_o,
    output reg  [31:0] csr_mcause_data_o,
    output reg         csr_mstatus_we_o,
    output reg  [31:0] csr_mstatus_data_o,

    // ========== 影子寄存器控制输出 (单Bank) ==========
    output reg         shadow_save_o,        // 保存x1-x31到影子寄存器
    output reg         shadow_restore_o,     // 从影子寄存器恢复x1-x31

    // ========== 对流水线的控制 ==========
    output reg         interrupt_taken_o,
    output reg         interrupt_flush_o,
    output reg  [31:0] interrupt_pc_o,

    // ========== 组合逻辑输出 ==========
    output wire        intr_take_now_o,       // PC提前跳转
    output wire        interrupt_accepted_o,  // 中断已接受
    output wire        interrupt_processing_o // 正在服务中断

);

// ========== 中断条件判断 ==========
wire interrupt_condition_all = intr_pending_i;

// ========== 中断PC选择 ==========
reg [31:0] interrupt_pc;

always @(*) begin
    if (mem_valid_i && (mem_pc_i != 32'b0)) begin
        if (mem_mem_re_i && !bus_ready_i)
            interrupt_pc = mem_pc_i;
        else
            interrupt_pc = mem_pc_i + 4;
    end else if (ex_valid_i && (ex_pc_i != 32'b0)) begin
        interrupt_pc = ex_pc_i;
    end else if (id_valid_i && (id_pc_i != 32'b0)) begin
        interrupt_pc = id_pc_i;
    end else begin
        interrupt_pc = if_pc_i;
    end
end

// ========== 状态寄存器 ==========
reg         interrupt_accepted;
reg         interrupt_processed;
reg [31:0]  saved_interrupt_pc;
reg [31:0]  saved_interrupt_cause;

// ========== 组合逻辑中断接受指示 ==========
// 单Bank设计: 仅在无中断服务时接受 (不支持嵌套抢占)
wire can_accept = !interrupt_accepted && !interrupt_processed;
wire intr_take_now = interrupt_condition_all && can_accept;
assign intr_take_now_o        = intr_take_now;
assign interrupt_accepted_o   = interrupt_accepted;
assign interrupt_processing_o = interrupt_processed;

always @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
        interrupt_accepted    <= 1'b0;
        interrupt_processed   <= 1'b0;
        saved_interrupt_pc    <= 32'b0;
        saved_interrupt_cause <= 32'b0;

        csr_mepc_we_o         <= 1'b0;
        csr_mepc_data_o       <= 32'b0;
        csr_mcause_we_o       <= 1'b0;
        csr_mcause_data_o     <= 32'b0;
        csr_mstatus_we_o      <= 1'b0;
        csr_mstatus_data_o    <= 32'b0;
        shadow_save_o         <= 1'b0;
        shadow_restore_o      <= 1'b0;
        interrupt_taken_o     <= 1'b0;
        interrupt_flush_o     <= 1'b0;
        interrupt_pc_o        <= 32'b0;

    end else begin
        // 默认值 (脉冲信号清零)
        csr_mepc_we_o     <= 1'b0;
        csr_mcause_we_o   <= 1'b0;
        csr_mstatus_we_o  <= 1'b0;
        shadow_save_o     <= 1'b0;
        shadow_restore_o  <= 1'b0;
        interrupt_taken_o <= 1'b0;
        interrupt_flush_o <= 1'b0;

        // ========== 中断进入 ==========
        if (interrupt_condition_all && can_accept) begin
            interrupt_accepted    <= 1'b1;
            saved_interrupt_pc    <= interrupt_pc;
            saved_interrupt_cause <= intr_cause_i;

            // 写入 CSR (mepc, mcause, mstatus)
            csr_mepc_we_o   <= 1'b1;
            csr_mepc_data_o <= interrupt_pc;
            csr_mcause_we_o <= 1'b1;
            csr_mcause_data_o <= intr_cause_i;
            csr_mstatus_we_o <= 1'b1;
            csr_mstatus_data_o <= {
                mstatus_i[31:13],
                2'b11,              // MPP = Machine
                mstatus_i[10:8],
                mstatus_i[3],       // MPIE = old MIE
                mstatus_i[6:4],
                1'b0,               // MIE = 0
                mstatus_i[2:0]
            };

            // 流水线控制
            interrupt_taken_o <= 1'b1;
            interrupt_flush_o <= 1'b1;
            interrupt_pc_o    <= interrupt_pc;

            // 单Bank影子保存: 中断接受时并行触发
            if (SHADOW_EN)
                shadow_save_o <= 1'b1;

        end
        // ========== 中断接受完成 ==========
        else if (interrupt_accepted) begin
            interrupt_accepted  <= 1'b0;
            interrupt_processed <= 1'b1;
        end
        // ========== MRET: 中断退出 ==========
        else if (id_ex_mret) begin
            interrupt_processed <= 1'b0;

            // 恢复mstatus
            csr_mstatus_we_o <= 1'b1;
            csr_mstatus_data_o <= {mstatus_i[31:13],
                                   2'b00,             // MPP <= 00
                                   mstatus_i[10:8],
                                   mstatus_i[7],      // MPIE <= 1
                                   mstatus_i[6:4],
                                   mstatus_i[7],      // MIE <= old MPIE
                                   mstatus_i[2:0]
                                  };

            // 单Bank影子恢复
            if (SHADOW_EN)
                shadow_restore_o <= 1'b1;
        end
    end
end

endmodule
