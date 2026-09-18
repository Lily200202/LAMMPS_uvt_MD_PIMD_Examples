#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LMP_BIN="${LMP_BIN:-lmp}"
MPI_BIN="${MPI_BIN:-mpirun}"
MPI_FLAGS="${MPI_FLAGS:---use-hwthread-cpus}"
NP="${NP:-32}"
PARTITION="${PARTITION:-32x1}"

PLUGIN_SO="${PLUGIN_SO:?Set PLUGIN_SO to libdeepmd_lmp.so}"
DEEPMD_PLUGIN_DIR="${DEEPMD_PLUGIN_DIR:-$(dirname "${PLUGIN_SO}")}"
DEEPMD_ROOT="${DEEPMD_ROOT:-$(cd "${DEEPMD_PLUGIN_DIR}/../.." && pwd)}"
DEEPMD_LIB_DIR="${DEEPMD_LIB_DIR:-${DEEPMD_ROOT}/lib}"
DEEPMD_OP_DIR="${DEEPMD_OP_DIR:-${DEEPMD_ROOT}/op/tf}"
TENSORFLOW_LIB_DIR="${TENSORFLOW_LIB_DIR:-}"
DEEPMD_RUNTIME_PATH="${DEEPMD_LIB_DIR}:${DEEPMD_OP_DIR}${TENSORFLOW_LIB_DIR:+:${TENSORFLOW_LIB_DIR}}"

DATA_FILE="${DATA_FILE:-${SCRIPT_DIR}/../input/conf.lmp}"
MODEL_PATH="${MODEL_PATH:-${SCRIPT_DIR}/../input/graph.pb}"
NSTEPS="${NSTEPS:-100000}"
RUN_DIR="${RUN_DIR:-${SCRIPT_DIR}/runs/nsteps_${NSTEPS}}"
THERMO_FREQ="${THERMO_FREQ:-100}"
DUMP_FREQ="${DUMP_FREQ:-100}"
TEMP="${TEMP:-300.0}"
TAU_T="${TAU_T:-0.100000}"
VEL_SEED="${VEL_SEED:-23456789}"
RDF_NBINS="${RDF_NBINS:-200}"
RDF_NEVERY="${RDF_NEVERY:-100}"
RDF_NREPEAT="${RDF_NREPEAT:-1}"
RDF_NFREQ="${RDF_NFREQ:-100}"

export OMPI_ALLOW_RUN_AS_ROOT="${OMPI_ALLOW_RUN_AS_ROOT:-1}"
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM="${OMPI_ALLOW_RUN_AS_ROOT_CONFIRM:-1}"
export OMPI_MCA_opal_warn_on_missing_libcuda="${OMPI_MCA_opal_warn_on_missing_libcuda:-0}"
export LAMMPS_PLUGIN_PATH="${DEEPMD_PLUGIN_DIR}${LAMMPS_PLUGIN_PATH:+:${LAMMPS_PLUGIN_PATH}}"
export LD_LIBRARY_PATH="${DEEPMD_RUNTIME_PATH}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

mkdir -p "${RUN_DIR}"
if find "${RUN_DIR}" -mindepth 1 ! -name run.out -print -quit | grep -q .; then
  echo "Refusing to overwrite non-empty RUN_DIR: ${RUN_DIR}" >&2
  echo "Set RUN_DIR to a new path, or move/remove existing files intentionally." >&2
  exit 1
fi

cd "${RUN_DIR}"
read -r -a MPI_FLAGS_ARRAY <<< "${MPI_FLAGS}"
exec "${MPI_BIN}" "${MPI_FLAGS_ARRAY[@]}" -np "${NP}" "${LMP_BIN}" \
  -in "${SCRIPT_DIR}/in.liquidwater_nvt_mainline.lmp" \
  -partition "${PARTITION}" \
  -log log.liquidwater_nvt_mainline \
  -var PLUGIN_SO "${PLUGIN_SO}" \
  -var DATA_FILE "${DATA_FILE}" \
  -var MODEL_PATH "${MODEL_PATH}" \
  -var NSTEPS "${NSTEPS}" \
  -var THERMO_FREQ "${THERMO_FREQ}" \
  -var DUMP_FREQ "${DUMP_FREQ}" \
  -var TEMP "${TEMP}" \
  -var TAU_T "${TAU_T}" \
  -var VEL_SEED "${VEL_SEED}" \
  -var RDF_NBINS "${RDF_NBINS}" \
  -var RDF_NEVERY "${RDF_NEVERY}" \
  -var RDF_NREPEAT "${RDF_NREPEAT}" \
  -var RDF_NFREQ "${RDF_NFREQ}"
