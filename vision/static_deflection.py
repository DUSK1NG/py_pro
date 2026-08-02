"""基于高对比度标记点的静态图片跨中挠度测量。"""

from __future__ import annotations

import math
from typing import Mapping

import cv2
import numpy as np


def _positive_finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}必须是有限正数。")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name}必须是有限正数。")
    return number


def calibrate_mm_per_pixel(length_mm: object, pixel_length: object) -> float:
    """根据标定物实际长度和像素长度返回 mm/像素。"""
    checked_length = _positive_finite(length_mm, "标定物实际长度")
    checked_pixels = _positive_finite(pixel_length, "标定物像素长度")
    return checked_length / checked_pixels


def _to_gray(image: object) -> np.ndarray:
    if not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("输入图片不能为空。")
    if image.ndim == 2:
        gray = image
    elif image.ndim == 3 and image.shape[2] in (3, 4):
        code = cv2.COLOR_BGR2GRAY if image.shape[2] == 3 else cv2.COLOR_BGRA2GRAY
        gray = cv2.cvtColor(image, code)
    else:
        raise ValueError("输入图片必须是灰度图、BGR 图或 BGRA 图。")
    if gray.dtype != np.uint8:
        raise ValueError("输入图片像素类型必须为 uint8。")
    return gray


def _validate_options(threshold: object, polarity: str) -> tuple[int, str]:
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("阈值必须是 0 到 255 之间的整数。")
    checked_threshold = int(threshold)
    if checked_threshold < 0 or checked_threshold > 255:
        raise ValueError("阈值必须是 0 到 255 之间的整数。")
    if polarity not in {"light", "dark"}:
        raise ValueError("标记点极性必须是 light 或 dark。")
    return checked_threshold, polarity


def detect_marker(
    image: np.ndarray,
    threshold: int = 128,
    polarity: str = "light",
    min_area: float = 50,
    max_area: float = 100000,
) -> dict[str, object]:
    """检测一枚高对比度标记点并返回中心、掩膜和标注图。"""
    checked_threshold, checked_polarity = _validate_options(threshold, polarity)
    checked_min_area = _positive_finite(min_area, "标记点最小面积")
    checked_max_area = _positive_finite(max_area, "标记点最大面积")
    if checked_min_area >= checked_max_area:
        raise ValueError("标记点面积范围无效。")

    gray = _to_gray(image)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    threshold_type = cv2.THRESH_BINARY if checked_polarity == "light" else cv2.THRESH_BINARY_INV
    _, mask = cv2.threshold(blurred, checked_threshold, 255, threshold_type)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[float, object]] = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < checked_min_area or area > checked_max_area:
            continue
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0:
            continue
        circularity = 4 * math.pi * area / perimeter**2
        if circularity >= 0.55:
            candidates.append((area * circularity, contour))

    if not candidates:
        raise ValueError("未检测到有效标记点。")
    candidates.sort(key=lambda item: item[0], reverse=True)
    if len(candidates) > 1 and candidates[0][0] < candidates[1][0] * 1.5:
        raise ValueError("检测到多个无法区分的标记点。")

    contour = candidates[0][1]
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        raise ValueError("标记点中心无法计算。")
    center = (
        float(moments["m10"] / moments["m00"]),
        float(moments["m01"] / moments["m00"]),
    )
    annotated = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(annotated, [contour], -1, (0, 255, 0), 2)
    cv2.circle(annotated, (round(center[0]), round(center[1])), 4, (0, 0, 255), -1)
    return {"center": center, "mask": mask, "annotated": annotated}


def measure_midspan_deflection(
    reference_image: np.ndarray,
    loaded_image: np.ndarray,
    calibration_length_mm: object,
    calibration_pixels: object,
    threshold: int = 128,
    polarity: str = "light",
    min_area: float = 50,
    max_area: float = 100000,
) -> dict[str, object]:
    """测量两张图片中标记点的跨中竖向位移。"""
    if not isinstance(reference_image, np.ndarray) or not isinstance(loaded_image, np.ndarray):
        raise ValueError("参考图和加载图必须是 NumPy 图片数组。")
    if reference_image.shape[:2] != loaded_image.shape[:2]:
        raise ValueError("参考图和加载图的尺寸必须一致。")
    mm_per_pixel = calibrate_mm_per_pixel(calibration_length_mm, calibration_pixels)
    reference = detect_marker(reference_image, threshold, polarity, min_area, max_area)
    loaded = detect_marker(loaded_image, threshold, polarity, min_area, max_area)
    reference_center = reference["center"]
    loaded_center = loaded["center"]
    pixel_displacement = float(loaded_center[1] - reference_center[1])
    return {
        "reference_center": reference_center,
        "loaded_center": loaded_center,
        "pixel_displacement": pixel_displacement,
        "mm_per_pixel": mm_per_pixel,
        "deflection_mm": -pixel_displacement * mm_per_pixel,
        "reference_mask": reference["mask"],
        "loaded_mask": loaded["mask"],
        "reference_annotated": reference["annotated"],
        "loaded_annotated": loaded["annotated"],
    }
