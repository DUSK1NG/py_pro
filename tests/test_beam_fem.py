"""Euler–Bernoulli 梁有限元求解器的行为测试。"""

import pytest

from mechanics.beam_fem import solve_fem
from mechanics.textbook_models import (
    BeamProblem,
    DistributedLoad,
    PointLoad,
    ProblemInputError,
    Support,
)


def simple_problem(**changes):
    values = {
        "length_mm": 1000.0,
        "elastic_modulus_mpa": 200_000.0,
        "inertia_mm4": 1_000_000.0,
        "supports": [Support(0.0, "pin"), Support(1000.0, "roller")],
        "point_loads": [],
        "distributed_loads": [],
    }
    values.update(changes)
    return BeamProblem(**values)


def test_fem_matches_simple_support_midspan_point_load():
    result = solve_fem(
        simple_problem(point_loads=[PointLoad(500.0, -1000.0)]), max_elements=40
    )

    assert result.max_deflection_mm == pytest.approx(
        -1000.0 * 1000.0**3 / (48.0 * 200_000.0 * 1_000_000.0), rel=1e-3
    )
    assert [reaction.vertical_n for reaction in result.reactions] == pytest.approx(
        [500.0, 500.0]
    )


def test_fem_matches_cantilever_tip_load():
    result = solve_fem(
        simple_problem(
            supports=[Support(0.0, "fixed"), Support(1000.0, "free")],
            point_loads=[PointLoad(1000.0, -100.0)],
        )
    )

    assert result.max_deflection_mm == pytest.approx(
        -100.0 * 1000.0**3 / (3.0 * 200_000.0 * 1_000_000.0), rel=1e-3
    )
    assert result.reactions[0].vertical_n == pytest.approx(100.0)
    assert result.reactions[0].moment_n_mm == pytest.approx(100_000.0)


def test_fem_inserts_exact_nodes_for_load_and_support_boundaries():
    result = solve_fem(
        simple_problem(
            supports=[Support(0.0, "pin"), Support(730.0, "roller")],
            point_loads=[PointLoad(175.0, -50.0)],
            distributed_loads=[DistributedLoad(310.0, 620.0, -1.0)],
        )
    )

    assert {0.0, 175.0, 310.0, 620.0, 730.0, 1000.0}.issubset(
        result.node_positions_mm
    )


def test_fem_partial_udl_preserves_global_equilibrium():
    result = solve_fem(
        simple_problem(distributed_loads=[DistributedLoad(200.0, 800.0, -2.0)])
    )

    assert sum(reaction.vertical_n for reaction in result.reactions) == pytest.approx(1200.0)
    assert result.checks["sum_vertical_n"] == pytest.approx(0.0, abs=1e-8)
    assert result.checks["sum_moment_about_0_n_mm"] == pytest.approx(0.0, abs=1e-8)


def test_fem_rejects_mechanism_with_clear_input_error():
    problem = simple_problem(
        supports=[Support(500.0, "free")], point_loads=[PointLoad(500.0, -100.0)]
    )

    with pytest.raises(ProblemInputError, match="机构或约束不足，刚度矩阵不可解"):
        solve_fem(problem)


def test_fem_rejects_a_fully_free_beam_as_a_mechanism():
    problem = simple_problem(supports=[Support(0.0, "free")])

    with pytest.raises(ProblemInputError):
        solve_fem(problem)


def test_fem_section_resultants_vary_quadratically_within_uniform_load():
    result = solve_fem(
        simple_problem(distributed_loads=[DistributedLoad(600.0, 800.0, -2.0)])
    )

    shear_650 = result.shear_at(650.0)
    shear_750 = result.shear_at(750.0)
    assert shear_750 - shear_650 == pytest.approx(-200.0)
    assert (
        result.moment_at(750.0)
        - 2.0 * result.moment_at(700.0)
        + result.moment_at(650.0)
    ) / 50.0**2 == pytest.approx(-2.0)


def test_fem_segments_preserve_both_shear_limits_at_a_point_load_node():
    result = solve_fem(
        simple_problem(point_loads=[PointLoad(500.0, -1000.0)]), max_elements=2
    )
    left, right = result.segments

    assert left.positions_mm[-1] < 500.0
    assert right.positions_mm[0] > 500.0
    assert left.shear_n[-1] != pytest.approx(right.shear_n[0])


def test_fem_solves_extreme_dimensioned_cantilever_without_false_mechanism():
    result = solve_fem(
        simple_problem(
            length_mm=1e9,
            elastic_modulus_mpa=1.0,
            inertia_mm4=1.0,
            supports=[Support(0.0, "fixed"), Support(1e9, "free")],
            point_loads=[PointLoad(1e9, -1.0)],
        )
    )

    assert result.reactions[0].vertical_n == pytest.approx(1.0)
