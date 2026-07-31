# FX-RV32 CoreMark Port Makefile
# Cross-compiles CoreMark for bare-metal RV32I

CROSS        = /home/yifengxin/riscv/bin/riscv32-unknown-elf-
CC           = $(CROSS)gcc
OBJCOPY      = $(CROSS)objcopy
OBJDUMP      = $(CROSS)objdump

COREMARK_DIR = /home/yifengxin/coremark_test/coremark-main
CORE_SRCS    = core_list_join.c core_main.c core_matrix.c core_state.c core_util.c
PORT_SRCS    = core_portme.c ee_printf.c soft_muldiv.c

VPATH = $(COREMARK_DIR):.

ARCH_FLAGS = -march=rv32i -mabi=ilp32
OPT_FLAGS  = -Os -ffreestanding -fno-builtin
WARN_FLAGS = -Wall

CFLAGS  = $(ARCH_FLAGS) $(OPT_FLAGS) $(WARN_FLAGS)
CFLAGS += -I$(COREMARK_DIR) -I.
CFLAGS += -DPERFORMANCE_RUN=1
CFLAGS += -DTOTAL_DATA_SIZE=1200
CFLAGS += -DMAIN_HAS_NOARGC=1
CFLAGS += -DMAIN_HAS_NORETURN=0
CFLAGS += '-DFLAGS_STR="-Os -ffreestanding"'
CFLAGS += -DITERATIONS=$(ITERATIONS)

LINKER_SCRIPT = link.ld
LDFLAGS     = -T $(LINKER_SCRIPT) -nostdlib -nostartfiles
LDLIBS      =

CORE_OBJS = $(CORE_SRCS:.c=.o)
PORT_OBJS = $(PORT_SRCS:.c=.o) startup.o
OBJS      = $(CORE_OBJS) $(PORT_OBJS)

TARGET_ELF = coremark.elf
TARGET_BIN = coremark.bin
TARGET_HEX = program.hex
TARGET_DIS = coremark.dis

ITERATIONS ?= 0

.PHONY: all clean dis hex sim

all: $(TARGET_HEX) $(TARGET_DIS)

$(TARGET_ELF): $(OBJS) $(LINKER_SCRIPT)
	$(CC) $(ARCH_FLAGS) $(LDFLAGS) -o $@ $(OBJS) $(LDLIBS)

$(TARGET_BIN): $(TARGET_ELF)
	$(OBJCOPY) -O binary $< $@

$(TARGET_HEX): $(TARGET_BIN)
	python3 bin2hex.py $< $@

$(TARGET_DIS): $(TARGET_ELF)
	$(OBJDUMP) -d $< > $@

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.o: %.s
	$(CC) $(ARCH_FLAGS) -c -o $@ $<

sim: $(TARGET_HEX)
	cp $(TARGET_HEX) ../sim/program.hex

clean:
	rm -f $(OBJS) $(TARGET_ELF) $(TARGET_BIN) $(TARGET_HEX) $(TARGET_DIS)
