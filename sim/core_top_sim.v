// sim/core_top_sim.v - Simulation wrapper for Verilator
// Wraps soc_top with tohost pass/fail detection and cycle timeout
`timescale 1ns/1ps

module core_top_sim (
    input  wire        clk_i,
    input  wire        rst_n_i,

    output wire        uart_tx_o,

    // debug
    output wire [31:0] debug_if_pc,
    output wire [31:0] debug_if_instr,

    // perf counters
    output wire [31:0] perf_total_time,
    output wire [31:0] perf_score,
    output wire [31:0] perf_iterations,
    output wire [31:0] perf_data_size,
    output wire [31:0] perf_seedcrc,
    output wire [31:0] perf_total_errors,

    // tohost result (for C++ harness)
    output wire        tohost_done,
    output wire        tohost_pass
);

// tohost monitoring signals
wire        tohost_we;
wire [31:0] tohost_wdata;

// peripheral tie-offs
wire [31:0] gpio_out;
wire [31:0] gpio_oe;

soc_top u_soc_top (
    .clk_i            (clk_i),
    .rst_n_i          (rst_n_i),
    .uart_tx_o        (uart_tx_o),
    .gpio_io          (),
    .gpio_in          (32'b0),
    .gpio_out         (gpio_out),
    .gpio_oe          (gpio_oe),
    .spi_sclk_o       (),
    .spi_mosi_o       (),
    .spi_miso_i       (1'b0),
    .spi_cs_o         (),
    .i2c_sda_io       (),
    .i2c_scl_io       (),
    .debug_if_pc      (debug_if_pc),
    .debug_if_instr   (debug_if_instr),
    .perf_total_time  (perf_total_time),
    .perf_score       (perf_score),
    .perf_iterations  (perf_iterations),
    .perf_data_size   (perf_data_size),
    .perf_seedcrc     (perf_seedcrc),
    .perf_total_errors(perf_total_errors),
    .tohost_we_o      (tohost_we),
    .tohost_wdata_o   (tohost_wdata)
);

// ==========================================================================
// tohost pass/fail detection
// RISC-V test convention: write 1 = PASS, any other value = FAIL
// ==========================================================================
reg tohost_done_r;
reg tohost_pass_r;

always @(posedge clk_i) begin
    if (!rst_n_i) begin
        tohost_done_r <= 1'b0;
        tohost_pass_r <= 1'b0;
    end else if (tohost_we && !tohost_done_r) begin
        tohost_done_r <= 1'b1;
        tohost_pass_r <= (tohost_wdata == 32'h1);
        if (tohost_wdata == 32'h1)
            $display("=== RISCV-TEST PASSED ===");
        else
            $display("=== RISCV-TEST FAILED (code=0x%08h) ===", tohost_wdata);
        $finish;
    end
end

// ==========================================================================
// simulation timeout (about 10M cycles at 200MHz = 50ms real time)
// ==========================================================================
reg [23:0] cycle_cnt;

always @(posedge clk_i) begin
    if (!rst_n_i)
        cycle_cnt <= 24'b0;
    else if (!tohost_done_r)
        cycle_cnt <= cycle_cnt + 1;
end

always @(posedge clk_i) begin
    if (cycle_cnt == 24'd10_000_000) begin
        $display("=== TIMEOUT: no tohost write after 10M cycles ===");
        $finish;
    end
end

assign tohost_done = tohost_done_r;
assign tohost_pass = tohost_pass_r;

endmodule
