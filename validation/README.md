# Validation Data and Reproduction Inputs

This directory contains the tests and processed numerical data used in the manuscript.
Large raw trajectories and partition-local LAMMPS logs are excluded; the retained inputs,
structures, models, and compact results permit independent reruns and numerical checks.
Plotting/fitting scripts and duplicate copies of manuscript figures are intentionally omitted.

## Manuscript map

| Manuscript item | Validation directory | Contents |
| --- | --- | --- |
| Figure 2 | `uvt_toy_models/classical_coupled` | Analytical TP-Classical MD input, time series, and summary |
| Figure 4(a-c) | `volmer_ml` | ML TP-Classical MD input and compact time series |
| Figure 4(d), SI S3 | `volmer_ml/results/volmer_rate_*` | 200-trajectory event table and reported fit summary |
| Figure 5 | `water_32beads` | 32-bead PILE-L/NHC inputs and processed RDF/temperature/radius-of-gyration data |
| Figure 6 | `uvt_toy_models/pimd_uvt_coupled` | Analytical TP-PIMD inputs and P=1/8/16 convergence data |
| Figure 7 | `volmer_ml` | 16-bead ML TP-PIMD input, compact time series, and O-H distributions |
| SI Figure S4 | `uvt_toy_models/pimd_uvt_coupled` | P=1/8/16 bead-convergence analysis |

## Software provenance

- LAMMPS implementation: [lammps/lammps PR #5107](https://github.com/lammps/lammps/pull/5107)
- Development branch used to curate these examples: commit
  [`689ecc2d2368e5861131c4a948a6f23f8c750258`](https://github.com/Lily200202/lammps/commit/689ecc2d2368e5861131c4a948a6f23f8c750258)
- DeepMD-kit interface: [deepmodeling/deepmd-kit PR #5498](https://github.com/deepmodeling/deepmd-kit/pull/5498)

The classical `fix uvt` output layout in the cited implementation places `N_e` at
`f_cp[1]`, independent of `tchain`. For `fix pimd/uvt`, ten nuclear outputs and the NHC
vectors precede the UVT extension; with the manuscript setting `tchain 3`, `N_e` is
`f_cp[23]`. The supplied inputs reflect these exact layouts.

## Raw-data policy

The original simulations generated multi-gigabyte bead trajectories and repetitive
partition logs. Those files are not needed to verify the reported observables and are not
stored in Git. Each case instead provides the model/input needed to rerun the calculation
and the processed numerical values reported in the paper. This keeps the archive reviewable
while preserving numerical reproducibility.
