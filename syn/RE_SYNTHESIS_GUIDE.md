# FX-RV32 TVLSI 论文重综合操作指南

> **背景**：论文 RTL 新增了 `mipr`/`meipr` 两个可编程中断优先级 CSR（~0.4 kGE），现有面积/功耗数据（24.9/32.4 kGE）基于旧 RTL 综合。需要重新综合并更新论文全部数字。
> **目标**：跑通两个配置的综合，收集报告，替换论文中的旧数据。

---

## 0. 代码状态确认（重要）

| 目录 | 角色 | 状态 |
|------|------|------|
| `/home/yifengxin/FX-RV32` | **TVLSI 论文代码（单 Bank）** | 已同步最新：含 mipr/meipr，**无 bank_controller**，**SHADOW_BANKS 默认=1**（单 Bank 影子寄存器，与论文一致） |
| `/home/yifengxin/FX-RV32_Custom` | RTAS 论文代码（多 Bank 嵌套） | **不要动**。bank_controller 只在 Custom 里有，SHADOW_BANKS=4 |

**只允许综合 `/home/yifengxin/FX-RV32`。** 不要碰 Custom 目录。

**基线适配说明**（Windows 端已完成，服务器同步时确认）：
- **`SHADOW_BANKS` 参数已彻底删除**（soc_top / core_top / id_top / regfile / interrupt_pipeline 五处），不是"默认=1"，是"不存在"
- `regfile.v`：单组 `shadow_registers[1:31]` = 31×32 = 992 FF（论文 Table 中的 7.46 kGE 对应此结构），无 bank_ptr 索引
- `interrupt_pipeline.v`：无 bank_ptr 管理、无嵌套输入（allow_nesting/bank_full/tail_chain/degradation 全部删除），`can_accept = !accepted && !processed`（不支持抢占）
- `bank_controller.v` 模块：基线中无例化、无引用（文件保留在仓库但未使用）
- 验证命令：`grep -rn "SHADOW_BANKS\|bank_ptr\|bank_controller" /home/yifengxin/FX-RV32/core/ /home/yifengxin/FX-RV32/soc/` 应无任何输出

---

## 1. 前提检查（逐条确认）

```bash
# a. 代码路径
ls /home/yifengxin/FX-RV32/core/core_top.v

# b. SMIC 库
ls /home/yifengxin/smic55_rvt_lib/synopsys/1.2v/scc55nll_hd_rvt_tt_v1p2_25c_basic.db

# c. DC 环境
ls /opt/eda/synopsys/syn.bashrc
```

三条都 OK 才能继续。

---

## 2. 跑综合（两个配置）

### 配置 A：SHADOW_EN=1（Shadow 版，论文的 32.4 kGE）

```bash
source /home/yifengxin/FX-RV32/DC_command.txt
cd /home/yifengxin/FX-RV32/syn
mkdir -p run_sh1 && cd run_sh1
dc_shell -f ../run_synth.tcl
```

> 脚本默认 `SHADOW_EN=1`（id_top.v / regfile.v / interrupt_pipeline.v 三处默认值均为 1），**直接跑即可**。

### 配置 B：SHADOW_EN=0（Baseline 版，论文的 24.9 kGE）

`SHADOW_EN` 参数没有透传到顶层，需要**临时修改 3 处 RTL 默认值**：

```bash
# 改 1 → 0（三个文件）
sed -i 's/parameter SHADOW_EN    = 1/parameter SHADOW_EN    = 0/' \
    /home/yifengxin/FX-RV32/core/id/id_top.v
sed -i 's/parameter SHADOW_EN    = 1/parameter SHADOW_EN    = 0/' \
    /home/yifengxin/FX-RV32/core/id/regfile.v
sed -i 's/parameter SHADOW_EN    = 1/parameter SHADOW_EN    = 0/' \
    /home/yifengxin/FX-RV32/core/interrupt/interrupt_pipeline.v

# 综合
source /home/yifengxin/FX-RV32/DC_command.txt
cd /home/yifengxin/FX-RV32/syn
mkdir -p run_en0 && cd run_en0
dc_shell -f ../run_synth.tcl

# 跑完恢复 1 → 1（必须！）
sed -i 's/parameter SHADOW_EN    = 0/parameter SHADOW_EN    = 1/' \
    /home/yifengxin/FX-RV32/core/id/id_top.v /home/yifengxin/FX-RV32/core/id/regfile.v \
    /home/yifengxin/FX-RV32/core/interrupt/interrupt_pipeline.v

# 验证已恢复
grep -n "parameter SHADOW_EN" /home/yifengxin/FX-RV32/core/id/id_top.v
```

> **警告：配置 B 跑完后必须把 3 处参数改回 1**，否则后续所有仿真/综合都变成无影子模式。

---

## 3. 收集结果

综合后每个 run 目录下生成：

| 文件 | 内容 |
|------|------|
| `area_en0.rpt` | 总面积（核心数字：kGE / μm²） |
| `area_hier_en0.rpt` | **逐模块面积分解**（论文 Table II/III 的数据源） |
| `power_en0.rpt` / `power_hier_en0.rpt` | 功耗（论文 Table II/III） |
| `timing_en0.rpt` | 关键路径（论文的 4.89/4.88 ns） |
| `soc_top_netlist.v` / `soc_top.ddc` | 网表备份 |

> 注意：脚本输出的文件名固定带 `en0` 后缀（历史命名），**跑 SHADOW_EN=1 时实际是 shadow 配置的数据**，不要被文件名误导。

**记录以下数字：**
- baseline（SHADOW_EN=0）：core_top 总面积、5 个组件面积、总功耗、关键路径
- shadow（SHADOW_EN=1）：同上

换算：`1 GE ≈ 1.12 μm²`，`kGE = μm² / 1.12 / 1000`

---

## 4. 论文更新清单（新数据出来后）

论文：`bare_jrnl_new_sample4.tex`（Windows 端）

| 位置 | 当前值 | 说明 |
|------|--------|------|
| Abstract（第 42 行） | 24.9 kGE (32.4 kGE) | 更新 |
| Introduction 贡献点 1（第 85 行） | 24.9 kGE | 更新 |
| Introduction 贡献点 3（第 96-97 行） | 28.6 kGE 对比、13% 更小 | 重算百分比 |
| Section III（第 166-168 行） | 24.9 / 32.4 / 7.46 kGE | 更新（7.46 kGE = shadow 增量，重算） |
| Section III 模块列表（第 225 行） | 中断控制器描述 | 已含 mipr，确认无需改 |
| Table II（area_en0） | 5 组件 + 24.89 kGE + 4.020 mW | **逐格替换** |
| Table III（area_sh1） | 5 组件 + 32.37 kGE + 5.838 mW | **逐格替换** |
| Section IV-B（第 529-552 行） | 27,879 / 36,252 μm² 等 | 全部替换 |
| Fig.10 面积柱状图 | 5 根柱子 | 重新生成（python/plot/Area/） |
| Fig.11 综合结果图 | 面积 + 关键路径 | 重新生成（python/plot/Synthesis/） |
| Conclusion（第 626-627 行） | 24.9 / 32.4 kGE | 更新 |

**预期变化**：mipr + meipr 两个 32-bit CSR 新增 ~0.4 kGE（CSR register file 组件 +0.2~0.3，Interrupt system +0.1~0.2）。关键路径预计不变或 +0.01~0.05 ns（比较器在非关键路径上）。

**修改原则**：
1. 面积数字、组件百分比、功耗、关键路径——全部以新报告为准
2. 百分比对比（13% 更小、+30%、2.9/3.8 kGE 差值）——用新数字重算
3. 不要改架构描述文字（架构没变，只是加了寄存器）

---

## 5. 注意事项

1. **不要动 `/home/yifengxin/FX-RV32_Custom`**（RTAS 多 Bank 代码）
2. 综合后 `git status` 检查：`id_top.v`/`regfile.v`/`interrupt_pipeline.v` 不应有未恢复的改动（SHADOW_EN 必须是 1）
3. 跑综合前确认 `run_synth.tcl` 是 LF 行尾（Windows 编辑会变 CRLF，`file run_synth.tcl` 检查；如果是 CRLF，`sed -i 's/\r$//' run_synth.tcl`）
4. 报告文件名 `en0` 后缀是历史遗留，不代表配置——自己做好 run_en0/run_sh1 目录区分
5. 如果 `elaborate soc_top` 报缺模块错误，对照脚本 analyze 列表（应含 uart_rx.v、spi_flash_ctrl.v，**不含** bank_controller.v）
