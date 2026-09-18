#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_DIR="${SCRIPT_DIR}/../analysis"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUN_DIR="${1:-${SCRIPT_DIR}/runs/nsteps_100000}"

cd "${RUN_DIR}"

"${PYTHON_BIN}" "${ANALYSIS_DIR}/average_rdf.py" . --pattern '*.rdf' --output rdf_nvt_mainline_avg.dat
"${PYTHON_BIN}" "${ANALYSIS_DIR}/structure_metrics.py" . --pattern '*.lammpstrj' --output structure_nvt_mainline.dat
"${PYTHON_BIN}" "${ANALYSIS_DIR}/rg2.py" . --pattern '*.lammpstrj' --output rg2_nvt_mainline.dat
"${PYTHON_BIN}" "${ANALYSIS_DIR}/collect_thermo.py" log.liquidwater_nvt_mainline.0 --output thermo_nvt_mainline_bead0.csv
