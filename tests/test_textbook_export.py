"""教材题报告与曲线导出的行为测试。"""

import csv
import inspect
from io import StringIO
from pathlib import Path

from mechanics.textbook_models import BeamProblem, PointLoad, Support
from mechanics.textbook_solver import solve_textbook_beam
from utils.export import build_textbook_csv as public_build_textbook_csv
from utils.report import build_textbook_pdf_report
from utils.textbook_export import build_textbook_csv, build_textbook_markdown
from vision.report_ui import render_report_exports


def _solved_problem():
    problem = BeamProblem(
        length_mm=1000.0,
        elastic_modulus_mpa=200_000.0,
        inertia_mm4=1_000_000.0,
        supports=[Support(0.0, "pin", "A"), Support(1000.0, "roller", "B")],
        point_loads=[PointLoad(500.0, -1000.0)],
    )
    return problem, solve_textbook_beam(problem)


def test_textbook_markdown_includes_required_solution_sections():
    problem, solution = _solved_problem()

    report = build_textbook_markdown(problem, solution)

    for heading in (
        "输入摘要",
        "求解方法与静定性",
        "支座反力",
        "平衡校核",
        "剪力/弯矩分段",
        "挠度曲线摘要",
        "解题步骤",
        "warnings",
    ):
        assert heading in report
    assert "1000 mm" in report
    assert "analytical" in report
    assert "500.000" in report


def test_textbook_csv_has_stable_curve_header_and_blank_non_reaction_rows():
    problem, solution = _solved_problem()

    rows = list(csv.DictReader(StringIO(build_textbook_csv(solution))))

    assert rows[0].keys() == {"x_mm", "deflection_mm", "reaction_vertical_n"}
    assert any(row["reaction_vertical_n"] == "" for row in rows)
    assert next(row for row in rows if float(row["x_mm"]) == 0.0)["reaction_vertical_n"] == "500.0"
    assert next(row for row in rows if float(row["x_mm"]) == 1000.0)["reaction_vertical_n"] == "500.0"


def test_textbook_csv_is_available_from_the_export_module():
    _, solution = _solved_problem()

    assert public_build_textbook_csv(solution).startswith("x_mm,deflection_mm,reaction_vertical_n\n")


def test_textbook_pdf_report_returns_pdf_bytes():
    problem, solution = _solved_problem()

    report = build_textbook_pdf_report(problem, solution)

    assert report.startswith(b"%PDF")
    assert len(report) > 500


def test_report_export_ui_accepts_cached_textbook_result():
    parameters = inspect.signature(render_report_exports).parameters

    assert "textbook_problem" in parameters
    assert "textbook_solution" in parameters


def test_styled_app_passes_cached_textbook_result_to_report_exports():
    source = Path("app_styled.py").read_text(encoding="utf-8")

    assert "textbook_problem=st.session_state.get(\"textbook_problem\")" in source
    assert "textbook_solution=st.session_state.get(\"textbook_solution\")" in source
