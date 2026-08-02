import numpy as np
import pytest

from utils.comparison import compare_deflection_curves


def test_identical_curves_have_zero_error_and_are_reasonable():
    result = compare_deflection_curves(
        [0, 50, 100],
        [0, -2, 0],
        [0, 50, 100],
        [0, -2, 0],
    )

    assert np.allclose(result["error_mm"], [0, 0, 0])
    assert result["max_abs_error_mm"] == pytest.approx(0)
    assert result["within_reasonable_range"] is True


def test_comparison_interpolates_theory_at_measured_positions():
    result = compare_deflection_curves(
        [0, 50, 100],
        [0, -2, 0],
        [25, 75],
        [-1, -0.5],
    )

    assert np.allclose(result["theoretical_at_measured_mm"], [-1, -1])
    assert np.allclose(result["error_mm"], [0, 0.5])


def test_comparison_avoids_infinite_relative_error_at_zero_theory():
    result = compare_deflection_curves([0, 10], [0, -1], [0, 10], [0.2, -1])

    assert np.isnan(result["relative_error_percent"][0])
    assert np.isfinite(result["relative_error_percent"][1])


def test_comparison_rejects_invalid_ranges_and_lengths():
    with pytest.raises(ValueError):
        compare_deflection_curves([0, 50], [0], [0, 50], [0, 1])
    with pytest.raises(ValueError):
        compare_deflection_curves([0, 50, 100], [0, -2, 0], [-1, 50], [0, -1])
