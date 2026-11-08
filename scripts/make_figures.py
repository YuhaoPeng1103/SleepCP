"""Paper figures for SleepCP.

Every figure is built from the per-run JSON files written by ``run_sacp.py``
and ``run_subject_aci.py``, and from the epoch-level export written by
``export_hypnogram.py`` (passed with ``--epoch-sets``).  Per-subject
coverage is merged across folds before any worst-subject or p10 statistic is
computed, because the subject-wise folds partition the cohort: each subject is
tested exactly once over the five folds, so the merged dict is a cohort-level
statistic rather than an average of overlapping ones.

The palette is the validated categorical order from the project's dataviz
reference (blue, orange, aqua, yellow, magenta).  Adjacent pairs clear the CVD
and normal-vision gates; the three lower-contrast slots always carry a visible
label, which the reference palette requires.  Scatter plots use only the first
three slots, the documented all-pairs-safe cap.

Usage:
    python scripts/make_figures.py --root results/main --out paper/figures
    python scripts/make_figures.py --demo --out paper/figures
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

# Validated categorical slots, in the reference order.
C_BLUE = "#2a78d6"
C_ORANGE = "#eb6834"
C_AQUA = "#1baf7a"
C_YELLOW = "#eda100"
C_MAGENTA = "#e87ba4"

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8983"
SURFACE = "#fcfcfb"
GRID = "#e4e3df"

STAGE_NAMES = ["W", "N1", "N2", "N3", "REM"]

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans",
        "font.size": 7.5,
        "axes.labelsize": 7.5,
        "axes.titlesize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.6,
        "axes.labelcolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "text.color": INK,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "grid.linestyle": "-",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "pdf.fonttype": 42,
    }
)


# --------------------------------------------------------------------------
# data loading
# --------------------------------------------------------------------------
def load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def merge_subject_coverage(entries: list[dict]) -> dict[str, float]:
    """One coverage value per subject, averaged over the runs that contain it.

    The folds partition the cohort, so each subject appears once per run; the
    seeds and backbones re-run the same partition. A plain ``dict.update``
    would let the last run read decide every subject, which is not the
    statistic the tables report. Averaging keeps the figure and the tables on
    the same definition.
    """
    total: dict[str, float] = {}
    count: dict[str, int] = {}
    for entry in entries:
        for subject, value in entry.get("per_subject_coverage", {}).items():
            key = str(subject)
            total[key] = total.get(key, 0.0) + float(value)
            count[key] = count.get(key, 0) + 1
    return {subject: total[subject] / count[subject] for subject in total}


def discover(root: Path, pattern: str) -> list[Path]:
    return sorted(root.rglob(pattern))


def collect(root: Path, pattern: str = "sacp.json") -> list[dict]:
    return [load(p) for p in discover(root, pattern)]


def budget_series(runs: list[dict], budget: int) -> dict:
    """Merged statistics for one warm-up budget across all runs."""
    entries = [r["budget_curve"][str(budget)] for r in runs if str(budget) in r.get("budget_curve", {})]
    if not entries:
        return {}
    merged = merge_subject_coverage(entries)
    values = np.asarray(list(merged.values()), dtype=float)
    return {
        "coverage": float(np.mean([e["coverage"] for e in entries])),
        "set_size": float(np.mean([e["set_size"] for e in entries])),
        "singleton_rate": float(np.mean([e["singleton_rate"] for e in entries])),
        "worst_subject_coverage": float(values.min()) if values.size else np.nan,
        "p10_subject_coverage": float(np.quantile(values, 0.1)) if values.size else np.nan,
        "subject_violation_rate": float((values < 0.9).mean()) if values.size else np.nan,
        "per_subject": merged,
        "n_runs": len(entries),
    }


def method_entry(runs: list[dict], key: str) -> dict:
    entries = [r[key] for r in runs if r.get(key)]
    if not entries:
        return {}
    merged = merge_subject_coverage(entries)
    values = np.asarray(list(merged.values()), dtype=float)
    return {
        "coverage": float(np.mean([e["coverage"] for e in entries])),
        "set_size": float(np.mean([e["set_size"] for e in entries])),
        "singleton_rate": float(np.mean([e["singleton_rate"] for e in entries])),
        "worst_subject_coverage": float(values.min()) if values.size else np.nan,
        "p10_subject_coverage": float(np.quantile(values, 0.1)) if values.size else np.nan,
        "subject_violation_rate": float((values < 0.9).mean()) if values.size else np.nan,
        "per_subject": merged,
        "n_runs": len(entries),
    }


# --------------------------------------------------------------------------
# figure helpers
# --------------------------------------------------------------------------
def _finish(fig, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out / name}.pdf")


def _nominal_line(ax, alpha: float, annotate: bool = True):
    label = f"nominal {int(round((1 - alpha) * 100))}%"
    # Dashed and drawn above the series: the marginal coverage curve sits on
    # top of the nominal value in the budget figure, and a solid line at the
    # same height would be invisible exactly where the reader needs it.
    # Legend entry only when the label is not written inside the plot.
    line = ax.axhline(
        1.0 - alpha,
        color=MUTED,
        lw=0.9,
        ls=(0, (4, 2)),
        zorder=4,
        label=None if annotate else label,
    )
    if annotate:
        ax.annotate(
            label,
            xy=(0.012, 1.0 - alpha),
            xycoords=("axes fraction", "data"),
            ha="left",
            va="bottom",
            fontsize=6.5,
            color=INK2,
        )
    return line


def _direct_label(ax, x, y, text, color, dx=0.0, dy=0.0, ha="left"):
    ax.annotate(
        text,
        xy=(x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        color=color,
        fontsize=7,
        fontweight="medium",
        ha=ha,
        va="center",
    )


# --------------------------------------------------------------------------
# fig 1: coverage vs label budget
# --------------------------------------------------------------------------
def fig_budget(runs: list[dict], budgets: list[int], alpha: float, out: Path) -> None:
    series = {b: budget_series(runs, b) for b in budgets}
    series = {b: s for b, s in series.items() if s}
    if not series:
        print("skip fig_budget: no budget curve")
        return
    bs = sorted(series)
    x = np.arange(len(bs))
    nominal = 1.0 - alpha

    fig, axes = plt.subplots(1, 2, figsize=(5.2, 2.3), sharex=True)
    ax_cov, ax_size = axes

    cov = np.array([series[b]["coverage"] for b in bs])
    worst = np.array([series[b]["worst_subject_coverage"] for b in bs])
    p10 = np.array([series[b]["p10_subject_coverage"] for b in bs])
    ax_cov.plot(x, cov, color=C_BLUE, lw=1.6, marker="o", ms=4.0, zorder=3, label="marginal")
    ax_cov.plot(x, p10, color=C_AQUA, lw=1.6, marker="o", ms=4.0, zorder=3, label="$p_{10}$ subject")
    ax_cov.plot(x, worst, color=C_ORANGE, lw=1.6, marker="o", ms=4.0, zorder=3, label="worst subject")
    _nominal_line(ax_cov, alpha, annotate=False)
    ax_cov.legend(loc="lower right", handlelength=1.4, borderaxespad=0.25, labelspacing=0.25)
    ax_cov.set_ylabel("coverage")
    ax_cov.set_title("Coverage", loc="left", color=INK)
    # Full-scale-from-zero would hide a ten-point gap; from 0 is honest but
    # unreadable, so the axis starts at 0.5 and the tick labels say where.
    ax_cov.set_ylim(0.5, 1.0)
    ax_cov.grid(axis="y", zorder=0)

    size = np.array([series[b]["set_size"] for b in bs])
    ax_size.plot(x, size, color=C_BLUE, lw=1.6, marker="o", ms=4.0, zorder=3)
    ax_size.set_ylabel("mean set size")
    ax_size.set_title("Efficiency", loc="left", color=INK)
    # Anchor the axis at the one-label floor so the reader sees the real
    # magnitude rather than a swing within a narrow window.
    ax_size.set_ylim(1.0, max(3.0, float(size.max()) + 0.3))
    ax_size.grid(axis="y", zorder=0)

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels([str(b) for b in bs])
        ax.set_xlabel("warm-up epochs per subject")

    fig.tight_layout()
    _finish(fig, out, "fig1_budget")


# --------------------------------------------------------------------------
# fig 2: per-subject coverage, global vs SACP
# --------------------------------------------------------------------------
def fig_subject_dumbbell(runs: list[dict], budget: int, alpha: float, out: Path) -> None:
    g = method_entry(runs, "global")
    s = budget_series(runs, budget)
    if not g or not s:
        print("skip fig_subject_dumbbell: missing global or budget entry")
        return
    subjects = sorted(set(g["per_subject"]) & set(s["per_subject"]), key=lambda k: g["per_subject"][k])
    if not subjects:
        return
    gv = np.array([g["per_subject"][k] for k in subjects])
    sv = np.array([s["per_subject"][k] for k in subjects])
    y = np.arange(len(subjects))

    fig, ax = plt.subplots(figsize=(3.4, 0.11 * len(subjects) + 0.7))
    for yi, a, b in zip(y, gv, sv):
        ax.plot([a, b], [yi, yi], color=MUTED, lw=1.0, zorder=2, solid_capstyle="round")
    ax.scatter(gv, y, s=14, color=C_BLUE, zorder=3, label="global CP", linewidths=0)
    ax.scatter(sv, y, s=14, color=C_ORANGE, zorder=3, label=f"SACP (m={budget})", linewidths=0)
    _nominal_line(ax, alpha)

    ax.set_yticks(y)
    ax.set_yticklabels(subjects, fontsize=6.5)
    ax.set_ylim(-0.8, len(subjects) - 0.2)
    ax.set_xlim(min(gv.min(), sv.min()) - 0.03, 1.0)
    ax.set_xlabel("per-subject coverage")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
    ax.grid(axis="x", zorder=0)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.005), ncol=2, handletextpad=0.2)
    fig.tight_layout()
    _finish(fig, out, "fig2_subjects")


# --------------------------------------------------------------------------
# fig 2b: per-subject coverage, global CP vs per-patient ACI
# --------------------------------------------------------------------------
def fig_subject_aci(runs: list[dict], alpha: float, out: Path) -> None:
    """Dumbbell of per-subject coverage for the two score families.

    Each segment runs from the pooled-calibration coverage of one patient to
    its coverage under an independent ACI stream for that patient. The two
    panels are the two scores, so the reader can see that the equalisation is
    a property of the adaptation rule rather than of the score.
    """
    panels = [("aps", "APS"), ("deficit", "smoothed deficit")]
    panels = [(k, lab) for k, lab in panels if any(f"global_{k}" in r.get("methods", {}) for r in runs)]
    if not runs or not panels:
        print("skip fig_subject_aci: no subject_aci.json files")
        return

    # Merge once so that every panel uses the same subject order and the same
    # x-limits; otherwise the reader cannot compare panels at a glance.
    data = {}
    for key, _label in panels:
        glob = merge_subject_coverage(
            [r["methods"][f"global_{key}"] for r in runs if f"global_{key}" in r.get("methods", {})]
        )
        aci = merge_subject_coverage(
            [r["methods"][f"subject_aci_{key}"] for r in runs if f"subject_aci_{key}" in r.get("methods", {})]
        )
        data[key] = (glob, aci, sorted(set(glob) & set(aci)))
    all_subjects = sorted({s for _g, _a, common in data.values() for s in common})
    if not all_subjects:
        print("skip fig_subject_aci: no merged per-subject coverage")
        return
    # Order patients by their pooled coverage in the first panel, so the
    # hardest patients sit at the bottom of both panels.
    first_glob = data[panels[0][0]][0]
    order = sorted(all_subjects, key=lambda k: first_glob.get(k, 1.0))

    lo = min(
        min(glob[k], aci[k])
        for glob, aci, _c in data.values()
        for k in order
        if k in glob and k in aci
    )
    lo = min(lo - 0.02, 1.0 - alpha - 0.06)

    fig, axes = plt.subplots(1, len(panels), figsize=(3.6 * len(panels), 3.2),
                             sharex=True, squeeze=False)
    for ax, (key, label) in zip(axes[0], panels):
        glob, aci, _common = data[key]
        subjects = [k for k in order if k in glob and k in aci]
        gv = np.array([glob[k] for k in subjects])
        av = np.array([aci[k] for k in subjects])
        y = np.arange(len(subjects))
        for yi, a, b in zip(y, gv, av):
            ax.plot([a, b], [yi, yi], color=MUTED, lw=0.9, zorder=2, solid_capstyle="round")
        ax.scatter(gv, y, s=13, color=C_BLUE, zorder=3, linewidths=0, label="global CP")
        ax.scatter(av, y, s=13, color=C_ORANGE, zorder=3, linewidths=0,
                   label="per-patient ACI")
        _nominal_line(ax, alpha, annotate=False)
        ax.set_yticks(y)
        ax.set_yticklabels(subjects, fontsize=6.0)
        ax.set_ylim(-0.8, len(order) - 0.2)
        ax.set_xlim(lo, 1.0)
        ax.set_xlabel("per-patient coverage")
        ax.set_title(label, loc="left", color=INK)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
        ax.grid(axis="x", zorder=0)
        # The dispersion, not the count of improvements, is the quantity the
        # figure is about: a good method moves every patient toward nominal,
        # which includes moving the over-covered ones down.
        ax.set_title(
            f"SD {gv.std(ddof=1):.3f} $\\to$ {av.std(ddof=1):.3f}",
            loc="right", fontsize=6.5, color=INK2,
        )
    handles = [
        plt.Line2D([], [], marker="o", ls="", ms=4, color=C_BLUE, label="global CP"),
        plt.Line2D([], [], marker="o", ls="", ms=4, color=C_ORANGE, label="per-patient ACI"),
        plt.Line2D([], [], ls="-", lw=0.8, color=MUTED,
                   label=f"nominal {int(round((1 - alpha) * 100))}%"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.02), handletextpad=0.3, fontsize=7)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _finish(fig, out, "fig2_subjects")


# --------------------------------------------------------------------------
# fig 3: efficiency / reliability Pareto frontier
# --------------------------------------------------------------------------
def fig_pareto(runs: list[dict], budgets: list[int], out: Path) -> None:
    g = method_entry(runs, "global")
    o = method_entry(runs, "oracle")
    path = {b: budget_series(runs, b) for b in budgets}
    path = {b: s for b, s in path.items() if s}
    if not g or not path:
        print("skip fig_pareto: missing data")
        return

    fig, ax = plt.subplots(figsize=(3.9, 2.7))
    # Budget 0 is the global predictor by construction, so it is drawn once,
    # as the blue global anchor, rather than duplicated as a frontier point.
    bs = [b for b in sorted(path) if b > 0] or sorted(path)
    sx = np.array([path[b]["set_size"] for b in bs])
    sy = np.array([path[b]["worst_subject_coverage"] for b in bs])

    # A line through points that sit on top of each other draws a meaningless
    # zig-zag. Only connect when the frontier actually spans the x-axis.
    x_span = float(sx.max() - sx.min())
    x_range = float(np.ptp(np.concatenate([[g["set_size"]], sx]))) or 1.0
    if sx.size > 1 and x_span > 0.05 * x_range:
        ax.plot(sx, sy, color=C_ORANGE, lw=1.2, zorder=2, alpha=0.9)

    # Direct labels, not a legend: the seven budget points collapse into a
    # cluster a tenth of a label wide, so a legend marker would sit on top of
    # them and read as an eighth point.
    ax.scatter(sx, sy, s=22, color=C_ORANGE, zorder=3, linewidths=0)
    ax.scatter([g["set_size"]], [g["worst_subject_coverage"]], s=46, color=C_BLUE,
               zorder=4, linewidths=0)
    if o:
        ax.scatter([o["set_size"]], [o["worst_subject_coverage"]], s=46, color=C_AQUA,
                   zorder=4, linewidths=0)

    ax.set_xlabel("mean set size  (smaller is cheaper)")
    ax.set_ylabel("worst-subject coverage  (higher is safer)")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))

    # Autoscaling here would magnify differences of a hundredth of a label
    # into a visible trend. The limits are set so that the axis spans a range
    # in which the flatness of the deployable path is what the eye reads.
    xs = np.concatenate([sx, [g["set_size"]]] + ([[o["set_size"]]] if o else []))
    ys = np.concatenate([sy, [g["worst_subject_coverage"]]]
                        + ([[o["worst_subject_coverage"]]] if o else []))
    ax.set_xlim(float(xs.min()) - 0.045, float(xs.max()) + 0.045)
    ax.set_ylim(float(ys.min()) - 0.012, float(ys.max()) + 0.012)
    ax.grid(True, zorder=0)

    ax.annotate(
        f"SACP, $m\\in$[{bs[0]}, {bs[-1]}]",
        xy=(float(np.median(sx)), float(sy.max())),
        xytext=(-12, 10),
        textcoords="offset points",
        ha="center",
        va="bottom",
        color=INK2,
        fontsize=7,
    )
    ax.annotate(
        "global CP",
        xy=(g["set_size"], g["worst_subject_coverage"]),
        xytext=(7, -8),
        textcoords="offset points",
        ha="left",
        va="top",
        color=INK2,
        fontsize=7,
    )
    if o:
        ax.annotate(
            "oracle (test labels)",
            xy=(o["set_size"], o["worst_subject_coverage"]),
            xytext=(8, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            color=INK2,
            fontsize=7,
        )
    fig.tight_layout()

    _finish(fig, out, "fig3_pareto")


# --------------------------------------------------------------------------
# fig 4: hypnogram with prediction sets
# --------------------------------------------------------------------------
def fig_hypnogram(epoch_path: Path, out: Path, window: int = 160) -> None:
    """True hypnogram above one row of prediction sets per construction."""
    if not epoch_path.exists():
        print(f"skip fig_hypnogram: {epoch_path} not found")
        return
    with np.load(epoch_path, allow_pickle=False) as data:
        labels = data["labels"].astype(int)
        starts = int(data["start"]) if "start" in data.files else 0
        windowed = bool(data["windowed"]) if "windowed" in data.files else False
        # Older exports name the two rows differently; accept either.
        aliases = {"global_sets": "global_aps", "sacp_sets": "sacp"}
        available = {aliases.get(k, k): data[k].astype(bool) for k in data.files if k.endswith("_sets") or k in
                     {"global_aps", "smooth_aps", "deficit", "aci"}}
    # Three rows, not four: the smoothed-APS row sits between the pooled and
    # the deficit rows and adds a colour without adding an argument.
    order = [("global_aps", "pooled APS"), ("deficit", "smoothed deficit"),
             ("aci", "per-patient ACI")]
    rows = [(key, label) for key, label in order if key in available]
    if not rows:
        print("skip fig_hypnogram: no set arrays in the export")
        return

    # ``windowed`` exports are already cut to the window and ``start`` records
    # where the window sits inside the recording, so it must not be reused as
    # an array index. Older exports carry the full recording instead.
    if not windowed and labels.size > window:
        lo = max(0, min(starts, labels.size - 1))
        labels = labels[lo:lo + window]
        available = {k: v[lo:lo + window] for k, v in available.items()}
    elif windowed and labels.size > window:
        labels = labels[:window]
        available = {k: v[:window] for k, v in available.items()}
    sets_by_row = [(label, available[key]) for key, label in rows]
    T = labels.size
    t = np.arange(T)

    n_rows = 1 + len(sets_by_row)
    fig = plt.figure(figsize=(7.0, 0.60 * n_rows + 1.15))
    gs = fig.add_gridspec(n_rows, 1, height_ratios=[1.15] + [1.0] * len(sets_by_row), hspace=0.34)
    ax_hyp = fig.add_subplot(gs[0])
    set_axes = [fig.add_subplot(gs[i + 1], sharex=ax_hyp) for i in range(len(sets_by_row))]

    ax_hyp.step(t, labels, where="post", color=INK, lw=1.1)
    ax_hyp.set_yticks(range(5))
    ax_hyp.set_yticklabels(STAGE_NAMES)
    ax_hyp.invert_yaxis()
    ax_hyp.set_ylabel("true stage")
    ax_hyp.set_title("Hypnogram (30 s epochs)", loc="left", color=INK)
    ax_hyp.grid(axis="y", zorder=0)
    ax_hyp.tick_params(labelbottom=False)

    colors = [C_BLUE, C_BLUE, C_ORANGE, C_AQUA]
    for ax, (label, sets), colour in zip(set_axes, sets_by_row, colors):
        # pcolormesh rather than imshow: a masked imshow antialiases the row
        # boundaries and leaves hairline artifacts across the whole panel.
        ax.pcolormesh(
            np.arange(T + 1) - 0.5,
            np.arange(6) - 0.5,
            np.ma.masked_where(~sets.T, np.zeros_like(sets.T, dtype=float)),
            cmap=matplotlib.colors.ListedColormap([to_rgba(colour, 0.5)]),
            vmin=0.0, vmax=1.0, shading="flat", antialiased=False, zorder=2,
        )
        # Mark the true class so the reader can see coverage without decoding
        # the hypnogram above.
        ax.scatter(t, labels, s=5, color=INK, zorder=4, linewidths=0)
        cov = sets[np.arange(T), labels].mean()
        ax.set_yticks(range(5))
        ax.set_yticklabels(STAGE_NAMES)
        # A one-line title over each panel keeps the long label out of the
        # left margin, where it collided with the panel above.
        ax.set_title(
            f"{label}   {label_size(sets):.2f} labels/epoch, coverage {cov:.2f}",
            loc="left", fontsize=6.8, color=INK2, pad=2,
        )
        ax.set_ylim(4.5, -0.5)
        ax.tick_params(labelbottom=False)

    last = set_axes[-1]
    last.set_xlabel("epoch within recording")
    last.set_xlim(-0.5, T - 0.5)
    last.tick_params(labelbottom=True)
    for ax in [ax_hyp] + set_axes[:-1]:
        ax.tick_params(axis="x", length=0)
    # No tight_layout here: the GridSpec fixes its own spacing, and calling
    # tight_layout on it triggers "Axes not compatible" and can move panels.
    _finish(fig, out, "fig4_hypnogram")


def label_size(sets: np.ndarray) -> float:
    """Mean number of labels per epoch."""
    return float(sets.sum(axis=1).mean())


# --------------------------------------------------------------------------
# demo data
# --------------------------------------------------------------------------
def demo_runs() -> list[dict]:
    rng = np.random.default_rng(0)
    subjects = [f"SC{400 + i:02d}" for i in range(20)]
    budgets = [0, 10, 20, 40, 80, 160, 320]
    runs = []
    for _ in range(5):
        base = {s: float(rng.normal(0.90, 0.035)) for s in subjects}
        curve = {}
        for m in budgets:
            shrink = 0.0 if m == 0 else 1.0 - np.exp(-m / 60.0)
            per = {s: float(np.clip(base[s] + shrink * (0.90 - base[s]) * 0.75, 0.5, 1.0)) for s in subjects}
            curve[str(m)] = {
                "coverage": float(np.mean(list(per.values())) + 0.004),
                "per_subject_coverage": per,
                "set_size": float(2.55 - 0.25 * shrink + rng.normal(0, 0.02)),
                "singleton_rate": float(0.48 + 0.10 * shrink),
            }
        gp = {s: float(np.clip(base[s], 0.5, 1.0)) for s in subjects}
        runs.append(
            {
                "budget_curve": curve,
                "global": {
                    "coverage": float(np.mean(list(gp.values())) + 0.004),
                    "per_subject_coverage": gp,
                    "set_size": 2.55,
                    "singleton_rate": 0.48,
                },
                "oracle": {
                    "coverage": 0.902,
                    "per_subject_coverage": {s: 0.902 for s in subjects},
                    "set_size": 2.15,
                    "singleton_rate": 0.62,
                },
            }
        )
    return runs


def demo_epoch_sets() -> dict:
    rng = np.random.default_rng(1)
    T = 400
    labels = np.zeros(T, dtype=int)
    # A plausible overnight sequence with a couple of REM bouts.
    labels[:40] = 0
    labels[40:110] = 2
    labels[110:150] = 3
    labels[150:190] = 2
    labels[190:230] = 4
    labels[230:300] = 2
    labels[300:330] = 1
    labels[330:370] = 2
    labels[370:] = 4
    global_sets = np.zeros((T, 5), dtype=bool)
    sacp_sets = np.zeros((T, 5), dtype=bool)
    for t in range(T):
        confusion = rng.random() < 0.15
        true = labels[t] if not confusion else int(rng.integers(0, 5))
        global_sets[t, true] = True
        sacp_sets[t, true] = True
        if rng.random() < 0.35:
            global_sets[t, int(rng.integers(0, 5))] = True
        if rng.random() < 0.18:
            sacp_sets[t, int(rng.integers(0, 5))] = True
    return {"labels": labels, "global_sets": global_sets, "sacp_sets": sacp_sets, "start": 60}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("results/main"))
    parser.add_argument("--out", type=Path, default=Path("paper/figures"))
    parser.add_argument("--alpha", type=float, default=0.1)
    parser.add_argument("--budget", type=int, default=20)
    parser.add_argument("--budgets", type=int, nargs="+", default=[0, 10, 20, 40, 80, 160, 320])
    parser.add_argument("--epoch-sets", type=Path, default=None)
    parser.add_argument("--demo", action="store_true", help="build figures from synthetic data")
    args = parser.parse_args()

    if args.demo:
        runs = demo_runs()
        # Demo artefacts stay out of the figure directory: the only files there
        # should be the ones the manuscript includes.
        epoch_path = args.out / "demo" / "_demo_epoch_sets.npz"
        epoch_path.parent.mkdir(parents=True, exist_ok=True)
        args.out.mkdir(parents=True, exist_ok=True)
        np.savez(epoch_path, **demo_epoch_sets())
    else:
        runs = collect(args.root, "sacp.json")
        if not runs:
            print("no sacp.json files found; pass --demo to preview the figures")
            return
        epoch_path = args.epoch_sets
        if epoch_path is None:
            print(
                "no --epoch-sets given; skipping the hypnogram figure "
                "(export one with scripts/export_hypnogram.py, see README)"
            )

    fig_budget(runs, args.budgets, args.alpha, args.out)
    aci_runs = collect(args.root, "subject_aci.json")
    if aci_runs:
        fig_subject_aci(aci_runs, args.alpha, args.out)
    else:
        fig_subject_dumbbell(runs, args.budget, args.alpha, args.out)
    fig_pareto(runs, args.budgets, args.out)
    if epoch_path is not None:
        fig_hypnogram(epoch_path, args.out)


if __name__ == "__main__":
    main()
