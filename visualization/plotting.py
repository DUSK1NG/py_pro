"""跨中集中力简支梁的剪力、弯矩和挠度图绘制。"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager


def _available_chinese_fonts() -> list[str]:
    """按可读性返回本机可用的中文无衬线字体。"""
    installed = {font.name for font in font_manager.fontManager.ttflist}
    preferred = [
        "Microsoft YaHei",
        "Noto Sans CJK SC",
        "Source Han Sans CN",
        "SimHei",
        "WenQuanYi Zen Hei",
        "DejaVu Sans",
    ]
    available = [font for font in preferred if font in installed]
    return available or ["DejaVu Sans"]


# Windows 优先微软雅黑，Linux 优先 Noto Sans CJK；配置后中文标题与坐标轴可正常保存到 PNG。
plt.rcParams["font.sans-serif"] = _available_chinese_fonts()
plt.rcParams["axes.unicode_minus"] = False

def _validate_result(result: object, curve_name: str) -> tuple[list[float], list[float]]:
    """验证绘图结果中横坐标和目标曲线数据可用。"""
    if not isinstance(result, dict) or "x" not in result or curve_name not in result:
        raise ValueError("绘图结果缺少必要数据。")

    x_values = result["x"]
    y_values = result[curve_name]
    if not isinstance(x_values, list) or not isinstance(y_values, list) or not x_values:
        raise ValueError("绘图数据必须为非空列表。")
    if len(x_values) != len(y_values):
        raise ValueError("横坐标和曲线数据长度必须一致。")

    values = x_values + y_values
    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        for value in values
    ):
        raise ValueError("绘图数据必须为有限数值。")

    return x_values, y_values


def _save_if_requested(figure: plt.Figure, save_path: str | Path | None) -> None:
    """在调用方提供路径时保存 PNG。"""
    if save_path is not None:
        figure.savefig(Path(save_path), dpi=150, bbox_inches="tight")


def plot_shear_force(
    result: dict[str, object], save_path: str | Path | None = None
) -> plt.Figure:
    """绘制剪力图并返回 Matplotlib Figure。"""
    x_values, shear_values = _validate_result(result, "shear")
    figure, axis = plt.subplots()
    axis.step(x_values, shear_values, where="post", label="剪力")
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(title="剪力图", xlabel="位置 x（mm）", ylabel="剪力 V（N）")
    axis.grid(True, alpha=0.3)
    axis.legend()
    _save_if_requested(figure, save_path)
    return figure
def _plot_curve(
    result: dict[str, object],
    curve_name: str,
    title: str,
    y_label: str,
    save_path: str | Path | None,
) -> plt.Figure:
    """绘制连续曲线并返回 Figure。"""
    x_values, y_values = _validate_result(result, curve_name)
    figure, axis = plt.subplots()
    axis.plot(x_values, y_values, label=title)
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(title=title, xlabel="位置 x（mm）", ylabel=y_label)
    axis.grid(True, alpha=0.3)
    axis.legend()
    _save_if_requested(figure, save_path)
    return figure


def plot_bending_moment(
    result: dict[str, object], save_path: str | Path | None = None
) -> plt.Figure:
    """绘制弯矩图并返回 Matplotlib Figure。"""
    return _plot_curve(result, "moment", "弯矩图", "弯矩 M（N·mm）", save_path)


def plot_deflection(
    result: dict[str, object], save_path: str | Path | None = None
) -> plt.Figure:
    """绘制理论挠度曲线并返回 Matplotlib Figure。"""
    return _plot_curve(
        result, "deflection", "理论挠度曲线", "挠度 v（mm）", save_path
    )
