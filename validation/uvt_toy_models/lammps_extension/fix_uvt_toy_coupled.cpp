/* ----------------------------------------------------------------------
   LAMMPS - Large-scale Atomic/Molecular Massively Parallel Simulator
   https://www.lammps.org/, Sandia National Laboratories
   LAMMPS development team: developers@lammps.org

   Copyright (2003) Sandia Corporation.  Under the terms of Contract
   DE-AC04-94AL85000 with Sandia Corporation, the U.S. Government retains
   certain rights in this software.  This software is distributed under
   the GNU General Public License.

   See the README file in the top-level LAMMPS directory.
------------------------------------------------------------------------- */

#include "fix_uvt_toy_coupled.h"

#include "atom.h"
#include "error.h"
#include "memory.h"
#include "modify.h"
#include "respa.h"
#include "update.h"

#include <cstring>

using namespace LAMMPS_NS;
using namespace FixConst;

/* ---------------------------------------------------------------------- */

FixUVTToyCoupled::FixUVTToyCoupled(LAMMPS *lmp, int narg, char **arg) :
    Fix(lmp, narg, arg), uvt_id(nullptr), uvt_fix(nullptr), ne(nullptr), nlevels_respa(0),
    kx(1.0), ke(1.0), g(0.0), n0(0.0), energy(0.0), x_current(0.0), ne_current(0.0),
    dedn_current(0.0), force_current(0.0)
{
  if (narg < 12) utils::missing_cmd_args(FLERR, "fix uvt/toy/coupled", error);

  scalar_flag = 1;
  vector_flag = 1;
  size_vector = 5;
  global_freq = 1;
  extscalar = 1;
  extvector = 1;

  int iarg = 3;
  uvt_id = utils::strdup(arg[iarg++]);

  while (iarg < narg) {
    if (strcmp(arg[iarg], "kx") == 0) {
      if (iarg + 2 > narg) utils::missing_cmd_args(FLERR, "fix uvt/toy/coupled kx", error);
      kx = utils::numeric(FLERR, arg[iarg + 1], false, lmp);
      iarg += 2;
    } else if (strcmp(arg[iarg], "ke") == 0) {
      if (iarg + 2 > narg) utils::missing_cmd_args(FLERR, "fix uvt/toy/coupled ke", error);
      ke = utils::numeric(FLERR, arg[iarg + 1], false, lmp);
      iarg += 2;
    } else if (strcmp(arg[iarg], "g") == 0) {
      if (iarg + 2 > narg) utils::missing_cmd_args(FLERR, "fix uvt/toy/coupled g", error);
      g = utils::numeric(FLERR, arg[iarg + 1], false, lmp);
      iarg += 2;
    } else if (strcmp(arg[iarg], "n0") == 0) {
      if (iarg + 2 > narg) utils::missing_cmd_args(FLERR, "fix uvt/toy/coupled n0", error);
      n0 = utils::numeric(FLERR, arg[iarg + 1], false, lmp);
      iarg += 2;
    } else {
      error->all(FLERR, "Unknown fix uvt/toy/coupled keyword: {}", arg[iarg]);
    }
  }
}

/* ---------------------------------------------------------------------- */

FixUVTToyCoupled::~FixUVTToyCoupled()
{
  delete[] uvt_id;
}

/* ---------------------------------------------------------------------- */

int FixUVTToyCoupled::setmask()
{
  int mask = 0;
  mask |= POST_FORCE;
  mask |= POST_FORCE_RESPA;
  mask |= MIN_POST_FORCE;
  return mask;
}

/* ---------------------------------------------------------------------- */

void FixUVTToyCoupled::init()
{
  uvt_fix = modify->get_fix_by_id(uvt_id);
  if (!uvt_fix) error->all(FLERR, "Fix uvt/toy/coupled could not find fix {}", uvt_id);

  int dim = -1;
  ne = static_cast<double *>(uvt_fix->extract("ne", dim));
  if (!ne || (dim != 0 && dim != 1))
    error->all(FLERR, "Fix uvt/toy/coupled requires fix {} to expose scalar ne", uvt_id);

  if (utils::strmatch(update->integrate_style, "^respa")) {
    nlevels_respa = ((Respa *) update->integrate)->nlevels;
    ((Respa *) update->integrate)->copy_flevel_f(nlevels_respa - 1);
  }
}

/* ---------------------------------------------------------------------- */

void FixUVTToyCoupled::setup(int vflag)
{
  post_force(vflag);
}

/* ---------------------------------------------------------------------- */

void FixUVTToyCoupled::min_setup(int vflag)
{
  post_force(vflag);
}

/* ---------------------------------------------------------------------- */

void FixUVTToyCoupled::post_force(int /*vflag*/)
{
  refresh_state();
  apply_force();
}

/* ---------------------------------------------------------------------- */

void FixUVTToyCoupled::post_force_respa(int vflag, int ilevel, int /*iloop*/)
{
  if (ilevel == nlevels_respa - 1) post_force(vflag);
}

/* ---------------------------------------------------------------------- */

void FixUVTToyCoupled::min_post_force(int vflag)
{
  post_force(vflag);
}

/* ---------------------------------------------------------------------- */

double FixUVTToyCoupled::compute_scalar()
{
  refresh_state();
  return dedn_current;
}

/* ---------------------------------------------------------------------- */

double FixUVTToyCoupled::compute_vector(int n)
{
  refresh_state();
  if (n == 0) return energy;
  if (n == 1) return ne_current;
  if (n == 2) return x_current;
  if (n == 3) return dedn_current;
  if (n == 4) return force_current;
  return 0.0;
}

/* ---------------------------------------------------------------------- */

void *FixUVTToyCoupled::extract(const char *str, int &dim)
{
  refresh_state();
  dim = 0;
  if (strcmp(str, "energy") == 0) return &energy;
  if (strcmp(str, "dedn") == 0) return &dedn_current;
  if (strcmp(str, "force") == 0) return &force_current;
  if (strcmp(str, "x") == 0) return &x_current;
  return nullptr;
}

/* ---------------------------------------------------------------------- */

void FixUVTToyCoupled::refresh_state()
{
  ne_current = ne ? *ne : 0.0;
  x_current = 0.0;

  double count = 0.0;
  double **x = atom->x;
  int *mask = atom->mask;
  int nlocal = atom->nlocal;

  for (int i = 0; i < nlocal; i++) {
    if (mask[i] & groupbit) {
      x_current += x[i][0];
      count += 1.0;
    }
  }

  double values[2] = {x_current, count};
  double totals[2] = {0.0, 0.0};
  MPI_Allreduce(values, totals, 2, MPI_DOUBLE, MPI_SUM, world);
  x_current = (totals[1] > 0.0) ? totals[0] / totals[1] : 0.0;

  const double dne = ne_current - n0;
  energy = 0.5 * kx * x_current * x_current + 0.5 * ke * dne * dne + g * x_current * ne_current;
  dedn_current = ke * dne + g * x_current;
  force_current = -kx * x_current - g * ne_current;
}

/* ---------------------------------------------------------------------- */

void FixUVTToyCoupled::apply_force()
{
  double **f = atom->f;
  int *mask = atom->mask;
  int nlocal = atom->nlocal;

  double count = 0.0;
  for (int i = 0; i < nlocal; i++)
    if (mask[i] & groupbit) count += 1.0;

  double total_count = 0.0;
  MPI_Allreduce(&count, &total_count, 1, MPI_DOUBLE, MPI_SUM, world);
  if (total_count <= 0.0) return;

  const double per_atom_force = force_current / total_count;
  for (int i = 0; i < nlocal; i++)
    if (mask[i] & groupbit) f[i][0] += per_atom_force;
}
