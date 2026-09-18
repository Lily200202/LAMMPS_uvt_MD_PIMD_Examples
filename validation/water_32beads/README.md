# 32-Bead Liquid-Water PIMD Validation

This case compares the PILE-L and Nose-Hoover-chain thermostats used in Figure 5.
Both calculations contain 128 water molecules and 32 beads at 300 K.

- `pile_l/`: PILE-L input and launcher.
- `nhc/`: NHC input and launcher (`tchain=3`, `tloop=1`).
- `input/`: common LAMMPS structure and DeepMD water model.
- `results/`: processed bead-averaged RDFs, instantaneous temperatures, and
  radius-of-gyration distributions for steps 20000-100000.
- `analysis/`: numerical reduction utilities for newly generated trajectories.

Raw bead trajectories, RDF block files, and partition logs are excluded because they total
several gigabytes. Plotting scripts and copies of Figure 5 are intentionally omitted.

Run either case with a LAMMPS executable containing the relevant PIMD implementation and a
compatible DeepMD plugin:

```bash
PLUGIN_SO=/absolute/path/libdeepmd_lmp.so LMP_BIN=/path/to/lmp ./pile_l/run.sh
PLUGIN_SO=/absolute/path/libdeepmd_lmp.so LMP_BIN=/path/to/lmp ./nhc/run.sh
```

Model SHA-256: `c272f943c16ae7d821d5f34693db626b0a9b503d345bb0c892135326fc83a233`.
