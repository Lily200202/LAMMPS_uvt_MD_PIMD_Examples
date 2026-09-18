#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import csv


def numeric_fields(line: str) -> bool:
    parts = line.split()
    if not parts:
        return False
    for part in parts:
        try:
            float(part)
        except ValueError:
            return False
    return True


def collect_lines(path: Path):
    rows = []
    with path.open() as fh:
        for line in fh:
            if numeric_fields(line):
                rows.append(line.split())
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="LAMMPS log or i-PI out file")
    parser.add_argument("--output", default="thermo_summary.csv", help="CSV output path")
    args = parser.parse_args()

    input_path = Path(args.input)
    rows = collect_lines(input_path)
    if not rows:
        raise SystemExit(f"No numeric thermo rows found in {input_path}")

    out_path = Path(args.output)
    with out_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    main()
