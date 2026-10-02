# Task 3 FEM delivery report

## Scope

Implemented `solve_fem(problem: BeamProblem, max_elements: int = 200)` in
`mechanics/beam_fem.py` for one-dimensional Euler--Bernoulli beams (mm, N,
MPa, mm^4).  The solver:

- builds a mesh that retains beam ends, supports, point loads, and distributed
  load boundaries exactly, while allocating the remaining elements up to the
  requested limit;
- assembles two-node `[v, theta]` beam elements with the standard
  `E * I / L_e^3` stiffness matrix and consistent uniform-load nodal vector;
- applies pin, roller, fixed, and free boundary conditions, solves the reduced
  system with `numpy.linalg.solve`, and reports a clear `ProblemInputError` for
  rank-deficient mechanisms;
- recovers reactions from `K @ u - F`, and returns nodal values, sampled
  deflections, section-resultant accessors, metadata, equilibrium checks,
  warnings, and method steps.

## Root cause and fix

The reduced stiffness matrix for a
mechanism could be numerically ill-conditioned without causing
`numpy.linalg.solve` to raise.  `_solve_reduced_system` now checks its matrix
rank before solving and converts rank deficiency to the required input error.

The equilibrium checks summed FEM reaction round-off directly, producing a
tiny residual (`-5.476176738739014e-07 N`) for an otherwise balanced partial
UDL case.  They now use `math.fsum` and normalize only scale-relative solver
round-off (`<= 1e-9` of the resultant scale) to zero; physically meaningful
imbalance remains visible.
