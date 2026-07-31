# setup lib path
set lib_path /home/yifengxin/smic55_rvt_lib/synopsys/1.2v
set search_path [list . $lib_path]
set target_library scc55nll_hd_rvt_tt_v1p2_25c_basic.db
set link_library [list * $target_library]
set symbol_library {}

set rtl_root /home/yifengxin/FX-RV32

# analyze RTL files
analyze -format verilog -lib WORK [list \
    $rtl_root/soc/top/soc_top.v \
    $rtl_root/core/core_top.v \
    $rtl_root/soc/mem/inst_rom.v \
    $rtl_root/soc/mem/data_ram.v \
    $rtl_root/soc/bus/bus_arbiter.v \
    $rtl_root/soc/periph/gpio.v \
    $rtl_root/soc/periph/timer.v \
    $rtl_root/soc/periph/uart_ctrl.v \
    $rtl_root/soc/periph/uart_tx.v \
    $rtl_root/soc/periph/uart_rx.v \
    $rtl_root/soc/periph/spi_master.v \
    $rtl_root/soc/periph/spi_flash_ctrl.v \
    $rtl_root/soc/periph/i2c_master.v \
    $rtl_root/core/ifu/ifu_top.v \
    $rtl_root/core/ifu/pc_reg.v \
    $rtl_root/core/id/ctrl.v \
    $rtl_root/core/id/decoder.v \
    $rtl_root/core/id/id_top.v \
    $rtl_root/core/id/imm_gen.v \
    $rtl_root/core/id/regfile.v \
    $rtl_root/core/exu/alu.v \
    $rtl_root/core/exu/branch.v \
    $rtl_root/core/exu/ex_top.v \
    $rtl_root/core/mem/mem_top.v \
    $rtl_root/core/mem/mem_ctrl.v \
    $rtl_root/core/wbu/wb_mux.v \
    $rtl_root/core/wbu/wb_top.v \
    $rtl_root/core/hazard/forwarding_unit.v \
    $rtl_root/core/hazard/hazard_unit.v \
    $rtl_root/core/pipeline/if_id_reg.v \
    $rtl_root/core/pipeline/id_ex_reg.v \
    $rtl_root/core/pipeline/ex_mem_reg.v \
    $rtl_root/core/pipeline/mem_wb_reg.v \
    $rtl_root/core/csr/csr_regfile.v \
    $rtl_root/core/csr/csr_instructions.v \
    $rtl_root/core/interrupt/interrupt_controller.v \
    $rtl_root/core/interrupt/interrupt_pipeline.v
]

# elaborate
elaborate soc_top
current_design soc_top
link
check_design

# timing constraints (200MHz, period=5ns)
create_clock -name clk -period 5 [get_ports clk_i]
set_input_delay -clock clk -max 2 [all_inputs]
set_output_delay -clock clk -max 2 [all_outputs]

# area optimization
set compile_optimize_netlist_area true

# ========== Power Analysis: MUST be enabled BEFORE compile ==========
set power_enable_analysis TRUE
# NOTE (2026-07-31 功耗差异调查结论):
# 本 DC (Q-2019.12-SP5-3) 无 set_power_default_toggle_rate /
# set_power_default_static_probability (CMD-005), 旧流程 (2026-06-10) 同样报错被忽略
# (见 FX-RV32_Custom/syn/banks_1_synth.log:1329-1332)。
# 因此与旧数据可比的测量条件 = 无任何 activity 注解, 保持与旧流程一致, 不加
# set_switching_activity, 否则数据活动传播会使功耗虚高 30-40%。

# synthesis
compile

# save outputs
write -f ddc -hierarchy -output soc_top.ddc
write -f verilog -hierarchy -output soc_top_netlist.v
write_sdf -version 2.1 soc_top.sdf
write_sdc soc_top.sdc

# reports
redirect -file area_en0.rpt {report_area}
redirect -file power_en0.rpt {report_power}
redirect -file timing_en0.rpt {report_timing}
redirect -file area_hier_en0.rpt {report_area -hierarchy}
redirect -file power_hier_en0.rpt {report_power -hierarchy}
redirect -file power_cell_en0.rpt {report_power -cell -hierarchy}

exit
