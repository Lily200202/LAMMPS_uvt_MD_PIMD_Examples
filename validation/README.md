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

## Software provenance and current inputs

The retained numerical CSVs and original metadata are archival results from the
manuscript calculations. Their curation snapshot is
[`689ecc2d2368e5861131c4a948a6f23f8c750258`](https://github.com/Lily200202/lammps/commit/689ecc2d2368e5861131c4a948a6f23f8c750258).
They have not been regenerated or relabeled by this input migration.

The runnable inputs now target the interface in
[`efa58a5a9858abaf70431be4c49a62dd38d6b135`](https://github.com/Lily200202/lammps/commit/efa58a5a9858abaf70431be4c49a62dd38d6b135)
on `Lily200202/lammps`, branch `constant-potential-uvt-pimd-uvt`.
The implementation is also proposed in [lammps/lammps PR #5107](https://github.com/lammps/lammps/pull/5107).
For submission reruns, choose the final reviewed code revision, record its full
commit ID, and rebuild LAMMPS and its plugins against the same headers and MPI.
The DeepMD electron-number interface is proposed in
[deepmodeling/deepmd-kit PR #5498](https://github.com/deepmodeling/deepmd-kit/pull/5498).

| Quantity | `fix uvt` | `fix pimd/uvt` |
| --- | --- | --- |
| Electron number | `f_cp[1]` | `f_cp[11]` |
| Combined temperature | `f_cp[2]` | `f_cp[12]` |
| Electron-number velocity | `f_cp[3]` | `f_cp[13]` |
| Energy derivative | `f_cp[4]` | `f_cp[14]` (individual bead) |
| Electronic kinetic energy | `f_cp[5]` | `f_cp[15]` |
| Electronic potential `-mu*Ne` | `f_cp[6]` | `f_cp[16]` |

These six indices do not depend on `tchain`. PIMD NHC outputs start at entry 17;
the launchers generate chain-energy expressions for the selected `TCHAIN`.
Average the PIMD derivative over bead logs before comparing it with `mu`.
The chemical-potential target is printed from the input variable because it is
no longer a fix-vector output. Separate nuclear/electronic thermostat-work
vector entries are no longer available; the PIMD fix scalar reports their total.

New runs use separate `reruns/` directories by default. See
[`RERUN.md`](RERUN.md) for the complete rerun commands and output locations.

## Raw-data policy

The original simulations generated multi-gigabyte bead trajectories and repetitive
partition logs. Those files are not needed to verify the reported observables and are not
stored in Git. Each case instead provides the model/input needed to rerun the calculation
and the processed numerical values reported in the paper. This keeps the archive reviewable
while preserving numerical reproducibility.
