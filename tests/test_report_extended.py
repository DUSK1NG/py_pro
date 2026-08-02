from tests.test_report import INPUTS, RESULT
from utils.report import build_markdown_report, build_pdf_report


MEASUREMENT = {"deflection_mm": -0.009}
COMPARISON = {
    "absolute_error_mm": 0.0014,
    "relative_error_percent": 13.44,
}


def test_report_can_include_measurement_and_comparison_summary():
    markdown = build_markdown_report(INPUTS, RESULT, MEASUREMENT, COMPARISON)

    assert "实测跨中挠度" in markdown
    assert "13.44%" in markdown


def test_pdf_report_accepts_measurement_and_comparison_summary():
    pdf = build_pdf_report(INPUTS, RESULT, MEASUREMENT, COMPARISON)

    assert pdf.startswith(b"%PDF")
