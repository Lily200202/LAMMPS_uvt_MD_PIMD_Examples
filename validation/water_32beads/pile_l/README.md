# PILE-L Water Run

This is the 32-bead, 300 K PILE-L reference used in Figure 5. Run with:

```bash
PLUGIN_SO=/absolute/path/libdeepmd_lmp.so LMP_BIN=/path/to/lmp ./run.sh
```

`postprocess.sh` reduces newly generated bead RDF and trajectory files to numerical data.
