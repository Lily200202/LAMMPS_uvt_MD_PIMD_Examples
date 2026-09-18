#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import math
import numpy as np


def parse_lammpstrj(path: Path):
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
            fh.readline()
            atoms = []
            for _ in range(natoms):
                atom_id, atom_type, x, y, z, ix, iy, iz = fh.readline().split()
                atoms.append(
                    (
                        int(atom_id),
                        int(atom_type),
                        float(x) + int(ix) * (bounds[0][1] - bounds[0][0]),
                        float(y) + int(iy) * (bounds[1][1] - bounds[1][0]),
                        float(z) + int(iz) * (bounds[2][1] - bounds[2][0]),
                    )
                )
            yield timestep, np.asarray(atoms, dtype=float)


def nearest_two_h(oxygen: np.ndarray, hydrogens: np.ndarray) -> np.ndarray:
    dvec = hydrogens[:, 2:5] - oxygen[2:5]
    dist2 = np.sum(dvec * dvec, axis=1)
    return hydrogens[np.argsort(dist2)[:2]]


def angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    v1 = a - b
    v2 = c - b
    cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    cosang = np.clip(cosang, -1.0, 1.0)
    return math.degrees(math.acos(cosang))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".", help="Directory containing bead trajectory files")
    parser.add_argument("--pattern", default="*.lammpstrj", help="Glob for trajectory files")
    parser.add_argument("--output", default="structure_metrics.dat", help="Output summary file")
    args = parser.parse_args()

    traj_dir = Path(args.directory)
    traj_files = sorted(traj_dir.glob(args.pattern))
    if not traj_files:
        raise SystemExit(f"No trajectory files found in {traj_dir}")

    oh_values = []
    hoh_values = []

    for traj in traj_files:
        for _, atoms in parse_lammpstrj(traj):
            oxygens = atoms[atoms[:, 1] == 1]
            hydrogens = atoms[atoms[:, 1] == 2]
            for oxygen in oxygens:
                pair = nearest_two_h(oxygen, hydrogens)
                oh_values.extend(np.linalg.norm(pair[:, 2:5] - oxygen[2:5], axis=1).tolist())
                hoh_values.append(angle_deg(pair[0, 2:5], oxygen[2:5], pair[1, 2:5]))

    oh_arr = np.asarray(oh_values)
    hoh_arr = np.asarray(hoh_values)
    summary = np.array(
        [
            [oh_arr.mean(), oh_arr.std(ddof=0)],
            [hoh_arr.mean(), hoh_arr.std(ddof=0)],
        ]
    )
    np.savetxt(traj_dir / args.output, summary, header="mean std\nOH_bond_length\nHOH_angle")


if __name__ == "__main__":
    main()
