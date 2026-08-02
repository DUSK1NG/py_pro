"""Streamlit 静态图片挠度识别、曲线提取和理论对比界面。"""

from __future__ import annotations

import cv2
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from utils.comparison import compare_deflection_curves, compare_single_deflection
from vision.deflection_curve import measure_deflection_curve
from vision.static_deflection import measure_midspan_deflection


def _decode_uploaded_image(uploaded_file: object) -> np.ndarray:
    if uploaded_file is None:
        raise ValueError("请先上传图片。")
    encoded = np.frombuffer(uploaded_file.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("图片无法读取，请上传 PNG、JPG 或 JPEG 文件。")
    return image


def _show_single_measurement(measurement: dict[str, object]) -> None:
    metric_columns = st.columns(3)
    metric_columns[0].metric(
        "像素位移", f"{measurement['pixel_displacement']:.2f} pixel"
    )
    metric_columns[1].metric(
        "标定比例", f"{measurement['mm_per_pixel']:.4f} mm/pixel"
    )
    metric_columns[2].metric(
        "实测跨中挠度", f"{measurement['deflection_mm']:.4f} mm"
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


def _show_curve_measurement(measurement: dict[str, object]) -> None:
    figure, axis = plt.subplots()
    axis.plot(
        measurement["x_mm"],
        measurement["measured_deflection_mm"],
        label="实测挠度",
        color="#2563eb",
    )
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(title="实测挠度曲线", xlabel="位置 x（mm）", ylabel="挠度 v（mm）")
    axis.grid(True, alpha=0.3)
    axis.legend()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)


def _show_single_comparison(theory_result: dict[str, object], measurement: dict[str, object]) -> None:
    comparison = compare_single_deflection(
        theory_result["max_deflection"], measurement["deflection_mm"]
    )
    st.markdown("#### 跨中理论/实测对比")
    columns = st.columns(3)
    columns[0].metric("理论挠度", f"{comparison['theoretical_deflection_mm']:.4f} mm")
    columns[1].metric("绝对误差", f"{comparison['absolute_error_mm']:.4f} mm")
    relative = comparison["relative_error_percent"]
    columns[2].metric(
        "相对误差",
        "无法计算" if relative is None else f"{relative:.2f}%",
    )
    if relative is None:
        st.info("理论挠度接近零，暂不计算相对误差。")
    elif comparison["within_reasonable_range"]:
        st.success("当前跨中测量相对误差不超过 10%，可作为初步实验结果。")
    else:
        st.warning("当前跨中测量相对误差超过 10%，建议检查标定和拍摄条件。")


def _show_curve_comparison(theory_result: dict[str, object], measurement: dict[str, object]) -> None:
    comparison = compare_deflection_curves(
        theory_result["x"],
        theory_result["deflection"],
        measurement["x_mm"],
        measurement["measured_deflection_mm"],
    )
    st.markdown("#### 挠度曲线理论/实测对比")
    columns = st.columns(3)
    columns[0].metric("最大绝对误差", f"{comparison['max_abs_error_mm']:.4f} mm")
    columns[1].metric("平均绝对误差", f"{comparison['mean_abs_error_mm']:.4f} mm")
    max_relative = comparison["max_relative_error_percent"]
    columns[2].metric(
        "最大相对误差",
        "无法计算" if max_relative is None else f"{max_relative:.2f}%",
    )
    figure, axis = plt.subplots()
    axis.plot(
        comparison["x_mm"],
        comparison["theoretical_at_measured_mm"],
        label="理论挠度",
        color="#7c3aed",
    )
    axis.plot(
        comparison["x_mm"],
        comparison["measured_deflection_mm"],
        label="实测挠度",
        color="#2563eb",
    )
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(title="理论与实测挠度对比", xlabel="位置 x（mm）", ylabel="挠度 v（mm）")
    axis.grid(True, alpha=0.3)
    axis.legend()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)
    if comparison["within_reasonable_range"]:
        st.success("曲线最大相对误差不超过 10%，可作为初步实验结果。")
    else:
        st.warning("曲线误差超过 10% 或无法计算相对误差，建议检查图像和标定。")


def render_image_measurement(theory_result: dict[str, object] | None = None) -> None:
    """渲染静态图片跨中测量、完整曲线和理论对比区域。"""
    st.markdown("### 图像测量")
    st.caption("上传未加载和加载后的图片，使用高对比度标记点或梁中心线测量实测挠度。")
    with st.expander("静态图片挠度识别", expanded=False):
        reference_file = st.file_uploader(
            "未加载图片", type=["png", "jpg", "jpeg"], key="reference_image"
        )
        loaded_file = st.file_uploader(
            "加载后图片", type=["png", "jpg", "jpeg"], key="loaded_image"
        )
        try:
            reference_image = _decode_uploaded_image(reference_file) if reference_file else None
            loaded_image = _decode_uploaded_image(loaded_file) if loaded_file else None
        except ValueError as error:
            st.error(f"图片读取失败：{error}")
            return

        threshold_col, polarity_col = st.columns(2)
        threshold = threshold_col.slider(
            "标记点/梁阈值", 0, 255, 128, key="marker_threshold"
        )
        polarity_label = polarity_col.selectbox(
            "目标颜色",
            ["浅色目标 / 深色背景", "深色目标 / 浅色背景"],
            key="marker_polarity",
        )
        calibration_col, pixel_col = st.columns(2)
        calibration_length = calibration_col.number_input(
            "标定物实际长度（mm）", min_value=0.001, value=50.0, key="calibration_length_mm"
        )
        calibration_pixels = pixel_col.number_input(
            "标定物像素长度（pixel）", min_value=0.001, value=100.0, key="calibration_pixels"
        )
        polarity = "light" if polarity_label.startswith("浅色") else "dark"

        if reference_image is not None:
            image_height, image_width = reference_image.shape[:2]
            st.caption(f"图片尺寸：{image_width} × {image_height} pixel")
            roi_columns = st.columns(4)
            roi_x = int(roi_columns[0].number_input("ROI x", 0, max(0, image_width - 1), 0, key="roi_x"))
            roi_y = int(roi_columns[1].number_input("ROI y", 0, max(0, image_height - 1), 0, key="roi_y"))
            roi_width = int(roi_columns[2].number_input("ROI 宽度", 1, image_width - roi_x, image_width - roi_x, key="roi_width"))
            roi_height = int(roi_columns[3].number_input("ROI 高度", 1, image_height - roi_y, image_height - roi_y, key="roi_height"))
            roi = (roi_x, roi_y, roi_width, roi_height)
        else:
            roi = (0, 0, 1, 1)

        single_col, curve_col = st.columns(2)
        if single_col.button("识别跨中标记点", key="measure_image_deflection"):
            try:
                if reference_image is None or loaded_image is None:
                    raise ValueError("请先上传两张图片。")
                st.session_state["image_measurement"] = measure_midspan_deflection(
                    reference_image,
                    loaded_image,
                    calibration_length_mm=calibration_length,
                    calibration_pixels=calibration_pixels,
                    threshold=threshold,
                    polarity=polarity,
                )
            except ValueError as error:
                st.error(f"跨中识别失败：{error}")
        if curve_col.button("提取完整挠度曲线", key="measure_deflection_curve"):
            try:
                if reference_image is None or loaded_image is None:
                    raise ValueError("请先上传两张图片。")
                st.session_state["curve_measurement"] = measure_deflection_curve(
                    reference_image,
                    loaded_image,
                    calibration_length_mm=calibration_length,
                    calibration_pixels=calibration_pixels,
                    roi=roi,
                    threshold=threshold,
                    polarity=polarity,
                )
            except ValueError as error:
                st.error(f"曲线提取失败：{error}")

        single_measurement = st.session_state.get("image_measurement")
        curve_measurement = st.session_state.get("curve_measurement")
        if single_measurement is not None:
            _show_single_measurement(single_measurement)
            if theory_result is not None:
                _show_single_comparison(theory_result, single_measurement)
        if curve_measurement is not None:
            _show_curve_measurement(curve_measurement)
            if theory_result is not None:
                _show_curve_comparison(theory_result, curve_measurement)
