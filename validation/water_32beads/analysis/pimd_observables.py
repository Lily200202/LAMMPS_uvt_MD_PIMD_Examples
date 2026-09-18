#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np


def parse_lammpstrj(path: Path, min_step: int, max_step: int | None):
    with path.open() as fh:
        while True:
            line = fh.readline()
            if not line:
                break
            if not line.startswith("ITEM: TIMESTEP"):
                continue
            timestep = int(fh.readline().strip())
            fh.readline()
            natoms = int(fh.readline().strip())
            fh.readline()
            bounds = [list(map(float, fh.readline().split()[:2])) for _ in range(3)]
            box = np.asarray([hi - lo for lo, hi in bounds], dtype=float)
            fh.readline()
            atoms = np.zeros((natoms, 8), dtype=float)
            for i in range(natoms):
                atom_id, atom_type, x, y, z, ix, iy, iz = fh.readline().split()
                atoms[i, 0] = int(atom_id)
                atoms[i, 1] = int(atom_type)
                atoms[i, 2] = float(x)
                atoms[i, 3] = float(y)
                atoms[i, 4] = float(z)
                atoms[i, 5] = float(x) + int(ix) * box[0]
                atoms[i, 6] = float(y) + int(iy) * box[1]
                atoms[i, 7] = float(z) + int(iz) * box[2]
            if timestep < min_step:
                continue
            if max_step is not None and timestep > max_step:
                continue
            yield timestep, atoms, box


def angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    v1 = a - b
    v2 = c - b
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0.0:
        return float("nan")
    cosang = np.dot(v1, v2) / denom
    cosang = np.clip(cosang, -1.0, 1.0)
    return math.degrees(math.acos(cosang))


def collect_structure(traj_files: list[Path], min_step: int, max_step: int | None):
    oh_values = []
    hoh_values = []
    nframes = 0

    for traj in traj_files:
        for _, atoms, box in parse_lammpstrj(traj, min_step, max_step):
            nframes += 1
            oxygens = atoms[atoms[:, 1] == 1]
            hydrogens = atoms[atoms[:, 1] == 2]
            for oxygen in oxygens:
                dvec = hydrogens[:, 2:5] - oxygen[2:5]
                dvec -= box * np.rint(dvec / box)
                dist2 = np.sum(dvec * dvec, axis=1)
                order = np.argsort(dist2)[:2]
                pair_vec = dvec[order]
                oh_values.extend(np.sqrt(np.sort(dist2)[:2]).tolist())
                hoh_values.append(angle_deg(pair_vec[0], np.zeros(3), pair_vec[1]))

    return np.asarray(oh_values), np.asarray(hoh_values), nframes


def parse_rg2_frames(path: Path, min_step: int, max_step: int | None):
    for timestep, atoms, _ in parse_lammpstrj(path, min_step, max_step):
        order = np.argsort(atoms[:, 0].astype(int))
        yield timestep, atoms[order, 5:8]


def collect_rg2(traj_files: list[Path], min_step: int, max_step: int | None):
    frame_iters = [parse_rg2_frames(path, min_step, max_step) for path in traj_files]
    rg2_values = []
    nframes = 0

    while True:
        frames = []
        steps = []
        for frame_iter in frame_iters:
            try:
                timestep, positions = next(frame_iter)
            except StopIteration:
                frames = []
                break
            steps.append(timestep)
            frames.append(positions)
        if not frames:
            break
        if len(set(steps)) != 1:
            raise SystemExit(f"Bead trajectory timesteps are not synchronized: {steps[:5]}")
        positions = np.stack(frames, axis=0)
        centroid = np.mean(positions, axis=0)
        rg2_values.append(np.mean(np.sum((positions - centroid[None, :, :]) ** 2, axis=2)))
        nframes += 1

    return np.asarray(rg2_values), nframes


def is_numeric_row(line: str) -> bool:
    fields = line.split()
    if not fields:
        return False
    try:
        [float(field) for field in fields]
    except ValueError:
        return False
    return True


def collect_thermo(log_files: list[Path], min_step: int, max_step: int | None):
    rows = []
    for path in log_files:
        header = None
        with path.open(errors="replace") as fh:
            for line in fh:
                fields = line.split()
                if fields[:4] == ["Step", "Temp", "PotEng", "KinEng"]:
                    header = fields
                    continue
                if header is None or not is_numeric_row(line):
                    continue
                values = [float(field) for field in fields]
                if len(values) < len(header):
                    continue
                step = int(values[0])
                if step < min_step:
                    continue
                if max_step is not None and step > max_step:
                    continue
                row = dict(zip(header, values))
                rows.append(row)
    return rows


def mean_std(values: np.ndarray):
    if values.size == 0:
        return float("nan"), float("nan")
    return float(np.mean(values)), float(np.std(values, ddof=0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="Directory containing bead trajectories and logs")
    parser.add_argument("--traj-pattern", default="[0-9][0-9].lammpstrj")
    parser.add_argument("--log-pattern", default="log.*.[0-9]*")
    parser.add_argument("--min-step", type=int, default=0)
    parser.add_argument("--max-step", type=int, default=None)
    parser.add_argument("--output", default="observables_summary.csv")
    args = parser.parse_args()

    directory = Path(args.directory)
    traj_files = sorted(directory.glob(args.traj_pattern))
    if not traj_files:
        raise SystemExit(f"No trajectory files found in {directory}")
    log_files = sorted(directory.glob(args.log_pattern))

    oh_values, hoh_values, structure_frames = collect_structure(traj_files, args.min_step, args.max_step)
    rg2_values, rg2_frames = collect_rg2(traj_files, args.min_step, args.max_step)
    thermo = collect_thermo(log_files, args.min_step, args.max_step)

    thermo_values = {key: [] for key in ("Temp", "KinEng", "PotEng")}
    for row in thermo:
        for key in thermo_values:
            if key in row:
                thermo_values[key].append(row[key])

    summary = {
        "case": directory.name,
        "min_step": args.min_step,
        "max_step": "" if args.max_step is None else args.max_step,
        "n_beads": len(traj_files),
        "structure_frames": structure_frames,
        "rg2_frames": rg2_frames,
        "thermo_rows": len(thermo),
    }
    for key, values in [
        ("OH_bond_A", oh_values),
        ("HOH_angle_deg", hoh_values),
        ("Rg2_A2", rg2_values),
        ("Temp_K", np.asarray(thermo_values["Temp"])),
        ("KinEng", np.asarray(thermo_values["KinEng"])),
        ("PotEng", np.asarray(thermo_values["PotEng"])),
    ]:
        mean, std = mean_std(values)
        summary[f"{key}_mean"] = mean
        summary[f"{key}_std"] = std

    out_path = directory / args.output
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary))
        writer.writeheader()
        writer.writerow(summary)

    print(out_path)
    for key in ["OH_bond_A", "HOH_angle_deg", "Rg2_A2", "Temp_K", "KinEng", "PotEng"]:
        print(f"{key}: mean={summary[f'{key}_mean']:.8g} std={summary[f'{key}_std']:.8g}")
    print(
        f"frames: structure={structure_frames} rg2={rg2_frames} thermo_rows={len(thermo)} "
        f"beads={len(traj_files)}"
    )


if __name__ == "__main__":
    main()
