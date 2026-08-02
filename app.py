"""简支梁理论分析 Streamlit 界面。"""

import streamlit as st

from mechanics import central_point_load, point_load, uniform_load
from utils.units import (
    convert_distributed_load_to_n_per_mm,
    convert_force_to_n,
    convert_length_to_mm,
)
from visualization.plotting import (
    plot_bending_moment,
    plot_deflection,
    plot_shear_force,
)


def calculate_beam(
    load_type: str,
    load_value: float,
    load_unit: str,
    length: float,
    length_unit: str,
    elastic_modulus: float,
    inertia_moment: float,
    position: float | None = None,
) -> dict[str, object]:
    """将界面输入转换并分派至对应的理论计算模块。"""
    length_mm = convert_length_to_mm(length, length_unit)
    if load_type == "跨中集中力":
        return central_point_load.sample_beam(
            length_mm, convert_force_to_n(load_value, load_unit), elastic_modulus, inertia_moment
        )
    if load_type == "任意位置集中力":
        if position is None:
            raise ValueError("请输入集中力作用位置 a。")
        return point_load.sample_beam(
            length_mm,
            convert_force_to_n(load_value, load_unit),
            convert_length_to_mm(position, length_unit),
            elastic_modulus,
            inertia_moment,
        )
    if load_type == "满跨均布荷载":
        return uniform_load.sample_beam(
            length_mm,
            convert_distributed_load_to_n_per_mm(load_value, load_unit),
            elastic_modulus,
            inertia_moment,
        )
    raise ValueError("不支持的荷载类型。")


def main() -> None:
    """渲染 Streamlit 页面。"""
    st.set_page_config(page_title="简支梁力学分析", layout="wide")
    st.title("简支梁力学分析与挠度计算")
    st.sidebar.header("参数输入")
    load_type = st.sidebar.selectbox("荷载类型", ["跨中集中力", "任意位置集中力", "满跨均布荷载"])
    length_unit = st.sidebar.selectbox("梁长单位", ["mm", "m"])
    length = st.sidebar.number_input("梁长 L", min_value=0.001, value=1000.0)
    elastic_modulus = st.sidebar.number_input("弹性模量 E（MPa）", min_value=0.001, value=200000.0)
    inertia_moment = st.sidebar.number_input("截面惯性矩 I（mm⁴）", min_value=0.001, value=1000000.0)
    if load_type == "满跨均布荷载":
        load_unit = st.sidebar.selectbox("均布荷载单位", ["N/mm", "N/m", "kN/m", "kN/mm"])
        load_value = st.sidebar.number_input("均布荷载 q", min_value=0.001, value=1.0)
        position = None
    else:
        load_unit = st.sidebar.selectbox("集中力单位", ["N", "kN"])
        load_value = st.sidebar.number_input("集中力 P", min_value=0.001, value=100.0)
        position = None
        if load_type == "任意位置集中力":
            position = st.sidebar.number_input("荷载位置 a", min_value=0.001, value=300.0)
    if st.sidebar.button("开始计算"):
        try:
            result = calculate_beam(load_type, load_value, load_unit, length, length_unit, elastic_modulus, inertia_moment, position)
            columns = st.columns(4)
            columns[0].metric("最大剪力（N）", f"{result['max_shear']:.3f}")
            columns[1].metric("最大弯矩（N·mm）", f"{result['max_moment']:.3f}")
            columns[2].metric("最大挠度（mm）", f"{result['max_deflection']:.6f}")
            columns[3].metric("最大挠度位置（mm）", f"{result['max_deflection_position']:.3f}")
            st.pyplot(plot_shear_force(result))
            st.pyplot(plot_bending_moment(result))
            st.pyplot(plot_deflection(result))
        except ValueError as error:
            st.error(str(error))


if __name__ == "__main__":
    main()
