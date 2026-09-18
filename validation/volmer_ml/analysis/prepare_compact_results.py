#!/usr/bin/env python3
"""Convert raw LAMMPS logs into the compact time series archived with the paper."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import numpy as np


def parse_log(path: Path) -> tuple[list[str], np.ndarray]:
    header = None
    rows: list[list[float]] = []
    with path.open(errors="replace") as handle:
        for line in handle:
            fields = line.split()
            if fields and fields[0] == "Step":
                header = fields
                continue
            if header is None:
                continue
            try:
                values = [float(value) for value in fields]
            except ValueError:
                continue
            if len(values) == len(header):
                rows.append(values)
    if header is None or not rows:
        raise ValueError(f"No thermo table found in {path}")
    return header, np.asarray(rows)


def write_csv(path: Path, names: list[str], columns: list[np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(names)
        writer.writerows(zip(*columns))


def compact_classical(log_path: Path, output: Path, dt_ps: float, stride: int) -> None:
    header, data = parse_log(log_path)
    col = {name: i for i, name in enumerate(header)}
    required = ("Step", "c_movetemp", "v_Ne", "c_dEdN", "v_muFix")
    missing = [name for name in required if name not in col]
    if missing:
        raise ValueError(f"Missing classical columns: {missing}")
    data = data[::stride]
    step = data[:, col["Step"]]
    write_csv(
        output,
        ["step", "time_ps", "temperature_K", "ne", "dedn_eV", "mu_eV"],
        [step, step * dt_ps, data[:, col["c_movetemp"]], data[:, col["v_Ne"]],
         data[:, col["c_dEdN"]], data[:, col["v_muFix"]]],
    )


def partition_number(path: Path) -> int:
    match = re.search(r"\.(\d+)$", path.name)
    if match is None:
        raise ValueError(f"Unexpected partition log name: {path}")
    return int(match.group(1))


def compact_pimd(log_dir: Path, output: Path, dt_ps: float, min_step: int, max_step: int) -> None:
    paths = sorted(log_dir.glob("log.pimd_uvt_volmer.*"), key=partition_number)
    if not paths:
        raise ValueError(f"No partition logs found in {log_dir}")

    header0 = None
    tables: dict[int, dict[int, np.ndarray]] = {}
    for path in paths:
        header, data = parse_log(path)
        if header0 is None:
            header0 = header
        elif header != header0:
            raise ValueError(f"Thermo header mismatch in {path}")
        col = {name: i for i, name in enumerate(header)}
        tables[partition_number(path)] = {
            int(row[col["Step"]]): row
            for row in data
            if min_step <= int(row[col["Step"]]) <= max_step
        }

    assert header0 is not None
    col = {name: i for i, name in enumerate(header0)}
    required = ("v_Ne", "c_dEdN", "v_NeKE", "v_MuPE", "v_Ecouple", "v_NHCTotal")
    missing = [name for name in required if name not in col]
    if missing:
        raise ValueError(f"Missing PIMD columns: {missing}")
    h_p_name = "v_HP" if "v_HP" in col else "f_cp[4]"

    steps = sorted(set.intersection(*(set(table) for table in tables.values())))
    beads = sorted(tables)
    arrays = {bead: np.vstack([tables[bead][step] for step in steps]) for bead in beads}
    ne = arrays[beads[0]][:, col["v_Ne"]]
    dedn = np.mean(np.vstack([arrays[bead][:, col["c_dEdN"]] for bead in beads]), axis=0)
    h_p = np.mean(np.vstack([arrays[bead][:, col[h_p_name]] for bead in beads]), axis=0)
    ne_ke = arrays[beads[0]][:, col["v_NeKE"]]
    mu_pe = arrays[beads[0]][:, col["v_MuPE"]]
    ecouple = arrays[beads[0]][:, col["v_Ecouple"]]
    nhc = np.sum(np.vstack([arrays[bead][:, col["v_NHCTotal"]] for bead in beads]), axis=0)
    h_ext = h_p + nhc + len(beads) * (ne_ke + mu_pe) - ecouple
    h_rel = (h_ext - h_ext[0]) / abs(h_ext[0])
    step_array = np.asarray(steps, dtype=float)
    write_csv(
        output,
        ["step", "time_ps", "ne", "dedn_bead_average_eV", "delta_h_ext_over_h0_abs"],
        [step_array, step_array * dt_ps, ne, dedn, h_rel],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classical-log", type=Path)
    parser.add_argument("--pimd-log-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    parser.add_argument("--dt", type=float, default=0.0002, help="timestep in ps")
    parser.add_argument("--classical-stride", type=int, default=40)
    parser.add_argument("--min-step", type=int, default=75000)
    parser.add_argument("--max-step", type=int, default=175000)
    args = parser.parse_args()
    if args.classical_log:
        compact_classical(args.classical_log, args.output_dir / "classical_timeseries.csv", args.dt,
                          args.classical_stride)
    if args.pimd_log_dir:
        compact_pimd(args.pimd_log_dir, args.output_dir / "pimd_p16_timeseries.csv", args.dt,
                     args.min_step, args.max_step)
    if not args.classical_log and not args.pimd_log_dir:
        parser.error("provide --classical-log and/or --pimd-log-dir")


if __name__ == "__main__":
    main()
