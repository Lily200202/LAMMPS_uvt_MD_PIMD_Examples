#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${SCRIPT_DIR}/input"
RUNS_DIR="${SCRIPT_DIR}/runs"

LMP_BIN="${LMP_BIN:-lmp}"
MPI_BIN="${MPI_BIN:-mpirun}"
TARGET="${TARGET:-both}"
BEADS="${BEADS:-16}"

PLUGIN_SO="${PLUGIN_SO:?Set PLUGIN_SO to libdeepmd_lmp.so}"
DEEPMD_PLUGIN_DIR="${DEEPMD_PLUGIN_DIR:-$(dirname "${PLUGIN_SO}")}"
DEEPMD_ROOT="${DEEPMD_ROOT:-$(cd "${DEEPMD_PLUGIN_DIR}/../.." && pwd)}"
DEEPMD_LIB_DIR="${DEEPMD_LIB_DIR:-${DEEPMD_ROOT}/lib}"
DEEPMD_OP_DIR="${DEEPMD_OP_DIR:-${DEEPMD_ROOT}/op/tf}"
TENSORFLOW_LIB_DIR="${TENSORFLOW_LIB_DIR:-}"
DEEPMD_RUNTIME_PATH="${DEEPMD_LIB_DIR}:${DEEPMD_OP_DIR}${TENSORFLOW_LIB_DIR:+:${TENSORFLOW_LIB_DIR}}"

DATA_FILE="${DATA_FILE:-${INPUT_DIR}/system.lmp}"
MODEL_PATH="${MODEL_PATH:-${INPUT_DIR}/model.pb}"
NSTEPS="${NSTEPS:-300000}"
THERMO_FREQ="${THERMO_FREQ:-1}"
TEMP="${TEMP:-300.0}"
MU="${MU:--3.0}"
TDAMP="${TDAMP:-0.05}"
UDAMP="${UDAMP:-0.05}"
TCHAIN="${TCHAIN:-3}"
TLOOP="${TLOOP:-1}"
VEL_SEED="${VEL_SEED:-4928459}"
NE_INIT="${NE_INIT:-0.648702}"
NE_VEL_INIT="${NE_VEL_INIT:-0.0}"
DT="${DT:-0.0002}"
TDOF="${TDOF:-549.0}"

if [[ ! -x "${LMP_BIN}" ]] && ! command -v "${LMP_BIN}" >/dev/null 2>&1; then
  echo "LAMMPS executable not found or not executable: ${LMP_BIN}" >&2
  exit 1
fi
if [[ "${TARGET}" != "classical" ]] && [[ ! -x "${MPI_BIN}" ]] && ! command -v "${MPI_BIN}" >/dev/null 2>&1; then
  echo "MPI launcher not found or not executable: ${MPI_BIN}" >&2
  exit 1
fi
if [[ ! -f "${PLUGIN_SO}" ]]; then
  echo "DeepMD plugin not found: ${PLUGIN_SO}" >&2
  exit 1
fi
if [[ ! -f "${DATA_FILE}" ]]; then
  echo "Data file not found: ${DATA_FILE}" >&2
  exit 1
fi
if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "Model file not found: ${MODEL_PATH}" >&2
  exit 1
fi

export OMPI_ALLOW_RUN_AS_ROOT="${OMPI_ALLOW_RUN_AS_ROOT:-1}"
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM="${OMPI_ALLOW_RUN_AS_ROOT_CONFIRM:-1}"
export OMPI_MCA_opal_warn_on_missing_libcuda="${OMPI_MCA_opal_warn_on_missing_libcuda:-0}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export DP_INTRA_OP_PARALLELISM_THREADS="${DP_INTRA_OP_PARALLELISM_THREADS:-1}"
export DP_INTER_OP_PARALLELISM_THREADS="${DP_INTER_OP_PARALLELISM_THREADS:-1}"
export LAMMPS_PLUGIN_PATH="${DEEPMD_PLUGIN_DIR}${LAMMPS_PLUGIN_PATH:+:${LAMMPS_PLUGIN_PATH}}"
export LD_LIBRARY_PATH="${DEEPMD_RUNTIME_PATH}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

mkdir -p "${RUNS_DIR}"
cd "${SCRIPT_DIR}"

cat > run_metadata.csv <<EOF
target,beads,dt,nsteps,thermo_freq,temp,mu,tdamp,udamp,tchain,tloop,vel_seed,ne_init,ne_vel_init,tdof,data_file,model_path,plugin_so
${TARGET},"${BEADS}",${DT},${NSTEPS},${THERMO_FREQ},${TEMP},${MU},${TDAMP},${UDAMP},${TCHAIN},${TLOOP},${VEL_SEED},${NE_INIT},${NE_VEL_INIT},${TDOF},${DATA_FILE},${MODEL_PATH},${PLUGIN_SO}
EOF

run_classical() {
  local case_dir="${RUNS_DIR}/classical"
  mkdir -p "${case_dir}"
  (
    cd "${case_dir}"
    "${LMP_BIN}" \
      -in "${INPUT_DIR}/in.classical_uvt_volmer.lmp" \
      -log log.classical_uvt_volmer \
      -var PLUGIN_SO "${PLUGIN_SO}" \
      -var DATA_FILE "${DATA_FILE}" \
      -var MODEL_PATH "${MODEL_PATH}" \
      -var NSTEPS "${NSTEPS}" \
      -var THERMO_FREQ "${THERMO_FREQ}" \
      -var TEMP "${TEMP}" \
      -var MU "${MU}" \
      -var TDAMP "${TDAMP}" \
      -var UDAMP "${UDAMP}" \
      -var VEL_SEED "${VEL_SEED}" \
      -var NE_INIT "${NE_INIT}" \
      -var NE_VEL_INIT "${NE_VEL_INIT}" \
      -var DT "${DT}" \
      > run.out 2>&1
  )
}

run_pimd_case() {
  local beads="$1"
  local case_dir="${RUNS_DIR}/pimd_p$(printf "%02d" "${beads}")"
  mkdir -p "${case_dir}"
  cp "${INPUT_DIR}/in.pimd_uvt_volmer.template.lmp" "${case_dir}/in.pimd_uvt_volmer.lmp"
  (
    cd "${case_dir}"
    "${MPI_BIN}" --oversubscribe -np "${beads}" "${LMP_BIN}" \
      -partition "${beads}x1" \
      -in "${case_dir}/in.pimd_uvt_volmer.lmp" \
      -log log.pimd_uvt_volmer \
      -var PLUGIN_SO "${PLUGIN_SO}" \
      -var DATA_FILE "${DATA_FILE}" \
      -var MODEL_PATH "${MODEL_PATH}" \
      -var NSTEPS "${NSTEPS}" \
      -var THERMO_FREQ "${THERMO_FREQ}" \
      -var TEMP "${TEMP}" \
      -var MU "${MU}" \
      -var TDAMP "${TDAMP}" \
      -var UDAMP "${UDAMP}" \
      -var TCHAIN "${TCHAIN}" \
      -var TLOOP "${TLOOP}" \
      -var VEL_SEED "${VEL_SEED}" \
      -var NE_INIT "${NE_INIT}" \
      -var NE_VEL_INIT "${NE_VEL_INIT}" \
      -var DT "${DT}" \
      -var TDOF "${TDOF}" \
      > run.out 2>&1
  )
}

case "${TARGET}" in
  classical)
    run_classical
    ;;
  pimd)
    for p in ${BEADS}; do run_pimd_case "${p}"; done
    ;;
  both)
    run_classical
    for p in ${BEADS}; do run_pimd_case "${p}"; done
    ;;
  *)
    echo "TARGET must be one of: classical, pimd, both" >&2
    exit 1
    ;;
esac
