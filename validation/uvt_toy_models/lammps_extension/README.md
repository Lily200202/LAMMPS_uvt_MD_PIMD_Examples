# Analytical Test Provider

`fix uvt/toy/coupled` supplies both the nuclear force and `dE/dN_e` for the analytical
validation model. It is validation-only code, not part of the proposed public LAMMPS API.


Copy both provider files into LAMMPS `src/EXTRA-FIX/` before configuring and
building with EXTRA-FIX, EXTRA-COMPUTE, REPLICA, and PLUGIN enabled.
The provider reads `Ne` through the fix extraction interface; it does not use a
chain-dependent UVT output index.

Its scalar output `f_toy` is `dE/dNe`. Its vector entries are:

| Entry | Quantity |
| --- | --- |
| `f_toy[1]` | Model potential energy |
| `f_toy[2]` | Electron number |
| `f_toy[3]` | Nuclear coordinate |
| `f_toy[4]` | Energy derivative `dE/dNe` |
| `f_toy[5]` | Nuclear force |
