"""
Trade-off Visualizer — Publication-Quality Graphs.

Generates research-grade visualizations for phase-ordering analysis:
1. Scatter plot: Code Size vs. Estimated Cycles (Pareto front)
2. Normalized bar chart (baseline = 1.0)
3. Pass interaction heatmap (pairwise A->B vs B->A)
4. Instruction category stacked bars
5. Reduction heatmap (% improvement from baseline)
6. Box plots: metric distributions across orderings
7. Dynamic vs static metric comparison
"""

from __future__ import annotations
import math
import os
from typing import Sequence

from compiler.benchmarks.metric_collector import BenchmarkMetrics

_plt = None
_np = None


def _ensure_matplotlib():
    global _plt, _np
    if _plt is None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        _plt = plt
    if _np is None:
        import numpy as np
        _np = np


def plot_tradeoff_scatter(
    results: Sequence[BenchmarkMetrics],
    title: str = "Phase-Ordering Trade-off: Code Size vs. Estimated Cycles",
    output_path: str = "tradeoff_scatter.png",
) -> str:
    """Scatter plot with Pareto front overlay."""
    _ensure_matplotlib()
    plt, np = _plt, _np

    fig, ax = plt.subplots(figsize=(10, 7))
    sizes = [r.code_size for r in results]
    cycles = [r.estimated_cycles for r in results]
    labels = [r.pass_order_label for r in results]

    scatter = ax.scatter(sizes, cycles, c=range(len(results)),
                         cmap="viridis", s=100, edgecolors="black", zorder=5)

    for i, label in enumerate(labels):
        short = label if len(label) < 30 else label[:27] + "..."
        ax.annotate(short, (sizes[i], cycles[i]),
                    textcoords="offset points", xytext=(8, 5),
                    fontsize=6, alpha=0.75)

    ax.set_xlabel("Code Size (instruction count)", fontsize=12)
    ax.set_ylabel("Estimated Cycles (weighted cost)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)

    pareto = _pareto_front(sizes, cycles)
    if len(pareto) > 1:
        p_sizes = [sizes[i] for i in pareto]
        p_cycles = [cycles[i] for i in pareto]
        paired = sorted(zip(p_sizes, p_cycles))
        ax.plot([p[0] for p in paired], [p[1] for p in paired],
                "r--", linewidth=1.5, alpha=0.7, label="Pareto front")
        ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_normalized_bars(
    results: Sequence[BenchmarkMetrics],
    title: str = "Normalized Performance (Baseline = 1.0)",
    output_path: str = "normalized_bars.png",
) -> str:
    """Bar chart with metrics normalized to baseline = 1.0."""
    _ensure_matplotlib()
    plt, np = _plt, _np

    baseline = next((r for r in results if not r.pass_order), None)
    if not baseline:
        return output_path

    optimized = [r for r in results if r.pass_order]
    if not optimized:
        return output_path

    labels = [r.pass_order_label for r in optimized]
    norm_size = [r.code_size / baseline.code_size if baseline.code_size else 1.0
                 for r in optimized]
    norm_cycles = [r.estimated_cycles / baseline.estimated_cycles if baseline.estimated_cycles else 1.0
                   for r in optimized]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.6), 6))
    ax.bar(x - width/2, norm_size, width, label="Code Size", color="#2196F3", edgecolor="black")
    ax.bar(x + width/2, norm_cycles, width, label="Est. Cycles", color="#FF9800", edgecolor="black")

    ax.axhline(y=1.0, color="red", linestyle="--", linewidth=1, alpha=0.7, label="Baseline")
    ax.set_xlabel("Pass Ordering", fontsize=11)
    ax.set_ylabel("Normalized Metric (1.0 = baseline)", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=7)
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_pass_interaction_heatmap(
    results: Sequence[BenchmarkMetrics],
    title: str = "Pass Interaction Matrix (Size: A->B vs B->A)",
    output_path: str = "pass_interaction.png",
) -> str:
    """Heatmap showing the effect of pass ordering on pairs.

    Cell (A, B) = code_size(A->B) - code_size(B->A).
    Negative means A->B is better (smaller code).
    """
    _ensure_matplotlib()
    plt, np = _plt, _np

    # Build lookup: tuple(pass_order) -> code_size
    lookup: dict[tuple[str, ...], int] = {}
    for r in results:
        key = tuple(r.pass_order)
        lookup[key] = r.code_size

    # Get unique pass names
    all_passes: set[str] = set()
    for r in results:
        all_passes.update(r.pass_order)
    passes = sorted(all_passes)

    n = len(passes)
    if n < 2:
        return output_path

    matrix = np.zeros((n, n))

    for i, a in enumerate(passes):
        for j, b in enumerate(passes):
            if i == j:
                matrix[i, j] = 0
            else:
                ab = lookup.get((a, b), None)
                ba = lookup.get((b, a), None)
                if ab is not None and ba is not None:
                    matrix[i, j] = ab - ba  # negative = A->B is better

    fig, ax = plt.subplots(figsize=(max(7, n * 1.2), max(6, n)))
    vmax = max(abs(matrix.min()), abs(matrix.max()), 1)
    im = ax.imshow(matrix, cmap="RdBu_r", aspect="auto", vmin=-vmax, vmax=vmax)

    ax.set_xticks(range(n))
    ax.set_xticklabels(passes, fontsize=10)
    ax.set_yticks(range(n))
    ax.set_yticklabels(passes, fontsize=10)
    ax.set_xlabel("Second Pass (B)", fontsize=11)
    ax.set_ylabel("First Pass (A)", fontsize=11)

    for i in range(n):
        for j in range(n):
            val = matrix[i, j]
            if val != 0:
                ax.text(j, i, f"{val:+.0f}", ha="center", va="center",
                        fontsize=9, color="black" if abs(val) < vmax * 0.6 else "white")

    ax.set_title(title, fontsize=13, fontweight="bold")
    fig.colorbar(im, ax=ax, label="Code Size Difference (A->B minus B->A)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_category_breakdown(
    results: Sequence[BenchmarkMetrics],
    title: str = "Instruction Category Breakdown by Ordering",
    output_path: str = "category_breakdown.png",
) -> str:
    """Stacked bar chart of instruction categories."""
    _ensure_matplotlib()
    plt, np = _plt, _np

    labels = [r.pass_order_label for r in results]
    categories = ["arithmetic", "comparison", "logical", "data_movement",
                  "control_flow", "function", "io"]
    colors = ["#E53935", "#1E88E5", "#43A047", "#FDD835",
              "#8E24AA", "#FB8C00", "#00ACC1"]

    data = {cat: [r.instruction_breakdown.get(cat, 0) for r in results]
            for cat in categories}

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.5), 6))

    bottom = np.zeros(len(labels))
    for cat, color in zip(categories, colors):
        values = np.array(data[cat], dtype=float)
        ax.bar(x, values, bottom=bottom, label=cat.replace("_", " ").title(),
               color=color, edgecolor="black", linewidth=0.5)
        bottom += values

    ax.set_xlabel("Pass Ordering", fontsize=11)
    ax.set_ylabel("Instruction Count", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=7)
    ax.legend(loc="upper right", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_reduction_heatmap(
    results: Sequence[BenchmarkMetrics],
    title: str = "Optimization Effectiveness (% Reduction from Baseline)",
    output_path: str = "reduction_heatmap.png",
) -> str:
    """Heatmap of percentage reduction across orderings."""
    _ensure_matplotlib()
    plt, np = _plt, _np

    baseline = next((r for r in results if not r.pass_order), None)
    optimized = [r for r in results if r.pass_order]
    if not baseline or not optimized:
        return output_path

    labels = [r.pass_order_label for r in optimized]
    size_red = [(1 - r.code_size / baseline.code_size) * 100 if baseline.code_size else 0
                for r in optimized]
    cycle_red = [(1 - r.estimated_cycles / baseline.estimated_cycles) * 100
                 if baseline.estimated_cycles else 0 for r in optimized]

    # Include dynamic metric if available
    rows = ["Code Size", "Est. Cycles"]
    data = [size_red, cycle_red]

    if baseline.dynamic_instruction_count > 0:
        dyn_red = [(1 - r.dynamic_instruction_count / baseline.dynamic_instruction_count) * 100
                   if baseline.dynamic_instruction_count else 0 for r in optimized]
        rows.append("Dynamic Insts")
        data.append(dyn_red)

    data_arr = np.array(data)

    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 0.7), 2 + len(rows)))
    vmax = max(abs(data_arr.min()), abs(data_arr.max()), 1)
    im = ax.imshow(data_arr, cmap="RdYlGn", aspect="auto", vmin=-5, vmax=max(50, vmax))

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=7)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=10)

    for i in range(len(rows)):
        for j in range(len(labels)):
            val = data_arr[i, j]
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                    fontsize=7, color="black" if abs(val) < 30 else "white")

    ax.set_title(title, fontsize=13, fontweight="bold")
    fig.colorbar(im, ax=ax, label="% Reduction")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_box_distributions(
    all_program_results: dict[str, Sequence[BenchmarkMetrics]],
    title: str = "Code Size Reduction Distribution Across Programs",
    output_path: str = "box_distributions.png",
) -> str:
    """Box plot showing distribution of code size reductions across orderings,
    for each benchmark program."""
    _ensure_matplotlib()
    plt, np = _plt, _np

    program_names = list(all_program_results.keys())
    reduction_data: list[list[float]] = []

    for name in program_names:
        results = all_program_results[name]
        baseline = next((r for r in results if not r.pass_order), None)
        if not baseline or baseline.code_size == 0:
            reduction_data.append([])
            continue
        reductions = [(1 - r.code_size / baseline.code_size) * 100
                      for r in results if r.pass_order]
        reduction_data.append(reductions)

    fig, ax = plt.subplots(figsize=(max(8, len(program_names) * 1.5), 6))
    bp = ax.boxplot(reduction_data, labels=program_names, patch_artist=True,
                    widths=0.6, showmeans=True, meanprops={"marker": "D", "markerfacecolor": "red"})

    colors = plt.cm.Set3(np.linspace(0, 1, len(program_names)))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)

    ax.set_xlabel("Benchmark Program", fontsize=12)
    ax.set_ylabel("Code Size Reduction (%)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, axis="y", alpha=0.3)
    ax.axhline(y=0, color="red", linestyle="--", alpha=0.5)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_dynamic_vs_static(
    results: Sequence[BenchmarkMetrics],
    title: str = "Static vs. Dynamic Instruction Count",
    output_path: str = "dynamic_vs_static.png",
) -> str:
    """Compare static code size with dynamic instruction count."""
    _ensure_matplotlib()
    plt, np = _plt, _np

    has_dynamic = any(r.dynamic_instruction_count > 0 for r in results)
    if not has_dynamic:
        return output_path

    labels = [r.pass_order_label for r in results]
    static = [r.code_size for r in results]
    dynamic = [r.dynamic_instruction_count for r in results]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(max(10, len(labels) * 0.6), 6))
    ax1.bar(x - width/2, static, width, label="Static Code Size", color="#2196F3", edgecolor="black")
    ax1.set_ylabel("Static Instructions", color="#2196F3", fontsize=11)

    ax2 = ax1.twinx()
    ax2.bar(x + width/2, dynamic, width, label="Dynamic Insts", color="#4CAF50", edgecolor="black")
    ax2.set_ylabel("Dynamic Instructions (executed)", color="#4CAF50", fontsize=11)

    ax1.set_xlabel("Pass Ordering", fontsize=11)
    ax1.set_title(title, fontsize=14, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=55, ha="right", fontsize=7)

    l1, lb1 = ax1.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lb1 + lb2, loc="upper right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def generate_all_plots(
    results: Sequence[BenchmarkMetrics],
    output_dir: str = "benchmark_results",
    program_name: str = "",
    all_program_results: dict[str, Sequence[BenchmarkMetrics]] | None = None,
) -> list[str]:
    """Generate all visualizations. Returns list of file paths."""
    os.makedirs(output_dir, exist_ok=True)
    prefix = f"{program_name}_" if program_name else ""

    paths = [
        plot_tradeoff_scatter(
            results,
            title=f"Phase-Ordering Trade-off{f': {program_name}' if program_name else ''}",
            output_path=os.path.join(output_dir, f"{prefix}tradeoff_scatter.png"),
        ),
        plot_normalized_bars(
            results,
            title=f"Normalized Performance{f': {program_name}' if program_name else ''}",
            output_path=os.path.join(output_dir, f"{prefix}normalized_bars.png"),
        ),
        plot_pass_interaction_heatmap(
            results,
            title=f"Pass Interaction{f': {program_name}' if program_name else ''}",
            output_path=os.path.join(output_dir, f"{prefix}pass_interaction.png"),
        ),
        plot_category_breakdown(
            results,
            title=f"Instruction Breakdown{f': {program_name}' if program_name else ''}",
            output_path=os.path.join(output_dir, f"{prefix}category_breakdown.png"),
        ),
        plot_reduction_heatmap(
            results,
            output_path=os.path.join(output_dir, f"{prefix}reduction_heatmap.png"),
        ),
        plot_dynamic_vs_static(
            results,
            title=f"Static vs. Dynamic{f': {program_name}' if program_name else ''}",
            output_path=os.path.join(output_dir, f"{prefix}dynamic_vs_static.png"),
        ),
    ]

    # Cross-program box plot (only when all results provided)
    if all_program_results and len(all_program_results) > 1:
        paths.append(
            plot_box_distributions(
                all_program_results,
                output_path=os.path.join(output_dir, "cross_program_box.png"),
            )
        )

    return [p for p in paths if p]


def compute_geomean_summary(
    all_program_results: dict[str, Sequence[BenchmarkMetrics]],
) -> dict[str, dict[str, float]]:
    """Compute geometric mean of normalized metrics across programs.

    Returns: {ordering_label: {metric_name: geomean_value}}
    Per Fleming & Wallace (1986), geometric mean is the correct
    aggregation for normalized performance ratios.
    """
    # Collect all ordering labels
    all_labels: set[str] = set()
    for results in all_program_results.values():
        for r in results:
            all_labels.add(r.pass_order_label)

    summary: dict[str, dict[str, float]] = {}

    for label in sorted(all_labels):
        size_ratios: list[float] = []
        cycle_ratios: list[float] = []
        dyn_ratios: list[float] = []

        for prog_name, results in all_program_results.items():
            baseline = next((r for r in results if not r.pass_order), None)
            target = next((r for r in results if r.pass_order_label == label), None)

            if not baseline or not target:
                continue

            if baseline.code_size > 0:
                size_ratios.append(target.code_size / baseline.code_size)
            if baseline.estimated_cycles > 0:
                cycle_ratios.append(target.estimated_cycles / baseline.estimated_cycles)
            if baseline.dynamic_instruction_count > 0 and target.dynamic_instruction_count > 0:
                dyn_ratios.append(target.dynamic_instruction_count / baseline.dynamic_instruction_count)

        summary[label] = {
            "geomean_size": _geomean(size_ratios) if size_ratios else 1.0,
            "geomean_cycles": _geomean(cycle_ratios) if cycle_ratios else 1.0,
            "geomean_dynamic": _geomean(dyn_ratios) if dyn_ratios else 1.0,
        }

    return summary


def _geomean(values: list[float]) -> float:
    """Geometric mean of a list of positive values."""
    if not values:
        return 1.0
    log_sum = sum(math.log(max(v, 1e-10)) for v in values)
    return math.exp(log_sum / len(values))


def _pareto_front(xs: list[int], ys: list[float]) -> list[int]:
    """Find indices on the Pareto front (minimizing both x and y)."""
    n = len(xs)
    is_pareto = [True] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if xs[j] <= xs[i] and ys[j] <= ys[i] and (xs[j] < xs[i] or ys[j] < ys[i]):
                is_pareto[i] = False
                break
    return [i for i in range(n) if is_pareto[i]]
