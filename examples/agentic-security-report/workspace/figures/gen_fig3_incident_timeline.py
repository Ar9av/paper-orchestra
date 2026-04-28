"""
fig_threat_incident_timeline
Horizontal timeline March 2025 – April 2026
Aspect ratio 16:9, 300 DPI
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime

BG   = '#FFFFFF'
TEXT = '#1A1A2E'
AXIS = '#CBD5E0'

# Severity colours
CRIT = '#C0392B'   # Critical – red
HIGH = '#E67E22'   # High     – orange
MED  = '#F1C40F'   # Medium   – yellow

severity_color = {'Critical': CRIT, 'High': HIGH, 'Medium': MED}

# Timeline endpoints (numeric months from March 2025 = 0)
START = datetime(2025, 3, 1)
END   = datetime(2026, 5, 1)

def to_x(dt):
    """Convert datetime to fraction of timeline."""
    total = (END - START).days
    return (dt - START).days / total

events = [
    (datetime(2025, 3, 15),  "Rules File Backdoor",              "High"),
    (datetime(2025, 4, 15),  "MCP Tool Poisoning",               "High"),
    (datetime(2025, 5, 20),  "GitHub MCP RCE",                   "Critical"),
    (datetime(2025, 7, 1),   "SANDWORM_MODE npm",                "Critical"),
    (datetime(2025, 7, 20),  "Malicious VS Code Ext. (1.5M)",    "High"),
    (datetime(2025, 9, 1),   "LangChain RCE\nCVSS 9.3",         "Critical"),
    (datetime(2026, 2, 15),  "8,000+ Exposed\nMCP Servers",      "Critical"),
    (datetime(2026, 3, 10),  "LiteLLM Supply\nChain Backdoor",   "Critical"),
    (datetime(2026, 4, 5),   "MCP SDK RCE\n150M+ Downloads",     "Critical"),
    (datetime(2026, 4, 20),  "Flowise RCE\nCVSS 10.0",          "Critical"),
]

# alternating above/below to avoid overlap
positions = [1, -1, 1, -1, 1, -1, 1, -1, 1, -1]

fig, ax = plt.subplots(figsize=(16, 6), dpi=300)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# ── timeline axis ──────────────────────────────────────────────────────────────
ax.axhline(0, color='#4A5568', linewidth=1.8, zorder=2)

# month ticks
months = []
dt = datetime(2025, 3, 1)
while dt <= datetime(2026, 5, 1):
    months.append(dt)
    m = dt.month + 1
    y = dt.year + (1 if m > 12 else 0)
    m = m if m <= 12 else m - 12
    dt = datetime(y, m, 1)

for m in months:
    xpos = to_x(m)
    ax.axvline(xpos, color=AXIS, linewidth=0.6, linestyle=':', zorder=1)
    label = m.strftime('%b\n%Y') if m.month in [1, 3, 6, 9, 12] else m.strftime('%b')
    ax.text(xpos, -0.08, label, ha='center', va='top', fontsize=6.5, color='#6B7280')

# ── events ─────────────────────────────────────────────────────────────────────
for (dt, label, sev), pos in zip(events, positions):
    x = to_x(dt)
    col = severity_color[sev]
    y_dot = 0
    y_text = pos * 0.42

    # stem
    ax.plot([x, x], [y_dot, y_text * 0.85], color=col,
            linewidth=1.2, zorder=3, alpha=0.7)
    # dot on axis
    ax.scatter(x, 0, s=80, color=col, zorder=5,
               edgecolors='white', linewidths=0.8)
    # label box
    va = 'bottom' if pos > 0 else 'top'
    ax.text(x, y_text, label, ha='center', va=va,
            fontsize=7, color=TEXT, fontweight='semibold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                      edgecolor=col, linewidth=0.8, alpha=0.95),
            zorder=6, multialignment='center')

# ── legend ─────────────────────────────────────────────────────────────────────
handles = [
    mpatches.Patch(color=CRIT, label='Critical'),
    mpatches.Patch(color=HIGH, label='High'),
    mpatches.Patch(color=MED,  label='Medium'),
]
ax.legend(handles=handles, loc='upper left', fontsize=9,
          framealpha=0.9, edgecolor=AXIS, title='Severity',
          title_fontsize=8)

# ── aesthetics ─────────────────────────────────────────────────────────────────
ax.set_xlim(-0.02, 1.04)
ax.set_ylim(-0.75, 0.75)
ax.set_title("Documented AI Coding Agent Security Incidents (March 2025–April 2026)",
             fontsize=13, fontweight='bold', color=TEXT, pad=12)
ax.axis('off')

# year bands
for year_start, year_end, label in [
    (datetime(2025, 3, 1),  datetime(2025, 12, 31), "2025"),
    (datetime(2026, 1, 1),  datetime(2026, 4, 30),  "2026"),
]:
    xs = to_x(year_start)
    xe = to_x(year_end)
    ax.text((xs + xe) / 2, -0.68, label, ha='center', va='bottom',
            fontsize=9, color='#4A5568', fontweight='bold')
    ax.annotate("", xy=(xe, -0.63), xytext=(xs, -0.63),
                arrowprops=dict(arrowstyle='<->', color='#4A5568', lw=1.2))

plt.tight_layout()
plt.savefig('/home/ubuntu/projects/immunity-agent/workspace/figures/fig_threat_incident_timeline.png',
            dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()
print("fig_threat_incident_timeline saved")
