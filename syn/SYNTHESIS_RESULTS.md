# FX-RV32 重综合结果（新基线，影子寄存器开/关）

> **日期**：2026-07-31
> **工具**：Synopsys DC Q-2019.12-SP5-3（经典版，linux64）
> **工艺**：SMIC 55nm RVT（scc55nll_hd_rvt_tt_v1p2_25c_basic.db，tt_v1p2_25c）
> **约束**：200 MHz（周期 5 ns），输入/输出延时 2 ns
> **RTL 基线**：TVLSI 论文代码，无 `SHADOW_BANKS`/`bank_ptr`/`bank_controller`（单组影子寄存器 `shadow_registers[1:31]` = 992 FF）
> **换算**：`1 GE ≈ 1.12 μm²`，`kGE = μm² / 1.12 / 1000`

---

## 1. 结果总览

| 指标 | Baseline（SHADOW_EN=0） | Shadow（SHADOW_EN=1） | **增量（影子开销）** |
|------|------|------|------|
| **u_core 面积** | 30,396 μm² = **27.14 kGE** | 38,774 μm² = **34.62 kGE** | **+8,378 μm² = +7.48 kGE（+24.6%）** |
| 其中 regfile | 12,328 μm² = 11.01 kGE | 20,689 μm² = 18.47 kGE | +8,361 μm² = +7.47 kGE（+67.8%） |
| soc_top 总面积 | 203,989 μm² = 182.1 kGE | 212,334 μm² = 189.6 kGE | +8,345 μm² = +7.45 kGE（+4.1%） |
| **u_core 功耗** | **4.246 mW** | **6.064 mW** | **+1.818 mW（+42.8%）** |
| 其中 regfile | 1.927 mW | 3.742 mW | +1.815 mW（+94.2%） |
| soc_top 总功耗 | 37.978 mW | 39.795 mW | +1.817 mW（+4.8%） |
| **关键路径** | 5.00 ns（slack 0.00） | 5.00 ns（slack 0.00） | 不变 |

**要点**：
- 影子寄存器开销几乎全部集中在 regfile：面积 +7.47 kGE、功耗 +2.24 mW，对应单组 `shadow_registers[1:31]`（31×32 = 992 FF）及保存/恢复逻辑
- 关键路径不受影子寄存器影响（均为 5.00 ns）
- soc_top 口径被 `u_data_ram`（64KB 寄存器堆化）主导（面积 ~80%、功耗 ~80%），论文表格应使用 **u_core 口径**

## 2. 与论文旧数据对比

| | 论文旧值（旧 RTL） | 本次新值 | 差值 |
|------|------|------|------|
| baseline u_core 面积 | 24.89 kGE | 27.14 kGE | +2.25 kGE |
| shadow u_core 面积 | 32.37 kGE | 34.62 kGE | +2.25 kGE |
| **影子增量** | **7.46 kGE** | **7.48 kGE** | **+0.02 kGE（一致）** |
| baseline u_core 功耗 | 4.020 mW | 4.246 mW | +0.226 mW（+5.6%） |
| shadow u_core 功耗 | 5.838 mW | 6.064 mW | +0.226 mW（+3.9%） |
| 关键路径 | 4.89 / 4.88 ns | 5.00 / 5.00 ns | +0.1 ns |

> **功耗测量方法**：与论文旧数据完全一致（无任何 activity 注解，纯 `set power_enable_analysis TRUE` + DC 默认/传播）。
> 详见 `POWER_DISCREPANCY_INVESTIGATION.md` 的调查结论——`set_power_default_toggle_rate` 在本 DC 从未可用过
> （旧流程 log 同样报 CMD-005），旧数据 4.020/5.838 mW 即为无注解测量结果。

影子增量 7.48 kGE 与论文的 7.46 kGE 基本一致（新基线结构与论文对应）。绝对值比论文大 ~2.25 kGE，可能来源：
1. 新增 `mipr`/`meipr` 两个可编程中断优先级 CSR 及外部中断子优先级仲裁（组合逻辑）
2. DC 版本/优化差异（Q-2019.12 经典版中 `set compile_optimize_netlist_area` 被忽略——该选项仅 DC NXT 支持）

## 3. 功耗分析条件

- `set power_enable_analysis TRUE`，**无任何 switching activity 注解**（无 SAIF/VCD，无 set_switching_activity），纯 DC 默认 + 零延迟传播
- 该条件与论文旧数据（2026-06-10）完全一致——本 DC 无 `set_power_default_toggle_rate`/`set_power_default_static_probability`（CMD-005），旧流程 log（`FX-RV32_Custom/syn/banks_1_synth.log:1329-1332`）同样报此错被忽略，故旧数据亦为无注解测量
- 功耗构成以寄存器时钟功耗为主（Net Switching ≈ 0.06-0.08 mW，Internal ≈ 37-40 mW）
- 附注：若对输入注解 0.1 toggle（早期错误尝试），数据活动传播会使功耗虚高 ~35%（baseline 5.585 / shadow 7.832 mW），与旧数据不可比，该版结果已弃用，备份于 `reports_annotated_0.1/`

## 4. 报告文件位置

| 目录 | 配置 | 内容 |
|------|------|------|
| `syn/run_sh1/` | SHADOW_EN=1（Shadow） | area_en0.rpt / area_hier_en0.rpt / power_en0.rpt / power_hier_en0.rpt / timing_en0.rpt / soc_top_netlist.v / soc_top.ddc |
| `syn/run_en0/` | SHADOW_EN=0（Baseline） | 同上 |

> 注：报告文件名固定带 `en0` 后缀（脚本历史命名），`run_sh1/` 中实际是 shadow 配置数据，勿被文件名误导。

## 5. 本次综合前修复的问题（RTL 同步后复现，已重新修复）

1. **core_top.v VER-956**：`mipr`/`meipr` 先使用（第 46/63 行）后声明（原第 262-263 行），DC PRESTO 不允许 net 先使用后声明，会导致整个设计 black box、面积=0。已把声明移至使用之前（语义不变）。
2. **run_synth.tcl 功耗命令**：`set_power_default_toggle_rate`/`set_power_default_static_probability` 在本 DC 版本不存在（CMD-005，Power Compiler 命令缺失）。首次误改为 `set_switching_activity` 注解导致功耗虚高，经调查（`POWER_DISCREPANCY_INVESTIGATION.md`）确认旧流程同样报 CMD-005，最终改为与旧流程一致的无注解测量。

## 6. 验证记录

- 综合日志无 Error，无 Black Box
- `grep -rn "SHADOW_BANKS\|bank_ptr\|bank_controller" core/ soc/` 无匹配（新基线确认）
- 综合后 3 处 `SHADOW_EN` 已恢复为 1 并验证
