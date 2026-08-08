"""一维 Euler–Bernoulli 梁有限元求解器（mm、N、MPa 制）。"""

from __future__ import annotations

from collections.abc import Callable
import math

import numpy as np

from mechanics.textbook_models import (
    BeamProblem,
    BeamSolution,
    ProblemClassification,
    ProblemInputError,
    Reaction,
    SegmentResult,
    build_diagram_data,
)


_SOLVE_ERROR = "机构或约束不足，刚度矩阵不可解"
_EPSILON = 1e-9


def solve_fem(problem: BeamProblem, max_elements: int = 200) -> BeamSolution:
    """解任意竖向荷载下的等截面 Euler–Bernoulli 梁。

    节点自由度按 ``[v, theta]`` 排列，位移向上为正、转角为位移对
    坐标的一阶导数。所有荷载边界都成为节点，因此集中力和均布荷载
    的一致节点荷载可无歧义地装配。
    """
    problem.validate()
    coordinates = _build_mesh(problem, max_elements)
    element_count = len(coordinates) - 1
    dof_count = 2 * len(coordinates)
    stiffness = np.zeros((dof_count, dof_count), dtype=float)
    load_vector = np.zeros(dof_count, dtype=float)
    rigidity = float(problem.elastic_modulus_mpa) * float(problem.inertia_mm4)

    for element, (start, end) in enumerate(zip(coordinates, coordinates[1:])):
        length = end - start
        dofs = _element_dofs(element)
        element_stiffness = _element_stiffness(rigidity, length)
        stiffness[np.ix_(dofs, dofs)] += element_stiffness
        intensity = _intensity_on_element(problem, start, end)
        load_vector[dofs] += _uniform_load_vector(intensity, length)

    index_by_position = {position: index for index, position in enumerate(coordinates)}
    for point_load in problem.point_loads:
        node = index_by_position[float(point_load.position_mm)]
        load_vector[2 * node] += float(point_load.force_n)

    constrained = _constrained_dofs(problem, index_by_position)
    displacement = _solve_reduced_system(
        stiffness, load_vector, constrained, float(problem.length_mm)
    )
    residual = stiffness @ displacement - load_vector
    reactions = _reactions(problem, index_by_position, residual)
    segments = _segments(
        coordinates, displacement, rigidity, problem, stiffness, load_vector
    )
    sampled_positions, sampled_deflections = _deflection_samples(
        coordinates, displacement
    )
    max_index = int(np.argmax(np.abs(sampled_deflections)))

    def deflection_at(position: float) -> float:
        element, xi = _locate_element(coordinates, position)
        return float(_shape_functions(xi, coordinates[element + 1] - coordinates[element]) @ displacement[_element_dofs(element)])

    def theta_at(position: float) -> float:
        element, xi = _locate_element(coordinates, position)
        length = coordinates[element + 1] - coordinates[element]
        return float(_shape_derivatives(xi, length) @ displacement[_element_dofs(element)])

    shear_at, moment_at = _section_resultants(
        coordinates, displacement, rigidity, problem, stiffness, load_vector
    )
    (
        max_shear,
        max_shear_position,
        max_moment,
        max_moment_position,
    ) = _curve_extrema(
        coordinates, problem, shear_at, moment_at
    )
    element_lengths = [end - start for start, end in zip(coordinates, coordinates[1:])]
    nodal_displacements = displacement[::2].tolist()
    nodal_rotations = displacement[1::2].tolist()
    return BeamSolution(
        method="fem",
        classification=_fem_classification(problem),
        x_mm=coordinates,
        deflection_mm=nodal_displacements,
        reactions=reactions,
        segments=segments,
        max_deflection_mm=float(sampled_deflections[max_index]),
        max_deflection_position_mm=float(sampled_positions[max_index]),
        shear_segments=segments,
        moment_segments=segments,
        checks=_equilibrium_checks(problem, reactions),
        steps=[
            "符号约定：向上力为正、向下挠度为负。",
            "每节点自由度为 [v, theta]，采用两节点 Euler–Bernoulli 梁单元。",
            f"网格：{len(coordinates)} 个节点、{element_count} 个单元。",
            "支座反力由 K @ u - F 恢复。",
        ],
        warnings=[
            "有限元采用 Euler–Bernoulli 梁：未考虑轴向、扭转、剪切变形或大挠度。"
        ],
        metadata={
            "node_count": len(coordinates),
            "element_count": element_count,
            "mesh": {
                "node_count": len(coordinates),
                "element_count": element_count,
                "minimum_element_length_mm": min(element_lengths),
                "maximum_element_length_mm": max(element_lengths),
                "load_and_support_boundaries_preserved": True,
            },
            "accuracy": {
                "model": "两节点 Euler–Bernoulli 梁单元",
                "description": "位移采用三次插值；结果精度受网格密度影响，可增加单元数作收敛校核。",
            },
        },
        node_positions_mm=coordinates,
        displacements_mm=nodal_displacements,
        rotations_rad=nodal_rotations,
        deflection_at=deflection_at,
        theta_at=theta_at,
        shear_at=shear_at,
        moment_at=moment_at,
        max_shear=max_shear,
        max_shear_position=max_shear_position,
        max_moment=max_moment,
        max_moment_position=max_moment_position,
        diagram_data=build_diagram_data(problem, reactions),
    )


def _build_mesh(problem: BeamProblem, max_elements: int) -> list[float]:
    if isinstance(max_elements, bool) or not isinstance(max_elements, int) or max_elements < 1:
        raise ProblemInputError("max_elements 必须是正整数。")
    required = sorted(
        {
            0.0,
            float(problem.length_mm),
            *(float(support.position_mm) for support in problem.supports),
            *(float(load.position_mm) for load in problem.point_loads),
            *(float(load.start_mm) for load in problem.distributed_loads),
            *(float(load.end_mm) for load in problem.distributed_loads),
        }
    )
    spans = [right - left for left, right in zip(required, required[1:])]
    if len(spans) > max_elements:
        raise ProblemInputError("max_elements 小于保留全部荷载和支座节点所需的单元数。")

    extra = max_elements - len(spans)
    total_length = float(problem.length_mm)
    ideal_extra = [extra * span / total_length for span in spans]
    counts = [1 + math.floor(value) for value in ideal_extra]
    remaining = max_elements - sum(counts)
    for index in sorted(
        range(len(spans)), key=lambda item: ideal_extra[item] % 1.0, reverse=True
    )[:remaining]:
        counts[index] += 1

    coordinates = [required[0]]
    for left, right, count in zip(required, required[1:], counts):
        coordinates.extend(left + (right - left) * item / count for item in range(1, count))
        coordinates.append(right)
    return coordinates


def _element_dofs(element: int) -> list[int]:
    return [2 * element, 2 * element + 1, 2 * element + 2, 2 * element + 3]


def _element_stiffness(rigidity: float, length: float) -> np.ndarray:
    base = np.array(
        [
            [12.0, 6.0 * length, -12.0, 6.0 * length],
            [6.0 * length, 4.0 * length**2, -6.0 * length, 2.0 * length**2],
            [-12.0, -6.0 * length, 12.0, -6.0 * length],
            [6.0 * length, 2.0 * length**2, -6.0 * length, 4.0 * length**2],
        ]
    )
    return rigidity / length**3 * base


def _uniform_load_vector(intensity: float, length: float) -> np.ndarray:
    return intensity * length / 2.0 * np.array(
        [1.0, length / 6.0, 1.0, -length / 6.0]
    )


def _intensity_on_element(problem: BeamProblem, start: float, end: float) -> float:
    midpoint = (start + end) / 2.0
    return sum(
        float(load.intensity_n_per_mm)
        for load in problem.distributed_loads
        if float(load.start_mm) < midpoint < float(load.end_mm)
    )


def _constrained_dofs(problem: BeamProblem, index_by_position: dict[float, int]) -> list[int]:
    constrained: list[int] = []
    for support in problem.supports:
        node = index_by_position[float(support.position_mm)]
        if support.kind in {"pin", "roller", "fixed"}:
            constrained.append(2 * node)
        if support.kind == "fixed":
            constrained.append(2 * node + 1)
    return sorted(constrained)


def _solve_reduced_system(
    stiffness: np.ndarray,
    load_vector: np.ndarray,
    constrained: list[int],
    characteristic_length: float,
) -> np.ndarray:
    all_dofs = np.arange(len(load_vector))
    free = np.setdiff1d(all_dofs, constrained)
    displacement = np.zeros_like(load_vector)
    if not len(free):
        return displacement
    reduced_stiffness = stiffness[np.ix_(free, free)]
    if np.linalg.matrix_rank(reduced_stiffness) == len(free):
        try:
            displacement[free] = np.linalg.solve(
                reduced_stiffness, load_vector[free]
            )
            return displacement
        except np.linalg.LinAlgError as error:
            raise ProblemInputError(_SOLVE_ERROR) from error

    dof_scale = np.ones(len(load_vector))
    dof_scale[1::2] = 1.0 / characteristic_length
    reduced_scale = dof_scale[free]
    scaled_stiffness = reduced_scale[:, None] * reduced_stiffness * reduced_scale
    if np.linalg.matrix_rank(scaled_stiffness) != len(free):
        raise ProblemInputError(_SOLVE_ERROR)
    try:
        scaled_displacement = np.linalg.solve(
            scaled_stiffness, reduced_scale * load_vector[free]
        )
        displacement[free] = reduced_scale * scaled_displacement
    except np.linalg.LinAlgError as error:
        raise ProblemInputError(_SOLVE_ERROR) from error
    return displacement


def _reactions(
    problem: BeamProblem, index_by_position: dict[float, int], residual: np.ndarray
) -> list[Reaction]:
    reactions: list[Reaction] = []
    for support in problem.supports:
        if support.kind == "free":
            continue
        node = index_by_position[float(support.position_mm)]
        reactions.append(
            Reaction(
                float(support.position_mm),
                float(residual[2 * node]),
                float(residual[2 * node + 1]) if support.kind == "fixed" else 0.0,
                support.kind,
            )
        )
    return reactions


def _segments(
    coordinates: list[float],
    displacement: np.ndarray,
    rigidity: float,
    problem: BeamProblem,
    stiffness: np.ndarray,
    load_vector: np.ndarray,
) -> list[SegmentResult]:
    shear_at, moment_at = _section_resultants(
        coordinates, displacement, rigidity, problem, stiffness, load_vector
    )
    segments: list[SegmentResult] = []
    for element, (start, end) in enumerate(zip(coordinates, coordinates[1:])):
        positions = [start, (start + end) / 2.0, end]
        if element:
            positions[0] = math.nextafter(start, end)
        if element < len(coordinates) - 2:
            positions[-1] = math.nextafter(end, start)
        segments.append(
            SegmentResult(
                start_mm=start,
                end_mm=end,
                positions_mm=positions,
                shear_n=[shear_at(position) for position in positions],
                bending_moment_n_mm=[moment_at(position) for position in positions],
                deflection_mm=[
                    float(
                        _shape_functions(
                            (position - start) / (end - start), end - start
                        )
                        @ displacement[_element_dofs(element)]
                    )
                    for position in positions
                ],
                shear_expression="数值采样（FEM）",
                moment_expression="数值采样（FEM）",
            )
        )
    return segments


def _fem_classification(problem: BeamProblem) -> ProblemClassification:
    reaction_components = sum(
        2 if support.kind == "fixed" else 1
        for support in problem.supports
        if support.kind != "free"
    )
    category = "超静定（数值解）" if reaction_components > 2 else "静定"
    return ProblemClassification(category, "fem")


def _curve_extrema(
    coordinates: list[float],
    problem: BeamProblem,
    shear_at: Callable[[float], float],
    moment_at: Callable[[float], float],
) -> tuple[float, float, float, float]:
    """比较每个单元的单侧端点，并在 V=0 处比较弯矩。"""
    shear_candidates: list[tuple[float, float]] = []
    moment_candidates: list[tuple[float, float]] = []
    for start, end in zip(coordinates, coordinates[1:]):
        start_query = math.nextafter(start, end)
        end_query = math.nextafter(end, start)
        shear_start = shear_at(start_query)
        shear_candidates.extend(
            [(shear_start, start), (shear_at(end_query), end)]
        )
        moment_candidates.extend(
            [(moment_at(start_query), start), (moment_at(end_query), end)]
        )
        intensity = _intensity_on_element(problem, start, end)
        if abs(intensity) > _EPSILON:
            stationary = start - shear_start / intensity
            if start < stationary < end:
                moment_candidates.append((moment_at(stationary), stationary))

    max_shear, max_shear_position = max(
        shear_candidates, key=lambda item: abs(item[0]), default=(0.0, 0.0)
    )
    max_moment, max_moment_position = max(
        moment_candidates, key=lambda item: abs(item[0]), default=(0.0, 0.0)
    )
    return max_shear, max_shear_position, max_moment, max_moment_position


def _deflection_samples(
    coordinates: list[float], displacement: np.ndarray
) -> tuple[list[float], list[float]]:
    positions: list[float] = []
    values: list[float] = []
    for element, (start, end) in enumerate(zip(coordinates, coordinates[1:])):
        length = end - start
        for fraction in range(11):
            if element and fraction == 0:
                continue
            xi = fraction / 10.0
            positions.append(start + xi * length)
            values.append(float(_shape_functions(xi, length) @ displacement[_element_dofs(element)]))
    return positions, values


def _shape_functions(xi: float, length: float) -> np.ndarray:
    return np.array(
        [
            1.0 - 3.0 * xi**2 + 2.0 * xi**3,
            length * (xi - 2.0 * xi**2 + xi**3),
            3.0 * xi**2 - 2.0 * xi**3,
            length * (-xi**2 + xi**3),
        ]
    )


def _shape_derivatives(xi: float, length: float) -> np.ndarray:
    return np.array(
        [
            (-6.0 * xi + 6.0 * xi**2) / length,
            1.0 - 4.0 * xi + 3.0 * xi**2,
            (6.0 * xi - 6.0 * xi**2) / length,
            -2.0 * xi + 3.0 * xi**2,
        ]
    )


def _section_resultants(
    coordinates: list[float],
    displacement: np.ndarray,
    rigidity: float,
    problem: BeamProblem,
    stiffness: np.ndarray,
    load_vector: np.ndarray,
) -> tuple[Callable[[float], float], Callable[[float], float]]:
    del stiffness, load_vector  # 结果量由位移场及本单元均布荷载恢复。

    def shear_at(position: float) -> float:
        element, xi = _locate_element(coordinates, position)
        length = coordinates[element + 1] - coordinates[element]
        local_position = xi * length
        intensity = _intensity_on_element(
            problem, coordinates[element], coordinates[element + 1]
        )
        derivatives = np.array([12.0 / length**3, 6.0 / length**2, -12.0 / length**3, 6.0 / length**2])
        homogeneous = rigidity * derivatives @ displacement[_element_dofs(element)]
        return float(homogeneous + intensity * (local_position - length / 2.0))

    def moment_at(position: float) -> float:
        element, xi = _locate_element(coordinates, position)
        length = coordinates[element + 1] - coordinates[element]
        local_position = xi * length
        intensity = _intensity_on_element(
            problem, coordinates[element], coordinates[element + 1]
        )
        derivatives = np.array(
            [
                (-6.0 + 12.0 * xi) / length**2,
                (-4.0 + 6.0 * xi) / length,
                (6.0 - 12.0 * xi) / length**2,
                (-2.0 + 6.0 * xi) / length,
            ]
        )
        homogeneous = rigidity * derivatives @ displacement[_element_dofs(element)]
        load_particular = intensity * (
            local_position**2 / 2.0
            - length * local_position / 2.0
            + length**2 / 12.0
        )
        return float(homogeneous + load_particular)

    return shear_at, moment_at


def _locate_element(coordinates: list[float], position: float) -> tuple[int, float]:
    value = float(position)
    if not 0.0 <= value <= coordinates[-1]:
        raise ProblemInputError("查询位置必须位于梁长范围内。")
    if value == coordinates[-1]:
        return len(coordinates) - 2, 1.0
    index = int(np.searchsorted(coordinates, value, side="right") - 1)
    length = coordinates[index + 1] - coordinates[index]
    return index, (value - coordinates[index]) / length


def _equilibrium_checks(problem: BeamProblem, reactions: list[Reaction]) -> dict[str, float]:
    forces = [(float(load.force_n), float(load.position_mm)) for load in problem.point_loads]
    forces.extend(
        (
            float(load.intensity_n_per_mm) * (float(load.end_mm) - float(load.start_mm)),
            (float(load.start_mm) + float(load.end_mm)) / 2.0,
        )
        for load in problem.distributed_loads
    )
    forces.extend((reaction.vertical_n, reaction.position_mm) for reaction in reactions)
    vertical = math.fsum(force for force, _ in forces)
    moment = math.fsum(force * position for force, position in forces) + math.fsum(
        reaction.moment_n_mm for reaction in reactions
    )
    vertical_scale = math.fsum(abs(force) for force, _ in forces)
    moment_scale = math.fsum(abs(force * position) for force, position in forces) + math.fsum(
        abs(reaction.moment_n_mm) for reaction in reactions
    )
    return {
        "sum_vertical_n": _normalize_equilibrium_residual(vertical, vertical_scale),
        "sum_moment_about_0_n_mm": _normalize_equilibrium_residual(moment, moment_scale),
    }


def _normalize_equilibrium_residual(value: float, scale: float) -> float:
    """Suppress solver round-off while preserving physically meaningful imbalance."""
    return 0.0 if abs(value) <= 1e-9 * max(1.0, scale) else value
