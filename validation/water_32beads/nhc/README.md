# NHC Water Run

This is the 32-bead, 300 K Nose-Hoover-chain comparison used in Figure 5. The manuscript
settings are `Tdamp=0.01`, `tchain=3`, and user-controlled `tloop=1`.

```bash
PLUGIN_SO=/absolute/path/libdeepmd_lmp.so LMP_BIN=/path/to/lmp ./run.sh
```

`postprocess.sh` reduces newly generated bead RDF and trajectory files to numerical data.
