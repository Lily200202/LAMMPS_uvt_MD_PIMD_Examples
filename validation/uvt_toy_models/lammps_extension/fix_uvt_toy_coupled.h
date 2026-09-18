/* -*- c++ -*- ----------------------------------------------------------
   LAMMPS - Large-scale Atomic/Molecular Massively Parallel Simulator
   https://www.lammps.org/, Sandia National Laboratories
   LAMMPS development team: developers@lammps.org

   Copyright (2003) Sandia Corporation.  Under the terms of Contract
   DE-AC04-94AL85000 with Sandia Corporation, the U.S. Government retains
   certain rights in this software.  This software is distributed under
   the GNU General Public License.

   See the README file in the top-level LAMMPS directory.
------------------------------------------------------------------------- */

#ifdef FIX_CLASS
// clang-format off
FixStyle(uvt/toy/coupled,FixUVTToyCoupled);
// clang-format on
#else

#ifndef LMP_FIX_UVT_TOY_COUPLED_H
#define LMP_FIX_UVT_TOY_COUPLED_H

#include "fix.h"

namespace LAMMPS_NS {

class FixUVTToyCoupled : public Fix {
 public:
  FixUVTToyCoupled(class LAMMPS *, int, char **);
  ~FixUVTToyCoupled() override;

  int setmask() override;
  void init() override;
  void setup(int) override;
  void min_setup(int) override;
  void post_force(int) override;
  void post_force_respa(int, int, int) override;
  void min_post_force(int) override;
  double compute_scalar() override;
  double compute_vector(int) override;
  void *extract(const char *, int &) override;

 private:
  char *uvt_id;
  class Fix *uvt_fix;
  double *ne;
  int nlevels_respa;
  double kx, ke, g, n0;
  double energy;
  double x_current;
  double ne_current;
  double dedn_current;
  double force_current;

  void refresh_state();
  void apply_force();
};

}    // namespace LAMMPS_NS

#endif
#endif
