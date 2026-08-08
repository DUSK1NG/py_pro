"""标准简支梁和悬臂梁的教材式静定解析解。"""

from __future__ import annotations

from collections.abc import Callable
import math
from typing import Literal

from mechanics.textbook_models import (
    BeamProblem,
    BeamSolution,
    DistributedLoad,
    PointLoad,
    ProblemInputError,
    Reaction,
    SegmentResult,
    Support,
)


_EPSILON = 1e-12


def supports_analytical(problem: BeamProblem) -> bool:
    """返回问题是否为本模块可直接解析的标准静定梁。"""
    problem.validate()
    supports = problem.supports
    kinds = [support.kind for support in supports]

    if kinds.count("pin") == 1 and kinds.count("roller") == 1:
        constrained = [support for support in supports if support.kind in {"pin", "roller"}]
        return (
            constrained[0].position_mm != constrained[1].position_mm
            and all(support.kind in {"pin", "roller", "free"} for support in supports)
        )

    fixed = [support for support in supports if support.kind == "fixed"]
    return (
        len(fixed) == 1
        and all(support.kind in {"fixed", "free"} for support in supports)
        and _is_beam_end(fixed[0].position_mm, problem.length_mm)
    )


def solve_simply_supported(problem: BeamProblem) -> BeamSolution:
    """解一个有一个铰支和一个滚支的静定梁，荷载向上为正。"""
    problem.validate()
    if not _is_simply_supported(problem):
        raise ProblemInputError("解析简支梁需要恰有一个 pin 和一个 roller，其余支座必须为 free。")

    left, right = sorted(
        (support for support in problem.supports if support.kind in {"pin", "roller"}),
        key=lambda support: support.position_mm,
    )
    external_resultants = _external_resultants(problem.point_loads, problem.distributed_loads)
    total_force = sum(force for force, _ in external_resultants)
    moment_about_left = sum(
        force * (position - left.position_mm) for force, position in external_resultants
    )
    right_vertical = -moment_about_left / (right.position_mm - left.position_mm)
    left_vertical = -total_force - right_vertical
    reactions = [
        Reaction(left.position_mm, left_vertical, 0.0, left.kind),
        Reaction(right.position_mm, right_vertical, 0.0, right.kind),
    ]
    return _build_solution(problem, reactions, "simply_supported")


def solve_cantilever(problem: BeamProblem) -> BeamSolution:
    """解固定端在梁端部的悬臂梁。"""
    problem.validate()
    if not _is_cantilever(problem):
        raise ProblemInputError("解析悬臂梁需要一个位于梁端的 fixed，其余支座必须为 free。")

    fixed = next(support for support in problem.supports if support.kind == "fixed")
    external_resultants = _external_resultants(problem.point_loads, problem.distributed_loads)
    vertical = -sum(force for force, _ in external_resultants)
    moment = -sum(
        force * (position - fixed.position_mm) for force, position in external_resultants
    )
    return _build_solution(
        problem,
        [Reaction(fixed.position_mm, vertical, moment, fixed.kind)],
        "cantilever",
    )


def _is_simply_supported(problem: BeamProblem) -> bool:
    supports = problem.supports
    constrained = [support for support in supports if support.kind in {"pin", "roller"}]
    return (
        len(constrained) == 2
        and {support.kind for support in constrained} == {"pin", "roller"}
        and constrained[0].position_mm != constrained[1].position_mm
        and all(support.kind in {"pin", "roller", "free"} for support in supports)
    )


def _is_cantilever(problem: BeamProblem) -> bool:
    fixed = [support for support in problem.supports if support.kind == "fixed"]
    return (
        len(fixed) == 1
        and _is_beam_end(fixed[0].position_mm, problem.length_mm)
        and all(support.kind in {"fixed", "free"} for support in problem.supports)
    )


def _is_beam_end(position: float, length: float) -> bool:
    return abs(position) <= _EPSILON or abs(position - length) <= _EPSILON


def _external_resultants(
    point_loads: list[PointLoad], distributed_loads: list[DistributedLoad]
) -> list[tuple[float, float]]:
    resultants = [(float(load.force_n), float(load.position_mm)) for load in point_loads]
    resultants.extend(
        (
            float(load.intensity_n_per_mm) * (float(load.end_mm) - float(load.start_mm)),
            (float(load.start_mm) + float(load.end_mm)) / 2.0,
        )
        for load in distributed_loads
    )
    return resultants


def _build_solution(
    problem: BeamProblem,
    reactions: list[Reaction],
    beam_kind: Literal["simply_supported", "cantilever"],
) -> BeamSolution:
    """以 Macaulay 括号构造曲线，并把扩展结果字段附加到 Task 1 的模型。"""
    length = float(problem.length_mm)
    is_right_fixed = beam_kind == "cantilever" and reactions[0].position_mm > 0.0
    canonical_problem, canonical_reactions = _canonical_problem(
        problem, reactions, is_right_fixed
    )
    shear, moment, raw_theta, raw_deflection = _curve_functions(
        canonical_problem, canonical_reactions
    )
    if beam_kind == "simply_supported":
        left, right = sorted(
            (reaction.position_mm for reaction in canonical_reactions),
        )
        c1 = (raw_deflection(left) - raw_deflection(right)) / (right - left)
        c0 = -raw_deflection(left) - c1 * left
    else:
        c0 = 0.0
        c1 = 0.0

    def canonical_deflection(position: float) -> float:
        return raw_deflection(position) + c0 + c1 * position

    def canonical_theta(position: float) -> float:
        return raw_theta(position) + c1

    if is_right_fixed:
        def shear_at(position: float) -> float:
            return -shear(length - position)

        def moment_at(position: float) -> float:
            return moment(length - position)

        def deflection_at(position: float) -> float:
            return canonical_deflection(length - position)

        def theta_at(position: float) -> float:
            return -canonical_theta(length - position)
    else:
        shear_at = shear
        moment_at = moment
        deflection_at = canonical_deflection
        theta_at = canonical_theta

    _validate_query_position(length, 0.0)
    segments = _segments(problem, shear_at, moment_at, deflection_at)
    x_mm = _unique_positions(
        position for segment in segments for position in segment.positions_mm
    )
    deflection_mm = [deflection_at(position) for position in x_mm]
    critical_positions = _critical_positions(length, theta_at, _breakpoints(problem))
    max_position = min(critical_positions, key=deflection_at)
    max_deflection = deflection_at(max_position)

    solution = BeamSolution(
        reactions=reactions,
        segments=segments,
        max_deflection_mm=max_deflection,
        max_deflection_position_mm=max_position,
    )
    # BeamSolution is intentionally a small Task 1 transport model.  These
    # fields are the normalized contract consumed by later textbook modules.
    solution.x_mm = x_mm
    solution.deflection_mm = deflection_mm
    solution.shear_at = _checked_curve(shear_at, length)
    solution.moment_at = _checked_curve(moment_at, length)
    solution.theta_at = _checked_curve(theta_at, length)
    solution.checks = _equilibrium_checks(problem, reactions)
    solution.steps = _steps(problem, reactions, beam_kind)
    solution.warnings = [
        "仅考虑竖向荷载与 Euler–Bernoulli 弯曲；未计算轴向、扭转、剪切变形或大挠度。"
    ]
    solution.method = "analytical"
    return solution


def _canonical_problem(
    problem: BeamProblem,
    reactions: list[Reaction],
    is_right_fixed: bool,
) -> tuple[BeamProblem, list[Reaction]]:
    """右端固定时镜像到左端固定的同一解析坐标系。"""
    if not is_right_fixed:
        return problem, reactions

    length = float(problem.length_mm)
    mirrored_supports = [
        Support(length - support.position_mm, support.kind, support.label)
        for support in problem.supports
    ]
    mirrored_points = [
        PointLoad(length - load.position_mm, load.force_n) for load in problem.point_loads
    ]
    mirrored_udls = [
        DistributedLoad(
            length - load.end_mm,
            length - load.start_mm,
            load.intensity_n_per_mm,
        )
        for load in problem.distributed_loads
    ]
    mirrored_problem = BeamProblem(
        length,
        problem.elastic_modulus_mpa,
        problem.inertia_mm4,
        mirrored_supports,
        mirrored_points,
        mirrored_udls,
    )
    mirrored_reactions = [
        Reaction(
            length - reaction.position_mm,
            reaction.vertical_n,
            -reaction.moment_n_mm,
            reaction.support_kind,
        )
        for reaction in reactions
    ]
    return mirrored_problem, mirrored_reactions


def _curve_functions(
    problem: BeamProblem, reactions: list[Reaction]
) -> tuple[
    Callable[[float], float],
    Callable[[float], float],
    Callable[[float], float],
    Callable[[float], float],
]:
    """返回剪力、弯矩及零积分常数的转角/挠度表达式。"""
    flexural_rigidity = float(problem.elastic_modulus_mpa) * float(problem.inertia_mm4)

    vertical_actions = [
        (reaction.vertical_n, reaction.position_mm) for reaction in reactions
    ] + [(load.force_n, load.position_mm) for load in problem.point_loads]
    distributed_actions = [
        (load.intensity_n_per_mm, load.start_mm, load.end_mm)
        for load in problem.distributed_loads
    ]
    fixed_moments = [
        (reaction.moment_n_mm, reaction.position_mm)
        for reaction in reactions
        if abs(reaction.moment_n_mm) > _EPSILON
    ]

    def shear(position: float) -> float:
        return sum(force for force, at in vertical_actions if position >= at) + sum(
            intensity * max(0.0, min(position, end) - start)
            for intensity, start, end in distributed_actions
        )

    def moment(position: float) -> float:
        return sum(
            force * _bracket(position, at, 1) for force, at in vertical_actions
        ) + sum(
            intensity
            * (_bracket(position, start, 2) - _bracket(position, end, 2))
            / 2.0
            for intensity, start, end in distributed_actions
        ) - sum(
            reaction_moment * _bracket(position, at, 0)
            for reaction_moment, at in fixed_moments
        )

    def raw_theta(position: float) -> float:
        return (
            sum(
                force * _bracket(position, at, 2) / 2.0
                for force, at in vertical_actions
            )
            + sum(
                intensity
                * (_bracket(position, start, 3) - _bracket(position, end, 3))
                / 6.0
                for intensity, start, end in distributed_actions
            )
            - sum(
                reaction_moment * _bracket(position, at, 1)
                for reaction_moment, at in fixed_moments
            )
        ) / flexural_rigidity

    def raw_deflection(position: float) -> float:
        return (
            sum(
                force * _bracket(position, at, 3) / 6.0
                for force, at in vertical_actions
            )
            + sum(
                intensity
                * (_bracket(position, start, 4) - _bracket(position, end, 4))
                / 24.0
                for intensity, start, end in distributed_actions
            )
            - sum(
                reaction_moment * _bracket(position, at, 2) / 2.0
                for reaction_moment, at in fixed_moments
            )
        ) / flexural_rigidity

    return shear, moment, raw_theta, raw_deflection


def _bracket(position: float, start: float, exponent: int) -> float:
    distance = position - start
    if distance < 0.0:
        return 0.0
    return 1.0 if exponent == 0 else distance**exponent


def _segments(
    problem: BeamProblem,
    shear_at: Callable[[float], float],
    moment_at: Callable[[float], float],
    deflection_at: Callable[[float], float],
) -> list[SegmentResult]:
    breakpoints = _breakpoints(problem)
    point_load_positions = {float(load.position_mm) for load in problem.point_loads}
    segments: list[SegmentResult] = []
    for start, end in zip(breakpoints, breakpoints[1:]):
        positions = [start + (end - start) * index / 20.0 for index in range(21)]
        # A point load makes shear discontinuous.  Preserve each adjacent
        # segment's one-sided physical value instead of assigning V(a+) to
        # the segment ending at a.
        if end in point_load_positions:
            positions[-1] = math.nextafter(end, start)
        if start in point_load_positions:
            positions[0] = math.nextafter(start, end)
        segments.append(
            SegmentResult(
                start_mm=start,
                end_mm=end,
                positions_mm=positions,
                shear_n=[shear_at(position) for position in positions],
                bending_moment_n_mm=[moment_at(position) for position in positions],
                deflection_mm=[deflection_at(position) for position in positions],
            )
        )
    return segments


def _breakpoints(problem: BeamProblem) -> list[float]:
    return _unique_positions(
        [0.0, float(problem.length_mm)]
        + [float(support.position_mm) for support in problem.supports]
        + [float(load.position_mm) for load in problem.point_loads]
        + [float(load.start_mm) for load in problem.distributed_loads]
        + [float(load.end_mm) for load in problem.distributed_loads]
    )


def _unique_positions(positions: object) -> list[float]:
    return sorted({float(position) for position in positions})


def _critical_positions(
    length: float,
    theta_at: Callable[[float], float],
    breakpoints: list[float],
) -> list[float]:
    """返回每个荷载/支座分段内的转角零点及所有分段端点。"""
    del length  # 端点由 breakpoints 提供；保留参数以兼容内部调用约定。
    candidates: list[float] = []
    for start, end in zip(breakpoints, breakpoints[1:]):
        candidates.extend((start, end))
        candidates.extend(_theta_roots_in_span(theta_at, start, end))
    return _unique_positions(candidates)


def _theta_roots_in_span(
    theta_at: Callable[[float], float], start: float, end: float
) -> list[float]:
    """利用分段三次转角式的导数分界，可靠定位该段的全部零点。"""
    span = end - start
    if span <= 0.0:
        return []

    values = [theta_at(start + span * fraction) for fraction in (0.0, 1 / 3, 2 / 3, 1.0)]
    a, b, c = _cubic_coefficients(values)
    stationary = _quadratic_roots(3.0 * a, 2.0 * b, c)
    normalized_bounds = [0.0] + [
        root for root in stationary if _EPSILON < root < 1.0 - _EPSILON
    ] + [1.0]
    normalized_bounds.sort()

    roots: list[float] = []
    for lower, upper in zip(normalized_bounds, normalized_bounds[1:]):
        lower_position = start + span * lower
        upper_position = start + span * upper
        lower_value = theta_at(lower_position)
        upper_value = theta_at(upper_position)
        if abs(lower_value) <= _EPSILON:
            roots.append(lower_position)
        if lower_value * upper_value < 0.0:
            roots.append(_bisect_zero(theta_at, lower_position, upper_position))
        if abs(upper_value) <= _EPSILON:
            roots.append(upper_position)
    return _unique_positions(roots)


def _cubic_coefficients(values: list[float]) -> tuple[float, float, float]:
    """由 t=0、1/3、2/3、1 的函数值恢复 a*t³+b*t²+c*t+d。"""
    y1 = 27.0 * (values[1] - values[0])
    y2 = 27.0 * (values[2] - values[0])
    y3 = values[3] - values[0]
    a = (y1 - y2 + 9.0 * y3) / 2.0
    c = (y1 - 3.0 * y3 + 2.0 * a) / 6.0
    b = y3 - a - c
    return a, b, c


def _quadratic_roots(a: float, b: float, c: float) -> list[float]:
    """求至多二次多项式的实根，系数退化时保持稳定。"""
    if abs(a) <= _EPSILON:
        return [] if abs(b) <= _EPSILON else [-c / b]
    discriminant = b * b - 4.0 * a * c
    if discriminant < -_EPSILON:
        return []
    root_discriminant = math.sqrt(max(0.0, discriminant))
    return [(-b - root_discriminant) / (2.0 * a), (-b + root_discriminant) / (2.0 * a)]


def _bisect_zero(
    theta_at: Callable[[float], float], left: float, right: float
) -> float:
    left_value = theta_at(left)
    for _ in range(60):
        middle = (left + right) / 2.0
        middle_value = theta_at(middle)
        if left_value * middle_value <= 0.0:
            right = middle
        else:
            left, left_value = middle, middle_value
    return (left + right) / 2.0


def _checked_curve(
    curve: Callable[[float], float], length: float
) -> Callable[[float], float]:
    def evaluate(position: float) -> float:
        _validate_query_position(length, position)
        return curve(float(position))

    return evaluate


def _validate_query_position(length: float, position: float) -> None:
    if not 0.0 <= float(position) <= length:
        raise ProblemInputError("查询位置必须位于梁长范围内。")


def _equilibrium_checks(problem: BeamProblem, reactions: list[Reaction]) -> dict[str, float]:
    forces_and_positions = _external_resultants(
        problem.point_loads, problem.distributed_loads
    ) + [(reaction.vertical_n, reaction.position_mm) for reaction in reactions]
    return {
        "sum_vertical_n": sum(force for force, _ in forces_and_positions),
        "sum_moment_about_0_n_mm": sum(
            force * position for force, position in forces_and_positions
        )
        + sum(reaction.moment_n_mm for reaction in reactions),
    }


def _steps(
    problem: BeamProblem, reactions: list[Reaction], beam_kind: str
) -> list[str]:
    support_text = ", ".join(
        f"x={reaction.position_mm:g} mm: R={reaction.vertical_n:g} N, M={reaction.moment_n_mm:g} N·mm"
        for reaction in reactions
    )
    boundary = (
        "边界条件：两支座处 v=0。"
        if beam_kind == "simply_supported"
        else "边界条件：固定端 v=0、theta=0。"
    )
    return [
        "符号约定：向上力为正、向下力为负；向下挠度为负。",
        "整体平衡：ΣFy=0，ΣM=0；均布荷载以 q·(x2-x1) 作用于中点。",
        f"反力代入：{support_text}",
        boundary,
        f"EI={problem.elastic_modulus_mpa:g}×{problem.inertia_mm4:g} N·mm²。",
    ]
