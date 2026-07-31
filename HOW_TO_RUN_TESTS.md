# FX-RV32 官方 RISC-V 测试运行指南

## 环境要求

| 工具 | 用途 |
|------|------|
| `riscv32-unknown-elf-gcc`（或 `riscv64-unknown-elf-gcc`） | 编译测试汇编文件 |
| `Verilator` | RTL 仿真 |
| `Python 3` | 运行编译脚本 |
| `git` | 克隆 riscv-tests（如未下载） |
| `make` | 构建仿真 |

Ubuntu 安装：

```bash
sudo apt install gcc-riscv64-unknown-elf verilator python3 git make
```

## 快速开始

### 第一步：准备测试集

如果还没有 riscv-tests，脚本会自动克隆：

```bash
cd mytests/
python3 run_riscv_tests.py
```

如果已经克隆好，确保目录结构为：

```
mytests/
  riscv-tests/
    env/p/          # riscv_test.h, encoding.h
    isa/
      macros/scalar/  # test_macros.h
      rv32ui-p-*.S    # RV32I 测试
      rv32um-p-*.S    # RV32M 测试
```

### 第二步：编译测试

```bash
cd mytests/
python3 run_riscv_tests.py
```

成功后会在 `mytests/test_hex/` 下生成 `.hex` 文件。

### 第三步：运行仿真

```bash
# 方法一：用 run_test.sh
cd mytests/test_hex/
./run_test.sh rv32ui-p-add

# 方法二：手动复制并运行
cp mytests/test_hex/rv32ui-p-add.hex sim/program.hex
cd sim/
make clean
make run RVTEST=1
```

### 第四步：查看结果

仿真输出会直接显示：

```
=== RISCV-TEST PASSED ===
```

或

```
=== RISCV-TEST FAILED (code=0x...) ===
```

超时会显示：

```
=== TIMEOUT: no tohost write after 10M cycles ===
```

## 测试类别说明

| 类别 | 内容 |
|------|------|
| `rv32ui-p` | RV32I 用户态指令测试（add, sub, and, or, xor, sll, srl, sra, slt, branch, jump, load, store 等） |
| `rv32um-p` | RV32M 乘除法测试（mul, mulh, div, rem 等） |

## 目录结构

```
FX-RV32/
  core/           # CPU 核心 RTL
  soc/            # SoC 集成、总线、外设
  sim/            # Verilator 仿真
    makefile        # 仿真构建脚本
    core_top_sim.v  # 仿真顶层 wrapper（含 tohost 检测）
    sim_main.cpp    # C++ 仿真驱动
    program.hex     # 待加载的测试程序（$readmemh）
  mytests/        # 测试相关
    run_riscv_tests.py  # 编译脚本
    test.ld             # 链接脚本
    test_hex/           # 编译生成的 .hex 文件
    riscv-tests/        # 官方测试集
  tb/             # 传统 testbench（ModelSim 用）
```

## 内存映射

| 设备 | 地址范围 | 说明 |
|------|----------|------|
| inst_rom | `0x00000000 - 0x00003FFF` | 16KB 指令 ROM（Harvard I$） |
| data_ram | `0x00000000 - 0x0000FFFF` | 64KB 数据 RAM（Harvard D$） |
| tohost | `0x80001000` | 测试结果报告（写1=PASS） |

代码从 0x00000000 开始执行，through 通过 `tohost` 外设写 1 报告测试通过。

## 编译单个自定义测试

```bash
riscv64-unknown-elf-gcc \
  -march=rv32im -mabi=ilp32 \
  -nostdlib -nostartfiles \
  -T mytests/test.ld \
  -o mytest.elf mytest.S

riscv64-unknown-elf-objcopy -O binary mytest.elf mytest.bin

python3 -c "
import sys
data = open('mytest.bin','rb').read()
if len(data) % 4:
    data += b'\x00' * (4 - len(data) % 4)
for i in range(0, len(data), 4):
    print(f'{int.from_bytes(data[i:i+4],\"little\"):08x}')
" > sim/program.hex

cd sim && make clean && make run RVTEST=1
```
