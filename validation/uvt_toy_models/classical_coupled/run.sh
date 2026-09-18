#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${SCRIPT_DIR}/input"

LMP_BIN="${LMP_BIN:-lmp}"
NSTEPS="${NSTEPS:-200000}"
THERMO_FREQ="${THERMO_FREQ:-100}"
DT="${DT:-0.002}"
TDAMP="${TDAMP:-0.5}"
X_INIT="${X_INIT:-1.0}"
VX_INIT="${VX_INIT:--0.35}"
NE_INIT="${NE_INIT:-2.1}"
NE_VEL_INIT="${NE_VEL_INIT:-0.0}"

cd "${SCRIPT_DIR}"

cat > run_metadata.csv <<EOF
dt,nsteps,thermo_freq,tdamp,x_init,vx_init,ne_init,ne_vel_init
${DT},${NSTEPS},${THERMO_FREQ},${TDAMP},${X_INIT},${VX_INIT},${NE_INIT},${NE_VEL_INIT}
EOF

exec "${LMP_BIN}" \
  -in "${INPUT_DIR}/in.classical_uvt_coupled.lmp" \
  -log log.classical_uvt \
  -var DT "${DT}" \
  -var TDAMP "${TDAMP}" \
  -var NSTEPS "${NSTEPS}" \
  -var THERMO_FREQ "${THERMO_FREQ}" \
  -var X_INIT "${X_INIT}" \
  -var VX_INIT "${VX_INIT}" \
  -var NE_INIT "${NE_INIT}" \
  -var NE_VEL_INIT "${NE_VEL_INIT}"
