"""Streamlit 静态图片挠度测量界面。"""

from __future__ import annotations

import cv2
import numpy as np
import streamlit as st

from vision.static_deflection import measure_midspan_deflection


def _decode_uploaded_image(uploaded_file: object) -> np.ndarray:
    """将 Streamlit 上传文件解码为 OpenCV BGR 图片。"""
    if uploaded_file is None:
        raise ValueError("请先上传图片。")
    encoded = np.frombuffer(uploaded_file.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("图片无法读取，请上传 PNG、JPG 或 JPEG 文件。")
    return image


def render_image_measurement() -> None:
    """渲染静态图片跨中挠度识别区域。"""
    st.markdown("### 图像测量")
    st.caption("上传未加载和加载后的图片，使用高对比度跨中标记点测量实测挠度。")
    with st.expander("静态图片跨中挠度识别", expanded=False):
        reference_file = st.file_uploader(
            "未加载图片",
            type=["png", "jpg", "jpeg"],
            key="reference_image",
        )
        loaded_file = st.file_uploader(
            "加载后图片",
            type=["png", "jpg", "jpeg"],
            key="loaded_image",
        )
        threshold_col, polarity_col = st.columns(2)
        threshold = threshold_col.slider(
            "标记点阈值",
            min_value=0,
            max_value=255,
            value=128,
            key="marker_threshold",
        )
        polarity_label = polarity_col.selectbox(
            "标记点颜色",
            ["浅色标记 / 深色背景", "深色标记 / 浅色背景"],
            key="marker_polarity",
        )
        calibration_length = st.number_input(
            "标定物实际长度（mm）",
            min_value=0.001,
            value=50.0,
            key="calibration_length_mm",
        )
        calibration_pixels = st.number_input(
            "标定物像素长度（pixel）",
            min_value=0.001,
            value=100.0,
            key="calibration_pixels",
        )
        if st.button("识别跨中挠度", key="measure_image_deflection"):
            try:
                reference_image = _decode_uploaded_image(reference_file)
                loaded_image = _decode_uploaded_image(loaded_file)
                polarity = "light" if polarity_label.startswith("浅色") else "dark"
                measurement = measure_midspan_deflection(
                    reference_image,
                    loaded_image,
                    calibration_length_mm=calibration_length,
                    calibration_pixels=calibration_pixels,
                    threshold=threshold,
                    polarity=polarity,
                )
                st.session_state["image_measurement"] = measurement
            except ValueError as error:
                st.error(f"图像测量失败：{error}")

        measurement = st.session_state.get("image_measurement")
        if measurement is not None:
            metric_columns = st.columns(3)
            metric_columns[0].metric(
                "像素位移",
                f"{measurement['pixel_displacement']:.2f} pixel",
            )
            metric_columns[1].metric(
                "标定比例",
                f"{measurement['mm_per_pixel']:.4f} mm/pixel",
            )
            metric_columns[2].metric(
                "实测跨中挠度",
                f"{measurement['deflection_mm']:.4f} mm",
            )
            image_columns = st.columns(2)
            image_columns[0].image(
                cv2.cvtColor(measurement["reference_annotated"], cv2.COLOR_BGR2RGB),
                caption="未加载标记点识别结果",
            )
            image_columns[1].image(
                cv2.cvtColor(measurement["loaded_annotated"], cv2.COLOR_BGR2RGB),
                caption="加载后标记点识别结果",
            )
