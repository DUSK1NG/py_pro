"""CSV 和图像字节导出工具。"""

from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Iterable

from matplotlib.figure import Figure

from utils.textbook_export import build_textbook_csv


def build_result_csv(result: dict[str, object]) -> str:
    """将理论结果中的标量字段导出为 field,value CSV。"""
    if not isinstance(result, dict):
        raise ValueError("计算结果必须是字典。")
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["field", "value"])
    for key, value in result.items():
        if isinstance(value, (list, tuple, dict)):
            continue
        if hasattr(value, "shape"):
            continue
        writer.writerow([key, value])
    return buffer.getvalue()


def build_curve_csv(
    x_mm: Iterable[object],
    theoretical_deflection_mm: Iterable[object],
    measured_deflection_mm: Iterable[object],
    error_mm: Iterable[object],
) -> str:
    """将理论/实测曲线和误差导出为 CSV。"""
    columns = [
        list(x_mm),
        list(theoretical_deflection_mm),
        list(measured_deflection_mm),
        list(error_mm),
    ]
    if len({len(column) for column in columns}) != 1:
        raise ValueError("曲线导出数据长度必须一致。")
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "x_mm",
            "theoretical_deflection_mm",
            "measured_deflection_mm",
            "error_mm",
        ]
    )
    writer.writerows(
        [float(value) for value in row]
        for row in zip(*columns)
    )
    return buffer.getvalue()


def figure_to_png_bytes(figure: Figure) -> bytes:
    """将 Matplotlib Figure 转换为 PNG 字节，供 Streamlit 下载。"""
    if not isinstance(figure, Figure):
        raise ValueError("待导出的对象必须是 Matplotlib Figure。")
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    return buffer.getvalue()

def build_measured_curve_csv(
    x_mm: Iterable[object],
    measured_deflection_mm: Iterable[object],
) -> str:
    """将实测挠度曲线导出为 CSV。"""
    x_values = [float(value) for value in x_mm]
    measured_values = [float(value) for value in measured_deflection_mm]
    if len(x_values) != len(measured_values):
        raise ValueError("实测曲线数据长度必须一致。")
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["x_mm", "measured_deflection_mm"])
    writer.writerows(zip(x_values, measured_values))
    return buffer.getvalue()


def build_load_deflection_csv(comparison: dict[str, object]) -> str:
    """导出多组荷载—挠度理论/实测对比 CSV。"""
    required = (
        "load_n",
        "measured_deflection_mm",
        "theoretical_deflection_mm",
        "error_mm",
        "relative_error_percent",
    )
    if not isinstance(comparison, dict) or any(key not in comparison for key in required):
        raise ValueError("荷载—挠度对比结果缺少必要字段。")
    columns = [list(comparison[key]) for key in required]
    if len({len(column) for column in columns}) != 1:
        raise ValueError("荷载—挠度导出数据长度必须一致。")
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(list(required))
    for row in zip(*columns):
        writer.writerow(
            ["" if value is None else float(value) for value in row]
        )
    return buffer.getvalue()
