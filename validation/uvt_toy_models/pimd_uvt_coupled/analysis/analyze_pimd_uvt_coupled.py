#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


PARAMS = {
    "kx": 5.0,
    "ke": 5.0,
    "g": 2.0,
    "N0": 1.0,
    "mu": 1.0,
    "T": 1.0,
}


def analytical_reference() -> dict[str, float]:
    kx = PARAMS["kx"]
    ke = PARAMS["ke"]
    g = PARAMS["g"]
    n0 = PARAMS["N0"]
    mu = PARAMS["mu"]
    denom = kx * ke - g * g
    return {
        "denom": denom,
        "xstar": -g * (mu + ke * n0) / denom,
        "nestar": kx * (mu + ke * n0) / denom,
    }


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
        raise SystemExit(f"No complete thermo rows found in {path}")
    return header, np.asarray(rows, dtype=float)


def read_case_metadata(case_dir: Path) -> dict[str, str]:
    path = case_dir / "case_metadata.csv"
    with path.open() as fh:
        return next(csv.DictReader(fh))


def active_beads_from_metadata(case_root: Path) -> set[int] | None:
    path = case_root / "run_metadata.csv"
    if not path.exists():
        return None
    with path.open() as fh:
        row = next(csv.DictReader(fh))
    beads = row.get("beads", "").strip()
    if not beads:
        return None
    return {int(value) for value in beads.replace(" ", ";").split(";") if value}


def mean_sem(values: np.ndarray) -> tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    mean = float(np.mean(values))
    sem = float(np.std(values, ddof=0) / np.sqrt(values.size))
    return mean, sem


def mean_block_sem(values: np.ndarray, nblocks: int = 20) -> tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    if values.size < nblocks:
        raise SystemExit(f"Need at least {nblocks} production samples for block SEM, got {values.size}")

    mean = float(np.mean(values))
    block_length = values.size // nblocks
    blocked = values[:block_length * nblocks].reshape(nblocks, block_length)
    block_means = np.mean(blocked, axis=1)
    sem = float(np.std(block_means, ddof=1) / np.sqrt(nblocks))
    return mean, sem


def log_paths(case_dir: Path) -> list[Path]:
    suffixed = sorted(case_dir.glob("log.pimd_uvt_coupled.*"))
    numeric = [path for path in suffixed if path.suffix[1:].isdigit()]
    if numeric:
        return numeric
    base = case_dir / "log.pimd_uvt_coupled"
    if base.exists():
        return [base]
    raise SystemExit(f"No log files found in {case_dir}")


def analyze_case(case_dir: Path, min_step: int, out_prefix: str) -> dict[str, float]:
    meta = read_case_metadata(case_dir)
    beads = int(meta["beads"])
    dt = float(meta["dt"])

    logs = log_paths(case_dir)
    parsed = [parse_log(path) for path in logs]
    header = parsed[0][0]
    columns = {name: i for i, name in enumerate(header)}
    required = [
        "Step",
        "v_temp_nuclear",
        "v_xlocal",
        "v_Ne_now",
        "v_Ne_dot_now",
        "v_dEdN_local",
        "v_dEdN_avg",
        "v_mu_now",
        "v_ne_ke",
        "v_uvt_extra",
        "v_h_p",
        "v_nhc_potential",
        "v_nhc_kinetic",
        "v_u_toy",
        "v_nuclear_ecouple",
        "v_ne_ecouple",
        "v_total_ecouple",
    ]
    missing = [name for name in required if name not in columns]
    if missing:
        raise SystemExit(f"Missing required thermo columns in {case_dir}: {missing}")

    by_step: list[dict[int, np.ndarray]] = []
    for _, arr in parsed:
        by_step.append({int(row[columns["Step"]]): row for row in arr})

    common_steps = sorted(set.intersection(*(set(mapping) for mapping in by_step)))
    if not common_steps:
        raise SystemExit(f"No common thermo steps across bead logs in {case_dir}")

    ref = analytical_reference()
    timeseries_rows: list[dict[str, float]] = []
    shared_ne_std = []
    shared_dedn_std = []
    hp_partition_std = []

    for step in common_steps:
        rows = [mapping[step] for mapping in by_step]
        xlocal = np.array([row[columns["v_xlocal"]] for row in rows], dtype=float)
        temp_nuclear_all = np.array([row[columns["v_temp_nuclear"]] for row in rows], dtype=float)
        dedn_local = np.array([row[columns["v_dEdN_local"]] for row in rows], dtype=float)
        ne_all = np.array([row[columns["v_Ne_now"]] for row in rows], dtype=float)
        ne_dot_all = np.array([row[columns["v_Ne_dot_now"]] for row in rows], dtype=float)
        dedn_avg_all = np.array([row[columns["v_dEdN_avg"]] for row in rows], dtype=float)
        mu_all = np.array([row[columns["v_mu_now"]] for row in rows], dtype=float)
        ne_ke_all = np.array([row[columns["v_ne_ke"]] for row in rows], dtype=float)
        uvt_extra_all = np.array([row[columns["v_uvt_extra"]] for row in rows], dtype=float)
        hp_all = np.array([row[columns["v_h_p"]] for row in rows], dtype=float)
        nhc_pot_all = np.array([row[columns["v_nhc_potential"]] for row in rows], dtype=float)
        nhc_ke_all = np.array([row[columns["v_nhc_kinetic"]] for row in rows], dtype=float)
        u_toy_all = np.array([row[columns["v_u_toy"]] for row in rows], dtype=float)
        nuclear_ecouple_all = np.array([row[columns["v_nuclear_ecouple"]] for row in rows], dtype=float)
        ne_ecouple_all = np.array([row[columns["v_ne_ecouple"]] for row in rows], dtype=float)
        total_ecouple_all = np.array([row[columns["v_total_ecouple"]] for row in rows], dtype=float)

        shared_ne_std.append(float(np.std(ne_all, ddof=0)))
        shared_dedn_std.append(float(np.std(dedn_avg_all, ddof=0)))
        hp_partition_std.append(float(np.std(hp_all, ddof=0)))

        row0 = rows[0]
        time = step * dt
        x_centroid = float(np.mean(xlocal))
        temp_nuclear = float(np.mean(temp_nuclear_all) / beads)
        dedn_bead_avg = float(np.mean(dedn_local))
        ne = float(row0[columns["v_Ne_now"]])
        ne_dot = float(row0[columns["v_Ne_dot_now"]])
        dedn_avg = float(row0[columns["v_dEdN_avg"]])
        mu_now = float(row0[columns["v_mu_now"]])
        h_p = float(np.mean(hp_all))
        h_nhc = float(np.sum(nhc_pot_all + nhc_ke_all))
        h_nhc_mean = float(np.mean(nhc_pot_all + nhc_ke_all))
        u_toy_sum = float(np.sum(u_toy_all))
        ne_ke = float(np.mean(ne_ke_all))
        uvt_extra = float(np.mean(uvt_extra_all))
        nuclear_ecouple = float(np.mean(nuclear_ecouple_all))
        ne_ecouple = float(np.mean(ne_ecouple_all))
        total_ecouple = float(np.mean(total_ecouple_all))
        legendre = -mu_now * ne
        # The PIMD/UVT electronic coordinate is shared by all beads.  The
        # equations of motion use the bead-averaged electronic force, which is
        # equivalent to the ring-polymer Hamiltonian form with P*K_Ne and
        # -P*mu*Ne in the conserved extended-energy diagnostic.
        ne_ke_rp = beads * ne_ke
        uvt_extra_rp = beads * uvt_extra
        h_ext_uvt = h_p + u_toy_sum + h_nhc + ne_ke_rp + uvt_extra_rp
        h_ext_work = h_p + u_toy_sum + ne_ke_rp + uvt_extra_rp + total_ecouple

        timeseries_rows.append(
            {
                "step": float(step),
                "time": time,
                "beads": float(beads),
                "temp_nuclear": temp_nuclear,
                "x_centroid": x_centroid,
                "xstar": ref["xstar"],
                "Ne": ne,
                "Nestar": ref["nestar"],
                "Ne_dot": ne_dot,
                "dEdN_avg": dedn_avg,
                "dEdN_bead_avg": dedn_bead_avg,
                "mu": mu_now,
                "dEdN_minus_mu": dedn_avg - PARAMS["mu"],
                "h_p": h_p,
                "u_toy_sum": u_toy_sum,
                "h_nhc": h_nhc,
                "h_nhc_mean": h_nhc_mean,
                "ne_kinetic": ne_ke,
                "legendre_minus_mu_ne": legendre,
                "uvt_extra": uvt_extra,
                "nuclear_ecouple": nuclear_ecouple,
                "ne_ecouple": ne_ecouple,
                "total_ecouple": total_ecouple,
                "h_ext_uvt": h_ext_uvt,
                "h_ext_work": h_ext_work,
            }
        )

    h_ext0 = timeseries_rows[0]["h_ext_uvt"]
    h_work0 = timeseries_rows[0]["h_ext_work"]
    h_ref_abs = max(abs(h_ext0), np.finfo(float).eps)
    h_work_ref_abs = max(abs(h_work0), np.finfo(float).eps)
    for row in timeseries_rows:
        row["delta_h_ext_uvt"] = row["h_ext_uvt"] - h_ext0
        row["delta_h_ext_uvt_over_h0_abs"] = row["delta_h_ext_uvt"] / h_ref_abs
        row["delta_h_ext_work"] = row["h_ext_work"] - h_work0
        row["delta_h_ext_work_over_h0_abs"] = row["delta_h_ext_work"] / h_work_ref_abs

    timeseries_path = case_dir / f"{out_prefix}_timeseries.csv"
    with timeseries_path.open("w", newline="") as fh:
        fieldnames = list(timeseries_rows[0])
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(timeseries_rows)

    arr = np.asarray([[row[key] for key in timeseries_rows[0].keys()] for row in timeseries_rows], dtype=float)
    key_index = {key: i for i, key in enumerate(timeseries_rows[0].keys())}
    mask = arr[:, key_index["step"]] >= min_step
    if not np.any(mask):
        raise SystemExit(f"No samples at or above min_step={min_step} in {case_dir}")

    x_mean, x_sem = mean_block_sem(arr[mask, key_index["x_centroid"]])
    temp_mean, temp_sem = mean_sem(arr[mask, key_index["temp_nuclear"]])
    ne_mean, ne_sem = mean_block_sem(arr[mask, key_index["Ne"]])
    dedn_mean, dedn_sem = mean_block_sem(arr[mask, key_index["dEdN_avg"]])
    dedn_bias_mean, dedn_bias_sem = mean_sem(arr[mask, key_index["dEdN_minus_mu"]])
    delta_h = arr[mask, key_index["delta_h_ext_uvt"]]
    delta_h_rel = arr[mask, key_index["delta_h_ext_uvt_over_h0_abs"]]
    delta_h_work = arr[mask, key_index["delta_h_ext_work"]]
    delta_h_work_rel = arr[mask, key_index["delta_h_ext_work_over_h0_abs"]]
    h_ext = arr[mask, key_index["h_ext_uvt"]]
    h_work = arr[mask, key_index["h_ext_work"]]
    h_mean_abs = max(abs(float(np.mean(h_ext))), np.finfo(float).eps)
    h_rms = max(float(np.sqrt(np.mean(h_ext * h_ext))), np.finfo(float).eps)
    h_work_mean_abs = max(abs(float(np.mean(h_work))), np.finfo(float).eps)
    h_work_rms = max(float(np.sqrt(np.mean(h_work * h_work))), np.finfo(float).eps)
    delta_h_rms = float(np.sqrt(np.mean(delta_h * delta_h)))
    delta_h_work_rms = float(np.sqrt(np.mean(delta_h_work * delta_h_work)))
    drift_slope = float(np.polyfit(arr[mask, key_index["time"]], delta_h, 1)[0]) if delta_h.size > 1 else float("nan")
    drift_slope_work = float(np.polyfit(arr[mask, key_index["time"]], delta_h_work, 1)[0]) if delta_h_work.size > 1 else float("nan")

    return {
        "beads": float(beads),
        "dt": dt,
        "nsteps": float(meta["nsteps"]),
        "thermo_freq": float(meta["thermo_freq"]),
        "tdamp": float(meta.get("tdamp", float("nan"))),
        "udamp": float(meta.get("udamp", meta.get("tdamp", float("nan")))),
        "min_step": float(min_step),
        "n_window": float(np.count_nonzero(mask)),
        "xstar": ref["xstar"],
        "nestar": ref["nestar"],
        "x_centroid_mean": x_mean,
        "x_centroid_sem": x_sem,
        "x_centroid_bias": x_mean - ref["xstar"],
        "temp_nuclear_mean": temp_mean,
        "temp_nuclear_sem": temp_sem,
        "temp_nuclear_bias": temp_mean - PARAMS["T"],
        "Ne_mean": ne_mean,
        "Ne_sem": ne_sem,
        "Ne_bias": ne_mean - ref["nestar"],
        "dEdN_mean": dedn_mean,
        "dEdN_sem": dedn_sem,
        "dEdN_minus_mu_mean": dedn_bias_mean,
        "dEdN_minus_mu_sem": dedn_bias_sem,
        "shared_Ne_std_max": max(shared_ne_std),
        "shared_dEdN_std_max": max(shared_dedn_std),
        "h_ext_initial": h_ext0,
        "delta_h_ext_mean": float(np.mean(delta_h)),
        "delta_h_ext_std": float(np.std(delta_h, ddof=0)),
        "delta_h_ext_max_abs": float(np.max(np.abs(delta_h))),
        "delta_h_ext_rms": delta_h_rms,
        "delta_h_ext_max_abs_over_h0_abs": float(np.max(np.abs(delta_h_rel))),
        "delta_h_ext_max_abs_over_h_mean_abs": float(np.max(np.abs(delta_h)) / h_mean_abs),
        "delta_h_ext_rms_over_h_rms": delta_h_rms / h_rms,
        "delta_h_ext_drift_slope": drift_slope,
        "delta_h_ext_drift_slope_over_h_mean_abs": drift_slope / h_mean_abs,
        "h_ext_work_initial": h_work0,
        "delta_h_ext_work_mean": float(np.mean(delta_h_work)),
        "delta_h_ext_work_std": float(np.std(delta_h_work, ddof=0)),
        "delta_h_ext_work_max_abs": float(np.max(np.abs(delta_h_work))),
        "delta_h_ext_work_rms": delta_h_work_rms,
        "delta_h_ext_work_max_abs_over_h0_abs": float(np.max(np.abs(delta_h_work_rel))),
        "delta_h_ext_work_max_abs_over_h_mean_abs": float(np.max(np.abs(delta_h_work)) / h_work_mean_abs),
        "delta_h_ext_work_rms_over_h_rms": delta_h_work_rms / h_work_rms,
        "delta_h_ext_work_drift_slope": drift_slope_work,
        "delta_h_ext_work_drift_slope_over_h_mean_abs": drift_slope_work / h_work_mean_abs,
        "h_p_partition_std_max": max(hp_partition_std),
        "timeseries_csv": timeseries_path.name,
    }


def read_classical_summary(path: Path) -> dict[str, float] | None:
    if not path.exists():
        return None
    with path.open() as fh:
        row = next(csv.DictReader(fh))
    return {key: float(value) for key, value in row.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze PIMD/UVT coupled toy validation.")
    parser.add_argument("case_root", nargs="?", default=".")
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--min-step", type=int, default=20000)
    parser.add_argument("--summary", default="pimd_uvt_coupled_summary.csv")
    parser.add_argument("--classical-summary", default="../classical_coupled/classical_uvt_summary.csv")
    parser.add_argument("--classical-output", default="pimd_uvt_classical_limit.csv")
    parser.add_argument("--prefix", default="pimd_uvt_coupled")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    runs_dir = case_root / args.runs_dir
    case_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir() and path.name.startswith("p"))
    active_beads = active_beads_from_metadata(case_root)
    if active_beads is not None:
        case_dirs = [
            path for path in case_dirs
            if int(read_case_metadata(path)["beads"]) in active_beads
        ]
    if not case_dirs:
        raise SystemExit(f"No bead-count run directories found in {runs_dir}")

    summaries = [analyze_case(case_dir, args.min_step, args.prefix) for case_dir in case_dirs]
    summaries.sort(key=lambda row: row["beads"])

    with (case_root / args.summary).open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)

    classical = read_classical_summary((case_root / args.classical_summary).resolve())
    p1_row = next((row for row in summaries if int(row["beads"]) == 1), None)
    if p1_row is not None:
        comparison = {
            "p_quantum": 1.0,
            "Ne_mean_p1": p1_row["Ne_mean"],
            "Ne_bias_vs_analytic": p1_row["Ne_bias"],
            "dEdN_mean_p1": p1_row["dEdN_mean"],
            "dEdN_minus_mu_p1": p1_row["dEdN_minus_mu_mean"],
            "x_centroid_mean_p1": p1_row["x_centroid_mean"],
            "x_centroid_bias_vs_analytic": p1_row["x_centroid_bias"],
        }
        if classical is not None:
            comparison.update(
                {
                    "Ne_mean_classical": classical["ne_mean"],
                    "Ne_p1_minus_classical": p1_row["Ne_mean"] - classical["ne_mean"],
                    "dEdN_mean_classical": classical["dedn_mean"],
                    "dEdN_p1_minus_classical": p1_row["dEdN_mean"] - classical["dedn_mean"],
                    "x_mean_classical": classical["x_mean"],
                    "x_p1_minus_classical": p1_row["x_centroid_mean"] - classical["x_mean"],
                }
            )

        with (case_root / args.classical_output).open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(comparison))
            writer.writeheader()
            writer.writerow(comparison)


if __name__ == "__main__":
    main()
