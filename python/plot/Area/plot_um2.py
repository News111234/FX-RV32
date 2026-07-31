import matplotlib.pyplot as plt
import numpy as np

# 数据：设计名称和面积 (μm²)
# PicoRV32 (full) 面积为 33086 μm²
designs = [
    'PicoRV32 (base)\n(Core)',
    'FX-RV32\n(Core)',
    'Sophon\n(Core)',
    'PicoRV32 (full)\n(Core)',
    'FX-RV32\n(SoC)',
    'CVA6\n(Core)'
]
area_um2 = [20832, 27776, 32032, 33086, 196112, 483728]

# 颜色（与kGE脚本一致）
colors = ['#aec7e8', '#ff7f0e', '#2ca02c', '#1f77b4', '#d62728', '#9467bd']

plt.figure(figsize=(11, 6))
bars = plt.bar(designs, area_um2, color=colors, edgecolor='black', linewidth=1.2)

# 柱顶数值标签
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.02 * max(area_um2),
             f'{int(height):,} µm²', ha='center', va='bottom', fontsize=9, fontname='serif')

plt.ylabel('Area (µm²)', fontsize=14, fontname='serif')
plt.title('Area Comparison of RISC-V Cores and SoC (µm²)', fontsize=16, fontname='serif')
plt.xticks(fontsize=10, fontname='serif')
plt.yticks(fontsize=12, fontname='serif')
plt.grid(axis='y', linestyle='--', alpha=0.5)

ax = plt.gca()
ax.ticklabel_format(axis='y', style='plain', useOffset=False)

plt.tight_layout()
plt.savefig('area_comparison_um2.pdf', format='pdf', dpi=300)
plt.savefig('area_comparison_um2.png', dpi=300)
plt.show()