"""常用简支梁截面属性计算。"""

import math


def _positive_finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}必须是有限正数。")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name}必须是有限正数。")
    return number


def rectangle_inertia(width: float, height: float) -> float:
    """返回矩形截面关于水平中性轴的惯性矩，输入单位为 mm。"""
    width_value = _positive_finite(width, "矩形宽度")
    height_value = _positive_finite(height, "矩形高度")
    return width_value * height_value**3 / 12.0


def circle_inertia(diameter: float) -> float:
    """返回实心圆截面惯性矩，输入直径单位为 mm。"""
    diameter_value = _positive_finite(diameter, "圆形直径")
    return math.pi * diameter_value**4 / 64.0


def section_inertia(section_type: str, **values: float) -> float:
    """按截面类型计算或校验惯性矩，返回单位为 mm⁴。"""
    if section_type == "矩形截面":
        return rectangle_inertia(values.get("width"), values.get("height"))
    if section_type == "圆形截面":
        return circle_inertia(values.get("diameter"))
    if section_type == "自定义":
        return _positive_finite(values.get("inertia"), "截面惯性矩")
    raise ValueError("不支持的截面类型。")
