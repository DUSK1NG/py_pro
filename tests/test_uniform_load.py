"""满跨均布荷载简支梁测试。"""

import math

import pytest

from mechanics.uniform_load import (
    bending_moment,
    deflection,
    sample_beam,
    shear_force,
    support_reactions,
)


def test_classic_uniform_load_results():
    """验证满跨均布荷载的经典反力、剪力、弯矩和挠度。"""
    length, intensity, modulus, inertia = 1000, 1, 200000, 1000000
    assert support_reactions(length, intensity) == (500.0, 500.0)
    assert shear_force(500, length, intensity) == 0.0
    assert bending_moment(500, length, intensity) == 125000.0
    expected = -5 * intensity * length**4 / (384 * modulus * inertia)
    assert math.isclose(deflection(500, length, intensity, modulus, inertia), expected)
    assert deflection(0, length, intensity, modulus, inertia) == 0.0
    assert deflection(length, length, intensity, modulus, inertia) == 0.0


def test_sample_summary_reports_midspan_extrema():
    result = sample_beam(1000, 1, 200000, 1000000)
    assert result["max_moment"] == 125000.0
    assert result["max_moment_position"] == 500.0
    assert result["max_deflection_position"] == 500.0


def test_uniform_load_rejects_invalid_intensity():
    with pytest.raises(ValueError):
        support_reactions(1000, 0)
