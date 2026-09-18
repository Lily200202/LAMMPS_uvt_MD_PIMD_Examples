# Analytical TP-Classical MD Test

The test uses

```text
U(x,N_e) = k_x x^2/2 + k_e (N_e-N_0)^2/2 + g x N_e
Phi(x,N_e) = U(x,N_e) - mu N_e
```

with `k_x=k_e=5`, `g=2`, `N_0=1`, `mu=1`, and `T=1`. The exact minimum is
`x*=-4/7` and `N_e*=10/7`. `fix uvt/toy/coupled` applies
`F_x=-(k_x x+g N_e)` and supplies `dE/dN_e=k_e(N_e-N_0)+g x`.

Copy the provider files from `../lammps_extension/` into `src/EXTRA-FIX/` before building
LAMMPS, then run:

```bash
LMP_BIN=/path/to/lmp ./run.sh
```

The archived `classical_uvt_timeseries.csv` and `classical_uvt_summary.csv` contain the
Figure 2 numerical values. For the reference production window, the measured means are
`<x>=-0.53872`, `<N_e>=1.40257`, `<dE/dN_e>=0.93542`, and `<T>=1.07412`; the maximum
relative extended-Hamiltonian excursion is `2.38e-5`.
