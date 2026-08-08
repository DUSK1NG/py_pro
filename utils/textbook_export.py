"""教材梁题的文本报告和曲线 CSV 导出。"""

from __future__ import annotations

import csv
from io import StringIO
from typing import Iterable

from mechanics.textbook_models import BeamProblem, BeamSolution


def _number(value: object, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def _curve_points(solution: BeamSolution) -> Iterable[tuple[float, float]]:
    """返回统一结果契约中的挠度曲线；兼容分段结果。"""
    x_values = getattr(solution, "x_mm", None)
    deflection_values = getattr(solution, "deflection_mm", None)
    if x_values is not None and deflection_values is not None:
        return zip(x_values, deflection_values)
    return (
        (position, deflection)
        for segment in solution.segments
        for position, deflection in zip(segment.positions_mm, segment.deflection_mm)
    )


def build_textbook_markdown(problem: BeamProblem, solution: BeamSolution) -> str:
    """生成包含教材题输入、反力、校核和求解过程的 Markdown 报告。"""
    classification = getattr(solution, "classification", None)
    method = getattr(solution, "method", "未知")
    category = getattr(classification, "category", "未知")
    checks = getattr(solution, "checks", {})
    steps = getattr(solution, "steps", ())
    warnings = getattr(solution, "warnings", ())

    input_lines = [
        f"- 梁长 L：{problem.length_mm:g} mm",
        f"- 弹性模量 E：{problem.elastic_modulus_mpa:g} MPa",
        f"- 截面惯性矩 I：{problem.inertia_mm4:g} mm⁴",
        f"- 支座：{', '.join(f'{support.label or support.kind}@{support.position_mm:g} mm' for support in problem.supports) or '无'}",
        f"- 集中力：{', '.join(f'{load.force_n:g} N@{load.position_mm:g} mm' for load in problem.point_loads) or '无'}",
        f"- 均布荷载：{', '.join(f'{load.intensity_n_per_mm:g} N/mm ({load.start_mm:g}–{load.end_mm:g} mm)' for load in problem.distributed_loads) or '无'}",
    ]
    reaction_lines = [
        f"- {reaction.support_kind}@{reaction.position_mm:g} mm：竖向 {_number(reaction.vertical_n)} N；反力矩 {_number(reaction.moment_n_mm)} N·mm"
        for reaction in solution.reactions
    ] or ["- 无"]
    check_lines = [f"- {name}：{_number(value, 6)}" for name, value in checks.items()] or ["- 无"]
    segment_lines = [
        (
            f"- {_number(segment.start_mm)}–{_number(segment.end_mm)} mm："
            f"剪力：{_number(segment.shear_n[0])} N → {_number(segment.shear_n[-1])} N；"
            f"弯矩：{_number(segment.bending_moment_n_mm[0])} N·mm"
            f" → {_number(segment.bending_moment_n_mm[-1])} N·mm；"
            f"{len(segment.positions_mm)} 个采样点"
        )
        for segment in solution.segments
    ] or ["- 无"]
    step_lines = [f"- {step}" for step in steps] or ["- 未提供"]
    warning_lines = [f"- {warning}" for warning in warnings] or ["- 无"]

    return "\n".join(
        [
            "# BeamLab 教材题求解报告",
            "",
            "## 输入摘要",
            *input_lines,
            "",
            "## 求解方法与静定性",
            f"- 求解方法：{method}",
            f"- 静定性：{category}",
            "",
            "## 支座反力",
            *reaction_lines,
            "",
            "## 平衡校核",
            *check_lines,
            "",
            "## 剪力/弯矩分段",
            *segment_lines,
            "",
            "## 挠度曲线摘要",
            f"- 最大挠度：{_number(solution.max_deflection_mm, 6)} mm",
            f"- 最大挠度位置：{_number(solution.max_deflection_position_mm)} mm",
            f"- 曲线采样点数：{sum(1 for _ in _curve_points(solution))}",
            "",
            "## 解题步骤",
            *step_lines,
            "",
            "## warnings",
            *warning_lines,
            "",
        ]
    )


def build_textbook_csv(solution: BeamSolution) -> str:
    """导出挠度曲线；仅反力位置填写对应竖向反力。"""
    reactions = {float(item.position_mm): item.vertical_n for item in solution.reactions}
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["x_mm", "deflection_mm", "reaction_vertical_n"])
    for position, deflection in _curve_points(solution):
        x_value = float(position)
        reaction = reactions.get(x_value)
        writer.writerow([x_value, float(deflection), "" if reaction is None else float(reaction)])
    return buffer.getvalue()
