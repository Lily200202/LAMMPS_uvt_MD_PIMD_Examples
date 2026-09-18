# Analytical TP-PIMD Test

This is the path-integral counterpart of `../classical_coupled`. The electronic coordinate
`N_e` is shared by all beads, while each bead evaluates its own nuclear force and
`dE/dN_e`; `fix pimd/uvt` averages the electronic response over beads.

The manuscript uses P=8 for the Figure 6 time series and P=1, 8, and 16 for the SI bead
convergence check. Compact time series and summaries for those bead counts are archived in
`runs/` and the top-level CSV files. Partition logs and screens are omitted.

Copy the provider files from `../lammps_extension/` into `src/EXTRA-FIX/` before building
LAMMPS, then run:

```bash
LMP_BIN=/path/to/lmp MPIEXEC=/path/to/mpirun BEADS="1 8 16" ./run.sh
```

The default input uses `tchain=3`; therefore the PIMD/UVT physical extension starts at
`f_cp[23]`. `postprocess.sh` regenerates numerical summary CSVs only. Plotting scripts and
manuscript figures are not included.
