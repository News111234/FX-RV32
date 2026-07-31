// rtl/interrupt/interrupt_controller.v — 中断控制器 (含优先级抢占)
`timescale 1ns/1ps

// ============================================================================
// 模块: interrupt_controller
// 功能: 中断控制器，含优先级编码、向量地址计算、抢占判定
//
// 中断优先级(由高到低): MEI(ID=11) > MTI(ID=7) > MSI(ID=3)
// 支持两种中断处理模式:
//   - 直接模式 (mtvec.MODE=00): 所有中断跳转至同一地址
//   - 向量模式 (mtvec.MODE=01): 按中断ID跳转至 base + cause*4

//省流:接收中断输入信号,根据已编码好的优先级决定intr_cause的更新顺序,拉起中断有效信号-
//-如果中断有效信号被拉起则根据mtvec的低2位决定中断地址的计算方式
// ============================================================================
module interrupt_controller (
    // ========== 系统接口 ==========
    input  wire        clk_i,             // 时钟信号
    input  wire        rst_n_i,           // 复位信号 (低电平有效)

    // ========== 外部中断源 ==========
    input  wire        intr_software_i,   // 软件中断
    input  wire        intr_timer_i,      // 定时器中断
    input  wire        intr_external_i,    // 外部中断 (GPIO | SPI | I2C OR-ed in core_top)

    // ========== CSR接口 ==========
    input  wire [31:0] mie_i,             // 中断使能寄存器
    input  wire [31:0] mip_i,             // 中断待处理寄存器
    input  wire [31:0] mstatus_i,         // 机器状态寄存器
    input  wire [31:0] mtvec_i,           // 中断向量基址寄存器
    input  wire [31:0] mipr_i,            // 中断优先级寄存器

    // ========== 中断控制器输出 ==========
    output wire        intr_pending_o,     // 有中断等待 (需要响应)
    output wire [31:0] intr_cause_o,       // 中断原因 (最高位=1表示中断)
    output wire [31:0] intr_handler_addr_o,// 中断处理程序入口地址

    // ========== 优先级输出 (给抢占判定) ==========
    output wire [3:0]  current_priority_o, // 当前服务中断优先级
    output wire [3:0]  new_priority_o      // 新中断优先级

);

// ========== 中断优先级编码 (可编程优先级) ==========
// 中断ID: 3=MSI, 7=MTI, 11=MEI
// 每个中断源的优先级由 mipr CSR 的 4-bit 字段独立配置 (0=禁用)
// 默认值 mipr[11:8]=11(MEI), mipr[7:4]=7(MTI), mipr[3:0]=3(MSI), 等效于原硬编码
// 同优先级时按 MEI > MTI > MSI 的固定顺序 tie-break
// 外部中断在 core_top 层由 GPIO|SPI|I2C OR 而成

wire [3:0] mei_prio = mipr_i[11:8];
wire [3:0] mti_prio = mipr_i[7:4];
wire [3:0] msi_prio = mipr_i[3:0];

wire meip = mie_i[11] && (mip_i[11] || intr_external_i);
wire mtip = mie_i[7]  && (mip_i[7]  || intr_timer_i);
wire msip = mie_i[3]  && (mip_i[3]  || intr_software_i);

// 只有优先级 > 0 的中断源才参与仲裁
wire mei_valid = meip && (mei_prio > 4'd0);
wire mti_valid = mtip && (mti_prio > 4'd0);
wire msi_valid = msip && (msi_prio > 4'd0);

// 全局中断使能 (M-mode)
wire global_ie = mstatus_i[3];

// 中断优先级编码 (含优先级值)
reg [31:0] intr_cause;
reg        intr_valid;
reg [3:0]  new_prio;         // 新中断的优先级值

always @(*) begin
    intr_valid = 1'b0;
    intr_cause = 32'b0;
    new_prio   = 4'd0;

    if (global_ie) begin
        // 比较器链: 找优先级最高的 pending 中断, 同优先级时 MEI > MTI > MSI
        if (mei_valid && (!mti_valid || mei_prio >= mti_prio)
                      && (!msi_valid || mei_prio >= msi_prio)) begin
            intr_valid = 1'b1;
            intr_cause = {1'b1, 31'd11};
            new_prio   = mei_prio;
        end else if (mti_valid && (!msi_valid || mti_prio >= msi_prio)) begin
            intr_valid = 1'b1;
            intr_cause = {1'b1, 31'd7};
            new_prio   = mti_prio;
        end else if (msi_valid) begin
            intr_valid = 1'b1;
            intr_cause = {1'b1, 31'd3};
            new_prio   = msi_prio;
        end
    end
end

// ========== 中断处理程序地址计算 ==========
wire [1:0] mtvec_mode = mtvec_i[1:0];
wire [31:0] mtvec_base = {mtvec_i[31:2], 2'b0};

reg [31:0] handler_addr;

always @(*) begin
    if (intr_valid) begin
        if (mtvec_mode == 2'b01)
            handler_addr = mtvec_base + (intr_cause[4:0] << 2);  // 向量模式
        else
            handler_addr = mtvec_base;                             // 直接模式
    end else begin
        handler_addr = 32'b0;
    end
end

// ========== 当前服务优先级跟踪 ==========
// current_priority: 0=无中断活跃, 非0=对应中断ID的优先级值
reg [3:0] current_priority;

always @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
        current_priority <= 4'd0;
    end else begin
        // 简单跟踪: intr_pending上升沿时更新
        // 提供当前/新中断优先级值
        if (intr_pending_o && current_priority == 4'd0) begin
            current_priority <= new_prio;  // 首次中断
        end else if (!intr_pending_o) begin
            current_priority <= 4'd0; // 无中断pending
        end
    end
end

assign intr_pending_o       = intr_valid;
assign intr_cause_o         = intr_cause;
assign intr_handler_addr_o  = handler_addr;

assign new_priority_o       = new_prio;
assign current_priority_o   = current_priority;

endmodule
