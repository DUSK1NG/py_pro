"""Streamlit 多组荷载—挠度 CSV 分析区域。"""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from utils.export import build_load_deflection_csv
from utils.load_deflection import (
    calculate_load_deflection_comparison,
    load_deflection_from_csv,
)


def _build_theoretical_values(
    loads: object,
    theory_result: dict[str, object],
) -> list[float]:
    current_load = float(theory_result.get("load_n", 0))
    if current_load <= 0:
        raise ValueError("当前理论结果缺少有效的 load_n，无法生成理论荷载—挠度曲线。")
    current_deflection = float(theory_result["max_deflection"])
    return [current_deflection * float(load) / current_load for load in loads]


def render_load_deflection_analysis(
    theory_result: dict[str, object] | None,
) -> None:
    """渲染 CSV 上传、荷载—挠度曲线和对比导出。"""
    st.markdown("### 荷载—挠度数据分析")
    if theory_result is None:
        st.info("请先完成理论计算，再上传多组荷载—挠度 CSV。")
        return
    with st.expander("上传荷载—挠度 CSV", expanded=False):
        st.caption("CSV 必须包含 load_n 和 measured_deflection_mm 两列，向下挠度为负。")
        uploaded = st.file_uploader(
            "选择 CSV 文件",
            type=["csv"],
            key="load_deflection_csv",
        )
        if uploaded is None:
            return
        try:
            parsed = load_deflection_from_csv(
                uploaded.getvalue().decode("utf-8-sig")
            )
            theoretical = _build_theoretical_values(
                parsed["load_n"], theory_result
            )
            comparison = calculate_load_deflection_comparison(
                parsed["load_n"],
                parsed["measured_deflection_mm"],
                theoretical,
            )
        except (UnicodeDecodeError, ValueError) as error:
            st.error(f"荷载—挠度 CSV 读取失败：{error}")
            return

        table = {
            "荷载（N）": comparison["load_n"],
            "实测挠度（mm）": comparison["measured_deflection_mm"],
            "理论挠度（mm）": comparison["theoretical_deflection_mm"],
            "误差（mm）": comparison["error_mm"],
            "相对误差（%）": comparison["relative_error_percent"],
        }
        st.dataframe(table, use_container_width=True)
        columns = st.columns(3)
        columns[0].metric("最大绝对误差", f"{comparison['max_abs_error_mm']:.6f} mm")
        columns[1].metric("平均绝对误差", f"{comparison['mean_abs_error_mm']:.6f} mm")
        maximum_relative = comparison["max_relative_error_percent"]
        columns[2].metric(
            "最大相对误差",
            "无法计算" if maximum_relative is None else f"{maximum_relative:.2f}%",
        )

        figure, axis = plt.subplots()
        axis.plot(
            comparison["load_n"],
            comparison["theoretical_deflection_mm"],
            marker="o",
            label="理论挠度",
            color="#7c3aed",
        )
        axis.plot(
            comparison["load_n"],
            comparison["measured_deflection_mm"],
            marker="s",
            label="实测挠度",
            color="#2563eb",
        )
        axis.set(
            title="荷载—跨中挠度曲线",
            xlabel="荷载（N）",
            ylabel="跨中挠度（mm）",
        )
        axis.grid(True, alpha=0.3)
        axis.legend()
        st.pyplot(figure, use_container_width=True)
        plt.close(figure)
        if comparison["within_reasonable_range"]:
            st.success("荷载—挠度数据的最大相对误差不超过 10%。")
        else:
            st.warning("荷载—挠度数据误差超过 10%，建议复核实验记录和标定。")
        st.download_button(
            "下载荷载—挠度对比 CSV",
            data=build_load_deflection_csv(comparison),
            file_name="load_deflection_comparison.csv",
            mime="text/csv",
            key="download_load_deflection_comparison_csv",
        )
