analyze -format verilog -lib WORK [list     $rtl_root/soc/top/soc_top.v     $rtl_root/core/core_top.v     $rtl_root/soc/mem/inst_rom.v     $rtl_root/soc/mem/data_ram.v     $rtl_root/soc/bus/bus_arbiter.v     $rtl_root/soc/periph/gpio.v     $rtl_root/soc/periph/timer.v     $rtl_root/soc/periph/uart_ctrl.v     $rtl_root/soc/periph/uart_tx.v     $rtl_root/soc/periph/spi_master.v     $rtl_root/soc/periph/i2c_master.v     $rtl_root/core/ifu/ifu_top.v     $rtl_root/core/ifu/pc_reg.v     $rtl_root/core/id/ctrl.v     $rtl_root/core/id/decoder.v     $rtl_root/core/id/id_top.v     $rtl_root/core/id/imm_gen.v     $rtl_root/core/id/regfile.v     $rtl_root/core/exu/alu.v     $rtl_root/core/exu/branch.v     $rtl_root/core/exu/ex_top.v     $rtl_root/core/mem/mem_top.v     $rtl_root/core/mem/mem_ctrl.v     $rtl_root/core/wbu/wb_mux.v     $rtl_root/core/wbu/wb_top.v     $rtl_root/core/hazard/forwarding_unit.v     $rtl_root/core/hazard/hazard_unit.v     $rtl_root/core/pipeline/if_id_reg.v     $rtl_root/core/pipeline/id_ex_reg.v     $rtl_root/core/pipeline/ex_mem_reg.v     $rtl_root/core/pipeline/mem_wb_reg.v     $rtl_root/core/csr/csr_regfile.v     $rtl_root/core/csr/csr_instructions.v     $rtl_root/core/interrupt/interrupt_controller.v     $rtl_root/core/interrupt/interrupt_pipeline.v
]
Error:  /home/yifengxin/FX-RV32/core/core_top.v:432: Instantiation u_ex_top has mixed ordered and named port connections (VER-147)
Error:  /home/yifengxin/FX-RV32/core/id/id_top.v:66: Syntax error at or near token ')'. (VER-294)
Error:  /home/yifengxin/FX-RV32/core/pipeline/id_ex_reg.v:76: Syntax error at or near token '('. (VER-294)
*** Presto compilation terminated with 3 errors. ***
0
# ▒▒▒
elaborate soc_top
  Loading link library 'scc55nll_hd_rvt_tt_v1p2_25c_basic'
  Loading link library 'gtech'
Elaborated 1 design.
Current design is now 'soc_top'.
Error:  Module 'core_top' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'core_top' cannot be found for elaboration. (ELAB-357)
Error:  Module 'inst_rom' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'inst_rom' cannot be found for elaboration. (ELAB-357)
Error:  Module 'data_ram' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'data_ram' cannot be found for elaboration. (ELAB-357)
Error:  Module 'bus_arbiter' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'bus_arbiter' cannot be found for elaboration. (ELAB-357)
Error:  Module 'uart_ctrl' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'uart_ctrl' cannot be found for elaboration. (ELAB-357)
Error:  Module 'gpio' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'gpio' cannot be found for elaboration. (ELAB-357)
Error:  Module 'timer' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'timer' cannot be found for elaboration. (ELAB-357)
Error:  Module 'spi_master' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'spi_master' cannot be found for elaboration. (ELAB-357)
Error:  Module 'i2c_master' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'i2c_master' cannot be found for elaboration. (ELAB-357)
1
current_design soc_top
Current design is 'soc_top'.
{soc_top}
link

  Linking design 'soc_top'
  Using the following designs and libraries:
  --------------------------------------------------------------------------
  soc_top                     /home/yifengxin/asic_synth/FX-RV32/soc_top.db
  scc55nll_hd_rvt_tt_v1p2_25c_basic (library) /home/yifengxin/smic55_rvt_lib/synopsys/1.2v/scc55nll_hd_rvt_tt_v1p2_25c_basic.db

Error:  Module 'core_top' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'inst_rom' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'data_ram' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'bus_arbiter' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'uart_ctrl' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'gpio' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'timer' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'spi_master' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Error:  Module 'i2c_master' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Warning: Design mismatches were detected by the linker and resolved in order to link the current design. You can use the report_design_mismatch command to see a list of design mismatches. (DESH-017)
1
check_design

****************************************
check_design summary:
Version:     Q-2019.12-SP5-3
Date:        Mon May 25 18:59:10 2026
****************************************

                   Name                                            Total
--------------------------------------------------------------------------------
Inputs/Outputs                                                     32
    Unconnected ports (LINT-28)                                    32

Designs                                                             8
    Black box (LINT-55)                                             8
--------------------------------------------------------------------------------

Warning: Design mismatches were detected by the linker and resolved in order to link the current design. You can use the report_design_mismatch command to see a list of design mismatches. (DESH-017)
1
# ʱ▒▒Լ▒▒200MHz▒▒
create_clock -name clk -period 5 [get_ports clk_i]
1
set_input_delay -clock clk -max 2 [all_inputs]
1
set_output_delay -clock clk -max 2 [all_outputs]
1
# ▒▒▒▒Ż▒
set compile_optimize_netlist_area true
true
# ▒▒▒▒
compile
Warning: Command 'compile' is translated to command 'compile_exploration'.  (DESH-014)
Error:  Module 'inst_rom' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Alib files are up-to-date.
Information: Running DC Explorer in default mode (physical mode disabled.) (OPT-1475)

============================================================================
| DesignWare Building Block Library  |         Version         | Available |
============================================================================
| Basic DW Building Blocks           | Q-2019.12-DWBB_201912.5 |     *     |
| Licensed DW Building Blocks        | Q-2019.12-DWBB_201912.5 |     *     |
============================================================================




Error:  Module 'inst_rom' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Loaded alib file './alib-52/scc55nll_hd_rvt_tt_v1p2_25c_basic.db.alib'

  Beginning Pass 1 Mapping
  ------------------------
  Processing 'soc_top'
Error:  Module 'inst_rom' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***

  Beginning Mapping Optimizations  (Exploration)
  -------------------------------
  Exploration Synthesis (Phase 1)
  Exploration Synthesis (Phase 2)
  Exploration Synthesis (Phase 3)
  Exploration Synthesis (Phase 4)
  Exploration Synthesis (Phase 5)
  Exploration Synthesis (Phase 6)
Error:  Module 'inst_rom' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
1
# ▒▒▒
write -f ddc -hierarchy -output soc_top.ddc
Error:  Module 'inst_rom' cannot be found for elaboration. (ELAB-357)
*** Presto compilation terminated with 1 errors. ***
Writing ddc file 'soc_top.ddc'.
1
write -f verilog -hierarchy -output soc_top_netlist.v
Writing verilog file '/home/yifengxin/asic_synth/FX-RV32/soc_top_netlist.v'.
1
write_sdf -version 2.1 soc_top.sdf
1
write_sdc soc_top.sdc
1
# ▒▒▒▒
redirect -file area.rpt {report_area}
redirect -file power.rpt {report_power}
redirect -file timing.rpt {report_timing}
redirect -file area_hier.rpt {report_area -hierarchy}
