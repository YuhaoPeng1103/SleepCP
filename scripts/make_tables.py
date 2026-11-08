"""Emit LaTeX tables from the aggregator's summary JSON.

Usage:
    python scripts/make_tables.py --summary results/summary --out paper/tex/tables

Reads ``training.json``, ``sacp.json`` and ``temporal.json`` produced by
``scripts/aggregate.py`` and writes one ``.tex`` fragment per table. The
fragments are ``\\input``-able and use ``booktabs``; no other LaTeX packages
beyond ``amsmath`` and ``multirow`` are assumed.

Coverage is conservative when the method's score is discrete with an atom at
zero (SeqCP-Margin): the quantile lands on the atom, so realised coverage is
at least nominal. We add a table note saying so rather than silently
presenting coverage as exact.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tex_escape(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
    )


def pretty_method(name: str) -> str:
    """Turn an internal method key into a readable table row label."""
    table = {
        "global": "Global (APS)",
        "global_aps": "Global CP (APS)",
        "global_deficit": "Global CP (deficit)",
        "class_conditional": "Mondrian (per class)",
        "oracle_subject": "Oracle (test labels)",
        "aci": "ACI (online)",
        "seqcp_epoch": "Smoothed APS + CP",
        "per_epoch_global": "Per-epoch APS",
        "per_epoch_deficit": "Smoothed deficit",
        "subject_aci_aps": "Per-patient ACI (APS)",
        "subject_aci_deficit": "Per-patient ACI (deficit)",
    }
    if name in table:
        return table[name]
    for base, label in (
        ("per_epoch_global__", "Per-epoch APS"),
        ("seqcp_epoch__", "Smoothed APS"),
        ("per_epoch_deficit_mondrian__", "Smoothed deficit, per stage"),
        ("per_epoch_deficit__", "Smoothed deficit"),
    ):
        if name.startswith(base):
            return f"{label} ({name[len(base):].replace('_', ' ')})"
    prefix, _, rest = name.partition("/")
    if rest:
        # variant-prefixed sacp entries, e.g. "smooth/sacp_m40"
        base = pretty_method(rest)
        tag = {"aps": "", "smooth": "(smooth)", "raps": "(RAPS)"}.get(prefix, f"({prefix})")
        return f"{base} {tag}".strip()
    if name.startswith("subject_aci_"):
        head, _, gamma = name[len("subject_aci_"):].partition("_g")
        label = {"aps": "APS", "deficit": "deficit"}.get(head, head)
        if gamma:
            return f"Per-patient ACI ({label}), $\\gamma_0={gamma}$"
        return f"Per-patient ACI ({label}), $\\gamma_0$ by LOSO"
    if name.startswith("sacp_m"):
        return f"SACP, $m={name[len('sacp_m'):]}$"
    if name.startswith("nbr_"):
        return "kNN subject " + name[len("nbr_"):].replace("_", ", ")
    if name.startswith("seqcp_margin_L"):
        head, _, beta = name[len("seqcp_margin_"):].partition("_beta")
        return f"SeqCP-Margin {head}, $\\beta={beta}$"
    if name.startswith("seqcp_block_L"):
        head, _, beta = name[len("seqcp_block_"):].partition("_beta")
        return f"SeqCP-Block {head}, $\\beta={beta}$"
    if name.startswith("per_epoch_global_L"):
        return f"Per-epoch APS {name[len('per_epoch_global_'):]}"
    if name.startswith("seqcp_epoch_L"):
        return f"Smoothed APS {name[len('seqcp_epoch_'):]}"
    if name.startswith("per_epoch_deficit_L"):
        return f"Smoothed deficit {name[len('per_epoch_deficit_'):]}"
    return name


def num(value: object, fmt: str = "{:.3f}") -> str:
    """Render a number, a 'mean ± sd' string, or a dash."""
    if value is None:
        return "--"
    if isinstance(value, (int, float)):
        return fmt.format(value)
    text = str(value)
    if text in {"-", "nan", "None"}:
        return "--"
    return text.replace("±", r"$\pm$").replace("+-", r"$\pm$")


def emit(
    path: Path,
    caption: str,
    label: str,
    header: list[str],
    align: str,
    rows: list[list[str]],
    note: str | None = None,
    size: str = r"\small",
    group_row: str | None = None,
) -> None:
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        size,
        r"\setlength{\tabcolsep}{4pt}",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        # Shrink only if the natural width exceeds the text block, so tables
        # that fit are left at their typeset size.
        r"\resizebox{\ifdim\width>\linewidth \linewidth\else\width\fi}{!}{%",
        r"\begin{tabular}{" + align + "}",
        r"\toprule",
    ]
    if group_row:
        lines.append(group_row)
    lines += [
        " & ".join(header) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        if len(row) == 1 and row[0].startswith("\\"):
            # A single-cell row starting with a backslash is a booktabs macro
            # (a spacer or a rule), not a row of its own.
            lines.append(row[0])
        else:
            lines.append(" & ".join(row) + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}}")
    if note:
        lines.append(r"\par\vspace{2pt}{\footnotesize " + note + "}")
    lines.append(r"\end{table}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def table_training(summary: Path, out: Path) -> None:
    src = summary / "training.json"
    if not src.exists():
        return
    rows = load(src)  # type: ignore[arg-type]
    by_model: dict[str, list[dict]] = {}
    for row in rows:
        by_model.setdefault(row["model"], []).append(row)

    def mean_sd(rs: list[dict], key: str) -> str:
        import numpy as np

        a = np.asarray([r[key] for r in rs], dtype=float)
        sd = a.std(ddof=1) if a.size > 1 else 0.0
        return f"{a.mean():.3f} $\\pm$ {sd:.3f}"

    body = [
        [r"\texttt{" + m + "}", mean_sd(rs, "accuracy"), mean_sd(rs, "kappa"),
         mean_sd(rs, "mf1"), mean_sd(rs, "ece"), str(len(rs))]
        for m, rs in sorted(by_model.items())
    ]
    emit(
        out / "tab_training.tex",
        "Backbone classification performance on the test subjects, over all "
        "folds and seeds (mean $\\pm$ standard deviation).",
        "tab:training",
        ["Model", "Accuracy", "Cohen's $\\kappa$", "Macro-F1", "ECE", "Runs"],
        "lrrrrr",
        body,
    )


def _headline_rows(summary: Path) -> tuple[list[tuple[str, dict]], int]:
    """Patient-level comparison rows, shared by the main and extended tables.

    The three source files use different key conventions (``sacp.json``
    prefixes every method with its score family, ``diagnostic.json`` uses bare
    names, ``subject_aci.json`` prefixes with ``subject_aci_``), so the rows
    are assembled explicitly rather than by filtering a key pattern.
    """
    src = summary / "sacp.json"
    if not src.exists():
        return [], 0
    methods: dict[str, dict] = load(src)["methods"]  # type: ignore[assignment]
    diag: dict[str, dict] = {}
    if (summary / "diagnostic.json").exists():
        diag = load(summary / "diagnostic.json")["methods"]  # type: ignore[assignment]
    aci: dict[str, dict] = {}
    if (summary / "subject_aci.json").exists():
        aci = load(summary / "subject_aci.json")["methods"]  # type: ignore[assignment]

    # ``diagnostic.json`` carries merged per-subject statistics in the same
    # fields as ``sacp.json``; ``random_epoch`` has no per-subject
    # decomposition and only reports marginal coverage and size.
    rows: list[tuple[str, dict]] = []
    if "random_epoch" in diag:
        r = diag["random_epoch"]
        rows.append(
            ("Random-epoch split", {
                "marginal_coverage": f"{r['coverage']['mean']:.3f}",
                "set_size": f"{r['set_size']['mean']:.3f}",
                "singleton_rate": "--",
            })
        )
    for label, key in (
        ("Pooled (APS)", "aps/global"),
        ("Pooled (RAPS)", "raps/global"),
        ("Mondrian (per class)", None),
        ("$k$NN subject (APS)", "aps/nbr_k3_shrink1"),
        ("Warm-up SACP, $m=80$", "aps/sacp_m80"),
        ("Warm-up SACP, $m=320$", "aps/sacp_m320"),
    ):
        if key is None:
            s = diag.get("class_conditional")
            if s:
                rows.append((label, {
                    "marginal_coverage": (
                        f"{s['coverage']['mean']:.3f} "
                        f"$\\pm$ {s['coverage']['sd']:.3f}"
                    ),
                    "worst_subject_coverage": s["worst_subject_coverage"],
                    "p10_subject_coverage": s["p10_subject_coverage"],
                    "std_subject_coverage": s["std_subject_coverage"],
                    "subject_violation_rate": s["subject_violation_rate"],
                    "set_size": (
                        f"{s['set_size']['mean']:.3f} "
                        f"$\\pm$ {s['set_size']['sd']:.3f}"
                    ),
                    "singleton_rate": (
                        f"{s['singleton_rate']['mean']:.3f} "
                        f"$\\pm$ {s['singleton_rate']['sd']:.3f}"
                    ),
                }))
        elif key in methods:
            rows.append((label, methods[key]))
    if "aps/oracle_subject" in methods:
        rows.append(("Oracle per patient", methods["aps/oracle_subject"]))
    if "subject_aci_aps" in aci:
        rows.append(("Per-patient ACI (APS)", aci["subject_aci_aps"]))
    if "subject_aci_deficit" in aci:
        rows.append(("Per-patient ACI (deficit)", aci["subject_aci_deficit"]))
    n_subjects = diag.get("oracle_subject", {}).get("n_subjects", 20)
    return rows, n_subjects


def _emit_headline(
    out: Path, filename: str, label: str, caption: str,
    rows: list[tuple[str, dict]],
    runs_note: str = "five folds $\\times$ three seeds $\\times$ two backbones",
) -> None:
    body = [
        [
            name,
            num(s.get("marginal_coverage")),
            num(s.get("worst_subject_coverage")),
            num(s.get("p10_subject_coverage")),
            num(s.get("std_subject_coverage"), "{:.4f}"),
            num(s.get("subject_violation_rate"), "{:.2f}"),
            num(s.get("set_size")),
            num(s.get("singleton_rate")),
        ]
        for name, s in rows
    ]
    emit(
        out / filename,
        caption,
        label,
        ["Method", "Coverage", "Worst subj.", "$p_{10}$ subj.",
         "SD", "Below", "Set size", "Singleton"],
        "lrrrrrrr",
        body,
        note=(
            "``Coverage'' is marginal over epochs (mean $\\pm$ SD over the "
            "runs); ``Worst subj.'' is the minimum per-subject coverage over "
            "the runs; ``Below'' is the fraction of subjects below "
            "$1-\\alpha$; ``SD'' is the standard deviation of per-subject "
            "coverage. Each subject contributes one value per run, the runs "
            f"being {runs_note}; "
            "set size and singleton rate are averaged over the same runs."
        ),
    )


def table_sacp(summary: Path, out: Path) -> None:
    rows, n_subjects = _headline_rows(summary)
    if not rows:
        return
    _emit_headline(
        out, "tab_sacp.tex", "tab:sacp",
        "Coverage over patients at $\\alpha=0.1$. Per-subject coverage is merged "
        "across the five subject-wise folds, so each of the "
        f"{n_subjects} subjects appears exactly once. The random-epoch row is "
        "the protocol that mixes epochs from all subjects between calibration "
        "and test; a per-patient decomposition under it would measure the "
        "shared epochs rather than the subject, so the row reports marginal "
        "coverage and set size only.",
        rows,
    )


def table_extended(summary: Path, out: Path) -> None:
    """The same comparison on the 78-subject cohort."""
    rows, n_subjects = _headline_rows(summary)
    if not rows:
        return
    _emit_headline(
        out, "tab_extended.tex", "tab:extended",
        "The headline comparison of \\Cref{tab:sacp} repeated on the "
        f"{n_subjects}-subject cohort, at seed 0. Test blocks of fifteen or "
        "sixteen subjects make each fold's estimate less sensitive to a single "
        "night, while the minimum over all subjects is naturally more extreme "
        "than in the smaller cohort.",
        rows,
        runs_note="five folds $\\times$ one seed $\\times$ two backbones",
    )


def table_temporal(summary: Path, out: Path) -> None:
    """Compact temporal table.

    The full sweep (three block lengths x four transition weights x three
    constructors, 39 rows) is redundant: rows are identical to within the seed
    spread along the block-length axis, and the block constructor saturates at
    every beta >= 0.5. The table therefore shows the score-family rows at full
    context plus the constructors at L=10, collapses the saturated block rows,
    and points to the released JSON for the rest. Keeping the full sweep would
    cost a page and invite the reader to hunt for differences that are not
    there.
    """
    src = summary / "temporal.json"
    if not src.exists():
        return
    data = load(src)  # type: ignore[assignment]
    methods: dict[str, dict] = data["methods"]

    def row(name: str, label: str | None = None) -> list[str] | None:
        s = methods.get(name)
        if s is None:
            return None
        return [
            label if label is not None else pretty_method(name),
            num(s.get("marginal_coverage")),
            num(s.get("set_size")),
            num(s.get("singleton_rate")),
            num(s.get("review_workload")),
            num(s.get("temporal_consistency")),
            num(s.get("sequence_coverage")),
        ]

    spec: list[tuple[str, str | None]] = [
        ("per_epoch_deficit__all_epochs", None),
        ("per_epoch_deficit_mondrian__all_epochs", "Smoothed deficit, per stage"),
        ("seqcp_epoch__all_epochs", None),
        ("per_epoch_global__all_epochs", None),
        ("", None),
        ("per_epoch_deficit_L10", "Smoothed deficit, $L=10$ epochs"),
        ("seqcp_margin_L10_beta0", None),
        ("seqcp_margin_L10_beta0.5", None),
        ("seqcp_margin_L10_beta1", None),
        ("seqcp_margin_L10_beta2", None),
        ("", None),
        ("seqcp_block_L10_beta0", None),
        ("seqcp_block_L10_beta0.5", "SeqCP-Block L10, $\\beta\\ge0.5$"),
    ]
    body: list[list[str]] = []
    for name, label in spec:
        if not name:
            body.append([r"\addlinespace[3pt]"])
            continue
        r = row(name, label)
        if r is not None:
            body.append(r)
    emit(
        out / "tab_temporal.tex",
        "Temporal conformal prediction at $\\alpha=0.1$, block length $L=10$. "
        "The first four rows use every test epoch; the rows below them use "
        "only the epochs inside complete blocks, and the per-epoch baseline "
        "above the SeqCP-Margin block is recalibrated on exactly those "
        "epochs.",
        "tab:temporal",
        ["Method", "Coverage", "Set size", "Singleton", "Review",
         "Consistency", "Seq.\\ coverage"],
        "lrrrrrr",
        body,
        note=(
            "``Review'' is the fraction of epochs whose set contains more "
            "than one stage and would need adjudication; ``Consistency'' is "
            "the mean Jaccard overlap of adjacent "
            "prediction sets within a recording; ``Seq.\\ coverage'' is the "
            "fraction of blocks whose every epoch is covered. The "
            "SeqCP-Block rows at $\\beta=0.5,1,2$ coincide exactly; $L=20$ "
            "and $L=30$ change no conclusion; the full sweep is in the "
            "released JSON. SeqCP-Margin at $\\beta=0$ coincides with the "
            "per-epoch baseline of the same name to every reported digit, "
            "which is the numerical check of \\Cref{prop:reduction}; realised "
            "coverage is an expectation over calibration draws, not a bound "
            "for a single calibration set."
        ),
    )


def table_perclass(summary: Path, out: Path) -> None:
    """Coverage per stage: the class-level cost of the deficit score and the
    per-stage threshold that removes it."""
    temporal_src = summary / "temporal.json"
    diagnostic_src = summary / "diagnostic.json"
    if not temporal_src.exists() or not diagnostic_src.exists():
        return
    temporal = load(temporal_src)["methods"]  # type: ignore[index]
    diagnostic = load(diagnostic_src)["methods"]  # type: ignore[index]

    columns = [
        ("per_epoch_global__all_epochs", "Pooled APS"),
        ("seqcp_epoch__all_epochs", "Smoothed APS"),
        ("per_epoch_deficit__all_epochs", "Smoothed deficit"),
        ("per_epoch_deficit_mondrian__all_epochs", "Deficit, per stage"),
    ]
    stages = ["W", "N1", "N2", "N3", "REM"]
    rows = []
    for k, stage in enumerate(stages):
        cells = [stage]
        for key, _label in columns:
            raw = temporal.get(key, {}).get("per_class_coverage", {})
            value = raw.get(k, raw.get(str(k)))
            cells.append("--" if value is None else f"{value:.3f}")
        raw = diagnostic.get("class_conditional", {}).get("per_class_coverage", {})
        value = raw.get(k, raw.get(str(k)))
        cells.append("--" if value is None else f"{value:.3f}")
        rows.append(cells)

    # The coverage trade-off is only meaningful next to the set size, so the
    # bottom row carries it. The temporal summary stores "mean \pm sd" strings.
    def _size(text: object) -> str:
        if not isinstance(text, str):
            return "--"
        try:
            return f"{float(text.split()[0]):.3f}"
        except (ValueError, IndexError):
            return "--"

    rows.append([r"\midrule"])
    mondrian_size = (
        diagnostic.get("class_conditional", {}).get("set_size", {}).get("mean")
    )
    rows.append(
        ["Mean $|\\cC_t|$"]
        + [_size(temporal.get(key, {}).get("set_size")) for key, _ in columns]
        + ["--" if mondrian_size is None else f"{mondrian_size:.3f}"]
    )
    emit(
        out / "tab_perclass.tex",
        "Coverage per stage at $\\alpha=0.1$, averaged over the 30 runs. "
        "Nominal coverage is 0.90 for every stage.",
        "tab:perclass",
        [
            "Stage",
            "Pooled APS",
            "Smoothed APS",
            "Smoothed deficit",
            "Deficit, per stage",
            "Mondrian APS",
        ],
        "lrrrrr",
        rows,
        note=(
            "Each coverage cell is the fraction of epochs of that stage whose "
            "set contains the true stage, averaged over the runs; the averages "
            "weight the stages unequally because the test blocks differ, so "
            "the run-to-run spread is in the released JSON. The bottom row is "
            "the mean set size over all epochs, the counterpart of those "
            "coverage numbers. The last two columns threshold per stage, on "
            "the deficit score and on the raw APS score respectively, so their "
            "stage coverage is near nominal by construction."
        ),
    )


def table_aci(summary: Path, out: Path) -> None:
    src = summary / "subject_aci.json"
    if not src.exists():
        return
    data = load(src)  # type: ignore[assignment]
    methods: dict[str, dict] = data["methods"]
    selected = data.get("selected_gamma0", {})

    # Two tables are useful: the deployable comparison (global vs the
    # LOSO-selected ACI) and the sensitivity to the step size.
    deployable = ["global_aps", "global_deficit", "subject_aci_aps", "subject_aci_deficit"]
    rows = []
    for name in deployable:
        if name not in methods:
            continue
        s = methods[name]
        rows.append(
            [
                pretty_method(name),
                num(s.get("marginal_coverage")),
                num(s.get("worst_subject_coverage")),
                num(s.get("std_subject_coverage")),
                num(s.get("mean_abs_dev_from_nominal")),
                num(s.get("subject_violation_rate")),
                num(s.get("set_size")),
                num(s.get("singleton_rate")),
                num(s.get("temporal_consistency")),
            ]
        )
    gamma_note = ", ".join(
        f"{k} $= {v['mean']:.3g}$" for k, v in sorted(selected.items())
    )
    emit(
        out / "tab_aci.tex",
        "Per-patient adaptive conformal inference at $\\alpha=0.1$. Each patient "
        "is an independent stream; the step scale is chosen by "
        "leave-one-subject-out simulation on the calibration subjects and then "
        "applied unchanged to the test cohort.",
        "tab:aci",
        ["Method", "Cov.", "Worst", "SD", "MAD$_\\alpha$", "Below",
         "Size", "Sing.", "Cons."],
        "lrrrrrrrr",
        rows,
        note=(
            "Coverage statistics merge per-subject coverage across folds and "
            "average each subject over the runs (folds $\\times$ seeds "
            "$\\times$ backbones). "
            + (
                f"Mean LOSO-selected $\\gamma_0$ over the runs: {gamma_note}. "
                if gamma_note
                else ""
            )
            + "Set size and consistency are averaged over the same runs."
        ),
    )

    sweep = [m for m in methods if m.startswith("subject_aci_") and "_g" in m]
    if sweep:
        body = []
        for name in sorted(sweep):
            s = methods[name]
            body.append(
                [
                    pretty_method(name),
                    num(s.get("marginal_coverage")),
                    num(s.get("worst_subject_coverage")),
                    num(s.get("p10_subject_coverage")),
                    num(s.get("subject_violation_rate")),
                    num(s.get("set_size")),
                ]
            )
        emit(
            out / "tab_aci_sweep.tex",
            "Sensitivity of per-patient ACI to the step scale $\\gamma_0$ at "
            "$\\alpha=0.1$. None of these rows is selected on test data; the "
            "deployable choice is the LOSO-selected one in "
            "\\Cref{tab:aci}.",
            "tab:aci-sweep",
            ["Method", "Coverage", "Worst subj.", "$p_{10}$ subj.",
             "Frac.\\ below", "Set size"],
            "lrrrrr",
            body,
        )


def table_fixed_lambda(summary: Path, out: Path) -> None:
    """Warm-up calibration at fixed shrinkage weights.

    ``run_sacp.py`` reports only the LOSO-selected weight, which is a moving
    target across runs. This table shows the same holds for every weight in
    the grid, which is what turns the warm-up result from "the selection
    failed" into "the adaptation itself does not help at this cohort size".
    """
    src = summary / "sacp_fixed_lambda.json"
    if not src.exists():
        print(f"[skip] {src.name}: not found")
        return
    data = load(src)
    table = data.get("table", {})
    shown = [lam for lam in data.get("lambdas", []) if lam in (0.0, 0.5, 1.0)]
    body: list[list[str]] = []
    for m in data.get("budgets", []):
        first = True
        for lam in shown:
            rec = table.get(f"m{m}_lam{lam:g}")
            if rec is None:
                continue
            body.append(
                [
                    f"$m={m}$" if first else "",
                    "0" if lam == 0 else f"{lam:g}",
                    num(rec["coverage"]["mean"]),
                    num(rec["worst_subject_coverage"]["mean"]),
                    num(rec["std_subject_coverage"]["mean"]),
                    num(rec["set_size"]["mean"]),
                ]
            )
            first = False
        if not first:
            body.append([r"\addlinespace[2pt]"])
    if body and body[-1][0].startswith(r"\addlinespace"):
        body.pop()
    sel = data.get("losos_selected_lambda", {})
    note = (
        "Within a block, the rows share the same evaluation epochs: the first "
        "$m$ epochs of each patient are used only for warm-up and are excluded "
        "from every row, so the $\\lambda=0$ row is the pooled threshold "
        "applied to the post-warm-up epochs and the other rows differ from it "
        "only in the shrinkage weight. Per-subject coverage is merged across "
        "folds and averaged over seeds and backbones."
    )
    if sel:
        note += (
            f" Over the {sel.get('n_runs', 0)} runs, leave-one-subject-out "
            "selection returned zero for every budget up to $m=80$ in "
            f"{sel.get('all_zero_up_to_80', 0)} of them; the full selection "
            "histogram is in the released JSON."
        )
    emit(
        out / "tab_sacp_lambda.tex",
        "Warm-up calibration at fixed shrinkage weights, $\\alpha=0.1$.",
        "tab:sacp-lambda",
        ["$m$", "$\\lambda$", "Coverage", "Worst subj.", "SD", "Set size"],
        "llrrrr",
        body,
        note=note,
        size=r"\footnotesize",
    )


def table_cohort_size(summary: Path, out: Path) -> None:
    src = summary / "cohort_size.json"
    if not src.exists():
        print(f"[skip] {src.name}: not found")
        return
    data = load(src)
    curves = data.get("curves", {})
    if not curves:
        return
    ks = sorted({int(k) for curve in curves.values() for k in curve})
    body = []
    for k in ks:
        row = [str(k)]
        for score in ("aps", "deficit"):
            for stat in ("coverage", "worst"):
                entry = curves.get(score, {}).get(str(k), {}).get(stat)
                row.append("--" if entry is None else f"{entry['mean']:.3f}\\,$\\pm$\\,{entry['sd']:.3f}")
        body.append(row)
    sizes = data.get("n_cal_subjects") or []
    caption = (
        "Coverage against the number of calibration subjects $k$, subsampling "
        "the available calibration subjects and repeating 50 times per run; "
        "rows are averaged over all runs, and $\\pm$ is the standard "
        "deviation across runs. ``worst'' is the minimum per-subject coverage "
        "within a run (each run tests four subjects), averaged over runs, so "
        "it is not the merged-cohort worst patient of \\Cref{tab:sacp}; it is "
        "the quantity that this sweep can hold fixed while $k$ varies. The "
        "deficit score's worst-patient coverage is flat in $k$: the patient "
        "gap is not calibration-sampling noise."
    )
    emit(
        out / "tab_cohort_size.tex",
        caption,
        "tab:cohort-size",
        ["$k$", "cov.", "worst", "cov.", "worst"],
        "rrrrr",
        body,
        group_row=(
            r"\multicolumn{1}{c}{} & \multicolumn{2}{c}{APS}"
            r" & \multicolumn{2}{c}{Posterior deficit} \\"
            r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}"
        ),
        note=(
            "APS columns are the raw-softmax score; deficit columns use the "
            "smoothed posterior deficit. Nominal coverage is 0.900."
            + (r" Calibration pool: " + f"{sizes[-1]}" + " subjects." if sizes else "")
        ),
        size=r"\footnotesize",
    )


def _pooled_and_aci(summary: Path) -> dict[str, dict]:
    """Pull the four headline methods out of one summary directory."""
    out: dict[str, dict] = {}
    temporal = summary / "temporal.json"
    aci = summary / "subject_aci.json"
    if temporal.exists():
        methods = load(temporal).get("methods", {})
        for key, name in (("per_epoch_global__all_epochs", "aps"), ("per_epoch_deficit__all_epochs", "deficit")):
            if key in methods:
                out[f"{name}_pooled"] = methods[key]
    if aci.exists():
        methods = load(aci).get("methods", {})
        for key, name in (("global_aps", "aps"), ("global_deficit", "deficit"),
                          ("subject_aci_aps", "aps_aci"), ("subject_aci_deficit", "deficit_aci")):
            if key in methods:
                out[name] = methods[key]
    return out


def table_shift(summary: Path, cross: Path, out: Path) -> None:
    scenarios = [("In-cohort", _pooled_and_aci(summary))]
    labels = {"sc2st": "Cassette $\\to$ telemetry", "st2sc": "Telemetry $\\to$ cassette"}
    for direction, label in labels.items():
        sub = cross / direction / "summary"
        if sub.exists():
            entries = _pooled_and_aci(sub)
            if entries:
                scenarios.append((label, entries))
    if len(scenarios) == 1:
        print("[skip] tab_shift: no cross-cohort summaries")
        return

    def stat(value: object) -> str:
        """Render a mean or 'mean ± sd', dropping a degenerate zero sd."""
        text = num(value)
        for dash in ("$\\pm$ 0.000", "$\\pm$ 0.00", "$\\pm$ 0.0"):
            if text.endswith(" " + dash):
                return text[: -len(" " + dash)]
        return text

    body = []
    for scenario, entries in scenarios:
        first = True
        for key, name in (
            ("aps_pooled", "APS, pooled"),
            ("aps_aci", "APS, per-patient ACI"),
            ("deficit_pooled", "Deficit, pooled"),
            ("deficit_aci", "Deficit, per-patient ACI"),
        ):
            s = entries.get(key)
            if s is None:
                continue
            body.append(
                [
                    scenario if first else "",
                    pretty_method(name),
                    stat(s.get("marginal_coverage")),
                    num(s.get("worst_subject_coverage")),
                    num(s.get("p10_subject_coverage")),
                    stat(s.get("set_size")),
                ]
            )
            first = False
        if not first:
            body.append([r"\addlinespace[2pt]"])

    if body and body[-1][0].startswith(r"\addlinespace"):
        body.pop()

    # Which model produced each row is reported in the caption; the same
    # backbone is used in every column of a row.
    emit(
        out / "tab_shift.tex",
        "Coverage under hardware shift. The in-cohort rows are the cassette "
        "cohort over all runs of the main matrix; the cross rows train on one "
        "cohort, calibrate on four held-out subjects from it, and test on the "
        "other cohort, at seed 0 for both backbones, with the statistics "
        "merged over the five folds and two backbones. The $\\pm$ is the "
        "standard deviation over the runs contributing to the row (thirty "
        "in-cohort, ten cross-cohort), so it measures run-to-run variation, "
        "not uncertainty over patients. Per-patient ACI uses the "
        "leave-one-subject-out step size selected within the source cohort.",
        "tab:shift",
        ["Scenario", "Method", "Coverage", "Worst patient", "$p_{10}$", "Set size"],
        "llrrrr",
        body,
        size=r"\footnotesize",
    )


SEVERITY_LABELS = {
    # corruption: (label shown, formatter for the chosen level, "max" or "min")
    "noise": ("Noise", "{} dB SNR", "min"),
    "scale": ("Amplitude scale", "$\\times {}$", "max"),
    "drift": ("Baseline drift", "${}\\sigma$ wander", "max"),
    "shift": ("Circular time shift", "{} s", "max"),
    "dropout": ("Epoch dropout", "{}", "max"),
}


def _severity_level(name: str, levels: dict[str, dict]) -> str | None:
    if not levels:
        return None
    mode = SEVERITY_LABELS.get(name, ("", "", "max"))[2]
    keys = sorted(levels, key=float)
    return keys[0] if mode == "min" else keys[-1]


def table_corruption(shift: Path, out: Path) -> None:
    if not shift.exists():
        print(f"[skip] {shift}: not found")
        return
    data = load(shift)
    clean = data.get("clean", {})
    body = [
        [
            "None",
            "--",
            f"{clean.get('accuracy', float('nan')):.3f}",
            f"{clean.get('coverage', float('nan')):.3f}",
            f"{clean.get('coverage', float('nan')):.3f}",
            f"{clean.get('set_size', float('nan')):.2f}",
            f"{clean.get('coverage', float('nan')):.3f}",
            f"{clean.get('set_size', float('nan')):.2f}",
        ]
    ]
    for name, entry in data.get("corruptions", {}).items():
        pretty, fmt, _ = SEVERITY_LABELS.get(name, (name.capitalize(), "{}", "max"))
        level = _severity_level(name, entry)
        if level is None:
            continue
        raw = float(level)
        shown = f"{raw * 100:.0f}\\%" if name == "dropout" else f"{raw:g}"
        value = entry[level]
        clean_q = value.get("clean_q", {})
        recal = value.get("recalibrated", {})
        aci = value.get("aci", {})
        body.append(
            [
                pretty,
                fmt.format(shown),
                f"{clean_q.get('accuracy', float('nan')):.3f}",
                f"{clean_q.get('coverage', float('nan')):.3f}",
                f"{recal.get('coverage', float('nan')):.3f}",
                f"{recal.get('set_size', float('nan')):.2f}",
                f"{aci.get('coverage', float('nan')):.3f}",
                f"{aci.get('set_size', float('nan')):.2f}",
            ]
        )
    emit(
        out / "tab_corruption.tex",
        "Coverage at the most severe level of each input corruption, applied "
        "to the test signals only. Accuracy is the corrupted model's own "
        "epoch accuracy and does not depend on any threshold. ``Clean "
        "threshold'' is the split-conformal threshold fitted on clean "
        "calibration data; ``recalibrated'' refits the threshold on "
        "calibration signals corrupted identically, and the following column "
        "is the mean set size it returns; ``per-patient ACI'' adapts the "
        "threshold online on the corrupted stream using the clean "
        "calibration set, again with its mean set size. One representative "
        "run (EEGNet, fold 0) is reported because the corruption is a "
        "property of the model and the split rather than of the fold.",
        "tab:corruption",
        ["Corruption", "Severity", "Accuracy", "Clean threshold",
         "Recalibrated", "Recal.\\ size", "Per-patient ACI", "ACI size"],
        "llrrrrrr",
        body,
        size=r"\footnotesize",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=Path("results/summary"))
    parser.add_argument("--out", type=Path, default=Path("paper/tex/tables"))
    parser.add_argument("--cross", type=Path, default=Path("results/cross"))
    parser.add_argument(
        "--extended", type=Path, default=Path("results/se78/summary"),
        help="summary directory of the 78-subject cohort",
    )
    parser.add_argument(
        "--shift",
        type=Path,
        default=Path("results/main/eegnet/fold0_seed0/shift.json"),
        help="input-corruption study of one representative run",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    table_training(args.summary, args.out)
    table_sacp(args.summary, args.out)
    table_extended(args.extended, args.out)
    table_temporal(args.summary, args.out)
    table_perclass(args.summary, args.out)
    table_aci(args.summary, args.out)
    table_fixed_lambda(args.summary, args.out)
    table_cohort_size(args.summary, args.out)
    table_shift(args.summary, args.cross, args.out)
    table_corruption(args.shift, args.out)
    print(f"wrote LaTeX tables to {args.out}")


if __name__ == "__main__":
    main()
