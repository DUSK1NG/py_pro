"""跨中集中力简支梁挠度与采样汇总测试。"""

import math

import pytest

from mechanics.central_point_load import deflection, sample_beam


def test_deflection_matches_classic_formula_at_midspan_and_supports():
    """挠度应满足经典公式及两端支承边界。"""
    expected_midspan = -100 * 1000**3 / (48 * 200000 * 1000000)

    assert math.isclose(deflection(0, 1000, 100, 200000, 1000000), 0.0)
    assert math.isclose(
        deflection(500, 1000, 100, 200000, 1000000), expected_midspan
    )
    assert math.isclose(deflection(1000, 1000, 100, 200000, 1000000), 0.0)


def test_deflection_is_symmetric_about_midspan():
    """对称荷载下左右对称位置的挠度相同。"""
    left_deflection = deflection(200, 1000, 100, 200000, 1000000)
    right_deflection = deflection(800, 1000, 100, 200000, 1000000)

    assert math.isclose(left_deflection, right_deflection)


def test_sample_summary_reports_exact_midspan_extrema():
    """汇总结果应直接给出跨中的经典极值。"""
    result = sample_beam(1000, 100, 200000, 1000000)

    assert result["max_shear"] == 50.0
    assert result["max_moment"] == 25000.0
    assert result["max_moment_position"] == 500.0
    assert result["max_deflection_position"] == 500.0
    assert math.isclose(result["max_deflection"], -100 / 9600)


def test_even_sample_count_still_reports_exact_midspan_extrema():
    """即使采样数组没有跨中点，汇总极值也必须准确。"""
    result = sample_beam(1000, 100, 200000, 1000000, sample_count=100)

    assert result["max_moment"] == 25000.0
    assert result["max_moment_position"] == 500.0
    assert result["max_deflection_position"] == 500.0


def test_deflection_rejects_non_positive_stiffness_inputs():
    """弹性模量和截面惯性矩必须为正数。"""
    with pytest.raises(ValueError):
        deflection(500, 1000, 100, 0, 1000000)
