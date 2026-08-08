"""教材题 Streamlit 输入层的轻量契约测试。"""

from mechanics.textbook_models import BeamProblem
from ui.textbook_solver_ui import build_problem_from_rows, render_textbook_solver


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


def test_textbook_solver_renderer_is_publicly_available():
    assert callable(render_textbook_solver)
