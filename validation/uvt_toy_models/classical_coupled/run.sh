#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${SCRIPT_DIR}/input"

LMP_BIN="${LMP_BIN:-lmp}"
NSTEPS="${NSTEPS:-200000}"
THERMO_FREQ="${THERMO_FREQ:-100}"
DT="${DT:-0.002}"
TDAMP="${TDAMP:-0.5}"
UDAMP="${UDAMP:-${TDAMP}}"
RUN_DIR="${RUN_DIR:-${SCRIPT_DIR}/reruns/nsteps_${NSTEPS}}"
X_INIT="${X_INIT:-1.0}"
VX_INIT="${VX_INIT:--0.35}"
NE_INIT="${NE_INIT:-2.1}"
NE_VEL_INIT="${NE_VEL_INIT:-0.0}"

mkdir -p "${RUN_DIR}"
if find "${RUN_DIR}" -mindepth 1 ! -name run.out -print -quit | grep -q .; then
  echo "Refusing to overwrite non-empty RUN_DIR: ${RUN_DIR}" >&2
  exit 1
fi
cd "${RUN_DIR}"

cat > run_metadata.csv <<EOF
dt,nsteps,thermo_freq,tdamp,udamp,x_init,vx_init,ne_init,ne_vel_init
${DT},${NSTEPS},${THERMO_FREQ},${TDAMP},${UDAMP},${X_INIT},${VX_INIT},${NE_INIT},${NE_VEL_INIT}
EOF

exec "${LMP_BIN}" \
  -in "${INPUT_DIR}/in.classical_uvt_coupled.lmp" \
  -log log.classical_uvt \
  -var DT "${DT}" \
  -var TDAMP "${TDAMP}" \
  -var UDAMP "${UDAMP}" \
  -var NSTEPS "${NSTEPS}" \
  -var THERMO_FREQ "${THERMO_FREQ}" \
  -var X_INIT "${X_INIT}" \
  -var VX_INIT "${VX_INIT}" \
  -var NE_INIT "${NE_INIT}" \
  -var NE_VEL_INIT "${NE_VEL_INIT}"
