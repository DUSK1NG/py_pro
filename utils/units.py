"""将界面单位转换为内部统一计算单位。"""

import math


def _validate_value(value: object) -> float:
    """验证换算输入为有限数值；允许零值。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("换算数值必须是有限数值。")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("换算数值必须是有限数值。")
    return number


def _convert(value: object, unit: object, factors: dict[str, float], label: str) -> float:
    number = _validate_value(value)
    if not isinstance(unit, str) or unit not in factors:
        raise ValueError(f"不支持的{label}单位：{unit}。")
    return number * factors[unit]


def convert_length_to_mm(value: object, unit: str) -> float:
    """将 mm 或 m 的长度转换为 mm。"""
    return _convert(value, unit, {"mm": 1.0, "m": 1000.0}, "长度")


def convert_force_to_n(value: object, unit: str) -> float:
    """将 N 或 kN 的力转换为 N。"""
    return _convert(value, unit, {"N": 1.0, "kN": 1000.0}, "力")


def convert_distributed_load_to_n_per_mm(value: object, unit: str) -> float:
    """将常用均布荷载单位转换为 N/mm。"""
    return _convert(
        value,
        unit,
        {"N/mm": 1.0, "N/m": 0.001, "kN/m": 1.0, "kN/mm": 1000.0},
        "均布荷载",
    )
