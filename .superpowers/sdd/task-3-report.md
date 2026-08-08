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

Two focused tests initially failed.  The reduced stiffness matrix for a
mechanism could be numerically ill-conditioned without causing
`numpy.linalg.solve` to raise.  `_solve_reduced_system` now checks its matrix
rank before solving and converts rank deficiency to the required input error.

The equilibrium checks summed FEM reaction round-off directly, producing a
tiny residual (`-5.476176738739014e-07 N`) for an otherwise balanced partial
UDL case.  They now use `math.fsum` and normalize only scale-relative solver
round-off (`<= 1e-9` of the resultant scale) to zero; physically meaningful
imbalance remains visible.

## TDD record

Added `test_fem_rejects_a_fully_free_beam_as_a_mechanism` before the
mechanism fix.  Its first focused run failed as expected because `solve_fem`
returned a solution instead of raising `ProblemInputError`.

Initial focused result:

```text
3 failed, 3 passed
```

After the minimal fixes:

```text
python -m pytest tests/test_beam_fem.py -q
6 passed in 0.50s
```

## Verification

```text
python -m pytest -q
103 passed in 2.24s
```

## Repair TDD record

The following regressions were written before changing `beam_fem.py`.

### Uniform-load section resultants

`test_fem_section_resultants_vary_quadratically_within_uniform_load` was run
as part of the focused RED command:

```text
python -m pytest tests/test_beam_fem.py -q
3 failed, 6 passed
```

It failed because the shear difference from 650 mm to 750 mm was
`-195.12195056676865 N`, rather than the required `-200 N`; the former
recovery used only the cubic displacement field and therefore omitted the
uniform-load particular solution.  The repair adds the local uniform-load
terms to recovered shear and bending moment.  GREEN command:

```text
python -m pytest tests/test_beam_fem.py -q
9 passed in 0.81s
```

Final suite verification after all three repairs:

```text
python -m pytest -q
106 passed in 1.87s
```

### Point-load node limits in segments

`test_fem_segments_preserve_both_shear_limits_at_a_point_load_node` was run
in the same RED command above.  It failed because the last left position was
exactly `500.0`, so both adjoining segments queried the right-side value.
The repair queries the left endpoint with `nextafter(end, start)` and the
right endpoint with `nextafter(start, end)`.  GREEN command:

```text
python -m pytest tests/test_beam_fem.py -q
9 passed in 0.81s
```

### Extreme-dimension mechanism detection

`test_fem_solves_extreme_dimensioned_cantilever_without_false_mechanism` was
run in the same RED command above.  It failed with
`ProblemInputError: 机构或约束不足，刚度矩阵不可解`; the unscaled numerical rank
test treated translational stiffness as zero relative to rotational entries.
The repair first uses the original solve path where it is full rank, and only
when that rank test fails, rescales rotational degrees of freedom by the beam
length before rechecking rank and solving.  GREEN command:

```text
python -m pytest tests/test_beam_fem.py -q
9 passed in 0.81s
```
