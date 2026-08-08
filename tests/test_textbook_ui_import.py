"""教材题 Streamlit 输入层的契约测试。"""

import pytest

from mechanics.textbook_models import BeamProblem, ProblemInputError
from ui import textbook_solver_ui

build_problem_from_rows = textbook_solver_ui.build_problem_from_rows


def test_build_problem_from_editor_rows_uses_textbook_dataclasses():
    problem = build_problem_from_rows(
        length_mm=1000.0,
        elastic_modulus_mpa=200_000.0,
        inertia_mm4=1_000_000.0,
        support_rows=[
            {"position_mm": 0.0, "kind": "pin", "label": "A"},
            {"position_mm": 1000.0, "kind": "roller", "label": "B"},
        ],
        point_load_rows=[{"position_mm": 500.0, "force_n": -1000.0}],
        distributed_load_rows=[
            {"start_mm": 100.0, "end_mm": 300.0, "intensity_n_per_mm": -2.0}
        ],
    )

    assert isinstance(problem, BeamProblem)
    assert problem.supports[0].kind == "pin"
    assert problem.point_loads[0].force_n == -1000.0
    assert problem.distributed_loads[0].end_mm == 300.0


def test_template_discards_cached_solution_and_problem():
    cached_solution = object()
    cached_problem = object()
    state = {
        "textbook_solution": cached_solution,
        "textbook_problem": cached_problem,
        "textbook_support_editor": "stale editor",
    }

    textbook_solver_ui.apply_simply_supported_template(state)

    assert "textbook_solution" not in state
    assert "textbook_problem" not in state
    assert state["textbook_support_rows"] == [
        {"position_mm": 0.0, "kind": "pin", "label": "A"},
        {"position_mm": 1000.0, "kind": "roller", "label": "B"},
    ]
    assert "textbook_support_editor" not in state


def test_cantilever_template_discards_cached_solution_and_problem():
    state = {
        "textbook_solution": object(),
        "textbook_problem": object(),
    }

    textbook_solver_ui.apply_cantilever_template(state)

    assert "textbook_solution" not in state
    assert "textbook_problem" not in state
    assert state["textbook_support_rows"] == [
        {"position_mm": 0.0, "kind": "fixed", "label": "A"},
        {"position_mm": 1000.0, "kind": "free", "label": "自由端"},
    ]


def test_clear_input_resets_defaults_and_discards_cached_results():
    state = {
        "textbook_length_mm": 2500.0,
        "textbook_modulus_mpa": 70_000.0,
        "textbook_inertia_mm4": 3_000_000.0,
        "textbook_support_rows": [{"position_mm": 10.0, "kind": "fixed", "label": "X"}],
        "textbook_point_load_rows": [{"position_mm": 10.0, "force_n": -5.0}],
        "textbook_distributed_load_rows": [
            {"start_mm": 0.0, "end_mm": 10.0, "intensity_n_per_mm": -1.0}
        ],
        "textbook_support_editor": "stale support editor",
        "textbook_point_load_editor": "stale point-load editor",
        "textbook_distributed_load_editor": "stale distributed-load editor",
        "textbook_solution": object(),
        "textbook_problem": object(),
    }

    textbook_solver_ui.apply_clear_input(state)

    assert state["textbook_length_mm"] == 1000.0
    assert state["textbook_modulus_mpa"] == 200_000.0
    assert state["textbook_inertia_mm4"] == 1_000_000.0
    assert state["textbook_support_rows"] == []
    assert state["textbook_point_load_rows"] == []
    assert state["textbook_distributed_load_rows"] == []
    assert "textbook_support_editor" not in state
    assert "textbook_point_load_editor" not in state
    assert "textbook_distributed_load_editor" not in state
    assert "textbook_solution" not in state
    assert "textbook_problem" not in state


def test_conversion_failure_keeps_cached_solution_and_problem():
    cached_solution = object()
    cached_problem = object()
    state = {
        "textbook_solution": cached_solution,
        "textbook_problem": cached_problem,
    }

    with pytest.raises(ProblemInputError):
        textbook_solver_ui.submit_textbook_problem(
            state,
            length_mm="not a number",
            elastic_modulus_mpa=200_000.0,
            inertia_mm4=1_000_000.0,
            support_rows=[],
            point_load_rows=[],
            distributed_load_rows=[],
        )

    assert state["textbook_solution"] is cached_solution
    assert state["textbook_problem"] is cached_problem


def test_styled_entrypoint_imports_textbook_solver_mode():
    import app_styled

    assert app_styled.render_textbook_solver.__module__ == "ui.textbook_solver_ui"
