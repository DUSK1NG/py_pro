"""Streamlit 页面计算调度测试。"""

import pytest

from app import calculate_beam


def test_calculate_beam_dispatches_all_load_types():
    common = {"length": 1, "length_unit": "m", "elastic_modulus": 200000, "inertia_moment": 1000000}
    midspan = calculate_beam(load_type="跨中集中力", load_value=1, load_unit="kN", **common)
    point = calculate_beam(load_type="任意位置集中力", load_value=1, load_unit="kN", position=0.3, **common)
    uniform = calculate_beam(load_type="满跨均布荷载", load_value=1, load_unit="kN/m", **common)
    assert midspan["max_moment_position"] == 500.0
    assert point["max_moment_position"] == 300.0
    assert uniform["max_moment_position"] == 500.0


def test_calculate_beam_rejects_unknown_load_type():
    with pytest.raises(ValueError):
        calculate_beam("未知荷载", 1, "N", 1, "m", 200000, 1000000)
