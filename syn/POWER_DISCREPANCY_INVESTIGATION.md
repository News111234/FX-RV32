# 功耗异常抬高的质疑与处理任务

> **给服务器上 Claude 的任务**：重综合后功耗比论文旧数据高了 39%，我们怀疑是测量方法被改导致的，需要你验证并处理。

---

## ✅ 调查结论（2026-07-31 完成，已处理）

**用户的质疑成立：功耗差异是测量方法被改导致的，与设计无关。现已用与旧流程一致的测量条件重测，功耗回到论文量级。**

### 结论 1：`set_power_default_toggle_rate` 确实不存在（CMD-005 属实）

- 三次独立验证（dc_shell 交互式）：两个命令均报 `Error: unknown command (CMD-005)`
- `all_nets`、`report_switching_activity`、`remove_switching_activity` 等 Power Compiler 命令同样缺失（CMD-080/CMD-005）——本 DC 安装（Q-2019.12-SP5-3）无 Power Compiler 命令集，banner 显示 Power Compiler (TM) 但命令未注册
- **铁证**：旧流程 log `FX-RV32_Custom/syn/banks_1_synth.log:1329-1332`：
  ```
  set_power_default_toggle_rate 0.1
  Error: unknown command 'set_power_default_toggle_rate' (CMD-005)
  set_power_default_static_probability 0.5
  Error: unknown command 'set_power_default_static_probability' (CMD-005)
  ```
  即 **2026-06-10 旧报告的流程同样报 CMD-005、命令同样被忽略**（error 不中断流程，报告照常生成）。"旧报告在此版本下正常生成 → 命令有效"的推断不成立：报告生成 ≠ 命令执行成功。

### 结论 2：旧数据（4.020/5.838 mW）的真实测量条件 = 无任何注解

旧报告特征证实：
- 旧报告警告为 PWR-414/415（unannotated primary inputs / sequential cell outputs）→ 无 per-net 注解
- 旧报告 Net Switching Power 仅 52.8 μW（≈0）→ 数据路径无活动，功耗 ≈ 纯寄存器时钟功耗

### 结论 3：新数据虚高 35-39% 的机理 = 我首次误加了 `set_switching_activity -toggle_rate 0.1 [all_inputs]`

输入端口注解 0.1 后，活动经零延迟仿真传播进内部逻辑，数据路径功耗从 ≈0 变成有活动 → u_core 5.585/7.832 mW（虚高）。面积完全相同的 regfile 功耗却涨 30-35% 正是此因。

### 处理结果：无注解重测（与旧流程一致），功耗回落到论文量级

综合脚本已改为无注解（`run_synth.tcl` 中已注明），两配置重新综合：

| 指标 | 论文旧值 | 无注解重测 | 差异 |
|------|---------|-----------|------|
| baseline u_core | 4.020 mW | **4.246 mW** | +5.6%（面积 +8%，合理） |
| shadow u_core | 5.838 mW | **6.064 mW** | +3.9% |
| baseline regfile | 1.925 mW | **1.927 mW** | +0.1%（几乎完全一致） |
| shadow regfile | 3.740 mW | **3.742 mW** | +0.05% |

- 面积/关键路径不变（203,989/212,334 μm²，5.00 ns）
- 已更新 `reports/baseline/`、`reports/shadow/` 的 power 报告及 `SYNTHESIS_RESULTS.md`
- 弃用的注解版结果备份于 `reports_annotated_0.1/`（不用于论文）

### 遗留建议

- 论文功耗数字（4.020/5.838 → 4.246/6.064 mW）可直接采用，测量条件一致
- 若后续想要"含数据活动"的功耗（更贴近实际工作负载），需提供 VCD/SAIF 文件做基于仿真的功耗分析，或换带 Power Compiler 授权的 DC/PT 环境——那是另一套方法，与论文旧数据不可比，需在论文中注明

---

## 1. 问题背景

重综合（2026-07-31）产出的功耗数据与论文旧数据差异过大：

| 指标 | 论文旧值 | 新综合值 | 差异 |
|------|---------|---------|------|
| baseline (SHADOW_EN=0) u_core 功耗 | 4.020 mW | 5.585 mW | **+39%** |
| shadow (SHADOW_EN=1) u_core 功耗 | 5.838 mW | 7.832 mW | **+34%** |

面积只增加了 +2.25 kGE（+8%），功耗却涨了近 40%，**不成比例**。

## 2. 我们的质疑：测量方法被改了

**旧数据（论文 4.020/5.838 mW）**：
- 综合脚本使用：
  ```
  set_power_default_toggle_rate 0.1
  set_power_default_static_probability 0.5
  ```
- DC 版本：Q-2019.12-SP5-3（旧报告头部明确显示）
- 旧报告（2026-06-10）在此版本下**正常生成**，说明这两个命令当时是有效的

**新数据（5.585/7.832 mW）**：
- 本次综合时，`SYNTHESIS_RESULTS.md` 记录了："`set_power_default_toggle_rate`/`set_power_default_static_probability` 在本 DC 版本不存在（CMD-005），已替换为 `set_switching_activity`（数据 0.1、时钟 0.5）"
- **我们怀疑这个判断有误**：同一个 DC 版本（Q-2019.12-SP5-3）在 6 月 10 日能正常执行这两个命令，没理由 7 月 31 日就"不存在"了

**铁证**（面积完全一致、功耗却暴涨）：

| 组件 | 旧面积 | 新面积 | 旧功耗 | 新功耗 |
|------|--------|--------|--------|--------|
| regfile (SHADOW_EN=0) | 11.01 kGE | 11.01 kGE（一致） | 1.925 mW | 2.604 mW（**+35%**） |
| regfile (SHADOW_EN=1) | 18.47 kGE | 18.47 kGE（一致） | 3.740 mW | 4.847 mW（**+30%**） |

面积完全相同的 regfile，功耗涨了 30-35%——**纯测量方法差异，与设计无关**。

另外，新报告大量出现 PWR-419 警告：
```
Warning: The net '...' is annotated with a toggle rate but no static probability.
A default static probability value of 0.500000 is used. (PWR-419)
```
说明 `set_switching_activity` 只注解了 toggle rate、未配 static probability，内部 net 活动靠传播——与 `set_power_default_toggle_rate`（所有未注解 net 统一默认 0.1 toggle + 0.5 static）的估算逻辑完全不同，结果不可比。

## 3. 需要你做的事

### 步骤 1：验证命令是否真的不存在

在 dc_shell 交互式执行：

```tcl
dc_shell> set_power_default_toggle_rate 0.1
```

- **不报错** → 命令存在，之前的 CMD-005 判断是误判（可能当时脚本有别的错误）
- **报 CMD-005** → 真不存在，跳到步骤 3

### 步骤 2：命令可用 → 用原始测量方法重跑功耗

把 `run_synth.tcl` 的功耗部分恢复为原始命令（当前 Windows 版脚本就是正确的，参考如下）：

```tcl
# ========== Power Analysis: MUST be enabled BEFORE compile ==========
set power_enable_analysis TRUE
set_power_default_toggle_rate 0.1
set_power_default_static_probability 0.5
```

删除/注释掉本次新增的 `set_switching_activity` 行。

**不需要重新综合**——只需要在已综合的设计上重新做功耗分析即可（更快）：

```tcl
# 方法 A: 在 dc_shell 中读回已综合的 ddc
read_ddc run_en0/soc_top.ddc
set_power_default_toggle_rate 0.1
set_power_default_static_probability 0.5
redirect -file reports/baseline/power.rpt {report_power}
redirect -file reports/baseline/power_hier.rpt {report_power -hierarchy}
redirect -file reports/baseline/power_cell.rpt {report_power -cell -hierarchy}
# shadow 同理: read_ddc run_sh1/soc_top.ddc
```

两个配置（SHADOW_EN=0 和 SHADOW_EN=1）都重跑，更新 `reports/baseline/` 和 `reports/shadow/` 下的三个 power 报告文件，并同步更新 `SYNTHESIS_RESULTS.md` 的功耗数据。

### 步骤 3：命令真不存在 → 接受新值

如果 `set_power_default_toggle_rate` 确实不存在（CMD-005 属实），则：
- 保留 `set_switching_activity` 方案
- 在 `SYNTHESIS_RESULTS.md` 中**明确标注**功耗测量方法与论文旧数据不可比（方法差异 +30-35%），论文将采用新值
- 不要静默使用新功耗数字

## 4. 预期结果

- 命令可用（大概率）：功耗应回落到 **~4.2-4.5 mW（baseline）/ ~6.1-6.5 mW（shadow）** 量级（设计本身 +8% 面积对应 +10-15% 功耗是合理的）
- 命令不可用：接受 5.585/7.832 mW，但论文中需注明测量方法

## 5. 参考文件

| 文件 | 内容 |
|------|------|
| `run_synth.tcl`（Windows 版，未改） | 原始功耗命令在第 66-70 行 |
| `reports/baseline/power*.rpt`、`reports/shadow/power*.rpt` | 本次新报告（含 PWR-419 警告） |
| `FX-RV32_Custom/syn/report/power/power_en0.rpt`（旧，参考） | 6 月 10 日旧报告，同 DC 版本，无 PWR-419 警告 |
| `SYNTHESIS_RESULTS.md` | 本次汇总（第 3 节记录了测量条件） |
