from io import BytesIO

import matplotlib.pyplot as plt

from utils.export import (
    build_curve_csv,
    build_load_deflection_csv,
    build_result_csv,
    figure_to_png_bytes,
)


def test_result_csv_contains_summary_fields():
    csv_text = build_result_csv(
        {"max_shear": 50, "max_moment": 25000, "max_deflection": -0.01}
    )

    assert "field,value" in csv_text
    assert "max_moment,25000" in csv_text


def test_curve_csv_contains_theory_measurement_and_error_columns():
    csv_text = build_curve_csv([0, 10], [0, -1], [0, -0.8], [0, 0.2])

    assert "x_mm,theoretical_deflection_mm,measured_deflection_mm,error_mm" in csv_text
    assert "10.0,-1.0,-0.8,0.2" in csv_text


def test_figure_export_returns_png_bytes():
    figure, axis = plt.subplots()
    axis.plot([0, 1], [0, 1])

    data = figure_to_png_bytes(figure)

    assert data.startswith(b"\x89PNG")
    assert len(data) > 100
    plt.close(figure)


def test_load_deflection_csv_contains_comparison_columns():
    csv_text = build_load_deflection_csv(
        {
            "load_n": [0, 20],
            "measured_deflection_mm": [0, -0.2],
            "theoretical_deflection_mm": [0, -0.2],
            "error_mm": [0, 0],
            "relative_error_percent": [None, 0],
        }
    )
    assert "load_n,measured_deflection_mm,theoretical_deflection_mm" in csv_text
    assert "20.0,-0.2,-0.2,0.0,0.0" in csv_text
