#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np


def read_rdf_blocks(path: Path) -> list[np.ndarray]:
    blocks: list[np.ndarray] = []
    with path.open() as fh:
        lines = [line.strip() for line in fh if line.strip()]

    i = 0
    while i < len(lines):
        if lines[i].startswith("#"):
            i += 1
            continue
        header = lines[i].split()
        if len(header) == 2:
            nrows = int(header[1])
            block = []
            for j in range(i + 1, i + 1 + nrows):
                block.append([float(x) for x in lines[j].split()[1:]])
            blocks.append(np.asarray(block, dtype=float))
            i += nrows + 1
        else:
            i += 1
    return blocks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".", help="Directory containing bead RDF files")
    parser.add_argument("--pattern", default="*.rdf", help="Glob for bead RDF files")
    parser.add_argument("--output", default="rdf_avg.dat", help="Output averaged RDF file")
    args = parser.parse_args()

    rdf_dir = Path(args.directory)
    files = sorted(rdf_dir.glob(args.pattern))
    if not files:
        raise SystemExit(f"No RDF files found in {rdf_dir}")

    all_blocks = []
    for path in files:
        all_blocks.extend(read_rdf_blocks(path))

    if not all_blocks:
        raise SystemExit("No RDF blocks parsed")

    avg = np.mean(np.stack(all_blocks, axis=0), axis=0)
    # LAMMPS compute rdf outputs columns as:
    # r, g_11, coord_11, g_12, coord_12, g_22, coord_22
    header = "r g_OO coord_OO g_OH coord_OH g_HH coord_HH"
    np.savetxt(rdf_dir / args.output, avg, header=header)


if __name__ == "__main__":
    main()
