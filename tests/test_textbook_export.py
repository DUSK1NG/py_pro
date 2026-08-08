"""教材题报告与曲线导出的行为测试。"""

import csv
import inspect
from io import StringIO
from pathlib import Path

import reportlab.platypus
import pytest

from mechanics.textbook_models import BeamProblem, PointLoad, ProblemInputError, Support
from mechanics.textbook_solver import solve_textbook_beam
from ui import textbook_solver_ui
from utils.export import build_textbook_csv as public_build_textbook_csv
from utils.report import build_textbook_pdf_report
from utils.textbook_export import build_textbook_csv, build_textbook_markdown
from vision import report_ui
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


def test_textbook_markdown_includes_shear_and_moment_values_for_each_segment():
    problem, solution = _solved_problem()

    report = build_textbook_markdown(problem, solution)

    segment = solution.segments[0]
    assert f"{segment.start_mm:.3f}–{segment.end_mm:.3f} mm" in report
    assert f"剪力：{segment.shear_n[0]:.3f} N → {segment.shear_n[-1]:.3f} N" in report
    assert (
        f"弯矩：{segment.bending_moment_n_mm[0]:.3f} N·mm"
        f" → {segment.bending_moment_n_mm[-1]:.3f} N·mm"
    ) in report


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


def test_textbook_pdf_builds_story_with_input_method_reactions_steps_and_curve_summary(
    monkeypatch,
):
    problem, solution = _solved_problem()
    paragraph_text = []

    class CapturingParagraph:
        def __init__(self, text, style):
            paragraph_text.append(text)

    class CapturingDocument:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, story):
            pass

    monkeypatch.setattr(reportlab.platypus, "Paragraph", CapturingParagraph)
    monkeypatch.setattr(reportlab.platypus, "SimpleDocTemplate", CapturingDocument)

    build_textbook_pdf_report(problem, solution)

    text = "\n".join(paragraph_text)
    for expected in ("输入摘要", "求解方法", "支座反力", "解题步骤", "挠度曲线摘要"):
        assert expected in text
    assert "analytical" in text
    assert "500.000" in text


class _FakePopover:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _FakeStreamlit:
    def __init__(self, *, clicked=False, report_format="Markdown"):
        self.clicked = clicked
        self.report_format = report_format
        self.popovers = []
        self.downloads = []

    def popover(self, label):
        self.popovers.append(label)
        return _FakePopover()

    def caption(self, text):
        pass

    def radio(self, *args, **kwargs):
        return self.report_format

    def button(self, *args, **kwargs):
        return self.clicked

    def download_button(self, label, **kwargs):
        self.downloads.append((label, kwargs))


def test_report_ui_hides_textbook_downloads_without_a_textbook_solution(monkeypatch):
    fake_streamlit = _FakeStreamlit()
    monkeypatch.setattr(report_ui, "st", fake_streamlit)

    render_report_exports(None, None)

    assert fake_streamlit.popovers == []
    assert fake_streamlit.downloads == []


def test_report_ui_does_not_build_markdown_or_pdf_until_generate_is_clicked(monkeypatch):
    problem, solution = _solved_problem()
    fake_streamlit = _FakeStreamlit(clicked=False)
    builders_called = []
    monkeypatch.setattr(report_ui, "st", fake_streamlit)
    monkeypatch.setattr(
        report_ui,
        "build_textbook_markdown",
        lambda *args: builders_called.append("markdown"),
    )
    monkeypatch.setattr(
        report_ui,
        "build_textbook_pdf_report",
        lambda *args: builders_called.append("pdf"),
    )

    render_report_exports(None, None, textbook_problem=problem, textbook_solution=solution)

    assert builders_called == []


@pytest.mark.parametrize(
    ("report_format", "expected_builder", "expected_label"),
    [
        ("Markdown", "markdown", "下载教材题 Markdown 报告"),
        ("PDF", "pdf", "下载教材题 PDF 报告"),
    ],
)
def test_report_ui_builds_the_selected_textbook_format_after_generate_click(
    monkeypatch, report_format, expected_builder, expected_label
):
    problem, solution = _solved_problem()
    fake_streamlit = _FakeStreamlit(clicked=True, report_format=report_format)
    builders_called = []
    monkeypatch.setattr(report_ui, "st", fake_streamlit)
    monkeypatch.setattr(
        report_ui,
        "build_textbook_markdown",
        lambda *args: builders_called.append("markdown") or "markdown report",
    )
    monkeypatch.setattr(
        report_ui,
        "build_textbook_pdf_report",
        lambda *args: builders_called.append("pdf") or b"%PDF-test",
    )

    render_report_exports(None, None, textbook_problem=problem, textbook_solution=solution)

    assert builders_called == [expected_builder]
    assert expected_label in [label for label, _ in fake_streamlit.downloads]


def test_report_ui_keeps_the_legacy_theory_report_branch_callable(monkeypatch):
    fake_streamlit = _FakeStreamlit(clicked=True, report_format="Markdown")
    generated = []
    monkeypatch.setattr(report_ui, "st", fake_streamlit)
    monkeypatch.setattr(
        report_ui,
        "build_markdown_report",
        lambda *args: generated.append(args) or "theory report",
    )

    render_report_exports(
        {
            "left_reaction": 500.0,
            "right_reaction": 500.0,
            "max_shear": 500.0,
            "max_moment": 250000.0,
            "max_deflection": -0.1,
            "max_deflection_position": 500.0,
        },
        {"梁长": "1000 mm"},
    )

    assert len(generated) == 1
    assert "下载 Markdown 报告" in [label for label, _ in fake_streamlit.downloads]


def test_report_export_ui_accepts_cached_textbook_result():
    parameters = inspect.signature(render_report_exports).parameters

    assert "textbook_problem" in parameters
    assert "textbook_solution" in parameters


def test_styled_app_passes_cached_textbook_result_to_report_exports():
    source = Path("app_styled.py").read_text(encoding="utf-8")

    assert "textbook_problem=st.session_state.get(\"textbook_export_problem\")" in source
    assert "textbook_solution=st.session_state.get(\"textbook_export_solution\")" in source


def test_failed_submission_keeps_result_but_invalidates_textbook_export_cache():
    cached_solution = object()
    cached_problem = object()
    state = {
        "textbook_solution": cached_solution,
        "textbook_problem": cached_problem,
        "textbook_export_solution": cached_solution,
        "textbook_export_problem": cached_problem,
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
    assert "textbook_export_solution" not in state
    assert "textbook_export_problem" not in state


def test_successful_submission_rebuilds_the_textbook_export_cache():
    state = {}

    solution = textbook_solver_ui.submit_textbook_problem(
        state,
        length_mm=1000.0,
        elastic_modulus_mpa=200_000.0,
        inertia_mm4=1_000_000.0,
        support_rows=[
            {"position_mm": 0.0, "kind": "pin", "label": "A"},
            {"position_mm": 1000.0, "kind": "roller", "label": "B"},
        ],
        point_load_rows=[{"position_mm": 500.0, "force_n": -1000.0}],
        distributed_load_rows=[],
    )

    assert state["textbook_export_solution"] is solution
    assert state["textbook_export_problem"] is state["textbook_problem"]


@pytest.mark.parametrize(
    "reset", [textbook_solver_ui.apply_simply_supported_template, textbook_solver_ui.apply_clear_input]
)
def test_templates_and_clear_input_invalidate_textbook_export_cache(reset):
    state = {
        "textbook_solution": object(),
        "textbook_problem": object(),
        "textbook_export_solution": object(),
        "textbook_export_problem": object(),
    }

    reset(state)

    assert "textbook_export_solution" not in state
    assert "textbook_export_problem" not in state
