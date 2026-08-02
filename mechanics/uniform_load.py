"""满跨均布荷载作用下简支梁的力学计算。"""

from utils.validation import (
    validate_position,
    validate_positive_finite,
    validate_sample_count,
)


def support_reactions(length: object, load_intensity: object) -> tuple[float, float]:
    """计算满跨均布荷载的左右支座反力（N）。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_intensity = validate_positive_finite(load_intensity, "均布荷载 q")
    reaction = checked_intensity * checked_length / 2
    return reaction, reaction


def shear_force(x: object, length: object, load_intensity: object) -> float:
    """计算位置 x 的剪力（N）。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    checked_intensity = validate_positive_finite(load_intensity, "均布荷载 q")
    return checked_intensity * checked_length / 2 - checked_intensity * checked_x


def bending_moment(x: object, length: object, load_intensity: object) -> float:
    """计算位置 x 的正弯矩（N·mm）。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    checked_intensity = validate_positive_finite(load_intensity, "均布荷载 q")
    return checked_intensity * checked_x * (checked_length - checked_x) / 2


def deflection(
    x: object,
    length: object,
    load_intensity: object,
    elastic_modulus: object,
    inertia_moment: object,
) -> float:
    """计算理论挠度（mm）；向下为负。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    checked_intensity = validate_positive_finite(load_intensity, "均布荷载 q")
    checked_modulus = validate_positive_finite(elastic_modulus, "弹性模量 E")
    checked_inertia = validate_positive_finite(inertia_moment, "截面惯性矩 I")
    numerator = -checked_intensity * checked_x * (
        checked_length**3 - 2 * checked_length * checked_x**2 + checked_x**3
    )
    return numerator / (24 * checked_modulus * checked_inertia)


def sample_beam(
    length: object,
    load_intensity: object,
    elastic_modulus: object,
    inertia_moment: object,
    sample_count: object = 101,
) -> dict[str, object]:
    """采样满跨均布荷载简支梁，并汇总跨中理论极值。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_intensity = validate_positive_finite(load_intensity, "均布荷载 q")
    checked_modulus = validate_positive_finite(elastic_modulus, "弹性模量 E")
    checked_inertia = validate_positive_finite(inertia_moment, "截面惯性矩 I")
    checked_count = validate_sample_count(sample_count)
    positions = [checked_length * index / (checked_count - 1) for index in range(checked_count)]
    shears = [shear_force(x, checked_length, checked_intensity) for x in positions]
    moments = [bending_moment(x, checked_length, checked_intensity) for x in positions]
    deflections = [deflection(x, checked_length, checked_intensity, checked_modulus, checked_inertia) for x in positions]
    midspan = checked_length / 2
    maximum_deflection = deflection(midspan, checked_length, checked_intensity, checked_modulus, checked_inertia)
    left_reaction, right_reaction = support_reactions(checked_length, checked_intensity)
    return {"left_reaction": left_reaction, "right_reaction": right_reaction, "x": positions, "shear": shears, "moment": moments, "deflection": deflections, "max_shear": checked_intensity * checked_length / 2, "max_moment": checked_intensity * checked_length**2 / 8, "max_moment_position": midspan, "max_deflection": maximum_deflection, "max_deflection_magnitude": abs(maximum_deflection), "max_deflection_position": midspan}
