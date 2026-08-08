"""教材梁题的 Streamlit 输入与结果界面。"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import pandas as pd
import streamlit as st

from mechanics.textbook_models import (
    BeamProblem,
    BeamSolution,
    DistributedLoad,
    PointLoad,
    ProblemInputError,
    Support,
)
from mechanics.textbook_solver import solve_textbook_beam


_SUPPORT_COLUMNS = ["position_mm", "kind", "label"]
_POINT_LOAD_COLUMNS = ["position_mm", "force_n"]
_DISTRIBUTED_LOAD_COLUMNS = ["start_mm", "end_mm", "intensity_n_per_mm"]

_DEFAULT_LENGTH_MM = 1000.0
_DEFAULT_MODULUS_MPA = 200_000.0
_DEFAULT_INERTIA_MM4 = 1_000_000.0
_EDITOR_KEYS = (
    "textbook_support_editor",
    "textbook_point_load_editor",
    "textbook_distributed_load_editor",
)


def _clear_cached_result(state: MutableMapping[str, Any]) -> None:
    state.pop("textbook_solution", None)
    state.pop("textbook_problem", None)


def _reset_editors(state: MutableMapping[str, Any]) -> None:
    for key in _EDITOR_KEYS:
        state.pop(key, None)


def _set_template_rows(
    state: MutableMapping[str, Any],
    *,
    support_rows: list[dict[str, object]],
    point_load_rows: list[dict[str, object]],
) -> None:
    state["textbook_length_mm"] = _DEFAULT_LENGTH_MM
    state["textbook_support_rows"] = support_rows
    state["textbook_point_load_rows"] = point_load_rows
    state["textbook_distributed_load_rows"] = []
    _clear_cached_result(state)
    _reset_editors(state)


def apply_simply_supported_template(state: MutableMapping[str, Any]) -> None:
    """应用简支梁模板，并作废此前求解结果。"""
    _set_template_rows(
        state,
        support_rows=[
            {"position_mm": 0.0, "kind": "pin", "label": "A"},
            {"position_mm": 1000.0, "kind": "roller", "label": "B"},
        ],
        point_load_rows=[{"position_mm": 500.0, "force_n": -1000.0}],
    )


def apply_cantilever_template(state: MutableMapping[str, Any]) -> None:
    """应用悬臂梁模板，并作废此前求解结果。"""
    _set_template_rows(
        state,
        support_rows=[
            {"position_mm": 0.0, "kind": "fixed", "label": "A"},
            {"position_mm": 1000.0, "kind": "free", "label": "自由端"},
        ],
        point_load_rows=[{"position_mm": 1000.0, "force_n": -1000.0}],
    )


def apply_clear_input(state: MutableMapping[str, Any]) -> None:
    """清空表格输入、复位标量默认值，并作废此前求解结果。"""
    state["textbook_length_mm"] = _DEFAULT_LENGTH_MM
    state["textbook_modulus_mpa"] = _DEFAULT_MODULUS_MPA
    state["textbook_inertia_mm4"] = _DEFAULT_INERTIA_MM4
    state["textbook_support_rows"] = []
    state["textbook_point_load_rows"] = []
    state["textbook_distributed_load_rows"] = []
    _clear_cached_result(state)
    _reset_editors(state)


def build_problem_from_rows(
    *,
    length_mm: float,
    elastic_modulus_mpa: float,
    inertia_mm4: float,
    support_rows: list[dict[str, object]],
    point_load_rows: list[dict[str, object]],
    distributed_load_rows: list[dict[str, object]],
) -> BeamProblem:
    """将表格编辑器行转换为教材求解器使用的数据模型。"""
    try:
        problem = BeamProblem(
            length_mm=float(length_mm),
            elastic_modulus_mpa=float(elastic_modulus_mpa),
            inertia_mm4=float(inertia_mm4),
            supports=[
                Support(
                    position_mm=float(row["position_mm"]),
                    kind=str(row["kind"]),
                    label=str(row.get("label", "")),
                )
                for row in support_rows
            ],
            point_loads=[
                PointLoad(
                    position_mm=float(row["position_mm"]),
                    force_n=float(row["force_n"]),
                )
                for row in point_load_rows
            ],
            distributed_loads=[
                DistributedLoad(
                    start_mm=float(row["start_mm"]),
                    end_mm=float(row["end_mm"]),
                    intensity_n_per_mm=float(row["intensity_n_per_mm"]),
                )
                for row in distributed_load_rows
            ],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ProblemInputError(f"表格输入无效：{error}") from error

    problem.validate()
    return problem


def submit_textbook_problem(
    state: MutableMapping[str, Any],
    *,
    length_mm: float,
    elastic_modulus_mpa: float,
    inertia_mm4: float,
    support_rows: list[dict[str, object]],
    point_load_rows: list[dict[str, object]],
    distributed_load_rows: list[dict[str, object]],
) -> BeamSolution:
    """求解并仅在成功后替换缓存结果。"""
    problem = build_problem_from_rows(
        length_mm=length_mm,
        elastic_modulus_mpa=elastic_modulus_mpa,
        inertia_mm4=inertia_mm4,
        support_rows=support_rows,
        point_load_rows=point_load_rows,
        distributed_load_rows=distributed_load_rows,
    )
    solution = solve_textbook_beam(problem)
    state["textbook_solution"] = solution
    state["textbook_problem"] = problem
    return solution


def render_textbook_solver() -> BeamSolution | None:
    """渲染教材题表单，并返回本次或上次成功求得的梁解。"""
    st.session_state.setdefault("textbook_length_mm", _DEFAULT_LENGTH_MM)
    st.session_state.setdefault("textbook_modulus_mpa", _DEFAULT_MODULUS_MPA)
    st.session_state.setdefault("textbook_inertia_mm4", _DEFAULT_INERTIA_MM4)
    st.session_state.setdefault(
        "textbook_support_rows",
        [
            {"position_mm": 0.0, "kind": "pin", "label": "A"},
            {"position_mm": 1000.0, "kind": "roller", "label": "B"},
        ],
    )
    st.session_state.setdefault(
        "textbook_point_load_rows",
        [{"position_mm": 500.0, "force_n": -1000.0}],
    )
    st.session_state.setdefault("textbook_distributed_load_rows", [])

    st.header("教材题求解器")
    st.caption("内部单位：mm、N、MPa、mm⁴；向下荷载和挠度为负值。")

    template_columns = st.columns(3)
    if template_columns[0].button("简支梁模板", width="stretch"):
        apply_simply_supported_template(st.session_state)
        st.rerun()
    if template_columns[1].button("悬臂梁模板", width="stretch"):
        apply_cantilever_template(st.session_state)
        st.rerun()
    if template_columns[2].button("清空输入", width="stretch"):
        apply_clear_input(st.session_state)
        st.rerun()

    with st.form("textbook_solver_form"):
        geometry_columns = st.columns(3)
        length_mm = geometry_columns[0].number_input(
            "梁长 L（mm）", min_value=0.001, key="textbook_length_mm"
        )
        elastic_modulus_mpa = geometry_columns[1].number_input(
            "弹性模量 E（MPa）", min_value=0.001, key="textbook_modulus_mpa"
        )
        inertia_mm4 = geometry_columns[2].number_input(
            "截面惯性矩 I（mm⁴）", min_value=0.001, key="textbook_inertia_mm4"
        )

        st.subheader("支座")
        support_rows = st.data_editor(
            pd.DataFrame(st.session_state["textbook_support_rows"], columns=_SUPPORT_COLUMNS),
            key="textbook_support_editor",
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "position_mm": st.column_config.NumberColumn("位置（mm）"),
                "kind": st.column_config.SelectboxColumn(
                    "类型", options=["fixed", "pin", "roller", "free"]
                ),
                "label": st.column_config.TextColumn("标签"),
            },
        )

        st.subheader("集中力")
        point_load_rows = st.data_editor(
            pd.DataFrame(
                st.session_state["textbook_point_load_rows"], columns=_POINT_LOAD_COLUMNS
            ),
            key="textbook_point_load_editor",
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "position_mm": st.column_config.NumberColumn("位置（mm）"),
                "force_n": st.column_config.NumberColumn("力（N，向下为负）"),
            },
        )

        st.subheader("均布荷载")
        distributed_load_rows = st.data_editor(
            pd.DataFrame(
                st.session_state["textbook_distributed_load_rows"],
                columns=_DISTRIBUTED_LOAD_COLUMNS,
            ),
            key="textbook_distributed_load_editor",
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "start_mm": st.column_config.NumberColumn("起点（mm）"),
                "end_mm": st.column_config.NumberColumn("终点（mm）"),
                "intensity_n_per_mm": st.column_config.NumberColumn(
                    "强度（N/mm，向下为负）"
                ),
            },
        )
        submitted = st.form_submit_button("求解教材题", type="primary", width="stretch")

    if submitted:
        try:
            submit_textbook_problem(
                st.session_state,
                length_mm=length_mm,
                elastic_modulus_mpa=elastic_modulus_mpa,
                inertia_mm4=inertia_mm4,
                support_rows=support_rows.to_dict("records"),
                point_load_rows=point_load_rows.to_dict("records"),
                distributed_load_rows=distributed_load_rows.to_dict("records"),
            )
        except (ProblemInputError, ValueError) as error:
            st.error(f"参数无法求解：{error}")

    solution = st.session_state.get("textbook_solution")
    problem = st.session_state.get("textbook_problem")
    if solution is None or problem is None:
        st.info("填写支座和荷载后，点击“求解教材题”查看结果。")
        return None

    classification = solution.classification
    st.success(f"已完成：{classification.method.upper()} · {classification.category}")

    st.subheader("输入摘要")
    st.dataframe(
        pd.DataFrame(
            [
                {"项目": "梁长 L", "数值": f"{problem.length_mm:g} mm"},
                {"项目": "弹性模量 E", "数值": f"{problem.elastic_modulus_mpa:g} MPa"},
                {"项目": "截面惯性矩 I", "数值": f"{problem.inertia_mm4:g} mm⁴"},
                {"项目": "支座数", "数值": len(problem.supports)},
                {"项目": "集中力数", "数值": len(problem.point_loads)},
                {"项目": "均布荷载数", "数值": len(problem.distributed_loads)},
            ]
        ),
        hide_index=True,
    )

    st.subheader("反力与平衡校核")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "位置（mm）": reaction.position_mm,
                    "支座": reaction.support_kind,
                    "竖向反力（N）": reaction.vertical_n,
                    "反力矩（N·mm）": reaction.moment_n_mm,
                }
                for reaction in solution.reactions
            ]
        ),
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(
            [{"校核项": name, "结果": value} for name, value in solution.checks.items()]
        ),
        hide_index=True,
    )

    chart_rows = [
        {
            "位置（mm）": position,
            "剪力（N）": shear,
            "弯矩（N·mm）": moment,
            "挠度（mm）": deflection,
        }
        for segment in solution.segments
        for position, shear, moment, deflection in zip(
            segment.positions_mm,
            segment.shear_n,
            segment.bending_moment_n_mm,
            segment.deflection_mm,
        )
    ]
    charts = pd.DataFrame(chart_rows)
    st.subheader("响应图")
    shear_tab, moment_tab, deflection_tab = st.tabs(["剪力图", "弯矩图", "挠度图"])
    with shear_tab:
        st.line_chart(charts, x="位置（mm）", y="剪力（N）", width="stretch")
    with moment_tab:
        st.line_chart(charts, x="位置（mm）", y="弯矩（N·mm）", width="stretch")
    with deflection_tab:
        st.line_chart(charts, x="位置（mm）", y="挠度（mm）", width="stretch")

    st.subheader("分段结果")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "起点（mm）": segment.start_mm,
                    "终点（mm）": segment.end_mm,
                    "采样点数": len(segment.positions_mm),
                }
                for segment in solution.segments
            ]
        ),
        hide_index=True,
    )

    st.subheader("FEM 网格元数据")
    st.dataframe(
        pd.DataFrame(
            [{"字段": name, "数值": value} for name, value in solution.metadata.items()]
        ),
        hide_index=True,
    )
    with st.expander("求解步骤与 warnings"):
        for step in solution.steps:
            st.write(step)
        for warning in solution.warnings:
            st.warning(warning)

    return solution
