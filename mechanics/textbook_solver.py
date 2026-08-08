"""教材梁题的统一求解入口。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from mechanics.analytical_beam import (
    solve_cantilever,
    solve_simply_supported,
)
from mechanics.beam_fem import solve_fem
from mechanics.textbook_models import BeamProblem, BeamSolution, ProblemInputError


ClassificationCategory = Literal["静定", "超静定（数值解）", "机构/约束不足"]
SolverMethod = Literal["analytical", "fem"]


@dataclass(frozen=True)
class ProblemClassification:
    """梁的静定性及应采用的求解方法。"""

    category: ClassificationCategory
    method: SolverMethod

    @property
    def status(self) -> ClassificationCategory:
        """分类文字的同义访问器，便于展示层直接使用。"""
        return self.category


def classify_problem(problem: BeamProblem) -> ProblemClassification:
    """验证输入后，按竖向弯曲自由度判定静定性和求解分支。"""
    problem.validate()
    reaction_components = sum(
        2 if support.kind == "fixed" else 1
        for support in problem.supports
        if support.kind != "free"
    )

    if reaction_components < 2:
        return ProblemClassification("机构/约束不足", "fem")
    if reaction_components > 2:
        return ProblemClassification("超静定（数值解）", "fem")
    if _supports_dispatch_analytically(problem):
        return ProblemClassification("静定", "analytical")
    return ProblemClassification("静定", "fem")


def _supports_dispatch_analytically(problem: BeamProblem) -> bool:
    """仅允许公共入口承诺的两种标准教材解析构型。"""
    supports = problem.supports
    pins = [support for support in supports if support.kind == "pin"]
    rollers = [support for support in supports if support.kind == "roller"]
    if len(pins) == len(rollers) == 1:
        return (
            pins[0].position_mm == 0
            and rollers[0].position_mm == problem.length_mm
            and all(support.kind in {"pin", "roller", "free"} for support in supports)
        )

    fixed = [support for support in supports if support.kind == "fixed"]
    return (
        len(fixed) == 1
        and fixed[0].position_mm in {0, problem.length_mm}
        and all(support.kind in {"fixed", "free"} for support in supports)
    )


def solve_textbook_beam(problem: BeamProblem) -> BeamSolution:
    """求解教材梁题并补齐跨解析/FEM 一致的结果字段。"""
    problem.validate()
    classification = classify_problem(problem)
    if classification.category == "机构/约束不足":
        raise ProblemInputError("机构或约束不足，无法建立稳定的梁模型。")

    if classification.method == "analytical":
        solver = (
            solve_cantilever
            if any(support.kind == "fixed" for support in problem.supports)
            else solve_simply_supported
        )
        result = _solve_with_input_error("解析", solver, problem)
    else:
        result = _solve_with_input_error("有限元", solve_fem, problem)
    return _normalize_result(result, classification)


def _solve_with_input_error(
    solver_name: str,
    solver: Callable[[BeamProblem], BeamSolution],
    problem: BeamProblem,
) -> BeamSolution:
    try:
        return solver(problem)
    except ProblemInputError as error:
        raise ProblemInputError(f"{solver_name}求解失败：{error}") from error
    except Exception as error:
        raise ProblemInputError(f"{solver_name}求解失败：{error}") from error


def _normalize_result(
    result: BeamSolution, classification: ProblemClassification
) -> BeamSolution:
    """把两个底层求解器的传输模型补齐为公共结果契约。"""
    result.method = classification.method
    result.classification = classification
    result.shear_segments = result.segments
    result.moment_segments = result.segments
    metadata = dict(getattr(result, "metadata", {}))
    metadata.update(
        {
            "method": classification.method,
            "classification": classification.category,
            "units": {"length": "mm", "force": "N", "modulus": "MPa", "inertia": "mm^4"},
            "deflection_sign": "向下为负",
        }
    )
    result.metadata = metadata
    return result
