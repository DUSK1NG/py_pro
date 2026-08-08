"""公共教材梁题入口的分流和结果契约。"""

from dataclasses import asdict, fields

import pytest

from mechanics.textbook_models import (
    BeamProblem,
    DistributedLoad,
    PointLoad,
    ProblemInputError,
    Support,
)
from mechanics.textbook_solver import (
    ProblemClassification,
    classify_problem,
    solve_textbook_beam,
)


def beam_problem(**changes):
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


def test_canonical_simple_support_uses_analytical_branch_and_normalized_contract():
    result = solve_textbook_beam(
        beam_problem(point_loads=[PointLoad(500.0, -1000.0)])
    )

    assert result.method == "analytical"
    assert result.classification == ProblemClassification("静定", "analytical")
    assert result.max_deflection_mm < 0.0
    assert set(asdict(result)) == {item.name for item in fields(type(result))}
    for field in (
        "reactions",
        "shear_segments",
        "moment_segments",
        "x_mm",
        "deflection_mm",
        "max_deflection_mm",
        "max_deflection_position_mm",
        "checks",
        "steps",
        "warnings",
        "metadata",
    ):
        assert hasattr(result, field)
    assert result.shear_segments is result.segments
    assert result.moment_segments is result.segments


def test_end_fixed_cantilever_uses_analytical_branch():
    result = solve_textbook_beam(
        beam_problem(
            supports=[Support(0.0, "fixed"), Support(1000.0, "free")],
            point_loads=[PointLoad(1000.0, -100.0)],
        )
    )

    assert result.method == "analytical"
    assert result.classification == ProblemClassification("静定", "analytical")


def test_two_point_loads_superpose_through_the_common_entrypoint():
    result = solve_textbook_beam(
        beam_problem(
            point_loads=[PointLoad(250.0, -400.0), PointLoad(750.0, -600.0)]
        )
    )

    assert [reaction.vertical_n for reaction in result.reactions] == pytest.approx(
        [450.0, 550.0]
    )
    assert result.checks["sum_vertical_n"] == pytest.approx(0.0)


def test_two_distributed_loads_superpose_through_the_common_entrypoint():
    result = solve_textbook_beam(
        beam_problem(
            distributed_loads=[
                DistributedLoad(0.0, 500.0, -2.0),
                DistributedLoad(500.0, 1000.0, -4.0),
            ]
        )
    )

    assert [reaction.vertical_n for reaction in result.reactions] == pytest.approx(
        [1250.0, 1750.0]
    )
    assert result.checks["sum_moment_about_0_n_mm"] == pytest.approx(0.0)


@pytest.mark.parametrize(
    "supports",
    [
        [Support(0.0, "roller"), Support(1000.0, "pin")],
        [Support(200.0, "pin"), Support(800.0, "roller")],
    ],
)
def test_noncanonical_two_support_layouts_are_dispatched_to_fem(supports):
    result = solve_textbook_beam(
        beam_problem(
            supports=supports,
            point_loads=[PointLoad(500.0, -1000.0)],
        )
    )

    assert result.method == "fem"
    assert result.classification == ProblemClassification("静定", "fem")


def test_three_supports_are_indeterminate_and_return_the_complete_common_contract():
    problem = beam_problem(
        supports=[Support(0.0, "pin"), Support(500.0, "roller"), Support(1000.0, "roller")],
        point_loads=[PointLoad(250.0, -1000.0)],
    )

    classification = classify_problem(problem)
    result = solve_textbook_beam(problem)

    assert classification == ProblemClassification("超静定（数值解）", "fem")
    assert result.method == "fem"
    assert result.classification == classification
    for field in (
        "method",
        "classification",
        "shear_segments",
        "moment_segments",
        "metadata",
        "x_mm",
        "deflection_mm",
        "checks",
    ):
        assert hasattr(result, field)
    assert result.shear_segments is result.segments
    assert result.moment_segments is result.segments
    assert len(result.x_mm) == len(result.deflection_mm) > 1
    assert result.metadata["method"] == "fem"
    assert result.metadata["classification"] == "超静定（数值解）"
    assert result.checks


def test_mechanism_is_classified_and_rejected_with_a_readable_input_error():
    problem = beam_problem(supports=[Support(500.0, "free")])

    assert classify_problem(problem) == ProblemClassification("机构/约束不足", "fem")
    with pytest.raises(ProblemInputError, match="机构或约束不足"):
        solve_textbook_beam(problem)


def test_invalid_input_is_validated_before_classification():
    problem = beam_problem(supports=[])

    with pytest.raises(ProblemInputError, match="至少需要一个支座"):
        classify_problem(problem)
