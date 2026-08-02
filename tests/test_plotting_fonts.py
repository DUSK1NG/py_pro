"""中文图形字体配置测试。"""

import warnings

import matplotlib

matplotlib.use("Agg")

from mechanics.central_point_load import sample_beam
from visualization.plotting import plot_deflection


def test_saving_chinese_plot_emits_no_missing_glyph_warning(tmp_path):
    """保存中文标题和坐标轴标签时不应产生缺字警告。"""
    result = sample_beam(1000, 100, 200000, 1000000)

    with warnings.catch_warnings():
        warnings.filterwarnings("error", message="Glyph .* missing from font")
        plot_deflection(result, tmp_path / "deflection.png")
