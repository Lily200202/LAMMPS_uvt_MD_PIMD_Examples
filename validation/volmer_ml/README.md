# Electron-Number-Dependent DeepMD Validation

This directory contains the machine-learning tests used for Figures 4 and 7.

- `input/model.pb`: electron-number-dependent DeepMD model.
- `input/system.lmp`: Pt(111)-water starting structure.
- `input/in.classical_uvt_volmer.lmp`: TP-Classical MD input.
- `input/in.pimd_uvt_volmer.template.lmp`: 16-bead TP-PIMD input template.
- `results/classical_timeseries.csv`: compact Figure 4(a-c) numerical data.
- `results/volmer_rate_events.csv`: event/censoring table for 200 trajectories at
  `mu_e = -1.8 eV`, used in Figure 4(d).
- `results/pimd_p16_timeseries.csv`: bead-reduced Figure 7(a-c) numerical data.
- `results/volmer_ml_oh_distribution_*.csv`: Figure 7(d) numerical data.

The rate event is the first moving window for which at least five of ten state samples are
in the product basin. State samples are spaced by 10 simulation steps and each resulting
event index represents 0.005 ps. Seventeen of 200 trajectories reacted. The manuscript's
origin-constrained fit uses the first 16 ordered events (the 29.405 ps endpoint is excluded),
giving `k_PCET = 3.71824 ns^-1` and uncentered `R^2 = 0.99347`.

Raw trajectories total many gigabytes and are omitted. `analysis/prepare_compact_results.py`
documents conversion of fresh LAMMPS logs into the archived compact series. Plotting and
fitting scripts, and copies of the manuscript figures, are intentionally not duplicated here.

## Run

Build LAMMPS from the implementation linked in `../README.md`, build the DeepMD plugin
from the version containing PR #5498, and make its runtime libraries discoverable. Then:

```bash
PLUGIN_SO=/absolute/path/libdeepmd_lmp.so LMP_BIN=/path/to/lmp TARGET=classical ./run.sh
PLUGIN_SO=/absolute/path/libdeepmd_lmp.so LMP_BIN=/path/to/lmp TARGET=pimd BEADS=16 ./run.sh
```

The classical input uses `f_cp[1]` for `N_e`. The PIMD input uses `f_cp[23]` because its
`tchain=3` vector contains ten nuclear and twelve NHC entries before the UVT extension.

Model SHA-256: `44695086af1fbaba1a907e76b31f68d4743637eb5c32be79b4c315319301949d`.
