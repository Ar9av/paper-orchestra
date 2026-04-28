"""
fig_secrets_leakage_comparison
Two sub-charts: leak rates (left) + GitHub secrets sprawl (right)
Aspect ratio 3:2, 300 DPI
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

BG   = '#FFFFFF'
TEXT = '#1A1A2E'
GRID = '#E8EBF0'
BLUE = '#2C5F8A'
RED  = '#C0392B'
AMBER= '#E67E22'

# 3:2 → 9×6 inches
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 7.34), dpi=300,
                                gridspec_kw={'width_ratios': [1, 1.4]})
fig.patch.set_facecolor(BG)

# ────────────────────────────────────────────────────────────────────────────
# LEFT: Grouped bar – commit secret leak rates
# ────────────────────────────────────────────────────────────────────────────
ax1.set_facecolor(BG)
labels  = ['AI Coding Agent\n(Claude Code)', 'Human\nBaseline']
values  = [3.2, 1.5]
colors  = [RED, BLUE]
x       = np.arange(len(labels))
bars    = ax1.bar(x, values, width=0.45, color=colors, zorder=3,
                  edgecolor='white', linewidth=0.6)

for bar, val in zip(bars, values):
    ax1.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 0.06,
             f'{val:.1f}%', ha='center', va='bottom',
             fontsize=10, fontweight='bold',
             color=bar.get_facecolor())

# 2.13x annotation
ax1.annotate("", xy=(1, 1.5), xytext=(0, 3.2),
             arrowprops=dict(arrowstyle='<->', color='#4A5568', lw=1.2))
ax1.text(0.5, 2.55, '2.13×', ha='center', va='center', fontsize=10,
         fontweight='bold', color='#4A5568',
         bbox=dict(boxstyle='round,pad=0.25', facecolor='#F8F9FA',
                   edgecolor='#CBD5E0', linewidth=0.8))

ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=9, color=TEXT)
ax1.set_ylabel("Commit Secret Leak Rate (%)", fontsize=9, color=TEXT)
ax1.set_ylim(0, 4.5)
ax1.set_title("Secret Leak Rate:\nAI vs. Human Commits",
              fontsize=10, fontweight='bold', color=TEXT, pad=8)
ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f%%'))
ax1.grid(axis='y', color=GRID, linewidth=0.7, zorder=0)
ax1.set_axisbelow(True)
for spine in ['top', 'right']:
    ax1.spines[spine].set_visible(False)
ax1.spines['left'].set_color(GRID)
ax1.spines['bottom'].set_color(GRID)

# ────────────────────────────────────────────────────────────────────────────
# RIGHT: GitHub secrets sprawl bar chart
# ────────────────────────────────────────────────────────────────────────────
ax2.set_facecolor(BG)

categories = ['Total Hardcoded\nSecrets (2024)', 'Total Hardcoded\nSecrets (2025)',
              'AI Service\nCredentials (2024)', 'AI Service\nCredentials (2025)']
# 2024 baseline derived: 28.65M / 1.34 ≈ 21.38M
# AI service 2024 baseline: 1.275M / 1.81 ≈ 0.704M
vals2 = [21.38, 28.65, 0.704, 1.275]
bar_colors = [BLUE, RED, BLUE, AMBER]

x2 = np.arange(len(categories))
bars2 = ax2.bar(x2, vals2, width=0.5, color=bar_colors, zorder=3,
                edgecolor='white', linewidth=0.6, alpha=0.90)

# Value labels
for bar, val in zip(bars2, vals2):
    ax2.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 0.25,
             f'{val:.2f}M', ha='center', va='bottom',
             fontsize=8.5, fontweight='bold',
             color=bar.get_facecolor())

# YoY annotations
ax2.annotate("+34% YoY",
             xy=(1, 28.65), xytext=(0.5, 32),
             fontsize=8.5, color=RED, fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=RED, lw=1.0),
             bbox=dict(boxstyle='round,pad=0.2', facecolor='#FDECEA',
                       edgecolor=RED, linewidth=0.6))

ax2.annotate("+81% YoY",
             xy=(3, 1.275), xytext=(2.5, 5),
             fontsize=8.5, color=AMBER, fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=AMBER, lw=1.0),
             bbox=dict(boxstyle='round,pad=0.2', facecolor='#FEF9E7',
                       edgecolor=AMBER, linewidth=0.6))

ax2.set_xticks(x2)
ax2.set_xticklabels(categories, fontsize=8, color=TEXT)
ax2.set_ylabel("Count (Millions)", fontsize=9, color=TEXT)
ax2.set_ylim(0, 38)
ax2.set_title("Hardcoded Secrets on Public GitHub:\nYoY Growth & AI Service Credentials",
              fontsize=10, fontweight='bold', color=TEXT, pad=8)
ax2.grid(axis='y', color=GRID, linewidth=0.7, zorder=0)
ax2.set_axisbelow(True)
for spine in ['top', 'right']:
    ax2.spines[spine].set_visible(False)
ax2.spines['left'].set_color(GRID)
ax2.spines['bottom'].set_color(GRID)

# ── shared source note ────────────────────────────────────────────────────────
fig.text(0.99, 0.01, "Source: GitGuardian State of Secrets Sprawl 2026",
         ha='right', va='bottom', fontsize=7.5, color='#6B7280', style='italic')

plt.tight_layout(w_pad=2.5)
plt.savefig('/home/ubuntu/projects/immunity-agent/workspace/figures/fig_secrets_leakage_comparison.png',
            dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()
print("fig_secrets_leakage_comparison saved")
