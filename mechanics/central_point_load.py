"""跨中集中力作用下简支梁的基础力学计算。"""

from utils.validation import (
    validate_position,
    validate_positive_finite,
    validate_sample_count,
)


def support_reactions(length: object, load: object) -> tuple[float, float]:
    """计算左、右支座反力（N）。"""
    validate_positive_finite(length, "梁长 L")
    checked_load = validate_positive_finite(load, "集中力 P")
    reaction = checked_load / 2
    return reaction, reaction


def shear_force(x: object, length: object, load: object) -> float:
    """计算位置 x 的剪力（N）；跨中返回左极限值。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    left_reaction, _ = support_reactions(checked_length, load)
    return left_reaction if checked_x <= checked_length / 2 else -left_reaction


def bending_moment(x: object, length: object, load: object) -> float:
    """计算位置 x 的正弯矩（N·mm）。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")

    if checked_x <= checked_length / 2:
        return checked_load * checked_x / 2
    return checked_load * (checked_length - checked_x) / 2


def deflection(
    x: object,
    length: object,
    load: object,
    elastic_modulus: object,
    inertia_moment: object,
) -> float:
    """计算理论挠度（mm）；向下挠度为负。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")
    checked_modulus = validate_positive_finite(elastic_modulus, "弹性模量 E")
    checked_inertia = validate_positive_finite(inertia_moment, "截面惯性矩 I")

    distance = min(checked_x, checked_length - checked_x)
    return (
        -checked_load * distance * (3 * checked_length**2 - 4 * distance**2)
        / (48 * checked_modulus * checked_inertia)
    )


def sample_beam(
    length: object,
    load: object,
    elastic_modulus: object,
    inertia_moment: object,
    sample_count: object = 101,
) -> dict[str, object]:
    """等间距采样梁上的理论结果，并返回最大值及其位置。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_load = validate_positive_finite(load, "集中力 P")
    checked_modulus = validate_positive_finite(elastic_modulus, "弹性模量 E")
    checked_inertia = validate_positive_finite(inertia_moment, "截面惯性矩 I")
    checked_count = validate_sample_count(sample_count)

    positions = [
        checked_length * index / (checked_count - 1)
        for index in range(checked_count)
    ]
    shears = [shear_force(x, checked_length, checked_load) for x in positions]
    moments = [bending_moment(x, checked_length, checked_load) for x in positions]
    deflections = [
        deflection(x, checked_length, checked_load, checked_modulus, checked_inertia)
        for x in positions
    ]

    midspan = checked_length / 2
    maximum_deflection = deflection(
        midspan,
        checked_length,
        checked_load,
        checked_modulus,
        checked_inertia,
    )

    return {
        "x": positions,
        "shear": shears,
        "moment": moments,
        "deflection": deflections,
        "max_shear": checked_load / 2,
        "max_moment": checked_load * checked_length / 4,
        "max_moment_position": midspan,
        "max_deflection": maximum_deflection,
        "max_deflection_magnitude": abs(maximum_deflection),
        "max_deflection_position": midspan,
    }
  
