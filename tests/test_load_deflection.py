import numpy as np
import pytest

from utils.load_deflection import (
    calculate_load_deflection_comparison,
    load_deflection_from_csv,
)


def test_csv_is_sorted_and_converted_to_arrays():
    result = load_deflection_from_csv(
        "load_n,measured_deflection_mm\n40,-0.4\n0,0\n20,-0.2\n"
    )
    assert np.array_equal(result["load_n"], np.array([0.0, 20.0, 40.0]))
    assert np.array_equal(
        result["measured_deflection_mm"], np.array([0.0, -0.2, -0.4])
    )


@pytest.mark.parametrize(
    "csv_text, message",
    [
        ("load_n\n1\n", "必须包含"),
        ("load_n,measured_deflection_mm\n1,\n", "空值"),
        ("load_n,measured_deflection_mm\n1,0\n1,-0.1\n", "不能重复"),
        ("load_n,measured_deflection_mm\n-1,0\n", "非负"),
        ("load_n,measured_deflection_mm\nabc,0\n", "数值"),
    ],
)
def test_csv_validation_errors_are_clear(csv_text, message):
    with pytest.raises(ValueError, match=message):
        load_deflection_from_csv(csv_text)


def test_comparison_has_zero_error_for_identical_curves():
    result = calculate_load_deflection_comparison(
        [0, 20, 40], [0, -0.2, -0.4], [0, -0.2, -0.4]
    )
    assert np.allclose(result["error_mm"], 0)
    assert result["max_abs_error_mm"] == pytest.approx(0)
    assert result["mean_abs_error_mm"] == pytest.approx(0)


def test_comparison_omits_relative_error_when_theory_is_zero():
    result = calculate_load_deflection_comparison([0, 10], [0, 0], [0, -1])
    assert result["relative_error_percent"][0] is None
    assert result["relative_error_percent"][1] == pytest.approx(100)


def test_comparison_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="长度必须一致"):
        calculate_load_deflection_comparison([0, 1], [0], [0, 0])
