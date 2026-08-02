"""Streamlit 理论/实测报告下载弹窗。"""

from __future__ import annotations

import streamlit as st

from utils.comparison import compare_deflection_curves, compare_single_deflection
from utils.report import build_markdown_report, build_pdf_report


def render_report_exports(
    theory_result: dict[str, object] | None,
    report_inputs: dict[str, object] | None,
    single_measurement: dict[str, object] | None = None,
    curve_measurement: dict[str, object] | None = None,
) -> None:
    """渲染持久化的 Markdown/PDF 报告导出弹窗。"""
    if theory_result is None or report_inputs is None:
        return
    with st.popover("导出报告"):
        st.caption("选择格式后生成当前理论与实测分析报告")
        report_format = st.radio(
            "报告格式",
            ["Markdown", "PDF"],
            horizontal=True,
            key="persistent_report_format",
        )
        if st.button("生成报告", key="persistent_generate_report"):
            measurement = single_measurement
            comparison = None
            if curve_measurement is not None:
                measurement = {"deflection_mm": float(curve_measurement["measured_deflection_mm"][len(curve_measurement["measured_deflection_mm"]) // 2])}
                comparison = compare_deflection_curves(
                    theory_result["x"],
                    theory_result["deflection"],
                    curve_measurement["x_mm"],
                    curve_measurement["measured_deflection_mm"],
                )
            elif single_measurement is not None:
                comparison = compare_single_deflection(
                    theory_result["max_deflection"],
                    single_measurement["deflection_mm"],
                )
            if report_format == "Markdown":
                data = build_markdown_report(report_inputs, theory_result, measurement, comparison)
                st.download_button(
                    "下载 Markdown 报告",
                    data=data,
                    file_name="beamlab_report.md",
                    mime="text/markdown",
                    key="persistent_download_markdown",
                )
            else:
                data = build_pdf_report(report_inputs, theory_result, measurement, comparison)
                st.download_button(
                    "下载 PDF 报告",
                    data=data,
                    file_name="beamlab_report.pdf",
                    mime="application/pdf",
                    key="persistent_download_pdf",
                )
