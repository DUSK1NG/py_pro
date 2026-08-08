"""Streamlit 理论/实测报告下载弹窗。"""

from __future__ import annotations

import streamlit as st

from utils.comparison import compare_deflection_curves, compare_single_deflection
from mechanics.textbook_models import BeamProblem, BeamSolution
from utils.export import build_textbook_csv
from utils.report import build_markdown_report, build_pdf_report, build_textbook_pdf_report
from utils.textbook_export import build_textbook_markdown


def render_report_exports(
    theory_result: dict[str, object] | None,
    report_inputs: dict[str, object] | None,
    single_measurement: dict[str, object] | None = None,
    curve_measurement: dict[str, object] | None = None,
    textbook_problem: BeamProblem | None = None,
    textbook_solution: BeamSolution | None = None,
) -> None:
    """渲染理论/实测或教材题的 Markdown、PDF 和 CSV 下载入口。"""
    has_theory_report = theory_result is not None and report_inputs is not None
    has_textbook_report = textbook_problem is not None and textbook_solution is not None
    if not has_theory_report and not has_textbook_report:
        return
    with st.popover("导出报告"):
        st.caption("选择格式后生成当前分析报告")
        report_format = st.radio(
            "报告格式",
            ["Markdown", "PDF"],
            horizontal=True,
            key="persistent_report_format",
        )
        if st.button("生成报告", key="persistent_generate_report"):
            if has_textbook_report and not has_theory_report:
                if report_format == "Markdown":
                    data = build_textbook_markdown(textbook_problem, textbook_solution)
                    label, file_name, mime, key = (
                        "下载教材题 Markdown 报告",
                        "beamlab_textbook_report.md",
                        "text/markdown",
                        "persistent_download_textbook_markdown",
                    )
                else:
                    data = build_textbook_pdf_report(textbook_problem, textbook_solution)
                    label, file_name, mime, key = (
                        "下载教材题 PDF 报告",
                        "beamlab_textbook_report.pdf",
                        "application/pdf",
                        "persistent_download_textbook_pdf",
                    )
                st.download_button(
                    label,
                    data=data,
                    file_name=file_name,
                    mime=mime,
                    key=key,
                )
            else:
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
        if has_textbook_report:
            st.download_button(
                "下载教材题曲线 CSV",
                data=build_textbook_csv(textbook_solution),
                file_name="beamlab_textbook_curve.csv",
                mime="text/csv",
                key="persistent_download_textbook_csv",
            )
