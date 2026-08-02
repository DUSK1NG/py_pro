import cv2
import numpy as np
import pytest

from vision.static_deflection import (
    calibrate_mm_per_pixel,
    detect_marker,
    measure_midspan_deflection,
)


def _marker_image(center: tuple[int, int], *, duplicate: bool = False) -> np.ndarray:
    image = np.zeros((120, 200, 3), dtype=np.uint8)
    cv2.circle(image, center, 10, (255, 255, 255), -1)
    if duplicate:
        cv2.circle(image, (center[0] + 50, center[1]), 10, (255, 255, 255), -1)
    return image


def test_detect_marker_returns_center_mask_and_annotation():
    result = detect_marker(_marker_image((80, 50)), threshold=128, polarity="light")

    assert result["center"][0] == pytest.approx(80, abs=1)
    assert result["center"][1] == pytest.approx(50, abs=1)
    assert result["mask"].shape == (120, 200)
    assert result["annotated"].shape == (120, 200, 3)


def test_measure_midspan_deflection_converts_downward_pixel_motion():
    reference = _marker_image((80, 50))
    loaded = _marker_image((80, 60))

    result = measure_midspan_deflection(
        reference,
        loaded,
        calibration_length_mm=50,
        calibration_pixels=100,
        threshold=128,
        polarity="light",
    )

    assert result["pixel_displacement"] == pytest.approx(10, abs=1)
    assert result["mm_per_pixel"] == pytest.approx(0.5)
    assert result["deflection_mm"] == pytest.approx(-5, abs=0.5)


def test_calibration_rejects_non_positive_inputs():
    with pytest.raises(ValueError):
        calibrate_mm_per_pixel(0, 100)
    with pytest.raises(ValueError):
        calibrate_mm_per_pixel(50, -1)


def test_marker_detection_rejects_empty_and_ambiguous_images():
    with pytest.raises(ValueError):
        detect_marker(np.zeros((0, 0), dtype=np.uint8))
    with pytest.raises(ValueError):
        detect_marker(np.zeros((120, 200, 3), dtype=np.uint8))
    with pytest.raises(ValueError):
        detect_marker(_marker_image((80, 50), duplicate=True))
