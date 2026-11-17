#!/usr/bin/env python3
"""Generate on-brand, grounded charts for the MSME Idea Hackathon 6.0 deck.

All numbers come straight from the team's IEEE paper (main.tex) and repo readme.
No values are invented. Colors use the validated dataviz reference palette
(sequential/diverging blue; status green; muted reference gray).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import matplotlib.font_manager as fm
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT, exist_ok=True)

# ---- fonts (Carlito == Calibri-compatible, matches the slides) ----
for p in ["/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",
          "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf"]:
    if os.path.exists(p):
        fm.fontManager.addfont(p)
try:
    plt.rcParams["font.family"] = "Carlito"
except Exception:
    plt.rcParams["font.family"] = "DejaVu Sans"

# ---- palette (validated dataviz reference) ----
INK     = "#0b0b0b"
SECOND  = "#52514e"
MUTED   = "#7c7a75"
GRID    = "#e6e5df"
AXIS    = "#c3c2b7"
BLUE    = "#2a78d6"
BLUE_DK = "#184f95"
GREEN   = "#0ca30c"
REDX    = "#d03b3b"
CARD    = "#ffffff"

BLUE_SEQ = LinearSegmentedColormap.from_list(
    "blueseq", ["#eef4fd", "#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95", "#0d366b"])
DIVG = LinearSegmentedColormap.from_list(
    "divg", ["#0d366b", "#2a78d6", "#9ec5f4", "#f0efec", "#f2a6a5", "#d03b3b", "#8f1f21"])

plt.rcParams.update({
    "figure.facecolor": CARD, "axes.facecolor": CARD, "savefig.facecolor": CARD,
    "axes.edgecolor": AXIS, "axes.linewidth": 1.0,
    "text.color": INK, "axes.labelcolor": SECOND, "xtick.color": MUTED, "ytick.color": MUTED,
    "font.size": 13,
})

def clean(ax, grid_axis="y"):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=1.0, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)

# ============================================================
# CHART 1 — Phase-ordering trade-off (Factorial benchmark)
# code size (x) vs estimated cycles (y); Table II of the paper.
# Story: SAME six passes, different ORDER -> very different result.
# ============================================================
seqs = [
    ("Baseline (no optimization)", 40, 81, "base"),
    ("CF → CSE → CP → DCE → SR", 16, 55, "best"),
    ("CSE → CP → CF → DCE → SR", 18, 57, "mid"),
    ("CP → CF → DCE → CSE → SR", 19, 58, "mid"),
    ("CF → DCE → CSE → CP → SR", 21, 60, "mid"),
    ("CP → DCE → CF → CSE → SR", 22, 61, "mid"),
    ("DCE → CF → CSE → CP → SR", 33, 72, "weak"),
]
fig, ax = plt.subplots(figsize=(8.7, 5.1), dpi=200)
clean(ax, grid_axis="both")
# optimized cloud
for name, x, y, k in seqs:
    if k == "mid":
        ax.scatter(x, y, s=150, color=BLUE, edgecolor="white", linewidth=2, zorder=5)
# baseline
bx, by = 40, 81
ax.scatter(bx, by, s=200, marker="s", color=MUTED, edgecolor="white", linewidth=2, zorder=6)
ax.annotate("Baseline · 40 insts, 81 cycles", (bx, by), xytext=(0, 15),
            textcoords="offset points", ha="center", va="bottom", fontsize=12,
            color=SECOND, weight="bold")
# weak (DCE-first)
wx, wy = 33, 72
ax.scatter(wx, wy, s=150, color=BLUE, edgecolor="white", linewidth=2, zorder=5)
ax.annotate("DCE-first ordering\n(same passes, weak result)", (wx, wy), xytext=(11, -8),
            textcoords="offset points", ha="left", va="top", fontsize=11.5, color=SECOND)
# best (Seq1, CF-first)
gx, gy = 16, 55
ax.scatter(gx, gy, s=300, color=GREEN, edgecolor="white", linewidth=2.5, zorder=7)
ax.annotate("Best ordering: CF-first\n16 insts · 55 cycles", (gx, gy), xytext=(14, -2),
            textcoords="offset points", ha="left", va="center", fontsize=12.5,
            color="#0a7a0a", weight="bold")
# arrow baseline -> best
ax.annotate("", xy=(gx + 1.4, gy + 1.2), xytext=(bx - 1.2, by - 1.4),
            arrowprops=dict(arrowstyle="-|>", color="#0a7a0a", lw=2.0,
                            connectionstyle="arc3,rad=0.13", alpha=0.75), zorder=4)
ax.text(25.0, 64.5, "−60% code size\n−32% cycles", color="#0a7a0a",
        fontsize=12.5, weight="bold", ha="center")
ax.set_xlabel("Code size  (IR instruction count)", fontsize=13, color=SECOND)
ax.set_ylabel("Estimated cycles  (ARM Cortex-M cost model)", fontsize=13, color=SECOND)
ax.set_xlim(10, 45); ax.set_ylim(50, 86)
ax.text(0.012, 1.11, "Same 6 passes, different order — the result swings from 40 to 16 instructions",
        transform=ax.transAxes, fontsize=15, weight="bold", color=INK)
ax.text(0.012, 1.035, "Factorial micro-benchmark  ·  lower-left is better  ·  721 orderings evaluated",
        transform=ax.transAxes, fontsize=12, color=MUTED)
# tiny legend (identity not by color alone: shape + label)
from matplotlib.lines import Line2D
leg = [Line2D([0],[0], marker="s", color="none", markerfacecolor=MUTED, markersize=11, label="Baseline"),
       Line2D([0],[0], marker="o", color="none", markerfacecolor=BLUE, markersize=11, label="Optimized ordering"),
       Line2D([0],[0], marker="o", color="none", markerfacecolor=GREEN, markersize=12, label="Best ordering")]
ax.legend(handles=leg, loc="lower right", frameon=False, fontsize=11.5, handletextpad=0.4)
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(os.path.join(OUT, "chart_tradeoff.png"), dpi=200, bbox_inches="tight")
plt.close(fig)

# ============================================================
# CHART 2 — Best-ordering code-size reduction across 8 programs
# readme "Key Research Results". Single hue (magnitude).
# ============================================================
progs = [("factorial",60.0),("isqrt",46.0),("bitcount",42.4),("fibonacci",40.9),
         ("collatz",38.1),("sha_mix",35.8),("power",33.8),("gcd",33.3)]
progs = sorted(progs, key=lambda t: t[1])   # asc so largest on top in barh
names = [p[0] for p in progs]; vals = [p[1] for p in progs]
fig, ax = plt.subplots(figsize=(8.7, 5.1), dpi=200)
clean(ax, grid_axis="x")
ypos = np.arange(len(names))
bars = ax.barh(ypos, vals, height=0.62, color=BLUE, zorder=3)
bars[-1].set_color(GREEN)  # factorial (top) = best, tie to scatter
ax.set_yticks(ypos); ax.set_yticklabels(names, fontsize=13, color=INK)
ax.set_xlim(0, 70)
for i, v in enumerate(vals):
    ax.text(v + 1.0, i, f"{v:.1f}%", va="center", ha="left", fontsize=12.5,
            color=INK, weight="bold")
ax.set_xlabel("Code-size reduction vs unoptimized baseline", fontsize=13, color=SECOND)
ax.text(0.0, 1.11, "Every benchmark gets smaller — validated, output-equivalent code",
        transform=ax.transAxes, fontsize=15, weight="bold", color=INK)
ax.text(0.0, 1.035, "8 MiBench-adapted programs  ·  best ordering per program  ·  geometric-mean reduction 23.8%",
        transform=ax.transAxes, fontsize=12, color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(os.path.join(OUT, "chart_reduction_bars.png"), dpi=200, bbox_inches="tight")
plt.close(fig)

# ============================================================
# CHART 3 — Reduction heatmap: 6 sequences x 3 metrics (Table III)
# ============================================================
seq_labels = ["Seq 1  CF-first", "Seq 2", "Seq 3", "Seq 4", "Seq 5", "Seq 6  DCE-first"]
metrics = ["Code size", "Est. cycles", "Dynamic insts"]
data = np.array([
    [60.0, 32.1, 34.6],
    [55.0, 29.6, 32.1],
    [52.5, 28.4, 30.9],
    [47.5, 25.9, 28.4],
    [45.0, 24.7, 27.2],
    [17.5, 11.1,  8.6],
])
fig, ax = plt.subplots(figsize=(7.8, 5.0), dpi=200)
im = ax.imshow(data, cmap=BLUE_SEQ, aspect="auto", vmin=0, vmax=65)
ax.set_xticks(range(len(metrics))); ax.set_xticklabels(metrics, fontsize=12.5, color=INK)
ax.set_yticks(range(len(seq_labels))); ax.set_yticklabels(seq_labels, fontsize=12, color=INK)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
# 2px surface gaps
ax.set_xticks(np.arange(-.5, len(metrics), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(seq_labels), 1), minor=True)
ax.grid(which="minor", color=CARD, linewidth=3)
ax.tick_params(which="minor", length=0)
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        v = data[i, j]
        ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=12.5,
                color="white" if v > 33 else INK, weight="bold")
ax.text(0.0, 1.13, "Constant-Folding-first wins on every metric",
        transform=ax.transAxes, fontsize=15, weight="bold", color=INK)
ax.text(0.0, 1.05, "% reduction from baseline  ·  darker = larger reduction  ·  factorial benchmark",
        transform=ax.transAxes, fontsize=11.5, color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(os.path.join(OUT, "chart_reduction_heatmap.png"), dpi=200, bbox_inches="tight")
plt.close(fig)

# ============================================================
# CHART 4 (appendix) — Pass-interaction heatmap (Table IV), diverging
# value = code-size delta when running row-pass BEFORE col-pass
# negative (blue) = running A before B REDUCES size (good).
# ============================================================
rows = ["AS", "CF", "CP", "CSE", "DCE", "SR"]
cols = ["AS", "CF", "CP", "CSE", "DCE"]
mat = np.array([
    [ 0,  3,  2,  0,  -5],
    [-3,  0, -1, -3, -11],
    [-2,  1,  0, -2, -10],
    [ 0,  3,  2,  0,  -5],
    [ 5, 11, 10,  5,   0],
    [ 0,  3,  2,  0,  -5],
], dtype=float)
fig, ax = plt.subplots(figsize=(7.8, 5.4), dpi=200)
norm = TwoSlopeNorm(vmin=-11, vcenter=0, vmax=11)
im = ax.imshow(mat, cmap=DIVG, norm=norm, aspect="auto")
ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, fontsize=13, color=INK)
ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows, fontsize=13, color=INK)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xticks(np.arange(-.5, len(cols), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(rows), 1), minor=True)
ax.grid(which="minor", color=CARD, linewidth=3)
ax.tick_params(which="minor", length=0)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat[i, j]
        ax.text(j, i, f"{v:+.0f}" if v != 0 else "0", ha="center", va="center",
                fontsize=12.5, color="white" if abs(v) > 6 else INK, weight="bold")
ax.set_xlabel("second pass", fontsize=12.5, color=SECOND)
ax.set_ylabel("first pass", fontsize=12.5, color=SECOND)
ax.text(0.0, 1.15, "Why order matters: fold & propagate BEFORE eliminating dead code",
        transform=ax.transAxes, fontsize=14.5, weight="bold", color=INK)
ax.text(0.0, 1.07, "code-size change when running row-pass before column-pass  ·  blue = reduces size",
        transform=ax.transAxes, fontsize=11.5, color=MUTED)
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cbar.outline.set_visible(False); cbar.ax.tick_params(length=0, labelsize=10, colors=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.92))
fig.savefig(os.path.join(OUT, "chart_pass_interaction.png"), dpi=200, bbox_inches="tight")
plt.close(fig)

print("charts written to", OUT)
for f in sorted(os.listdir(OUT)):
    print("  ", f)
