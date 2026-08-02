from utils.export import build_measured_curve_csv


def test_measured_curve_csv_contains_position_and_measurement():
    csv_text = build_measured_curve_csv([0, 10], [0, -2])

    assert csv_text == (
        "x_mm,measured_deflection_mm\n"
        "0.0,0.0\n"
        "10.0,-2.0\n"
    )
