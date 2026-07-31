# CLAUDE_CN.md

FX-RV32 项目中文说明，供 Claude Code 使用。本文档是 `CLAUDE.md` 的中文补充版本。

## 项目概述

FX-RV32 是一个 5 级流水线 RISC-V CPU（仅 RV32I，不含 M 扩展），带外设，采用 Verilog 编写。目标 FPGA：Xilinx Kintex-7 xc7k325tffg900-2，主频 200MHz。作者：易凤欣，北京航空航天大学。

**重要：** Python 汇编器 `riscv_asm7.py` 支持 RV32M/A/F/D/C 伪指令，但硬件仅实现 RV32I。M 扩展指令（mul、div 等）在此核心上无法正确执行。

## 构建与仿真命令

### Verilator 仿真（CoreMark 性能测试）

```bash
cd sim && make          # 编译生成 obj_dir/Vcore_top_sim
cd sim && make run      # 编译 + 运行仿真
cd sim && make clean    # 清理编译产物
```

仿真 C++ 驱动（`sim/sim_main.cpp`）：每 5ns 翻转时钟，复位 100ns，然后运行直到 CoreMark `perf_score != 0` 或 30ms 超时。顶层模块为 `core_top_sim`（CoreMark 性能计数器包装层）。

**`core_top_sim.v` 存在两个版本：**
- `core/core_top_sim.v`（76 行）— 精简版 Verilator 包装器。例化 `soc_top`，通过层次化引用抓取总线写操作来捕获 CoreMark 结果。**这是 sim Makefile 实际使用的文件。**
- `uvm/core_top_sim.txt`（1411 行）— 扩展调试版，引出大量内部信号（各级流水线、寄存器文件、CSR、hazard/forwarding、中断信号）。**仅供参考，不参与任何编译流程。** 如需在 Verilator 中观察更多内部信号，可将此文件中的相关信号合并到 `core/core_top_sim.v`。

**仿真环境准备：** sim Makefile（注意文件名是小写的 `makefile`）通过 `find -L rtl -name "*.v"` 搜索 RTL 源文件。`sim/rtl -> ..` 软链接应该已经存在，验证：
```bash
ls -l sim/rtl   # 应显示指向 .. 的软链接
```
如缺失，创建：`cd sim && ln -s .. rtl`（Linux/WSL）。

**生成测试程序（program.hex）：**

```bash
# 推荐：使用 asm_to_hex.py 一步生成
cd python && python asm_to_hex.py ../mytests/test2_fib.S ../sim/program.hex

# 备选：两步流程（汇编器 + convert_hex.py）
cd python && python riscv_asm7.py input.s > /tmp/machine_code.txt
cd mytests && python convert_hex.py /tmp/machine_code.txt ../sim/program.hex

# UVM 测试同样可用：
cd python && python asm_to_hex.py ../uvm/alu_test.s ../uvm/alu_test.hex
```

**`python/asm_to_hex.py`** 是推荐的一步式汇编转 hex 工具。它内部调用 `riscv_asm7.py` 的汇编器，可输出纯 hex、UVM hex 或 Verilog ROM 格式（`--rom` 参数）。自动处理 `.space` 指令（填 0）和 `@` 地址标记。

### Python 汇编器

```bash
cd python && python riscv_asm7.py              # 交互模式
cd python && python riscv_asm7.py input.s      # 汇编文件，输出到屏幕
cd python && python riscv_asm7.py input.s > output.hex  # 保存到文件
```

**`riscv_asm7.py`** 是主力汇编器（v16）。支持标签、伪指令、数据指令（`.section`、`.ascii`、`.word`、`.byte`、`.globl`、`.balign`）、CSR 指令、`%hi()`/`%lo()` 地址修饰符、字符常量。输出为 32 位十六进制机器码。

**`riscv_arm.py`** 是更早的简化交互式汇编器，适合快速编码单条指令。

**其他 Python 工具：**
- `python/asm_to_hex.py` — 一步式 `.s` → `.hex` 转换器。`--rom` 参数可直接输出 Verilog ROM 格式。
- `python/rom_output/gen_rom.py` — 将 hex 机器码转换为 Verilog `rom[i]=32'hXXXXX;` 格式。
- `python/jal_branch_recognize/recognize_jal_branch.py` — 解析 hex 并在每条 JAL/B 型指令后插入 2 条 NOP（适用于早期无硬件冒险处理的流水线版本）。

### UVM 验证（Modelsim/Questa）

`uvm/` 目录包含 CPU 核心的 UVM 1.2 验证环境：

```bash
# 汇编测试程序（推荐）
cd python && python asm_to_hex.py ../uvm/alu_test.s ../uvm/alu_test.hex

# 命令行仿真（无 GUI）
cd uvm
vsim -c -do "set HEX_FILE alu_test.hex; set TEST_NAME cpu_test_alu; do run_msim.tcl"

# 带 GUI 波形
vsim -do "set HEX_FILE alu_test.hex; set GUI_MODE 1; do run_msim.tcl"

# 不同测试类
vsim -c -do "set HEX_FILE alu_test.hex; set TEST_NAME cpu_test_interrupt; do run_msim.tcl"
vsim -c -do "set HEX_FILE ../sim/program.hex; set TEST_NAME cpu_test_coremark; do run_msim.tcl"

# Windows 快速启动
cd uvm && run_uvm.bat alu_test.hex
cd uvm && run_uvm.bat alu_test.hex gui   # 带波形
```

| UVM 测试类 | 说明 |
|-----------|------|
| `cpu_test_alu` | 运行 hex 程序，仿真结束时报告结果 |
| `cpu_test_interrupt` | 运行 hex 程序，在 2000 周期时触发定时器中断 |
| `cpu_test_hazard` | 用于 RAW/load-use 冒险测试 |
| `cpu_test_coremark` | 运行直到 `perf_score != 0`（30ms 超时）|

| TCL 变量 | 默认值 | 说明 |
|----------|--------|------|
| `TEST_NAME` | `cpu_test_alu` | UVM 测试类名 |
| `HEX_FILE` | `""` | 测试程序 hex 文件路径 |
| `GUI_MODE` | `0` | 1=打开波形窗口 |
| `DUMP_VCD` | `0` | 1=生成 VCD 波形 |
| `COV_ENABLE` | `1` | 1=启用代码覆盖率 |
| `WAVE_ENABLE` | `1` | 1=添加波形分组 |

### Vivado 综合 / FPGA 比特流

使用 Vivado 工程 `vivado/RISCV_TEST/RISCV_TEST.xpr`。顶层模块为 `soc_top_fpga`（`soc/top/soc_top_fpga.v`），引脚约束在仓库根目录的 `constraints.xdc` 中：
- 200MHz LVDS 差分时钟：AD12/AD11
- UART TX：Y23
- 8 个 LED：T28/V19/U30/U29/V20/V26/W24/W23

### Design Compiler 综合

`source DC_command.txt` 加载 Synopsys 环境并运行 `run_synth.tcl`。脚本目标为 SMIC 55nm 工艺库，200MHz 时钟约束。

**已知问题**（详见 `error.md`）：
- `core_top.v:432` — 混合有序/命名端口连接 (VER-147)
- `core/id/id_top.v:66` — 语法错误 (VER-294)
- `core/pipeline/id_ex_reg.v:76` — 语法错误 (VER-294)

三个错误导致综合失败，所有子模块变为黑盒。

## 架构

### 流水线：IF → ID → EX → MEM → WB

- **IF**（`core/ifu/`）：PC 寄存器和取指。`ifu_top.v` 在 `intr_target > branch_target > jump_target > pc+4` 中选择下一 PC。
- **ID**（`core/id/`）：译码器、控制单元、立即数生成器、寄存器文件（32 个通用寄存器 + 31 个影子寄存器）。
- **EX**（`core/exu/`）：ALU、分支单元。同时多路选择来自 MEM/WB 的转发数据。CSR 指令在此阶段执行。
- **MEM**（`core/mem/`）：访存控制，向 SoC 总线仲裁器发起总线请求。
- **WB**（`core/wbu/`）：写回多路选择器，选择 ALU 结果、访存数据、PC+4 或 CSR 结果。

流水线寄存器：`if_id_reg`、`id_ex_reg`、`ex_mem_reg`、`mem_wb_reg`，位于 `core/pipeline/`。

### 冒险处理

- **Load-use 冒险**（`core/hazard/hazard_unit.v`）：当 load 指令在 EX 阶段但尚未进入 MEM，且下一条指令读取其目标寄存器时，流水线停顿 IF/ID 一周期。
- **转发**（`core/hazard/forwarding_unit.v`）：通过转发路径解决 RAW 冒险。优先级：MEM 阶段 load 数据（`bus_rdata`，最高，2026 年 6 月新增）> EX/MEM ALU 结果 > MEM/WB 结果（最低）。MEM→EX 的 load 数据直传路径（`forward=2'b11`）使 load-use 依赖可在 1 个停顿时钟周期内完成。

### 中断系统

- **interrupt_controller**（`core/interrupt/interrupt_controller.v`）：优先级编码器（MEI > MTI > SPI > I2C > MSI）。支持 Direct 和 Vectored 两种模式。
- **interrupt_pipeline**（`core/interrupt/interrupt_pipeline.v`）：协调中断接受时序。截至 2026 年 5 月，实现了**恒定 2 周期中断延迟**。`bus_ready_i` 端口区分 MEM load 已完成/未完成状态——已完成的 load 允许正常结束（mepc = mem_pc+4），未完成的 load 被取消（mepc = mem_pc，bus_re_o 被 kill）。
- **CSR**（`core/csr/`）：CSR 寄存器文件（`mstatus`、`mepc`、`mcause`、`mtvec`、`mie`、`mip`）及 CSR 指令执行。

### 影子寄存器（硬件上下文保存/恢复）

中断进入时，寄存器文件（`core/id/regfile.v`）在单周期内将 x1-x31 保存到 31 个内部影子寄存器。MRET 时恢复。写优先级：shadow_restore > 正常 WB > shadow_save。

**SHADOW_EN 参数：** 控制影子寄存器硬件是否启用。分别在 `core/id/id_top.v`（第 18 行）和 `core/interrupt/interrupt_pipeline.v`（第 22 行）中定义。**当前默认值：均为 `0`**（禁用）。如需启用，将两处都改为 `1`。两个参数相互独立——只改一个会导致部分功能运行。

### SoC 集成（`soc/`）

```
soc_top (soc/top/soc_top.v)           — 仿真顶层：CPU + 存储器 + 外设
soc_top_fpga (soc/top/soc_top_fpga.v) — FPGA 顶层：添加 IBUFDS、IOBUF、LED心跳
bus_arbiter (soc/bus/bus_arbiter.v)   — 按地址路由 CPU 总线请求
inst_rom (soc/mem/inst_rom.v)          — 指令 ROM（编译时确定程序）
data_ram (soc/mem/data_ram.v)          — 64KB 数据 RAM
```

### 内存映射

| 地址范围 | 设备 | 大小 |
|---------|------|------|
| 0x0000_0000 - 0x0000_FFFF | RAM | 64KB |
| 0x1000_0000 - 0x1000_0FFF | UART | 4KB |
| 0x1000_1000 - 0x1000_1FFF | GPIO | 4KB |
| 0x1000_2000 - 0x1000_2FFF | Timer | 4KB |
| 0x1000_3000 - 0x1000_3FFF | SPI | 4KB |
| 0x1000_4000 - 0x1000_4FFF | I2C | 4KB |

### 中断 ID

| ID | 来源 |
|----|------|
| 3 | 软件中断 |
| 7 | 定时器中断 |
| 11 | 外部中断（GPIO/SPI/I2C 或逻辑合并） |

SPI（ID 12）和 I2C（ID 13）中断在 SoC 层面合并为外部中断（ID 11）。ISR 必须轮询各外设状态寄存器以确定实际中断源。

### 外设（`soc/periph/`）

- **UART**（`uart_ctrl.v`、`uart_tx.v`）：默认 115200 波特率，TX FIFO（默认 16 字节深度，可通过 `FIFO_DEPTH` 参数配置），**仅支持发送，无接收功能**。
- **GPIO**（`gpio.v`）：32 位双向，每引脚独立方向控制，支持电平/边沿触发中断。
- **Timer**（`timer.v`）：32 位递减计数器，单次/自动重载模式。
- **SPI 主机**（`spi_master.v`）：4 种模式（CPOL/CPHA），8/16 位传输，MSB/LSB 优先可配，时钟分频。
- **I2C 主机**（`i2c_master.v`）：标准（100kHz）和快速（400kHz）模式，7 位设备地址。

## Verilog 编码规范

- **端口命名**：输入后缀 `_i`，输出后缀 `_o`（如 `clk_i`、`rst_n_i`、`bus_re_o`）
- **模块例化**：前缀 `u_`（如 `u_alu`、`u_ex_top`）
- **低电平复位**：`rst_n_i` 全局低电平有效
- **流水线阶段前缀**：`if_*`、`id_*`、`ex_*`、`mem_*`、`wb_*`
- **NOP 编码**：`0x00000013`（addi x0, x0, 0）
- **信号命名扩展**：`_for_hazard` 后缀表示送往冒险/转发单元；`pipe_csr_*` 前缀表示中断流水线 CSR 更新信号；`intr_flush_*` 表示中断触发的流水线刷新

## 测试程序

预编译的指令 ROM 测试程序位于 `soc/mem/test_inst_rom/`：
- `inst_rom_mul_test.v` — 乘除法测试（**注意：** 硬件已不再支持 M 扩展，此为遗留测试）
- `uart/inst_rom_uart_basic.v` — UART 基本发送测试
- `gpio/` — GPIO 各类测试
- `timer/` — 定时器测试
- `spi/` — SPI 测试
- `i2c/` — I2C 测试

汇编测试程序位于 `mytests/`：
- `test1_vvadd.S` — 向量加法（143 周期）
- `test2_fib.S` — 斐波那契（97 周期）
- `test3_matmul.S` — 矩阵乘法（23 周期）
- `test4_bubble.S` — 冒泡排序（1081 周期）
- `test5_lfsr.S` — LFSR（2053 周期）
- `test6_forwarding.S` — 转发逻辑测试
- `test7_branching.S` — 分支指令测试
- `test8_memdep.S` — 访存依赖测试
- `test9_interrupt.S` / `test9_mixedwork.S` — 中断和混合负载测试
- `load_use_test.s` — load-use 冒险测试
- `deterministic_test.S`（仓库根目录）— 确定性执行测试

链接脚本 `test.ld` 将 `.text` 放在地址 0x0，`.data` 放在 0x100。

## 关键设计文档

| 文档 | 内容 |
|------|------|
| `doc/uart_design.md` | UART 架构、寄存器映射、总线握手、代码示例 |
| `doc/load_use_hazard_analysis.md` | **已知 bug：** load-use 停顿会重复执行指令——缺少 ID/EX 的 NOP 插入 |
| `doc/load_use_forwarding_optimization.md` | MEM→EX 直接转发路径设计（2026 年 6 月） |
| `doc/auipc_bug_analysis.md` | **已知硬件 bug：** AUIPC 使用 PC=0 而非实际 PC 值——导致陷阱处理地址错误 |
| `doc/auipc_fix_changelog.md` | 软件规避方案：将 auipc+addi 替换为 lui+addi |
| `doc/ecall_exception_plan.md` / `doc/ecall_test_report.md` | ECALL 异常处理方案与测试报告 |
| `doc/coremark_results.md` | CoreMark 性能测试结果 |
| `doc/riscv_tests_and_uvm_integration.md` | RISC-V 官方测试与 UVM 集成 |
| `doc/deterministic_test_progress.md` | 确定性执行测试进展跟踪 |
| `doc/interrupt/` | 中断相关设计文档（影子寄存器、2 周期延迟、向量模式等） |
| `uvm/UVM_仿真指南.md` | UVM 仿真完整指南——环境搭建、使用说明、已知问题与修复记录 |
| `uvm/README.md` | UVM 验证环境架构说明 |
| `image.md` | Mermaid 架构图（核心流水线 + SoC 总线/外设） |

## 重要提示

- **AUIPC 硬件 bug**（见 `doc/auipc_bug_analysis.md`）：AUIPC 计算 `rd = 0 + (imm << 12)` 而非正确的 `rd = PC + (imm << 12)`——ALU 未收到实际的 PC 值。这导致所有 30 个 RISC-V 基础测试的陷阱处理地址错误（mtvec 指向错误位置），每个测试都显示相同的 106 周期结果。软件规避方案：在 hex 适配脚本中将 `auipc rd, 0` + `addi rd, rd, offset` 替换为 `lui rd, upper` + `addi rd, rd, lower`。Bug 位于 `core/exu/alu.v`。
- **Load-use 冒险 bug**（见 `doc/load_use_hazard_analysis.md`）：发生 load-use 停顿时，hazard 单元只暂停 IF/ID 和 PC，但**未**向 ID/EX 插入 NOP。这导致 load 指令和依赖指令各执行两次。对 RAM 读取而言功能上被掩盖（幂等读），但对 FIFO 外设会导致数据丢失。
- **UART 仅发送**：无接收（RX）功能。CTRL 寄存器（偏移 0x08）无法通过软件写入，因为总线仲裁器不转发地址偏移——它总是驱动 `uart_addr_o = UART_BASE`。
- **Design Compiler 综合失败** —— `error.md` 中的三个 Verilog 语法错误修复前 DC 综合无法通过。
- **`uvm/rtl_filelist.f`** 列出了 UVM 编译的所有 RTL 源文件。添加/删除 RTL 文件时需同步更新此列表。
- **中断控制器优先级：** MEI（外部，ID=11）> MTI（定时器，ID=7）> SPI（ID=12）> I2C（ID=13）> MSI（软件，ID=3）。
- **寄存器映射与比特位定义**详见 `README.md` 中各外设的寄存器表。
- Python 汇编器支持 M/A/F/D/C 伪指令，但**硬件仅实现 RV32I**——mul/div 等指令在硬件上无法正确执行。
