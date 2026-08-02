from utils.report import build_markdown_report, build_pdf_report


INPUTS = {
    "荷载类型": "跨中集中力",
    "荷载大小": "100 N",
    "梁长": "1000 mm",
    "弹性模量": "200000 MPa",
    "截面信息": "矩形截面 b=20 mm, h=30 mm",
    "截面惯性矩": "45000 mm⁴",
}

RESULT = {
    "left_reaction": 50.0,
    "right_reaction": 50.0,
    "max_shear": 50.0,
    "max_moment": 25000.0,
    "max_deflection": -0.0104167,
    "max_deflection_position": 500.0,
}


def test_markdown_report_contains_inputs_and_results():
    report = build_markdown_report(INPUTS, RESULT)

    assert report.startswith("# BeamLab 简支梁分析报告")
    assert "矩形截面 b=20 mm, h=30 mm" in report
    assert "左支座反力" in report
    assert "25000.000 N·mm" in report


def test_pdf_report_returns_pdf_bytes():
    report = build_pdf_report(INPUTS, RESULT)

    assert report.startswith(b"%PDF")
    assert len(report) > 500
