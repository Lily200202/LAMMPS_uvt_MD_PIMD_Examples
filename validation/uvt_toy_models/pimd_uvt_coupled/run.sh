#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${SCRIPT_DIR}/input"
RUNS_DIR="${SCRIPT_DIR}/runs"

LMP_BIN="${LMP_BIN:-lmp}"
MPIEXEC="${MPIEXEC:-mpirun}"
BEADS="${BEADS:-1 8 16}"
NSTEPS="${NSTEPS:-100000}"
THERMO_FREQ="${THERMO_FREQ:-100}"
DT="${DT:-0.002}"
TDAMP="${TDAMP:-0.5}"
UDAMP="${UDAMP:-${TDAMP}}"
TCHAIN="${TCHAIN:-3}"
TLOOP="${TLOOP:-1}"
TEMP="${TEMP:-1.0}"
MU="${MU:-1.0}"
NE_INIT="${NE_INIT:-2.1}"
NE_VEL_INIT="${NE_VEL_INIT:-0.0}"
X_CENTROID_INIT="${X_CENTROID_INIT:-1.0}"
X_SPREAD="${X_SPREAD:-0.3}"
VX_INIT="${VX_INIT:--0.35}"

if [[ ! -x "${LMP_BIN}" ]] && ! command -v "${LMP_BIN}" >/dev/null 2>&1; then
  echo "LAMMPS executable not found or not executable: ${LMP_BIN}" >&2
  exit 1
fi

if [[ ! -x "${MPIEXEC}" ]] && ! command -v "${MPIEXEC}" >/dev/null 2>&1; then
  echo "MPI launcher not found or not executable: ${MPIEXEC}" >&2
  exit 1
fi

mkdir -p "${RUNS_DIR}"
cd "${SCRIPT_DIR}"

cat > run_metadata.csv <<EOF
beads,dt,nsteps,thermo_freq,temp,tdamp,udamp,tchain,tloop,mu,ne_init,ne_vel_init,x_centroid_init,x_spread,vx_init
${BEADS// /;},${DT},${NSTEPS},${THERMO_FREQ},${TEMP},${TDAMP},${UDAMP},${TCHAIN},${TLOOP},${MU},${NE_INIT},${NE_VEL_INIT},${X_CENTROID_INIT},${X_SPREAD},${VX_INIT}
EOF

generate_xworld() {
  local p="$1"
  python3 - "$p" "${X_CENTROID_INIT}" "${X_SPREAD}" <<'PY'
import sys

p = int(sys.argv[1])
center = float(sys.argv[2])
spread = float(sys.argv[3])

if p == 1:
    values = [center]
else:
    values = [
        center + spread * (2.0 * i / (p - 1) - 1.0)
        for i in range(p)
    ]

print(" ".join(f"{value:.12f}" for value in values))
PY
}

for p in ${BEADS}; do
  case_dir="${RUNS_DIR}/p$(printf "%02d" "${p}")"
  mkdir -p "${case_dir}"

  xworld="$(generate_xworld "${p}")"
  input_file="${case_dir}/in.pimd_uvt_coupled.lmp"

  sed \
    -e "s|@XINIT_WORLD@|${xworld}|g" \
    "${INPUT_DIR}/in.pimd_uvt_coupled.template.lmp" > "${input_file}"

  cat > "${case_dir}/case_metadata.csv" <<EOF
beads,dt,nsteps,thermo_freq,temp,tdamp,udamp,tchain,tloop,mu,ne_init,ne_vel_init,x_centroid_init,x_spread,vx_init,xinit_world
${p},${DT},${NSTEPS},${THERMO_FREQ},${TEMP},${TDAMP},${UDAMP},${TCHAIN},${TLOOP},${MU},${NE_INIT},${NE_VEL_INIT},${X_CENTROID_INIT},${X_SPREAD},${VX_INIT},"${xworld}"
EOF

  (
    cd "${case_dir}"
    export OMPI_ALLOW_RUN_AS_ROOT=1
    export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
    export OMPI_MCA_opal_warn_on_missing_libcuda=0
    export OMP_NUM_THREADS=1

    "${MPIEXEC}" --oversubscribe -np "${p}" "${LMP_BIN}" \
      -partition "${p}x1" \
      -in "${input_file}" \
      -log log.pimd_uvt_coupled \
      -var DT "${DT}" \
      -var TDAMP "${TDAMP}" \
      -var UDAMP "${UDAMP}" \
      -var TCHAIN "${TCHAIN}" \
      -var TLOOP "${TLOOP}" \
      -var TEMP "${TEMP}" \
      -var MU "${MU}" \
      -var NSTEPS "${NSTEPS}" \
      -var THERMO_FREQ "${THERMO_FREQ}" \
      -var NE_INIT "${NE_INIT}" \
      -var NE_VEL_INIT "${NE_VEL_INIT}" \
      -var VX_INIT "${VX_INIT}" \
      > run.out 2>&1
  )
done
