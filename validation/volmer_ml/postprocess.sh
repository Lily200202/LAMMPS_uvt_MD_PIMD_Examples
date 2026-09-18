#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CLASSICAL_LOG="${CLASSICAL_LOG:-${SCRIPT_DIR}/runs/classical/log.classical_uvt_volmer}"
PIMD_LOG_DIR="${PIMD_LOG_DIR:-${SCRIPT_DIR}/runs/pimd_p16}"

"${PYTHON_BIN}" "${SCRIPT_DIR}/analysis/prepare_compact_results.py" \
  --classical-log "${CLASSICAL_LOG}" --pimd-log-dir "${PIMD_LOG_DIR}"
