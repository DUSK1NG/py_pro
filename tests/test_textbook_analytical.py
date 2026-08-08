"""标准静定教材梁解析解的可观察基准。"""

import pytest

from mechanics.analytical_beam import (
    solve_cantilever,
    solve_simply_supported,
    supports_analytical,
)
from mechanics.textbook_models import (
    BeamProblem,
    DistributedLoad,
    PointLoad,
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


def test_midspan_point_load_has_balanced_reactions_and_textbook_deflection():
    problem = simple_problem(point_loads=[PointLoad(500.0, -1000.0)])

    result = solve_simply_supported(problem)

    assert [reaction.vertical_n for reaction in result.reactions] == pytest.approx(
        [500.0, 500.0]
    )
    assert result.max_deflection_mm == pytest.approx(
        -1000.0 * 1000.0**3 / (48.0 * 200_000.0 * 1_000_000.0)
    )
    assert result.max_deflection_position_mm == pytest.approx(500.0)
    assert result.deflection_mm[0] == pytest.approx(0.0)
    assert result.deflection_mm[-1] == pytest.approx(0.0)


def test_partial_udl_uses_resultant_centroid_and_includes_load_boundaries():
    problem = simple_problem(distributed_loads=[DistributedLoad(200.0, 800.0, -2.0)])

    result = solve_simply_supported(problem)

    assert sum(reaction.vertical_n for reaction in result.reactions) == pytest.approx(1200.0)
    assert result.checks["sum_vertical_n"] == pytest.approx(0.0, abs=1e-8)
    assert result.checks["sum_moment_about_0_n_mm"] == pytest.approx(0.0, abs=1e-8)
    assert {200.0, 800.0}.issubset(
        {position for segment in result.segments for position in segment.positions_mm}
    )


def test_cantilever_tip_force_has_fixed_reaction_moment_and_boundary_conditions():
    problem = BeamProblem(
        1000.0,
        200_000.0,
        1_000_000.0,
        [Support(0.0, "fixed"), Support(1000.0, "free")],
        [PointLoad(1000.0, -100.0)],
        [],
    )

    result = solve_cantilever(problem)

    assert result.reactions[0].vertical_n == pytest.approx(100.0)
    assert result.reactions[0].moment_n_mm == pytest.approx(100_000.0)
    assert result.deflection_mm[0] == pytest.approx(0.0)
    assert result.theta_at(0.0) == pytest.approx(0.0)
    assert result.max_deflection_mm == pytest.approx(-100.0 * 1000.0**3 / (3.0 * 200_000.0 * 1_000_000.0))


def test_point_load_creates_shear_jump_and_udl_changes_moment_by_integral():
    problem = simple_problem(
        point_loads=[PointLoad(500.0, -1000.0)],
        distributed_loads=[DistributedLoad(600.0, 800.0, -2.0)],
    )

    result = solve_simply_supported(problem)

    assert result.shear_at(500.001) - result.shear_at(499.999) == pytest.approx(-1000.0)
    assert result.moment_at(700.0) - result.moment_at(600.0) == pytest.approx(
        -48_000.0,
        abs=1e-8,
    )


def test_only_canonical_support_arrangements_are_analytical():
    assert supports_analytical(simple_problem())
    assert supports_analytical(
        simple_problem(supports=[Support(0.0, "fixed"), Support(1000.0, "free")])
    )
    assert not supports_analytical(
        simple_problem(supports=[Support(0.0, "pin"), Support(1000.0, "pin")])
    )
