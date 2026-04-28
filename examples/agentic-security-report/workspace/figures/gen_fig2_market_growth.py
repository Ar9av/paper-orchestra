"""
fig_market_growth_gen_ai_cybersecurity
Bar + trend line: Gen AI in Cybersecurity market 2025-2031
Aspect ratio 16:9, 300 DPI
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

BG   = '#FFFFFF'
BAR  = '#2C5F8A'
LINE = '#C0392B'
TEXT = '#1A1A2E'
GRID = '#E8EBF0'

years  = [2025, 2026, 2027, 2028, 2029, 2030, 2031]
values = [8.65, 10.93, 13.83, 17.50, 22.14, 28.01, 35.46]
x      = np.arange(len(years))

# 16:9 at 300 DPI → 1600×900 px  (figsize in inches: 16/3 × 9/3 = ~5.33×3)
# Use 10.67 × 6 for comfortable readability
fig, ax = plt.subplots(figsize=(10.67, 6), dpi=300)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

bars = ax.bar(x, values, color=BAR, width=0.55, zorder=3,
              edgecolor='#1A3A5C', linewidth=0.5, alpha=0.92)

# Value labels on bars
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
            f'${val:.2f}B', ha='center', va='bottom', fontsize=8.5,
            color=TEXT, fontweight='bold')

# Trend line (same data, smoother curve)
ax_twin = ax.twinx()
ax_twin.plot(x, values, color=LINE, linewidth=2.2, marker='o',
             markersize=6, markerfacecolor='white', markeredgewidth=2,
             markeredgecolor=LINE, zorder=4)
ax_twin.set_ylim(0, 42)
ax_twin.set_ylabel("Market Size ($ Billion)", fontsize=10, color=LINE, labelpad=8)
ax_twin.tick_params(axis='y', colors=LINE, labelsize=9)
for spine in ax_twin.spines.values():
    spine.set_visible(False)

# CAGR annotation
ax.annotate("CAGR: 26.5%\n(MarketsandMarkets)",
            xy=(5.1, 30), fontsize=9.5, color=LINE, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#FDECEA',
                      edgecolor=LINE, linewidth=0.8))

# axes
ax.set_xlim(-0.5, len(years) - 0.5)
ax.set_ylim(0, 42)
ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in years], fontsize=10, color=TEXT)
ax.set_yticks([])
ax.set_xlabel("Year", fontsize=11, color=TEXT, labelpad=8)
ax.set_title("Generative AI in Cybersecurity Market Growth (2025–2031)",
             fontsize=13, fontweight='bold', color=TEXT, pad=14)

# grid lines
ax.yaxis.set_major_locator(mticker.MultipleLocator(5))
ax.set_ylim(0, 42)
ax.grid(axis='y', color=GRID, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

# spines
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_color(GRID)
ax.tick_params(axis='y', left=False)

# source note
fig.text(0.99, 0.01, "Source: MarketsandMarkets", ha='right', va='bottom',
         fontsize=7.5, color='#6B7280', style='italic')

plt.tight_layout()
plt.savefig('/home/ubuntu/projects/immunity-agent/workspace/figures/fig_market_growth_gen_ai_cybersecurity.png',
            dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()
print("fig_market_growth_gen_ai_cybersecurity saved")
