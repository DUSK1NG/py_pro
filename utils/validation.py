"""第一阶段使用的输入参数校验函数。"""

import math


def validate_positive_finite(value: object, name: str) -> float:
    """验证 value 为有限正数，并返回 float 类型结果。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}必须是有限正数。")

    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name}必须是有限正数。")

    return number


def validate_position(position: object, length: object) -> float:
    """验证位置 x 位于梁的范围 [0, L] 内。"""
    checked_length = validate_positive_finite(length, "梁长 L")
    if isinstance(position, bool) or not isinstance(position, (int, float)):
        raise ValueError("位置 x 必须是有限数值。")

    checked_position = float(position)
    if not math.isfinite(checked_position) or not 0 <= checked_position <= checked_length:
        raise ValueError("位置 x 必须位于梁长范围 [0, L] 内。")

    return checked_position


def validate_sample_count(sample_count: object) -> int:
    """验证采样点数是不小于 3 的整数。"""
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 3:
        raise ValueError("采样点数量必须是不小于 3 的整数。")

    return sample_count
