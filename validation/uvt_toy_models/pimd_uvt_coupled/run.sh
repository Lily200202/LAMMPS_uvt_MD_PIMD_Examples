#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${SCRIPT_DIR}/input"
CASE_ROOT="${CASE_ROOT:-${SCRIPT_DIR}/reruns}"
RUNS_DIR="${RUNS_DIR:-${CASE_ROOT}/runs}"

LMP_BIN="${LMP_BIN:-lmp}"
MPIEXEC="${MPIEXEC:-mpirun}"
MPI_FLAGS="${MPI_FLAGS:-}"
read -r -a MPI_FLAGS_ARRAY <<< "${MPI_FLAGS}"
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

[[ "${TCHAIN}" =~ ^[1-9][0-9]*$ ]] || { echo "TCHAIN must be positive" >&2; exit 1; }
chain_energy_terms() {
  local block="$1" index
  local terms=()
  for ((index=0; index<TCHAIN; index++)); do
    terms+=("f_cp[$((17 + block*TCHAIN + index))]")
  done
  local IFS=+
  echo "${terms[*]}"
}
nhc_potential="$(chain_energy_terms 2)"
nhc_kinetic="$(chain_energy_terms 3)"

mkdir -p "${RUNS_DIR}" "${CASE_ROOT}"
RUNS_DIR="$(cd "${RUNS_DIR}" && pwd)"
CASE_ROOT="$(cd "${CASE_ROOT}" && pwd)"
cd "${CASE_ROOT}"

for p in ${BEADS}; do
  case_dir="${RUNS_DIR}/p$(printf "%02d" "${p}")"
  if [[ -d "${case_dir}" ]] && find "${case_dir}" -mindepth 1 ! -name run.out -print -quit | grep -q .; then
    echo "Refusing to overwrite non-empty case directory: ${case_dir}" >&2
    exit 1
  fi
done

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
    -e "s|@NHC_POTENTIAL@|${nhc_potential}|g" \
    -e "s|@NHC_KINETIC@|${nhc_kinetic}|g" \
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

    "${MPIEXEC}" "${MPI_FLAGS_ARRAY[@]}" -np "${p}" "${LMP_BIN}" \
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
