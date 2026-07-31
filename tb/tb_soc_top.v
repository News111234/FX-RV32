// tb/tb_soc_top.v - SoC 顶层仿真测试平台
`timescale 1ns/1ps

module tb_soc_top;

// 时钟和复位
reg clk;
reg rst_n;

// 顶层端口连接
wire uart_tx;
wire [31:0] gpio_io;
wire spi_sclk;
wire spi_mosi;
wire spi_miso;
wire spi_cs;
wire i2c_sda;
wire i2c_scl;
wire [31:0] debug_if_pc;
wire [31:0] debug_if_instr;
wire [31:0] perf_total_time;
wire [31:0] perf_score;
wire [31:0] perf_iterations;
wire [31:0] perf_data_size;
wire [31:0] perf_seedcrc;
wire [31:0] perf_total_errors;

// 实例化 SoC 顶层
soc_top u_soc_top (
    .clk_i          (clk),
    .rst_n_i        (rst_n),

    .uart_tx_o      (uart_tx),

    .gpio_io        (gpio_io),

    .spi_sclk_o     (spi_sclk),
    .spi_mosi_o     (spi_mosi),
    .spi_miso_i     (spi_miso),
    .spi_cs_o       (spi_cs),

    .i2c_sda_io     (i2c_sda),
    .i2c_scl_io     (i2c_scl),

    .debug_if_pc    (debug_if_pc),
    .debug_if_instr (debug_if_instr),

    .perf_total_time   (perf_total_time),
    .perf_score        (perf_score),
    .perf_iterations   (perf_iterations),
    .perf_data_size    (perf_data_size),
    .perf_seedcrc      (perf_seedcrc),
    .perf_total_errors (perf_total_errors)
);

// 时钟生成 (200MHz)
initial begin
    clk = 0;
    forever #2.5 clk = ~clk;
end

// 复位生成
initial begin
    rst_n = 0;
    #100;
    rst_n = 1;
end

// 增加周期计数和结果检测
reg [31:0] cycle_cnt;
reg result_done;

initial begin
    cycle_cnt = 0;
    result_done = 0;
end

always @(posedge clk) begin
    if (!rst_n) begin
        cycle_cnt <= 0;
        result_done <= 0;
    end else if (!result_done) begin
        cycle_cnt <= cycle_cnt + 1;
    end
end

// 监控 tohost 地址（0x80001000，RISC-V 官方测试标准）
// RISC-V 测试约定：写 1 表示 PASS，写其他值表示 FAIL
always @(posedge clk) begin
    if (u_soc_top.core_bus_we && 
        u_soc_top.core_bus_addr == 32'h80001000) begin
        if (u_soc_top.core_bus_wdata == 32'h1)
            $display("=== TEST PASSED at cycle %0d ===", cycle_cnt);
        else
            $display("=== TEST FAILED code=%0d at cycle %0d ===", 
                     u_soc_top.core_bus_wdata, cycle_cnt);
        $finish;
    end
end
// 监控 0x100~0x14F (results 区域) 的写入
always @(posedge clk) begin
    if (u_soc_top.core_bus_we && 
        (u_soc_top.core_bus_addr >= 32'h00000140) &&
        (u_soc_top.core_bus_addr <= 32'h0000018F)) begin
        $display("Results[%0d] = %0d", 
                 (u_soc_top.core_bus_addr - 32'h00000140) >> 2,
                 u_soc_top.core_bus_wdata);
    end
end
// // 可选：添加超时保护
// initial begin
//     #20000000;  // 20ms 超时
//     $finish;
// end

// 性能指标监控（无需显示，但可以在 final 块中输出到文件，这里保留注释）
// 我们不在 testbench 中使用 $display，避免干扰。
// 如果需要记录性能指标，可以在 final 块中写入文件，但此处省略。

endmodule