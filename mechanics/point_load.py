"""任意内部位置集中力作用下简支梁的力学计算。"""

from utils.validation import validate_position, validate_positive_finite


def _validate_load_position(position: object, length: object) -> tuple[float, float]:
    """验证荷载位置 a 严格位于两个支座之间。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_position = validate_position(position, checked_length)
    if checked_position == 0 or checked_position == checked_length:
        raise ValueError("荷载位置 a 必须满足 0 < a < L。")
    return checked_length, checked_position


def support_reactions(
    length: object, load: object, position: object
) -> tuple[float, float]:
    """计算位置 a 的向下集中力产生的左右支座反力（N）。"""
    checked_length, checked_position = _validate_load_position(position, length)
    checked_load = validate_positive_finite(load, "集中力 P")
    left_reaction = checked_load * (checked_length - checked_position) / checked_length
    right_reaction = checked_load * checked_position / checked_length
    return left_reaction, right_reaction


def shear_force(x: object, length: object, load: object, position: object) -> float:
    """计算位置 x 的剪力（N）；荷载点采用左极限。"""
    checked_length, checked_position = _validate_load_position(position, length)
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")
    left_reaction, _ = support_reactions(checked_length, checked_load, checked_position)
    return left_reaction if checked_x <= checked_position else left_reaction - checked_load


def bending_moment(x: object, length: object, load: object, position: object) -> float:
    """计算位置 x 的正弯矩（N·mm）。"""
    checked_length, checked_position = _validate_load_position(position, length)
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")
    left_reaction, _ = support_reactions(checked_length, checked_load, checked_position)
    if checked_x <= checked_position:
        return left_reaction * checked_x
    return left_reaction * checked_x - checked_load * (checked_x - checked_position)

def deflection(
    x: object,
    length: object,
    load: object,
    position: object,
    elastic_modulus: object,
    inertia_moment: object,
) -> float:
    """计算任意位置集中力下位置 x 的理论挠度（mm）。"""
    checked_length, checked_position = _validate_load_position(position, length)
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")
    checked_modulus = validate_positive_finite(elastic_modulus, "弹性模量 E")
    checked_inertia = validate_positive_finite(inertia_moment, "截面惯性矩 I")
    opposite_distance = checked_length - checked_position

    if checked_x <= checked_position:
        numerator = -checked_load * opposite_distance * checked_x * (
            checked_length**2 - opposite_distance**2 - checked_x**2
        )
    else:
        right_distance = checked_length - checked_x
        numerator = -checked_load * checked_position * right_distance * (
            checked_length**2 - checked_position**2 - right_distance**2
        )

    return numerator / (6 * checked_length * checked_modulus * checked_inertia)


def sample_beam(
    length: object,
    load: object,
    position: object,
    elastic_modulus: object,
    inertia_moment: object,
    sample_count: object = 101,
) -> dict[str, object]:
    """采样任意位置集中力简支梁，并汇总理论极值。"""
    from utils.validation import validate_sample_count

    checked_length, checked_position = _validate_load_position(position, length)
    checked_load = validate_positive_finite(load, "集中力 P")
    checked_modulus = validate_positive_finite(elastic_modulus, "弹性模量 E")
    checked_inertia = validate_positive_finite(inertia_moment, "截面惯性矩 I")
    checked_count = validate_sample_count(sample_count)

    positions = [
        checked_length * index / (checked_count - 1)
        for index in range(checked_count)
    ]
    positions = sorted(set(positions + [checked_position]))

    shears = [
        shear_force(x, checked_length, checked_load, checked_position)
        for x in positions
    ]
    moments = [
        bending_moment(x, checked_length, checked_load, checked_position)
        for x in positions
    ]
    deflections = [
        deflection(
            x,
            checked_length,
            checked_load,
            checked_position,
            checked_modulus,
            checked_inertia,
        )
        for x in positions
    ]
    max_deflection_index = min(
        range(len(deflections)), key=lambda index: deflections[index]
    )

    return {
        "x": positions,
        "shear": shears,
        "moment": moments,
        "deflection": deflections,
        "max_shear": max(abs(value) for value in shears),
        "max_moment": (
            checked_load
            * checked_position
            * (checked_length - checked_position)
            / checked_length
        ),
        "max_moment_position": checked_position,
        "max_deflection": deflections[max_deflection_index],
        "max_deflection_magnitude": abs(deflections[max_deflection_index]),
        "max_deflection_position": positions[max_deflection_index],
    }