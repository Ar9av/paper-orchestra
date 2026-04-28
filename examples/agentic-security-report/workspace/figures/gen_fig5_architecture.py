"""
fig_prismor_system_architecture
Three-layer block diagram
Aspect ratio 4:3, 300 DPI
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

BG   = '#FFFFFF'
TEXT = '#1A1A2E'
LTEXT = '#FFFFFF'

# layer colors
C_TOP    = '#2471A3'   # blue – developer workstation
C_CLOAK  = '#E67E22'   # orange
C_WARDEN = '#C0392B'   # red
C_SWEEP  = '#7D3C98'   # purple
C_BOTTOM = '#566573'   # gray
C_MID_BG = '#F0F3F4'   # light gray for middle layer background

fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.axis('off')
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)

def rbox(ax, x, y, w, h, color, label, sublabels=None,
         text_color=LTEXT, fontsize=9, corner=0.3):
    """Draw a rounded rectangle with label and optional sub-bullets."""
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad={corner}",
                          linewidth=1.2,
                          edgecolor='white',
                          facecolor=color,
                          alpha=0.93,
                          zorder=3)
    ax.add_patch(rect)
    if sublabels:
        ax.text(x + w / 2, y + h - 0.32, label,
                ha='center', va='top', fontsize=fontsize,
                fontweight='bold', color=text_color, zorder=4)
        for i, sub in enumerate(sublabels):
            ax.text(x + w / 2, y + h - 0.72 - i * 0.38, f'• {sub}',
                    ha='center', va='top', fontsize=7, color=text_color,
                    zorder=4, alpha=0.92)
    else:
        ax.text(x + w / 2, y + h / 2, label,
                ha='center', va='center', fontsize=fontsize,
                fontweight='bold', color=text_color, zorder=4,
                multialignment='center')

def arrow(ax, x1, y1, x2, y2, color='#4A5568'):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=1.5, mutation_scale=14),
                zorder=5)

# ──────────────────────────────────────────────────────────────────────────────
# TOP LAYER – Developer Workstation
rbox(ax, 0.4, 6.4, 9.2, 1.2, C_TOP,
     "Developer Workstation\nClaude Code  ·  Cursor  ·  Windsurf  ·  OpenClaw",
     fontsize=9.5)

# Arrow: top → middle
arrow(ax, 5.0, 6.4, 5.0, 5.85)

# MIDDLE LAYER – background band
mid_bg = FancyBboxPatch((0.3, 3.1), 9.4, 2.65,
                        boxstyle="round,pad=0.2",
                        linewidth=0.8, edgecolor='#BDC3C7',
                        facecolor=C_MID_BG, alpha=0.5, zorder=1)
ax.add_patch(mid_bg)
ax.text(5.0, 5.9, "Prismor Defense Layers", ha='center', va='bottom',
        fontsize=8, color='#6B7280', style='italic')

box_y  = 3.25
box_h  = 2.35
box_w  = 2.85
gap    = 0.2

# CLOAK box
rbox(ax, 0.45, box_y, box_w, box_h, C_CLOAK,
     "CLOAK",
     sublabels=["Pre-emptive Secret Sub.",
                "decloak.sh (PreToolUse)",
                "recloak-mcp.sh (PostToolUse)",
                "userprompt-guard.sh"],
     fontsize=8.5)

# WARDEN box
rbox(ax, 0.45 + box_w + gap, box_y, box_w, box_h, C_WARDEN,
     "WARDEN",
     sublabels=["25+ detection rules",
                "enforce / observe mode",
                "YAML policy engine",
                "10 threat categories"],
     fontsize=8.5)

# SWEEP box
rbox(ax, 0.45 + 2*(box_w + gap), box_y, box_w, box_h, C_SWEEP,
     "SWEEP",
     sublabels=["Gitleaks 170+ patterns",
                "AES-256-CBC vault",
                "transcript scanner",
                "redact / delete / dry-run"],
     fontsize=8.5)

# Arrows: middle → bottom
arrow(ax, 5.0, 3.25, 5.0, 2.7)

# BOTTOM LAYER
rbox(ax, 0.4, 1.35, 9.2, 1.25, C_BOTTOM,
     "Immunity Feed — 217 Ed25519-signed advisories   ·   SQLite + JSONL Audit Trail",
     fontsize=8.5)

# Left/right data-flow arrows between boxes (bidirectional hints)
for cx in [0.45 + box_w + gap/2, 0.45 + 2*box_w + 1.5*gap]:
    ax.annotate("", xy=(cx + 0.05, box_y + box_h/2),
                xytext=(cx - 0.05, box_y + box_h/2),
                arrowprops=dict(arrowstyle='<->', color='#BDC3C7',
                                lw=1.0, mutation_scale=10), zorder=5)

# feed arrows up to each middle box
for cx in [0.45 + box_w/2, 0.45 + box_w + gap + box_w/2,
           0.45 + 2*(box_w + gap) + box_w/2]:
    arrow(ax, cx, 2.6, cx, 3.22, color='#8E9BA8')

# ── title ──────────────────────────────────────────────────────────────────────
ax.set_title("Prismor Defense-in-Depth Architecture",
             fontsize=12, fontweight='bold', color=TEXT, pad=8)

# ── layer annotation labels ────────────────────────────────────────────────────
for y_pos, lbl in [(7.0, "Input Layer"), (4.58, "Defense Layers"), (2.0, "Intelligence & Audit")]:
    ax.text(9.82, y_pos, lbl, ha='right', va='center', fontsize=7,
            color='#6B7280', style='italic', rotation=90)

plt.tight_layout()
plt.savefig('/home/ubuntu/projects/immunity-agent/workspace/figures/fig_prismor_system_architecture.png',
            dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()
print("fig_prismor_system_architecture saved")
