"""最终审查缺陷的端到端回归测试。"""

from __future__ import annotations

import csv
from dataclasses import asdict, fields
from io import StringIO

import pytest

from mechanics.analytical_beam import solve_simply_supported
from mechanics.beam_fem import solve_fem
from mechanics.textbook_models import (
    BeamProblem,
    BeamSolution,
    DistributedLoad,
    PointLoad,
    Support,
)
from mechanics.textbook_solver import solve_textbook_beam
from ui import textbook_solver_ui
from utils.textbook_export import build_textbook_csv, build_textbook_markdown


def _problem(*loads: PointLoad) -> BeamProblem:
    return BeamProblem(
        length_mm=1000.0,
        elastic_modulus_mpa=200_000.0,
        inertia_mm4=1_000_000.0,
        supports=[Support(0.0, "pin", "A"), Support(1000.0, "roller", "B")],
        point_loads=list(loads),
    )


@pytest.mark.parametrize("solver", [solve_simply_supported, solve_fem])
def test_upward_midspan_load_keeps_positive_maximum_deflection(solver):
    result = solver(_problem(PointLoad(500.0, 1000.0)))

    assert result.max_deflection_mm == pytest.approx(0.1041666667, rel=1e-6)
    assert result.max_deflection_position_mm == pytest.approx(500.0)


@pytest.mark.parametrize("solver", [solve_simply_supported, solve_fem])
def test_mixed_signed_loads_choose_largest_absolute_deflection_and_keep_its_sign(solver):
    result = solver(
        _problem(PointLoad(250.0, 1000.0), PointLoad(750.0, -100.0))
    )

    sampled_largest = max(
        (
            (position, value)
            for segment in result.segments
            for position, value in zip(segment.positions_mm, segment.deflection_mm)
        ),
        key=lambda item: abs(item[1]),
    )
    assert result.max_deflection_mm > 0.0
    assert abs(result.max_deflection_mm) >= abs(sampled_largest[1]) - 1e-9
    assert 0.0 < result.max_deflection_position_mm < 1000.0


_COMMON_SOLUTION_FIELDS = {
    "method",
    "classification",
    "x_mm",
    "deflection_mm",
    "max_deflection_mm",
    "max_deflection_position_mm",
    "reactions",
    "segments",
    "shear_segments",
    "moment_segments",
    "checks",
    "steps",
    "warnings",
    "metadata",
    "node_positions_mm",
    "displacements_mm",
    "rotations_rad",
    "deflection_at",
    "theta_at",
    "shear_at",
    "moment_at",
    "max_shear",
    "max_shear_position",
    "max_moment",
    "max_moment_position",
    "diagram_data",
}


@pytest.mark.parametrize("solver", [solve_simply_supported, solve_fem])
def test_beam_solution_declares_and_serializes_the_complete_public_contract(solver):
    result = solver(_problem(PointLoad(500.0, -1000.0)))

    declared = {item.name for item in fields(BeamSolution)}
    serialized = asdict(result)
    assert _COMMON_SOLUTION_FIELDS <= declared
    assert _COMMON_SOLUTION_FIELDS <= serialized.keys()
    assert result.shear_segments == result.segments
    assert result.moment_segments == result.segments


def test_analytical_and_fem_results_expose_textbook_expressions_extrema_and_diagram_data():
    analytical = solve_textbook_beam(_problem(PointLoad(500.0, -1000.0)))
    fem = solve_fem(_problem(PointLoad(500.0, -1000.0)))

    assert all(segment.shear_expression.startswith("V(x) =") for segment in analytical.segments)
    assert all(segment.moment_expression.startswith("M(x) =") for segment in analytical.segments)
    assert all(segment.shear_expression == "数值采样（FEM）" for segment in fem.segments)
    assert all(segment.moment_expression == "数值采样（FEM）" for segment in fem.segments)
    assert analytical.max_shear == pytest.approx(500.0)
    assert analytical.max_moment == pytest.approx(250_000.0)
    assert analytical.max_moment_position == pytest.approx(500.0)
    assert analytical.diagram_data["beam_length_mm"] == 1000.0
    assert analytical.diagram_data["point_loads"][0]["force_n"] == -1000.0
    assert fem.metadata["mesh"]["element_count"] > 1
    assert fem.metadata["accuracy"]["description"]


def test_markdown_and_ui_expose_textbook_outputs_and_fem_node_details():
    problem = _problem(PointLoad(500.0, -1000.0))
    analytical_report = build_textbook_markdown(problem, solve_textbook_beam(problem))
    fem_report = build_textbook_markdown(problem, solve_fem(problem))

    for expected in ("V(x) =", "M(x) =", "最大剪力", "最大弯矩", "受力简图数据"):
        assert expected in analytical_report
    for expected in ("FEM 节点挠度", "网格说明", "精度说明"):
        assert expected in fem_report

    render_names = textbook_solver_ui.render_textbook_solver.__code__.co_names
    render_constants = "\n".join(
        value
        for value in textbook_solver_ui.render_textbook_solver.__code__.co_consts
        if isinstance(value, str)
    )
    assert "shear_expression" in render_names
    assert "moment_expression" in render_names
    assert "max_shear" in render_names
    assert "diagram_data" in render_names
    assert "FEM 节点挠度" in render_constants


@pytest.mark.parametrize(
    ("solver", "expected_method"),
    [(solve_simply_supported, "analytical"), (solve_fem, "fem")],
)
def test_direct_solvers_populate_classification_for_reports(solver, expected_method):
    problem = _problem(PointLoad(500.0, -1000.0))
    result = solver(problem)

    assert result.classification.category == "静定"
    assert result.classification.method == expected_method
    assert "静定性：未知" not in build_textbook_markdown(problem, result)


@pytest.mark.parametrize(
    "solver",
    [solve_simply_supported, lambda problem: solve_fem(problem, max_elements=2)],
)
def test_resultant_extrema_use_one_sided_endpoints_and_internal_shear_zero(solver):
    problem = _problem()
    problem.distributed_loads = [DistributedLoad(500.0, 1000.0, -1.0)]

    result = solver(problem)

    assert result.max_shear == pytest.approx(-375.0, abs=1e-6)
    assert result.max_shear_position == pytest.approx(1000.0)
    assert result.max_moment == pytest.approx(70_312.5, abs=1e-6)
    assert result.max_moment_position == pytest.approx(625.0, abs=1e-9)


def test_fem_moment_extrema_keep_one_sided_internal_support_endpoints():
    problem = _problem(PointLoad(250.0, -1000.0))
    problem.supports = [
        Support(0.0, "pin", "A"),
        Support(500.0, "fixed", "B"),
        Support(1000.0, "roller", "C"),
    ]

    result = solve_fem(problem, max_elements=4)

    assert result.max_moment == pytest.approx(-93_750.0, abs=1e-6)
    assert result.max_moment_position == pytest.approx(500.0)


def test_csv_uses_separate_curve_and_reaction_rows_with_complete_fields():
    solution = solve_textbook_beam(
        _problem(PointLoad(0.0, -1000.0))
    )
    csv_text = build_textbook_csv(solution)
    reader = csv.DictReader(StringIO(csv_text))
    rows = list(reader)

    assert reader.fieldnames[:3] == ["x_mm", "deflection_mm", "reaction_vertical_n"]
    assert {
        "row_type",
        "shear_n",
        "moment_n",
        "rotation_rad",
        "reaction_moment_n",
        "method",
        "classification",
        "check_sum_vertical_n",
    } <= set(reader.fieldnames)
    curve_rows = [row for row in rows if row["row_type"] == "curve"]
    reaction_rows = [row for row in rows if row["row_type"] == "reaction"]
    assert curve_rows and all(row["reaction_vertical_n"] == "" for row in curve_rows)
    assert all(row["shear_n"] != "" and row["moment_n"] != "" for row in curve_rows)
    assert len(reaction_rows) == 2
    left_reaction = next(row for row in reaction_rows if float(row["x_mm"]) == 0.0)
    assert left_reaction["reaction_vertical_n"] == "1000.0"
    assert left_reaction["method"] == "analytical"
    assert left_reaction["classification"] == "静定"
