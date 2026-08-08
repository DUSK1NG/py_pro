"""教材梁题求解器使用的独立数据模型（内部单位：mm、N、MPa、mm⁴）。"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Literal


SupportKind = Literal["fixed", "pin", "roller", "free"]
_SUPPORT_KINDS = frozenset({"fixed", "pin", "roller", "free"})


class ProblemInputError(ValueError):
    """梁问题的几何、材料或荷载输入不合法。"""


@dataclass
class Support:
    position_mm: float
    kind: SupportKind
    label: str = ""


@dataclass
class PointLoad:
    position_mm: float
    force_n: float


@dataclass
class DistributedLoad:
    start_mm: float
    end_mm: float
    intensity_n_per_mm: float


@dataclass
class Reaction:
    position_mm: float
    vertical_n: float
    moment_n_mm: float
    support_kind: SupportKind


@dataclass
class SegmentResult:
    start_mm: float
    end_mm: float
    positions_mm: list[float] = field(default_factory=list)
    shear_n: list[float] = field(default_factory=list)
    bending_moment_n_mm: list[float] = field(default_factory=list)
    deflection_mm: list[float] = field(default_factory=list)


@dataclass
class BeamSolution:
    reactions: list[Reaction] = field(default_factory=list)
    segments: list[SegmentResult] = field(default_factory=list)
    max_deflection_mm: float = 0.0
    max_deflection_position_mm: float = 0.0


@dataclass
class BeamProblem:
    length_mm: float
    elastic_modulus_mpa: float
    inertia_mm4: float
    supports: list[Support]
    point_loads: list[PointLoad] = field(default_factory=list)
    distributed_loads: list[DistributedLoad] = field(default_factory=list)

    def validate(self) -> None:
        """验证求解范围内的梁、支座和竖向荷载输入。"""
        length = _positive_finite(self.length_mm, "梁长 L")
        _positive_finite(self.elastic_modulus_mpa, "弹性模量 E")
        _positive_finite(self.inertia_mm4, "截面惯性矩 I")

        if not self.supports:
            raise ProblemInputError("至少需要一个支座。")

        support_positions: set[float] = set()
        for support in self.supports:
            if support.kind not in _SUPPORT_KINDS:
                raise ProblemInputError(f"不支持的支座类型：{support.kind}。")
            position = _finite_float(support.position_mm, "支座位置")
            _validate_position(position, length, "支座位置")
            if position in support_positions:
                raise ProblemInputError("支座位置不能重复。")
            support_positions.add(position)

        for load in self.point_loads:
            _validate_position(
                _finite_float(load.position_mm, "集中力位置"), length, "集中力位置"
            )
            _finite_float(load.force_n, "集中力")

        for load in self.distributed_loads:
            start = _finite_float(load.start_mm, "均布荷载起点")
            end = _finite_float(load.end_mm, "均布荷载终点")
            _validate_position(start, length, "均布荷载起点")
            _validate_position(end, length, "均布荷载终点")
            if start >= end:
                raise ProblemInputError("均布荷载起点必须小于终点。")
            _finite_float(load.intensity_n_per_mm, "均布荷载强度")

    def total_vertical_load_n(self) -> float:
        """返回所有竖向荷载的代数和；向上为正，向下为负。"""
        self.validate()
        point_total = sum(float(load.force_n) for load in self.point_loads)
        distributed_total = sum(
            float(load.intensity_n_per_mm) * (float(load.end_mm) - float(load.start_mm))
            for load in self.distributed_loads
        )
        return point_total + distributed_total


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProblemInputError(f"{name}必须是有限数值。")
    number = float(value)
    if not math.isfinite(number):
        raise ProblemInputError(f"{name}必须是有限数值。")
    return number


def _positive_finite(value: object, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0:
        raise ProblemInputError(f"{name}必须大于零。")
    return number


def _validate_position(position: float, length: float, name: str) -> None:
    if not 0 <= position <= length:
        raise ProblemInputError(f"{name}必须位于梁长范围内。")
