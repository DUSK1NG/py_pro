"""理论挠度与实验挠度数据对比。"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def _as_curve(values: Iterable[object], name: str) -> np.ndarray:
    try:
        array = np.asarray(list(values), dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name}必须是一维有限数值序列。") from error
    if array.ndim != 1 or array.size < 2 or not np.all(np.isfinite(array)):
        raise ValueError(f"{name}必须是一维有限数值序列，且至少包含两个点。")
    return array


def compare_deflection_curves(
    theoretical_x_mm: Iterable[object],
    theoretical_deflection_mm: Iterable[object],
    measured_x_mm: Iterable[object],
    measured_deflection_mm: Iterable[object],
    relative_floor: float = 1e-9,
    reasonable_relative_error_percent: float = 10.0,
) -> dict[str, object]:
    """将理论曲线插值到实测位置并计算误差指标。"""
    theory_x = _as_curve(theoretical_x_mm, "理论横坐标")
    theory_y = _as_curve(theoretical_deflection_mm, "理论挠度")
    measured_x = _as_curve(measured_x_mm, "实测横坐标")
    measured_y = _as_curve(measured_deflection_mm, "实测挠度")
    if theory_x.size != theory_y.size or measured_x.size != measured_y.size:
        raise ValueError("横坐标和挠度数据长度必须一致。")
    if np.any(np.diff(theory_x) <= 0) or np.any(np.diff(measured_x) <= 0):
        raise ValueError("横坐标必须严格递增。")
    if measured_x[0] < theory_x[0] or measured_x[-1] > theory_x[-1]:
        raise ValueError("实测横坐标必须位于理论曲线范围内。")
    if not math.isfinite(relative_floor) or relative_floor <= 0:
        raise ValueError("相对误差下限必须是正数。")
    if (
        not math.isfinite(reasonable_relative_error_percent)
        or reasonable_relative_error_percent < 0
    ):
        raise ValueError("合理误差阈值必须是非负有限数。")

    theory_at_measured = np.interp(measured_x, theory_x, theory_y)
    error = measured_y - theory_at_measured
    absolute_error = np.abs(error)
    relative_error = np.full_like(absolute_error, np.nan)
    non_zero_theory = np.abs(theory_at_measured) > relative_floor
    relative_error[non_zero_theory] = (
        absolute_error[non_zero_theory] / np.abs(theory_at_measured[non_zero_theory]) * 100
    )
    valid_relative = relative_error[np.isfinite(relative_error)]
    max_relative = float(np.max(valid_relative)) if valid_relative.size else None
    return {
        "x_mm": measured_x,
        "theoretical_at_measured_mm": theory_at_measured,
        "measured_deflection_mm": measured_y,
        "error_mm": error,
        "absolute_error_mm": absolute_error,
        "relative_error_percent": relative_error,
        "max_abs_error_mm": float(np.max(absolute_error)),
        "mean_abs_error_mm": float(np.mean(absolute_error)),
        "max_relative_error_percent": max_relative,
        "within_reasonable_range": (
            max_relative is not None
            and max_relative <= reasonable_relative_error_percent
        ),
    }


def compare_single_deflection(
    theoretical_deflection_mm: object,
    measured_deflection_mm: object,
    reasonable_error_percent: float = 10.0,
) -> dict[str, float | bool | None]:
    """对比跨中单点理论挠度与实测挠度。"""
    try:
        theoretical = float(theoretical_deflection_mm)
        measured = float(measured_deflection_mm)
    except (TypeError, ValueError) as error:
        raise ValueError("理论和实测挠度必须是有限数值。") from error
    if not math.isfinite(theoretical) or not math.isfinite(measured):
        raise ValueError("理论和实测挠度必须是有限数值。")
    absolute_error = abs(measured - theoretical)
    relative_error = None if abs(theoretical) <= 1e-9 else absolute_error / abs(theoretical) * 100
    return {
        "theoretical_deflection_mm": theoretical,
        "measured_deflection_mm": measured,
        "absolute_error_mm": absolute_error,
        "relative_error_percent": relative_error,
        "within_reasonable_range": (
            relative_error is not None and relative_error <= reasonable_error_percent
        ),
    }
