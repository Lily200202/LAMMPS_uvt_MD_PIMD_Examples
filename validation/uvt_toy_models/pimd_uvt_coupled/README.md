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

The physical output block starts at `f_cp[11]`, independent of `TCHAIN`.
The launcher fills the NHC energy expressions for the selected chain length.
New inputs, logs, and metadata are written under `reruns/` by default;
set `CASE_ROOT` to select a fresh output root. `MPI_FLAGS` supplies launcher-specific
options; it is empty by default. For Open MPI on a smaller local machine,
`MPI_FLAGS="--oversubscribe"` can be set explicitly.

`postprocess.sh` reads this new output root and regenerates numerical summary
CSVs there. It averages `f_cp[14]` over beads; it does not treat each bead's
value as an already averaged response. Removed separate thermostat-work fields
are omitted, while total work comes from the fix scalar. The combined temperature
is retained alongside the nuclear temperature. The archived CSVs remain unchanged.

The reduction checks the number of bead logs and their headers before combining
them. It needs at least 20 production samples for its existing block-SEM estimate.
An optional `CLASSICAL_SUMMARY` must identify a newly generated classical summary;
archived classical results are not automatically mixed with fresh PIMD data.
Plotting scripts and manuscript figures are not included.
