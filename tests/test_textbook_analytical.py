"""标准静定教材梁解析解的可观察基准。"""

import pytest

from mechanics.analytical_beam import (
    _critical_positions,
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


def test_segments_keep_point_load_shear_jump_at_the_shared_breakpoint():
    result = solve_simply_supported(
        simple_problem(point_loads=[PointLoad(500.0, -1000.0)])
    )

    left_segment, right_segment = result.segments

    assert left_segment.positions_mm[-1] < 500.0
    assert right_segment.positions_mm[0] > 500.0
    assert left_segment.shear_n[-1] == pytest.approx(500.0)
    assert right_segment.shear_n[0] == pytest.approx(-500.0)


def test_multiple_point_loads_and_partial_udls_find_the_internal_maximum_deflection():
    problem = simple_problem(
        point_loads=[PointLoad(310.0, -700.0), PointLoad(760.0, 300.0)],
        distributed_loads=[
            DistributedLoad(360.0, 365.0, -90.0),
            DistributedLoad(650.0, 655.0, 50.0),
        ],
    )

    result = solve_simply_supported(problem)

    assert result.max_deflection_position_mm == pytest.approx(404.8234069)
    assert result.max_deflection_mm == pytest.approx(-0.0608987672)
    assert result.theta_at(result.max_deflection_position_mm) == pytest.approx(0.0)


def test_critical_position_search_finds_all_roots_within_each_breakpoint_span():
    roots = _critical_positions(
        1.0,
        lambda position: (position - 0.1001) * (position - 0.1002),
        [0.0, 0.3, 1.0],
    )

    assert roots == pytest.approx([0.0, 0.1001, 0.1002, 0.3, 1.0])


def test_right_fixed_cantilever_with_internal_loads_is_supported():
    problem = simple_problem(
        supports=[Support(0.0, "free"), Support(1000.0, "fixed")],
        point_loads=[PointLoad(250.0, -200.0), PointLoad(700.0, 100.0)],
        distributed_loads=[
            DistributedLoad(300.0, 450.0, -2.0),
            DistributedLoad(600.0, 800.0, 1.0),
        ],
    )

    result = solve_cantilever(problem)

    assert result.deflection_mm[-1] == pytest.approx(0.0)
    assert result.theta_at(1000.0) == pytest.approx(0.0)
    assert result.checks["sum_vertical_n"] == pytest.approx(0.0, abs=1e-8)
