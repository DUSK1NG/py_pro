"""多组荷载—挠度 CSV 解析、校验和误差计算。"""

from __future__ import annotations

import csv
from io import StringIO
from typing import Iterable

import numpy as np


REQUIRED_COLUMNS = ("load_n", "measured_deflection_mm")


def _as_float(value: str | None, field: str, row_number: int) -> float:
    if value is None or not value.strip():
        raise ValueError(f"第 {row_number} 行的 {field} 为空值。")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"第 {row_number} 行的 {field} 必须是数值。") from error
    if not np.isfinite(number):
        raise ValueError(f"第 {row_number} 行的 {field} 必须是有限数值。")
    return number


def load_deflection_from_csv(data: str) -> dict[str, object]:
    """读取荷载—挠度 CSV，按荷载升序返回 NumPy 数组。"""
    if not isinstance(data, str) or not data.strip():
        raise ValueError("CSV 内容不能为空。")
    reader = csv.DictReader(StringIO(data))
    fieldnames = reader.fieldnames or []
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        raise ValueError(f"CSV 必须包含列：{', '.join(missing)}。")

    loads: list[float] = []
    measured: list[float] = []
    for row_number, row in enumerate(reader, start=2):
        load = _as_float(row.get("load_n"), "load_n", row_number)
        value = _as_float(
            row.get("measured_deflection_mm"),
            "measured_deflection_mm",
            row_number,
        )
        if load < 0:
            raise ValueError("load_n 必须是非负数。")
        loads.append(load)
        measured.append(value)

    if len(loads) < 2:
        raise ValueError("CSV 至少需要两行数据。")
    if len(set(loads)) != len(loads):
        raise ValueError("load_n 不能重复。")
    order = np.argsort(np.asarray(loads, dtype=float))
    return {
        "load_n": np.asarray(loads, dtype=float)[order],
        "measured_deflection_mm": np.asarray(measured, dtype=float)[order],
    }


def calculate_load_deflection_comparison(
    load_n: Iterable[object],
    measured_deflection_mm: Iterable[object],
    theoretical_deflection_mm: Iterable[object],
    relative_floor: float = 1e-9,
    reasonable_relative_error_percent: float = 10.0,
) -> dict[str, object]:
    """计算多组荷载下理论/实测跨中挠度及误差。"""
    if relative_floor <= 0 or not np.isfinite(relative_floor):
        raise ValueError("相对误差下限必须是正数。")
    if reasonable_relative_error_percent < 0 or not np.isfinite(
        reasonable_relative_error_percent
    ):
        raise ValueError("合理误差阈值必须是非负有限数。")

    arrays = [
        np.asarray(list(values), dtype=float)
        for values in (load_n, measured_deflection_mm, theoretical_deflection_mm)
    ]
    if len({array.size for array in arrays}) != 1:
        raise ValueError("荷载、实测挠度和理论挠度长度必须一致。")
    if arrays[0].size == 0:
        raise ValueError("比较数据不能为空。")
    if not all(np.all(np.isfinite(array)) for array in arrays):
        raise ValueError("比较数据必须是有限数值。")

    loads, measured, theoretical = arrays
    error = measured - theoretical
    absolute_error = np.abs(error)
    relative = np.full(theoretical.shape, None, dtype=object)
    valid = np.abs(theoretical) >= relative_floor
    relative[valid] = absolute_error[valid] / np.abs(theoretical[valid]) * 100
    relative_values = [None if value is None else float(value) for value in relative]
    finite_relative = np.asarray(
        [value for value in relative_values if value is not None], dtype=float
    )
    max_relative = (
        float(np.max(finite_relative)) if finite_relative.size else None
    )
    return {
        "load_n": loads,
        "measured_deflection_mm": measured,
        "theoretical_deflection_mm": theoretical,
        "error_mm": error,
        "absolute_error_mm": absolute_error,
        "relative_error_percent": relative_values,
        "max_abs_error_mm": float(np.max(absolute_error)),
        "mean_abs_error_mm": float(np.mean(absolute_error)),
        "max_relative_error_percent": max_relative,
        "within_reasonable_range": max_relative is not None
        and max_relative <= reasonable_relative_error_percent,
    }
