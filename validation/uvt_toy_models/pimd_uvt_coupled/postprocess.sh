#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MIN_STEP="${MIN_STEP:-20000}"

CASE_ROOT="${CASE_ROOT:-${SCRIPT_DIR}/reruns}"
args=("${CASE_ROOT}" --min-step "${MIN_STEP}")
if [[ -n "${CLASSICAL_SUMMARY:-}" ]]; then
  args+=(--classical-summary "${CLASSICAL_SUMMARY}")
fi
"${PYTHON_BIN}" "${SCRIPT_DIR}/analysis/analyze_pimd_uvt_coupled.py" "${args[@]}"
