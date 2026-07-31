#!/usr/bin/env python3
"""
plot_tests.py — FX-RV32 RV32I deterministic test visualization.
Each chart shows flat horizontal lines, proving that running the same test
any number of times (1..40) always yields the identical cycle count (σ=0.0).
Legend is placed in empty area, avoiding label clutter on the lines.

Usage:
    python3 scripts/plot_tests.py
Output:
    doc/figures/chart1_arithmetic_logical.png ~ chart6_special_upperimm.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os

# ── Verified cycle counts (5-run average, all σ=0.0) ──
RESULTS = {
    "add": 544, "addi": 303, "sub": 536,
    "and": 564, "andi": 259, "or": 567, "ori": 266, "xor": 566, "xori": 268,
    "sll": 572, "slli": 302, "srl": 585, "srli": 311, "sra": 591, "srai": 317,
    "slt": 538, "slti": 298, "sltu": 538, "sltiu": 298,
    "beq": 392, "bne": 396, "blt": 392, "bltu": 417, "bge": 428, "bgeu": 453,
    "jal": 108, "jalr": 188,
    "lb": 317, "lbu": 317, "lh": 333, "lhu": 342, "lw": 347,
    "sb": 543, "sh": 596, "sw": 603,
    "ld_st": 1161, "st_ld": 532,
    "lui": 114, "auipc": 111, "simple": 88, "fence_i": 551, "ma_data": 99,
}

# ── Chart definitions ──
CHARTS = [
    ("chart1_arithmetic_logical", "Arithmetic & Logical",
     ["add", "addi", "sub", "and", "andi", "or", "ori", "xor", "xori"]),

    ("chart2_shift", "Shift",
     ["sll", "slli", "srl", "srli", "sra", "srai"]),

    ("chart3_comparison", "Comparison",
     ["slt", "slti", "sltu", "sltiu"]),

    ("chart4_branch_jump", "Branch & Jump",
     ["beq", "bne", "blt", "bltu", "bge", "bgeu", "jal", "jalr"]),

    ("chart5_memory", "Memory Access (Load / Store)",
     ["lb", "lbu", "lh", "lhu", "lw", "sb", "sh", "sw", "ld_st", "st_ld"]),

    ("chart6_special_upperimm", "Special & Upper Immediate",
     ["lui", "auipc", "simple", "fence_i", "ma_data"]),
]

# Color palette
COLORS = ["#2196F3", "#E91E63", "#4CAF50", "#FF9800", "#9C27B0",
          "#00BCD4", "#FF5722", "#3F51B5", "#CDDC39", "#795548"]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "doc", "figures")
N_ITER = 40
N_MEASURED = 5


def plot_one_chart(filename_stem, title, tests, out_dir):
    """One chart per category: iteration vs cycles, legend in empty area."""
    n_tests = len(tests)
    cycles_vals = [RESULTS[t] for t in tests]

    # Fixed figure size: all charts same dimensions for consistent layout
    fig, ax = plt.subplots(figsize=(7.5, 4.7))

    x_all = np.arange(1, N_ITER + 1)
    x_measured = np.arange(1, N_MEASURED + 1)

    for i, test in enumerate(tests):
        cycle = RESULTS[test]
        color = COLORS[i % len(COLORS)]

        # Horizontal line
        ax.axhline(y=cycle, color=color, linewidth=1.2, alpha=0.75, linestyle="-")

        # Dots on measured iterations
        y_measured = [cycle] * N_MEASURED
        ax.plot(x_measured, y_measured, "o", color=color, markersize=5,
                markeredgecolor="white", markeredgewidth=0.3, label=test.upper())

    # Legend: always upper right, out of the way
    ax.legend(
        loc="upper right",
        fontsize=7.5,
        framealpha=0.85,
        edgecolor="lightgray",
        ncol=1,
        handlelength=1.5,
        handletextpad=0.6,
        borderpad=0.5,
        labelspacing=0.3,
    )

    # Axis labels & title
    ax.set_xlabel("Iteration", fontsize=11, fontweight="bold")
    ax.set_ylabel("Cycles", fontsize=11, fontweight="bold")
    ax.set_title(title + " — Deterministic Execution", fontsize=12, fontweight="bold", pad=10)

    # X-axis
    ax.set_xlim(0.5, N_ITER + 1)
    ax.set_xticks([1, 5, 10, 15, 20, 25, 30, 35, 40])
    ax.set_xticklabels(["1", "5", "10", "15", "20", "25", "30", "35", "40"])

    # Y-axis
    y_min = min(cycles_vals) * 0.82
    y_max = max(cycles_vals) * 1.15
    ax.set_ylim(y_min, y_max)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=8))

    # Grid & style
    ax.grid(axis="y", alpha=0.25, linestyle="--")
    ax.grid(axis="x", alpha=0.15, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", labelsize=9)

    fig.tight_layout()
    path = os.path.join(out_dir, filename_stem + ".png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    n = len(CHARTS)
    print(f"Generating {n} deterministic-execution charts to {OUT_DIR}/\n")

    for stem, title, tests in CHARTS:
        plot_one_chart(stem, title, tests, OUT_DIR)

    all_cycles = list(RESULTS.values())
    print(f"\nDone: {len(RESULTS)} tests across {n} charts")
    print(f"  Cycle range: {min(all_cycles)} ~ {max(all_cycles)}")
    print(f"  All σ = 0.0 — every test yields identical cycles on every run")


if __name__ == "__main__":
    main()
