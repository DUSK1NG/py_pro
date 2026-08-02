"""弯矩图和挠度图的测试。"""

import matplotlib

matplotlib.use("Agg")

from mechanics.central_point_load import sample_beam
from visualization.plotting import plot_bending_moment, plot_deflection


def test_moment_and_deflection_plots_use_sample_data_and_save_png(tmp_path):
    """两张曲线图应使用采样数据，并能保存为非空 PNG。"""
    result = sample_beam(1000, 100, 200000, 1000000)
    moment_path = tmp_path / "moment.png"
    deflection_path = tmp_path / "deflection.png"

    moment_figure = plot_bending_moment(result, moment_path)
    deflection_figure = plot_deflection(result, deflection_path)

    assert list(moment_figure.axes[0].lines[0].get_xdata()) == result["x"]
    assert list(moment_figure.axes[0].lines[0].get_ydata()) == result["moment"]
    assert list(deflection_figure.axes[0].lines[0].get_xdata()) == result["x"]
    assert list(deflection_figure.axes[0].lines[0].get_ydata()) == result["deflection"]
    assert moment_path.is_file() and moment_path.stat().st_size > 0
    assert deflection_path.is_file() and deflection_path.stat().st_size > 0
