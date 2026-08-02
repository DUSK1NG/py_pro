"""简支梁分析报告生成工具。"""

from __future__ import annotations

from html import escape
from io import BytesIO
from typing import Mapping


def _number(value: object, digits: int = 6) -> str:
    return f"{float(value):.{digits}f}"


def build_markdown_report(
    inputs: Mapping[str, object],
    result: Mapping[str, object],
) -> str:
    """生成可下载的 Markdown 理论分析报告。"""
    input_lines = [f"- **{key}**：{value}" for key, value in inputs.items()]
    result_lines = [
        f"- **左支座反力**：{_number(result['left_reaction'], 3)} N",
        f"- **右支座反力**：{_number(result['right_reaction'], 3)} N",
        f"- **最大剪力**：{_number(result['max_shear'], 3)} N",
        f"- **最大弯矩**：{_number(result['max_moment'], 3)} N·mm",
        f"- **最大挠度**：{_number(result['max_deflection'], 6)} mm",
        f"- **最大挠度位置**：{_number(result['max_deflection_position'], 3)} mm",
    ]
    return "\n".join(
        [
            "# BeamLab 简支梁分析报告",
            "",
            "## 输入参数",
            *input_lines,
            "",
            "## 理论计算结果",
            *result_lines,
            "",
            "## 适用条件",
            "两端理想简支、均匀等截面、材料线弹性、满足小挠度假设。",
            "本报告不包含 OpenCV 实测数据。",
            "",
        ]
    )


def build_pdf_report(
    inputs: Mapping[str, object],
    result: Mapping[str, object],
) -> bytes:
    """生成 PDF 报告并返回字节内容。"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as error:  # pragma: no cover - dependency is declared in requirements
        raise RuntimeError("生成 PDF 需要安装 reportlab 依赖。") from error

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BeamLabTitle",
        parent=styles["Title"],
        fontName="STSong-Light",
        fontSize=18,
        leading=24,
    )
    body_style = ParagraphStyle(
        "BeamLabBody",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=10,
        leading=16,
    )
    heading_style = ParagraphStyle(
        "BeamLabHeading",
        parent=styles["Heading2"],
        fontName="STSong-Light",
        fontSize=13,
        leading=18,
    )

    input_rows = [[Paragraph("输入参数", heading_style), ""]]
    input_rows.extend(
        [
            Paragraph(escape(str(key)), body_style),
            Paragraph(escape(str(value)), body_style),
        ]
        for key, value in inputs.items()
    )
    result_rows = [
        [Paragraph("计算结果", heading_style), ""],
        [Paragraph("左支座反力", body_style), f"{_number(result['left_reaction'], 3)} N"],
        [Paragraph("右支座反力", body_style), f"{_number(result['right_reaction'], 3)} N"],
        [Paragraph("最大剪力", body_style), f"{_number(result['max_shear'], 3)} N"],
        [Paragraph("最大弯矩", body_style), f"{_number(result['max_moment'], 3)} N·mm"],
        [Paragraph("最大挠度", body_style), f"{_number(result['max_deflection'], 6)} mm"],
        [Paragraph("最大挠度位置", body_style), f"{_number(result['max_deflection_position'], 3)} mm"],
    ]

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    table_style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf1ff")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c7e0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )
    story = [
        Paragraph("BeamLab 简支梁分析报告", title_style),
        Spacer(1, 8),
        Table(input_rows, colWidths=[42 * mm, 118 * mm], style=table_style),
        Spacer(1, 12),
        Table(result_rows, colWidths=[42 * mm, 118 * mm], style=table_style),
        Spacer(1, 12),
        Paragraph("适用条件：两端理想简支、均匀等截面、材料线弹性、满足小挠度假设。", body_style),
        Paragraph("本报告不包含 OpenCV 实测数据。", body_style),
    ]
    document.build(story)
    return buffer.getvalue()

def _merge_measurement_summary(
    inputs: Mapping[str, object],
    measurement: Mapping[str, object] | None,
    comparison: Mapping[str, object] | None,
) -> dict[str, object]:
    merged = dict(inputs)
    if measurement is not None and "deflection_mm" in measurement:
        merged["实测跨中挠度"] = f"{float(measurement['deflection_mm']):.6f} mm"
    if comparison is not None:
        if "absolute_error_mm" in comparison:
            merged["绝对误差"] = f"{float(comparison['absolute_error_mm']):.6f} mm"
        if comparison.get("relative_error_percent") is not None:
            merged["相对误差"] = f"{float(comparison['relative_error_percent']):.2f}%"
        if "max_abs_error_mm" in comparison:
            merged["最大曲线绝对误差"] = f"{float(comparison['max_abs_error_mm']):.6f} mm"
        if "mean_abs_error_mm" in comparison:
            merged["平均曲线绝对误差"] = f"{float(comparison['mean_abs_error_mm']):.6f} mm"
    return merged


_original_build_markdown_report = build_markdown_report
_original_build_pdf_report = build_pdf_report


def build_markdown_report(
    inputs: Mapping[str, object],
    result: Mapping[str, object],
    measurement: Mapping[str, object] | None = None,
    comparison: Mapping[str, object] | None = None,
) -> str:
    merged = _merge_measurement_summary(inputs, measurement, comparison)
    report = _original_build_markdown_report(merged, result)
    if measurement is not None or comparison is not None:
        report = report.replace("本报告不包含 OpenCV 实测数据。", "本报告包含 OpenCV 实测摘要和误差结果。")
    return report


def build_pdf_report(
    inputs: Mapping[str, object],
    result: Mapping[str, object],
    measurement: Mapping[str, object] | None = None,
    comparison: Mapping[str, object] | None = None,
) -> bytes:
    merged = _merge_measurement_summary(inputs, measurement, comparison)
    return _original_build_pdf_report(merged, result)
