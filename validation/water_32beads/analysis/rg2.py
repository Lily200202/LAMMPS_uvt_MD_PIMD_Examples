#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np


def parse_lammpstrj_frames(path: Path):
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
            data = np.zeros((natoms, 4), dtype=float)
            for i in range(natoms):
                atom_id, atom_type, x, y, z, ix, iy, iz = fh.readline().split()
                data[i, 0] = int(atom_id)
                data[i, 1] = float(x) + int(ix) * (bounds[0][1] - bounds[0][0])
                data[i, 2] = float(y) + int(iy) * (bounds[1][1] - bounds[1][0])
                data[i, 3] = float(z) + int(iz) * (bounds[2][1] - bounds[2][0])
            order = np.argsort(data[:, 0].astype(int))
            yield timestep, data[order]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".", help="Directory containing bead trajectory files")
    parser.add_argument("--pattern", default="*.lammpstrj", help="Glob for bead trajectory files")
    parser.add_argument("--output", default="rg2.dat", help="Output summary file")
    args = parser.parse_args()

    traj_dir = Path(args.directory)
    traj_files = sorted(traj_dir.glob(args.pattern))
    if len(traj_files) < 2:
        raise SystemExit("Rg^2 analysis requires at least two bead trajectories")

    frame_iters = [parse_lammpstrj_frames(path) for path in traj_files]
    rg2_values = []

    while True:
        frames = []
        for it in frame_iters:
            try:
                frames.append(next(it))
            except StopIteration:
                frames = []
                break
        if not frames:
            break

        _, first = frames[0]
        positions = np.stack([frame[:, 1:4] for _, frame in frames], axis=0)
        centroid = np.mean(positions, axis=0)
        rg2 = np.mean(np.sum((positions - centroid[None, :, :]) ** 2, axis=2))
        rg2_values.append(rg2)

    values = np.asarray(rg2_values)
    summary = np.array([[values.mean(), values.std(ddof=0)]])
    np.savetxt(traj_dir / args.output, summary, header="Rg2_mean Rg2_std")


if __name__ == "__main__":
    main()
