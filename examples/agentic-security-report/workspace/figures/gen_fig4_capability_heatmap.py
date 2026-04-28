"""
fig_capability_coverage_heatmap
Table-style heatmap: 12 vendors × 7 capabilities
Aspect ratio 4:3, 300 DPI
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.colors import ListedColormap

BG   = '#FFFFFF'
TEXT = '#1A1A2E'

# ── data from experimental_log.md §8 ─────────────────────────────────────────
# YES=2, Partial=1, NO=0; OWASP out of 10 (stored as float)
# Columns: Claude Code Hook | Secrets Cloaking | Post-hoc Sweep |
#          MCP Detection | Air-gap/Local | Policy-as-Code | OWASP

# For OWASP we store raw score; we'll handle it separately with a gradient

vendors = [
    "Prismor",
    "Snyk/Invariant",
    "Pillar Security",
    "Prompt Security",
    "Runlayer",
    "Zenity",
    "Lakera AI",
    "Endor Labs",
    "CrowdStrike AIDR",
    "LLM Guard (OSS)",
    "NeMo Guardrails",
    "MCP-Scan (OSS)",
]

# Binary caps (YES=2, Partial=1, NO=0)
bin_data = np.array([
    # Hook  Cloak  Sweep  MCP   Airgap PoC
    [2,     2,     2,     2,    2,     2],     # Prismor
    [0,     0,     0,     2,    1,     0],     # Snyk/Invariant  (YES CLI=2 for MCP)
    [0,     0,     0,     0,    2,     0],     # Pillar Security (YES VPC=2)
    [0,     0,     0,     2,    1,     0],     # Prompt Security (YES Gateway=2)
    [0,     0,     0,     2,    0,     0],     # Runlayer
    [0,     0,     0,     0,    0,     0],     # Zenity
    [0,     0,     0,     0,    0,     0],     # Lakera AI
    [1,     0,     0,     0,    0,     0],     # Endor Labs
    [0,     0,     0,     1,    0,     0],     # CrowdStrike AIDR
    [0,     0,     0,     0,    2,     0],     # LLM Guard
    [0,     0,     0,     0,    2,     1],     # NeMo Guardrails
    [0,     0,     0,     2,    2,     0],     # MCP-Scan
])

owasp_scores = [6.5, 3, 4, 5, 2, 3, 4, 3, 4, 3, 3, 1]

caps_bin   = ["Claude Code\nHook", "Secrets\nCloaking", "Post-hoc\nSweep",
              "MCP\nDetection", "Air-gap\n/ Local", "Policy-as\n-Code"]
cap_owasp  = "OWASP\n(of 10)"

n_vendors = len(vendors)
n_bin     = len(caps_bin)

# ── figure ─────────────────────────────────────────────────────────────────────
# 4:3 aspect → 8×6 inches
fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.axis('off')

# cell geometry
cell_w = 1.0
cell_h = 0.7

total_cols = n_bin + 1  # binary + OWASP
total_rows = n_vendors

# ── draw cells ─────────────────────────────────────────────────────────────────
def cell_color_bin(val):
    if val == 2:   return '#27AE60'   # YES  – green
    elif val == 1: return '#F39C12'   # Partial – amber
    else:          return '#E74C3C'   # NO   – red

def cell_color_owasp(score):
    # gradient: 0=red, 5=yellow, 10=green
    t = score / 10.0
    if t < 0.5:
        r = 1.0; g = t * 2 * 0.78; b = 0.0
    else:
        r = (1 - t) * 2 * 0.78; g = 0.78; b = 0.0
    return (r, g, b)

def label_bin(val):
    return {2: 'YES', 1: 'Partial', 0: 'NO'}[val]

prismor_row = 0  # index

for r, vendor in enumerate(vendors):
    y = (total_rows - 1 - r) * cell_h
    is_prismor = (r == prismor_row)

    # vendor label
    ax.text(-0.15, y + cell_h / 2, vendor,
            ha='right', va='center', fontsize=8,
            fontweight='bold' if is_prismor else 'normal',
            color='#C0392B' if is_prismor else TEXT)

    # binary capability cells
    for c in range(n_bin):
        x = c * cell_w
        val = bin_data[r, c]
        fc  = cell_color_bin(val)
        lbl = label_bin(val)
        # background rect
        rect = mpatches.FancyBboxPatch(
            (x + 0.04, y + 0.05), cell_w - 0.08, cell_h - 0.10,
            boxstyle="round,pad=0.04", linewidth=0.4,
            edgecolor='white', facecolor=fc, alpha=0.88)
        ax.add_patch(rect)
        txt_col = 'white' if val != 1 else '#4A3000'
        ax.text(x + cell_w / 2, y + cell_h / 2, lbl,
                ha='center', va='center', fontsize=6.5,
                fontweight='bold', color=txt_col)

    # OWASP gradient cell
    x = n_bin * cell_w
    sc = owasp_scores[r]
    fc = cell_color_owasp(sc)
    rect = mpatches.FancyBboxPatch(
        (x + 0.04, y + 0.05), cell_w - 0.08, cell_h - 0.10,
        boxstyle="round,pad=0.04", linewidth=0.4,
        edgecolor='white', facecolor=fc, alpha=0.88)
    ax.add_patch(rect)
    ax.text(x + cell_w / 2, y + cell_h / 2, f'{sc:.1f}/10',
            ha='center', va='center', fontsize=7,
            fontweight='bold', color='white')

    # Prismor row highlight border
    if is_prismor:
        highlight = mpatches.FancyBboxPatch(
            (-0.02, y + 0.02), (n_bin + 1) * cell_w + 0.04, cell_h - 0.04,
            boxstyle="round,pad=0.02", linewidth=1.8,
            edgecolor='#C0392B', facecolor='none', zorder=10)
        ax.add_patch(highlight)

# ── column headers ─────────────────────────────────────────────────────────────
header_y = total_rows * cell_h + 0.15
for c, cap in enumerate(caps_bin):
    ax.text(c * cell_w + cell_w / 2, header_y, cap,
            ha='center', va='bottom', fontsize=7.5,
            fontweight='bold', color=TEXT,
            multialignment='center')
ax.text(n_bin * cell_w + cell_w / 2, header_y, cap_owasp,
        ha='center', va='bottom', fontsize=7.5,
        fontweight='bold', color=TEXT, multialignment='center')

# ── legend ─────────────────────────────────────────────────────────────────────
legend_y = -0.85
handles = [
    mpatches.Patch(color='#27AE60', label='YES'),
    mpatches.Patch(color='#F39C12', label='Partial'),
    mpatches.Patch(color='#E74C3C', label='NO'),
]
ax.legend(handles=handles, loc='lower center',
          bbox_to_anchor=(0.5, -0.12),
          ncol=3, fontsize=8.5, framealpha=0.9,
          edgecolor='#CBD5E0', title='Capability Status',
          title_fontsize=8)

# ── title ─────────────────────────────────────────────────────────────────────
ax.set_title("Vendor Capability Coverage Matrix",
             fontsize=12, fontweight='bold', color=TEXT, pad=14)

ax.set_xlim(-2.2, (n_bin + 1) * cell_w + 0.2)
ax.set_ylim(-1.1, (total_rows + 1) * cell_h + 0.3)

plt.tight_layout()
plt.savefig('/home/ubuntu/projects/immunity-agent/workspace/figures/fig_capability_coverage_heatmap.png',
            dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()
print("fig_capability_coverage_heatmap saved")
