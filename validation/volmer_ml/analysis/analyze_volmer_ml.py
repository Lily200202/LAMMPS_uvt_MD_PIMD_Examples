#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


def numeric_row(line: str) -> list[float] | None:
    fields = line.split()
    if not fields:
        return None
    try:
        return [float(field) for field in fields]
    except ValueError:
        return None


def parse_log(path: Path) -> tuple[list[str], np.ndarray]:
    header: list[str] | None = None
    rows: list[list[float]] = []
    with path.open(errors="replace") as fh:
        for line in fh:
            fields = line.split()
            if fields and fields[0] == "Step":
                header = fields
                continue
            if header is None:
                continue
            row = numeric_row(line)
            if row is None or len(row) != len(header):
                continue
            rows.append(row)
    if header is None or not rows:
        raise SystemExit(f"No thermo rows found in {path}")
    return header, np.asarray(rows, dtype=float)


def log_paths(case_dir: Path, stem: str) -> list[Path]:
    suffixed = sorted(path for path in case_dir.glob(f"{stem}.*") if path.suffix[1:].isdigit())
    if suffixed:
        return suffixed
    base = case_dir / stem
    if base.exists():
        return [base]
    raise SystemExit(f"No logs found for {case_dir}/{stem}")


def mean_sem(values: np.ndarray) -> tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    return float(np.mean(values)), float(np.std(values, ddof=0) / np.sqrt(values.size))


def summarize_rows(label: str, rows_by_bead: list[tuple[list[str], np.ndarray]], min_step: int) -> dict[str, float | str]:
    header = rows_by_bead[0][0]
    cols = {name: i for i, name in enumerate(header)}
    required = ["Step", "c_movetemp", "v_Ne", "v_NeDot", "c_dEdN", "v_dEdNfix", "v_muFix"]
    missing = [name for name in required if name not in cols]
    if missing:
        raise SystemExit(f"{label}: missing thermo columns {missing}")

    maps = [{int(row[cols["Step"]]): row for row in arr} for _, arr in rows_by_bead]
    common_steps = sorted(set.intersection(*(set(mapping) for mapping in maps)))
    common_steps = [step for step in common_steps if step >= min_step]
    if not common_steps:
        raise SystemExit(f"{label}: no common thermo steps at min_step={min_step}")

    ne = []
    nedot = []
    dedn_compute = []
    dedn_fix = []
    mu = []
    movetemp = []
    shared_ne_std = []
    shared_dedn_std = []

    for step in common_steps:
        rows = [mapping[step] for mapping in maps]
        ne_all = np.array([row[cols["v_Ne"]] for row in rows], dtype=float)
        dedn_all = np.array([row[cols["v_dEdNfix"]] for row in rows], dtype=float)
        shared_ne_std.append(float(np.std(ne_all, ddof=0)))
        shared_dedn_std.append(float(np.std(dedn_all, ddof=0)))
        row0 = rows[0]
        ne.append(row0[cols["v_Ne"]])
        nedot.append(row0[cols["v_NeDot"]])
        dedn_compute.append(float(np.mean([row[cols["c_dEdN"]] for row in rows])))
        dedn_fix.append(row0[cols["v_dEdNfix"]])
        mu.append(row0[cols["v_muFix"]])
        movetemp.append(float(np.mean([row[cols["c_movetemp"]] for row in rows])))

    ne_arr = np.asarray(ne)
    nedot_arr = np.asarray(nedot)
    dedn_provider_arr = np.asarray(dedn_compute)
    dedn_fix_arr = np.asarray(dedn_fix)
    mu_arr = np.asarray(mu)
    temp_arr = np.asarray(movetemp)

    ne_mean, ne_sem = mean_sem(ne_arr)
    dedn_mean, dedn_sem = mean_sem(dedn_provider_arr)
    dedn_fix_mean, dedn_fix_sem = mean_sem(dedn_fix_arr)
    temp_mean, temp_sem = mean_sem(temp_arr)
    nedot_mean, nedot_sem = mean_sem(nedot_arr)
    return {
        "case": label,
        "beads": len(rows_by_bead),
        "min_step": min_step,
        "n_samples": len(common_steps),
        "step_first": common_steps[0],
        "step_last": common_steps[-1],
        "temp_move_mean": temp_mean,
        "temp_move_sem": temp_sem,
        "ne_mean": ne_mean,
        "ne_sem": ne_sem,
        "ne_dot_mean": nedot_mean,
        "ne_dot_sem": nedot_sem,
        "dedn_mean": dedn_mean,
        "dedn_sem": dedn_sem,
        "dedn_fix_mean": dedn_fix_mean,
        "dedn_fix_sem": dedn_fix_sem,
        "mu_mean": float(np.mean(mu_arr)),
        "dedn_minus_mu_mean": float(np.mean(dedn_provider_arr - mu_arr)),
        "dedn_compute_minus_fix_max_abs": float(np.max(np.abs(dedn_provider_arr - dedn_fix_arr))),
        "shared_ne_std_max": float(np.max(shared_ne_std)),
        "shared_dedn_std_max": float(np.max(shared_dedn_std)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--min-step", type=int, default=0)
    args = parser.parse_args()

    root = args.root
    runs = root / "runs"
    summaries: list[dict[str, float | str]] = []

    classical = runs / "classical"
    if classical.exists():
        parsed = [parse_log(path) for path in log_paths(classical, "log.classical_uvt_volmer")]
        summaries.append(summarize_rows("classical", parsed, args.min_step))

    for case_dir in sorted(runs.glob("pimd_p*")):
        parsed = [parse_log(path) for path in log_paths(case_dir, "log.pimd_uvt_volmer")]
        summaries.append(summarize_rows(case_dir.name, parsed, args.min_step))

    if not summaries:
        raise SystemExit(f"No completed runs found under {runs}")

    out = root / "volmer_ml_summary.csv"
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)

    print(f"Wrote {out}")
    for row in summaries:
        print(
            f"{row['case']}: <Ne>={float(row['ne_mean']):.6g}, "
            f"<dE/dNe>-<mu>={float(row['dedn_minus_mu_mean']):.6g}, "
            f"<T_move>={float(row['temp_move_mean']):.6g}"
        )


if __name__ == "__main__":
    main()
