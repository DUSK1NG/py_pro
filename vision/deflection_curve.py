"""基于梁中心线的静态图片完整挠度曲线提取。"""

from __future__ import annotations

import cv2
import numpy as np

from vision.static_deflection import (
    _to_gray,
    _validate_options,
    calibrate_mm_per_pixel,
)


def _validate_roi(roi: tuple[int, int, int, int], shape: tuple[int, ...]) -> tuple[int, int, int, int]:
    if not isinstance(roi, tuple) or len(roi) != 4:
        raise ValueError("ROI 必须是 (x, y, width, height)。")
    x, y, width, height = roi
    if any(isinstance(value, bool) or not isinstance(value, int) for value in roi):
        raise ValueError("ROI 参数必须是整数。")
    image_height, image_width = shape[:2]
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ValueError("ROI 宽度和高度必须为正数。")
    if x + width > image_width or y + height > image_height:
        raise ValueError("ROI 必须位于图片范围内。")
    return x, y, width, height


def _beam_mask(image: np.ndarray, threshold: int, polarity: str) -> np.ndarray:
    checked_threshold, checked_polarity = _validate_options(threshold, polarity)
    gray = _to_gray(image)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    threshold_type = cv2.THRESH_BINARY if checked_polarity == "light" else cv2.THRESH_BINARY_INV
    _, mask = cv2.threshold(blurred, checked_threshold, 255, threshold_type)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def extract_beam_centerline(
    image: np.ndarray,
    roi: tuple[int, int, int, int],
    threshold: int = 128,
    polarity: str = "light",
    max_gap: int = 10,
) -> dict[str, object]:
    """提取 ROI 内梁中心线，返回像素坐标、掩膜和标注图。"""
    if isinstance(max_gap, bool) or not isinstance(max_gap, int) or max_gap < 0:
        raise ValueError("允许补齐的最大缺口必须是非负整数。")
    gray = _to_gray(image)
    x0, y0, width, height = _validate_roi(roi, gray.shape)
    mask = _beam_mask(image, threshold, polarity)
    roi_mask = mask[y0 : y0 + height, x0 : x0 + width]
    y_values = np.full(width, np.nan, dtype=float)
    for column in range(width):
        rows = np.flatnonzero(roi_mask[:, column])
        if rows.size:
            y_values[column] = float(np.median(rows) + y0)

    valid = np.isfinite(y_values)
    if valid.sum() < max(10, width // 2):
        raise ValueError("ROI 内未提取到足够的梁中心线。")
    valid_indices = np.flatnonzero(valid)
    missing_indices = np.flatnonzero(~valid)
    if missing_indices.size:
        gaps = np.split(missing_indices, np.where(np.diff(missing_indices) > 1)[0] + 1)
        if any(len(gap) > max_gap for gap in gaps):
            raise ValueError("梁中心线缺失区域过大，无法可靠插值。")
        y_values[~valid] = np.interp(missing_indices, valid_indices, y_values[valid])

    x_values = np.arange(x0, x0 + width, dtype=float)
    annotated = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    points = np.column_stack((x_values, y_values)).astype(np.int32)
    cv2.polylines(annotated, [points], False, (0, 0, 255), 2)
    return {
        "x_pixel": x_values,
        "y_pixel": y_values,
        "mask": mask,
        "annotated": annotated,
    }


def measure_deflection_curve(
    reference_image: np.ndarray,
    loaded_image: np.ndarray,
    calibration_length_mm: object,
    calibration_pixels: object,
    roi: tuple[int, int, int, int],
    threshold: int = 128,
    polarity: str = "light",
    max_gap: int = 10,
) -> dict[str, object]:
    """提取参考/加载中心线并返回毫米单位实测挠度曲线。"""
    if not isinstance(reference_image, np.ndarray) or not isinstance(loaded_image, np.ndarray):
        raise ValueError("参考图和加载图必须是 NumPy 图片数组。")
    if reference_image.shape[:2] != loaded_image.shape[:2]:
        raise ValueError("参考图和加载图的尺寸必须一致。")
    mm_per_pixel = calibrate_mm_per_pixel(calibration_length_mm, calibration_pixels)
    reference = extract_beam_centerline(reference_image, roi, threshold, polarity, max_gap)
    loaded = extract_beam_centerline(loaded_image, roi, threshold, polarity, max_gap)
    x_pixel = reference["x_pixel"]
    if not np.array_equal(x_pixel, loaded["x_pixel"]):
        raise ValueError("参考图和加载图的中心线横坐标不一致。")
    pixel_displacement = loaded["y_pixel"] - reference["y_pixel"]
    return {
        "x_pixel": x_pixel,
        "x_mm": (x_pixel - x_pixel[0]) * mm_per_pixel,
        "reference_y_pixel": reference["y_pixel"],
        "loaded_y_pixel": loaded["y_pixel"],
        "pixel_displacement": pixel_displacement,
        "measured_deflection_mm": -pixel_displacement * mm_per_pixel,
        "mm_per_pixel": mm_per_pixel,
        "reference_mask": reference["mask"],
        "loaded_mask": loaded["mask"],
        "reference_annotated": reference["annotated"],
        "loaded_annotated": loaded["annotated"],
    }
