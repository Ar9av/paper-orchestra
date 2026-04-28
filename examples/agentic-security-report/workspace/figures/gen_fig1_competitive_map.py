"""
fig_competitive_positioning_map
2D scatter: Specificity to AI Coding Agents vs Runtime Enforcement Level
Aspect ratio 4:3, 300 DPI
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── color palette ──────────────────────────────────────────────────────────────
BG      = '#FFFFFF'
GRID    = '#E8EBF0'
QUAD_BG = '#F5F7FA'
PRISMOR = '#C0392B'   # red – Prismor
OTHERS  = '#2C5F8A'   # muted blue – competitors
TEXT    = '#1A1A2E'

# ── figure size: 4:3 at 300 DPI → 1600×1200 px ────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# ── quadrant shading ───────────────────────────────────────────────────────────
ax.axvline(0.5, color=GRID, linewidth=1.2, zorder=1)
ax.axhline(0.5, color=GRID, linewidth=1.2, zorder=1)

for (xmin, xmax, ymin, ymax) in [
    (0.5, 1.0, 0.5, 1.0),   # top-right   (highlight)
]:
    ax.fill_between([xmin, xmax], [ymin, ymin], [ymax, ymax],
                    color='#FDECEA', alpha=0.5, zorder=0)

# ── data ───────────────────────────────────────────────────────────────────────
vendors = [
    ("Prismor",            0.95, 0.95, True),
    ("Snyk/Invariant",     0.70, 0.45, False),
    ("Pillar Security",    0.65, 0.30, False),
    ("Prompt Security",    0.50, 0.40, False),
    ("Runlayer",           0.75, 0.35, False),
    ("Zenity",             0.25, 0.30, False),
    ("Lakera AI",          0.20, 0.55, False),
    ("Endor Labs",         0.60, 0.20, False),
    ("Palo Alto AIRS",     0.15, 0.55, False),
    ("CrowdStrike AIDR",   0.15, 0.50, False),
    ("Wiz AI-SPM",         0.10, 0.25, False),
    ("LLM Guard (OSS)",    0.20, 0.30, False),
]

for name, x, y, is_prismor in vendors:
    if is_prismor:
        ax.scatter(x, y, s=280, marker='*', color=PRISMOR, zorder=5,
                   linewidths=0.8, edgecolors='#7B0F0F')
        ax.annotate(name, (x, y),
                    xytext=(6, 8), textcoords='offset points',
                    fontsize=9, fontweight='bold', color=PRISMOR,
                    va='bottom')
    else:
        ax.scatter(x, y, s=70, marker='o', color=OTHERS, zorder=4,
                   linewidths=0.6, edgecolors='#1A3A5C', alpha=0.85)
        # Smart label offsets to reduce crowding
        offsets = {
            "Snyk/Invariant":   (5, 5),
            "Pillar Security":  (5, -12),
            "Prompt Security":  (-5, 7),
            "Runlayer":         (5, 5),
            "Zenity":           (5, -12),
            "Lakera AI":        (-65, 5),
            "Endor Labs":       (5, 5),
            "Palo Alto AIRS":   (-78, 5),
            "CrowdStrike AIDR": (-90, -12),
            "Wiz AI-SPM":       (5, 5),
            "LLM Guard (OSS)":  (5, -12),
        }
        dx, dy = offsets.get(name, (5, 5))
        ax.annotate(name, (x, y),
                    xytext=(dx, dy), textcoords='offset points',
                    fontsize=7, color=TEXT, va='center')

# ── quadrant labels ────────────────────────────────────────────────────────────
quad_kw = dict(fontsize=7.5, color='#6B7280', fontstyle='italic',
               ha='center', va='center', zorder=2)
ax.text(0.25, 0.75, "Generic LLM\nRuntime Enforcement", **quad_kw)
ax.text(0.75, 0.75, "Agent-Native\nRuntime Enforcement\n(Prismor)",
        fontsize=7.5, color='#A93226', fontstyle='italic',
        ha='center', va='center', fontweight='bold', zorder=2)
ax.text(0.25, 0.25, "Generic LLM\nStatic / Advisory", **quad_kw)
ax.text(0.75, 0.25, "Agent-Adjacent\nStatic / Advisory", **quad_kw)

# ── axes ───────────────────────────────────────────────────────────────────────
ax.set_xlim(-0.03, 1.08)
ax.set_ylim(-0.03, 1.08)
ax.set_xlabel("Specificity to AI Coding Agents", fontsize=10, color=TEXT, labelpad=8)
ax.set_ylabel("Runtime Enforcement Level", fontsize=10, color=TEXT, labelpad=8)
ax.set_title("Competitive Positioning Map: AI Coding Agent Security Vendors",
             fontsize=11, fontweight='bold', color=TEXT, pad=12)

ax.tick_params(colors=TEXT, labelsize=8)
ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_xticklabels(['0\n(Generic)', '0.25', '0.5', '0.75', '1.0\n(Agent-native)'])
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(['0\n(Static only)', '0.25', '0.5', '0.75', '1.0\n(Hook-layer)'])

# spines
for spine in ax.spines.values():
    spine.set_visible(False)
ax.grid(False)

# legend
h1 = mpatches.Patch(color=PRISMOR, label='Prismor')
h2 = mpatches.Patch(color=OTHERS,  label='Competitors')
ax.legend(handles=[h1, h2], loc='lower right', fontsize=8,
          framealpha=0.9, edgecolor=GRID)

plt.tight_layout()
plt.savefig('/home/ubuntu/projects/immunity-agent/workspace/figures/fig_competitive_positioning_map.png',
            dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()
print("fig_competitive_positioning_map saved")
