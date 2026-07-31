# Verilator simulation makefile for FX-RV32
TOP = core_top_sim

# Find all RTL source files
CORE_SOURCES = $(shell find ../core -name "*.v" 2>/dev/null)
SOC_SOURCES  = $(shell find ../soc -name "*.v" ! -name "soc_top_fpga.v" 2>/dev/null)
LOCAL_SOURCES = $(shell find . -maxdepth 1 -name "*.v" 2>/dev/null)
SOURCES = $(CORE_SOURCES) $(SOC_SOURCES) $(LOCAL_SOURCES)

# C++ harness
SIM_CPP = sim_main.cpp

# Base Verilator flags
VERILATOR_FLAGS = --cc --exe --build -j 8 --top-module $(TOP) \
                  -Wno-fatal \
                  -Wno-PINMISSING \
                  -Wno-MULTIDRIVEN \
                  -Wno-LATCH \
                  -Wno-WIDTHTRUNC \
                  -Wno-WIDTHEXPAND \
                  -Wno-CASEINCOMPLETE \
                  -Wno-UNSIGNED

# Enable RVTEST define for loading program.hex into inst_rom
ifdef RVTEST
  VERILATOR_FLAGS += -DRVTEST
endif

# Target executable
EXE = obj_dir/V$(TOP)

all: $(EXE)

$(EXE): $(SOURCES) $(SIM_CPP)
	verilator $(VERILATOR_FLAGS) $(SIM_CPP) $(SOURCES)

run: $(EXE)
	./$(EXE)

clean:
	rm -rf obj_dir

.PHONY: all run clean
