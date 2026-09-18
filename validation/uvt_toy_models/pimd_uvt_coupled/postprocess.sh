#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MIN_STEP="${MIN_STEP:-20000}"

cd "${SCRIPT_DIR}"
"${PYTHON_BIN}" analysis/analyze_pimd_uvt_coupled.py . --min-step "${MIN_STEP}"
