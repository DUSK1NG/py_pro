"""BeamLab 工程分析工作台：Streamlit 优化入口。"""

import streamlit as st
from utils.units import convert_modulus_to_mpa

from app import calculate_beam
from visualization.plotting import (
    plot_bending_moment,
    plot_deflection,
    plot_shear_force,
)


def _theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@400;500;600;700&display=swap');

        :root {
            --navy: #1e3a8a;
            --ink: #172033;
            --muted: #64748b;
            --line: #dbe5f1;
        }

        html, body, [class*="css"] {
            font-family: "Fira Sans", sans-serif;
            color: var(--ink);
        }

        .stApp {
            background: #f8fafc;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #eef4ff 0%, #f8fafc 58%);
            border-right: 1px solid var(--line);
        }

        .brand {
            padding: 0.4rem 0 1.2rem;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1.4rem;
        }

        .brand h1 {
            color: var(--navy);
            font-size: 2rem;
            letter-spacing: -0.04em;
            margin: 0;
        }

        .brand p {
            color: var(--muted);
            margin: 0.35rem 0 0;
            font-size: 0.92rem;
        }

        .section-label {
            color: var(--navy);
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            font-size: 0.75rem;
            margin: 1rem 0 0.4rem;
        }

        .metric-card {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 1rem 1.05rem;
            box-shadow: 0 5px 18px rgba(30, 58, 138, 0.06);
            min-height: 104px;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.8rem;
        }

        .metric-value {
            color: var(--navy);
            font-family: "Fira Code", monospace;
            font-size: 1.15rem;
            font-weight: 600;
            margin-top: 0.45rem;
        }

        .stButton > button {
            background: var(--navy);
            color: white;
            border: 0;
            border-radius: 9px;
            min-height: 44px;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background: #172554;
            box-shadow: 0 5px 14px rgba(30, 58, 138, 0.22);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="BeamLab · 简支梁分析",
        page_icon="∿",
        layout="wide",
    )

    _theme()

    st.markdown(
        """
        <div class="brand">
            <h1>BeamLab</h1>
            <p>简支梁理论分析工作台 · Mechanics first</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("## 参数面板")
    st.sidebar.caption("输入实验参数，统一换算后计算理论响应")

    load_type = st.sidebar.selectbox(
        "荷载类型",
        ["跨中集中力", "任意位置集中力", "满跨均布荷载"],
    )

    st.sidebar.markdown(
        '<div class="section-label">几何与材料</div>',
        unsafe_allow_html=True,
    )

    length_value_col, length_unit_col = st.sidebar.columns([2, 1])
    length = length_value_col.number_input(
        "梁长 L",
        min_value=0.001,
        value=1000.0,
    )
    length_unit = length_unit_col.selectbox(
        "单位",
        ["mm", "m"],
        key="length_unit",
    )

    modulus_value_col, modulus_unit_col = st.sidebar.columns([2, 1])
    elastic_modulus_input = modulus_value_col.number_input(
        "弹性模量 E",
        min_value=0.001,
        value=200000.0,
    )
    modulus_unit = modulus_unit_col.selectbox(
        "单位",
        ["MPa", "GPa"],
        key="modulus_unit",
    )

    inertia_value_col, inertia_unit_col = st.sidebar.columns([2, 1])
    inertia_moment = inertia_value_col.number_input(
        "截面惯性矩 I",
        min_value=0.001,
        value=1000000.0,
    )
    inertia_unit_col.caption("mm⁴")

    st.sidebar.markdown(
        '<div class="section-label">荷载输入</div>',
        unsafe_allow_html=True,
    )

    if load_type == "满跨均布荷载":
        load_value_col, load_unit_col = st.sidebar.columns([2, 1])

        load_value = load_value_col.number_input(
            "均布荷载 q",
            min_value=0.001,
            value=1.0,
        )

        load_unit = load_unit_col.selectbox(
            "单位",
            ["N/mm", "N/m", "kN/m", "kN/mm"],
            key="uniform_load_unit",
        )

        position = None

    else:
        load_value_col, load_unit_col = st.sidebar.columns([2, 1])

        load_value = load_value_col.number_input(
            "集中力 P",
            min_value=0.001,
            value=100.0,
        )

        load_unit = load_unit_col.selectbox(
            "单位",
            ["N", "kN"],
            key="point_load_unit",
        )

        if load_type == "任意位置集中力":
            position_value_col, position_unit_col = st.sidebar.columns([2, 1])

            position = position_value_col.number_input(
                "荷载位置 a",
                min_value=0.001,
                value=300.0,
            )

            position_unit_col.caption(length_unit)

        else:
            position = None

    if st.sidebar.button("开始计算", use_container_width=True):
        try:
            result = calculate_beam(
                load_type=load_type,
                load_value=load_value,
                load_unit=load_unit,
                length=length,
                length_unit=length_unit,
                elastic_modulus=convert_modulus_to_mpa(
                    elastic_modulus_input,
                    modulus_unit,
                ),
                inertia_moment=inertia_moment,
                position=position,
            )

            st.markdown("### 计算结果")

            cards = [
                ("最大剪力", f"{result['max_shear']:.3f} N"),
                ("最大弯矩", f"{result['max_moment']:.3f} N·mm"),
                ("最大挠度", f"{result['max_deflection']:.6f} mm"),
                (
                    "最大挠度位置",
                    f"{result['max_deflection_position']:.3f} mm",
                ),
            ]

            columns = st.columns(4)

            for column, (label, value) in zip(columns, cards):
                column.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("### 理论图表")

            shear_tab, moment_tab, deflection_tab = st.tabs(
                ["剪力图", "弯矩图", "挠度曲线"]
            )

            with shear_tab:
                st.pyplot(
                    plot_shear_force(result),
                    use_container_width=True,
                )

            with moment_tab:
                st.pyplot(
                    plot_bending_moment(result),
                    use_container_width=True,
                )

            with deflection_tab:
                st.pyplot(
                    plot_deflection(result),
                    use_container_width=True,
                )

        except ValueError as error:
            st.error(f"参数无法计算：{error}")

    else:
        st.info("从左侧输入梁参数并点击“开始计算”，查看理论响应。")


if __name__ == "__main__":
    main()
