# Input Assets

This directory stores the shared physical inputs used by all three validation branches.

Files:

- `conf.lmp`: LAMMPS data file used by both 32-bead runs
- `init.xyz`: corresponding initialization structure in XYZ format
- `graph.pb`: DeepMD water model used by both runs

All validation branches should use these same inputs so that differences come from the thermostat/integration path rather than from inconsistent starting conditions.
