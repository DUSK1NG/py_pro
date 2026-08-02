import cv2
import numpy as np
import pytest

from vision.deflection_curve import extract_beam_centerline, measure_deflection_curve


def _beam_image(offset: int = 0, gap: tuple[int, int] | None = None) -> np.ndarray:
    image = np.zeros((100, 220, 3), dtype=np.uint8)
    points = np.array(
        [[10, 40 + offset], [110, 48 + offset], [210, 40 + offset]],
        dtype=np.int32,
    )
    cv2.polylines(image, [points], False, (255, 255, 255), 8)
    if gap is not None:
        cv2.rectangle(image, (gap[0], 0), (gap[1], 99), (0, 0, 0), -1)
    return image


def test_extract_beam_centerline_returns_pixel_curve_and_interpolates_gap():
    result = extract_beam_centerline(
        _beam_image(gap=(90, 95)),
        roi=(0, 20, 220, 60),
        threshold=128,
        polarity="light",
        max_gap=10,
    )

    assert len(result["x_pixel"]) > 180
    assert len(result["x_pixel"]) == len(result["y_pixel"])
    center_index = int(np.argmin(np.abs(result["x_pixel"] - 110)))
    assert result["y_pixel"][center_index] == pytest.approx(48, abs=2)


def test_measure_deflection_curve_converts_uniform_downward_motion():
    result = measure_deflection_curve(
        _beam_image(0),
        _beam_image(4),
        calibration_length_mm=50,
        calibration_pixels=100,
        roi=(0, 20, 220, 60),
        threshold=128,
        polarity="light",
    )

    assert len(result["x_mm"]) == len(result["measured_deflection_mm"])
    assert np.nanmedian(result["measured_deflection_mm"]) == pytest.approx(-2, abs=0.5)


def test_curve_extraction_rejects_invalid_roi_and_missing_beam():
    with pytest.raises(ValueError):
        extract_beam_centerline(_beam_image(), roi=(0, 0, 0, 20))
    with pytest.raises(ValueError):
        extract_beam_centerline(np.zeros((100, 220, 3), dtype=np.uint8), roi=(0, 0, 220, 100))
