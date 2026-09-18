# Analytical Coupled-Model Validation

The two cases use

```text
U(x, N_e) = k_x x^2 / 2 + k_e (N_e - N_0)^2 / 2 + g x (N_e - N_0)
```

to validate classical and path-integral constant-potential propagation against an
analytical equilibrium. Copy the two files in `lammps_extension/` into
`src/EXTRA-FIX/` before configuring LAMMPS, or add the equivalent style to the build by
another supported LAMMPS extension mechanism.
