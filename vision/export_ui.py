"""理论和实测结果的 Streamlit 下载控件。"""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from utils.comparison import compare_deflection_curves
from utils.export import (
    build_curve_csv,
    build_measured_curve_csv,
    build_result_csv,
    figure_to_png_bytes,
)
from visualization.plotting import plot_bending_moment, plot_deflection, plot_shear_force


def render_theory_exports(theory_result: dict[str, object] | None) -> None:
    if theory_result is None:
        return
    with st.expander("理论数据与图表导出", expanded=False):
        st.download_button(
            "下载理论结果 CSV",
            data=build_result_csv(theory_result),
            file_name="theory_result.csv",
            mime="text/csv",
            key="download_theory_result_csv",
        )
        plotters = [
            ("下载剪力图 PNG", plot_shear_force, "shear_force.png", "theory_shear_png"),
            ("下载弯矩图 PNG", plot_bending_moment, "bending_moment.png", "theory_moment_png"),
            ("下载挠度图 PNG", plot_deflection, "deflection.png", "theory_deflection_png"),
        ]
        columns = st.columns(3)
        for column, (label, plotter, filename, key) in zip(columns, plotters):
            figure = plotter(theory_result)
            column.download_button(
                label,
                data=figure_to_png_bytes(figure),
                file_name=filename,
                mime="image/png",
                key=key,
            )
            plt.close(figure)


def render_measurement_exports(
    curve_measurement: dict[str, object] | None,
    theory_result: dict[str, object] | None,
) -> None:
    if curve_measurement is None:
        return
    with st.expander("实测数据与对比结果导出", expanded=False):
        figure, axis = plt.subplots()
        axis.plot(
            curve_measurement["x_mm"],
            curve_measurement["measured_deflection_mm"],
            label="实测挠度",
        )
        axis.set(xlabel="位置 x（mm）", ylabel="挠度 v（mm）", title="实测挠度曲线")
        axis.grid(True, alpha=0.3)
        axis.legend()
        st.download_button(
            "下载实测曲线 PNG",
            data=figure_to_png_bytes(figure),
            file_name="measured_deflection_curve.png",
            mime="image/png",
            key="export_measured_curve_png",
        )
        plt.close(figure)
        st.download_button(
            "下载实测曲线 CSV",
            data=build_measured_curve_csv(
                curve_measurement["x_mm"],
                curve_measurement["measured_deflection_mm"],
            ),
            file_name="measured_deflection_curve.csv",
            mime="text/csv",
            key="export_measured_curve_csv",
        )
        if theory_result is not None:
            comparison = compare_deflection_curves(
                theory_result["x"],
                theory_result["deflection"],
                curve_measurement["x_mm"],
                curve_measurement["measured_deflection_mm"],
            )
            st.download_button(
                "下载理论/实测对比 CSV",
                data=build_curve_csv(
                    comparison["x_mm"],
                    comparison["theoretical_at_measured_mm"],
                    comparison["measured_deflection_mm"],
                    comparison["error_mm"],
                ),
                file_name="deflection_comparison.csv",
                mime="text/csv",
                key="export_deflection_comparison_csv",
            )
