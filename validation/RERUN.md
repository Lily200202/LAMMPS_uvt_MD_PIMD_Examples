# Rerunning the examples after the interface update

The checked-in CSVs and original metadata are archival data. New outputs use
`reruns/` by default. Select a new output directory for each rerun; launchers
refuse to reuse a nonempty case directory. Do not replace manuscript values
until the corresponding production runs and reductions have finished.

## Build and record the software

1. Choose and record the final LAMMPS commit on
   `Lily200202/lammps:constant-potential-uvt-pimd-uvt`. The inputs target the
   interface introduced by `efa58a5a98` and are compatible with the separately
   proposed numerical fixes. Review and merge the fixes you intend to use
   before collecting submission data.
2. Copy the two files in `uvt_toy_models/lammps_extension/` into
   `src/EXTRA-FIX/` before configuring LAMMPS. Enable REPLICA, EXTRA-FIX,
   EXTRA-COMPUTE, and PLUGIN, and build with MPI.
3. Rebuild the DeepMD plugin against these exact LAMMPS headers and the same
   MPI implementation. It must provide `deepmd/fparam/dedn` and
   `fparam_from_fix`. Record the DeepMD commit and model hashes.

The existing physical parameters, structures, models, damping times, seeds,
and production lengths have been retained. Changes concern command syntax,
output definitions, the one-dimensional combined-temperature setup, output
locations, and configurable trajectory output.

## Production commands

Run from the repository root. Use absolute paths below and an unused `OUT`.
`MPI_FLAGS` is empty by default; supply MPI-specific options only when needed.
Provide at least one MPI process per bead. These commands run sequentially
when entered in order; each simulation may take substantial time.

```bash
export LMP_BIN=/absolute/path/to/lmp
export MPI_BIN=/absolute/path/to/mpirun
export MPIEXEC="$MPI_BIN"
export PLUGIN_SO=/absolute/path/to/libdeepmd_lmp.so
export DEEPMD_ROOT=/absolute/path/to/deepmd-install
export OMP_NUM_THREADS=1
export DP_INTRA_OP_PARALLELISM_THREADS=1
export DP_INTER_OP_PARALLELISM_THREADS=1
OUT=/absolute/path/to/new-results

RUN_DIR="$OUT/toy-classical" \
  bash validation/uvt_toy_models/classical_coupled/run.sh
CASE_ROOT="$OUT/toy-pimd" BEADS="1 8 16" \
  bash validation/uvt_toy_models/pimd_uvt_coupled/run.sh
RUN_DIR="$OUT/water-nhc" NP=32 PARTITION=32x1 \
  bash validation/water_32beads/nhc/run.sh
RUN_DIR="$OUT/water-pile-l" NP=32 PARTITION=32x1 \
  bash validation/water_32beads/pile_l/run.sh
RUNS_DIR="$OUT/pt-water" TARGET=both BEADS="8 16 32" DUMP_FREQ=100 \
  bash validation/volmer_ml/run.sh
```

| Case | Default production steps | Output |
| --- | --- | --- |
| Classical analytical model | 200000 | Log and metadata under `RUN_DIR` |
| Analytical PIMD, each bead count | 100000 | Per-bead logs and metadata under `CASE_ROOT/runs/pXX` |
| Water, NHC / PILE-L | 100000 each | Per-bead trajectories, RDF blocks, logs, and final structures under `RUN_DIR` |
| Pt-water classical / each PIMD bead count | 300000 each | Logs under `RUNS_DIR/classical` or `pimd_pXX`; optional trajectories |

For the Pt-water production bead-number test use P=8,16,32. A P=1 smoke check
is only an input/interface check, not a data point in that bead-number test.
`DUMP_FREQ=100` saves structural frames every 100 steps; the default zero
omits these files. Dumps do not change the integration settings.

## Numerical reduction

```bash
CASE_ROOT="$OUT/toy-pimd" MIN_STEP=20000 \
  bash validation/uvt_toy_models/pimd_uvt_coupled/postprocess.sh
bash validation/water_32beads/nhc/postprocess.sh "$OUT/water-nhc"
bash validation/water_32beads/pile_l/postprocess.sh "$OUT/water-pile-l"
```

The water wrappers provide basic whole-file reductions. To match the archived
production window for structure and temperature, use the existing windowed
utility on each new water run, for example:

```bash
python3 validation/water_32beads/analysis/pimd_observables.py "$OUT/water-nhc" \
  --min-step 20000 --max-step 100000
```

The analytical reducer requires all bead logs and at least 20 production
samples for the existing block-SEM method. The current PIMD derivative is
bead-local; the reducer averages it explicitly. It also checks agreement
between that derivative and the analytical provider on each bead. The old
separate nuclear/electronic thermostat-work vector fields are omitted;
only the available total work is reported. Extended-energy sums remain
numerical diagnostics to inspect on the completed runs.

A fresh classical summary may be supplied through `CLASSICAL_SUMMARY` for
the P=1 comparison. Archived classical statistics are not loaded automatically.
The repository does not contain the Pt-water figure/fit pipeline or the
200-trajectory reaction-rate initialization workflow. Those calculations,
and the revision-specific timing, fixed-electron-number control, and
finite-difference sensitivity tests, require their existing separate workflows.
The validation inputs here do not substitute for those additional reruns.

## Short checks before submission jobs

Override `NSTEPS` and `THERMO_FREQ` for a short run in a separate output root.
For water, also use matching `NP`/`PARTITION` and smaller RDF/output intervals,
for example `NP=2 PARTITION=2x1 NSTEPS=2 THERMO_FREQ=1 DUMP_FREQ=1
RDF_NEVERY=1 RDF_NFREQ=1`. These checks verify loading, input parsing, and
output wiring; they do not establish convergence or reproduce archived results.


The updated inputs were checked with LAMMPS `9f15ec8ed3` (based on the
`efa58a5a98` interface), MPICH, and the unchanged analytical provider and
DeepMD models. Eight short simulations covered all six input types:
classical analytical, analytical PIMD (P=1 and 2, plus a chain-length check),
classical Pt-water, P=2 Pt-water, and P=2 water with NHC and PILE_L.
Analytical and water postprocessing, derivative wiring, saved frames, and
output-directory protection also passed. These checks used 40 analytical
steps or two ML-model steps, rather than production sampling. The Pt-water
inputs retain a pre-existing triclinic-box performance warning; TensorFlow
also emitted CUDA registration messages during the CPU checks.
