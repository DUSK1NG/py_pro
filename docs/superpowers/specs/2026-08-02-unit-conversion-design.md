# 单位换算层设计

## 目标

新增统一单位换算层，让未来界面的下拉选项可安全转换为内部计算单位。力学计算模块继续只使用 mm、N、N/mm、MPa 和 mm⁴。

## 模块与接口

新增 `utils/units.py`：

- `convert_length_to_mm(value, unit) -> float`：支持 `mm`、`m`。
- `convert_force_to_n(value, unit) -> float`：支持 `N`、`kN`。
- `convert_distributed_load_to_n_per_mm(value, unit) -> float`：支持 `N/mm`、`N/m`、`kN/m`、`kN/mm`。

所有函数拒绝布尔值、非数值、NaN、无穷大和不支持的单位，并抛出中文 `ValueError`。换算层不调用力学或绘图模块。

## 换算规则

- `1 m = 1000 mm`
- `1 kN = 1000 N`
- `1 N/m = 0.001 N/mm`
- `1 kN/m = 1 N/mm`
- `1 kN/mm = 1000 N/mm`

本阶段不创建 Streamlit 下拉框；未来界面直接把下拉选项字符串传入这些函数。

## 验收

测试验证上述换算、保留零值（适用于将来的荷载输入）、非法单位拒绝和非法数值拒绝。既有力学与绘图测试必须全部通过。
