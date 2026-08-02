"""简支梁内力与挠度图绘制模块的测试。"""

import matplotlib

matplotlib.use("Agg")

import pytest
from matplotlib.figure import Figure

from mechanics.central_point_load import sample_beam
from visualization.plotting import plot_shear_force


def test_shear_plot_returns_figure_and_uses_sample_data():
    """剪力图应返回 Figure，并保持采样数据不变。"""
    result = sample_beam(1000, 100, 200000, 1000000)

    figure = plot_shear_force(result)

    assert isinstance(figure, Figure)
    assert list(figure.axes[0].lines[0].get_xdata()) == result["x"]
    assert list(figure.axes[0].lines[0].get_ydata()) == result["shear"]


def test_shear_plot_rejects_missing_or_inconsistent_data():
    """缺少数据或数组长度不一致时应拒绝绘图。"""
    with pytest.raises(ValueError):
        plot_shear_force({"x": [0, 1], "shear": [1]})
