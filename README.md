# 简支梁力学分析与挠度监测系统

[![Tests](https://github.com/DUSK1NG/py_pro/actions/workflows/tests.yml/badge.svg)](https://github.com/DUSK1NG/py_pro/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)

这是一个面向材料力学实验的简支梁理论分析与静态图片挠度测量工具，支持三类静力荷载、OpenCV 图像识别、理论/实测对比和数据导出。

> 当前版本采用“上传两张静态图片”的方案，不包含视频、实时摄像头和连续帧监测。

## 当前功能

- 跨中集中力、任意位置集中力、满跨均布荷载；
- 支座反力、剪力、弯矩和理论挠度计算；
- 剪力图、弯矩图和挠度曲线；
- 矩形截面、圆形截面和自定义截面惯性矩；
- 长度、荷载和弹性模量单位下拉选择；
- 弹性模量支持 MPa 和 GPa；
- 可选导出 Markdown 或 PDF 理论分析报告；
- 77 项自动化测试。

OpenCV 采用静态图片方案：用户上传未加载图片和加载后图片，完成标记点识别、像素标定、完整挠度曲线和理论/实测对比。本项目不包含视频读取、实时摄像头或连续帧监测功能。

## 安装与测试

在项目根目录执行：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -v
```

## 启动界面

推荐启动优化后的界面：

```powershell
streamlit run app_styled.py
```

基础界面仍可通过以下命令启动：

```powershell
streamlit run app.py
```

## 项目结构

```text
mechanics/       力学计算、荷载模型和截面属性
vision/          静态图片识别、曲线提取和 Streamlit 图像区
visualization/   剪力、弯矩和挠度图
utils/           单位、校验、对比、报告和 CSV 导出
tests/           理论、图像、导出和界面相关测试
sample_data/     示例 CSV 和实验装置参考图
docs/            实验说明、报告提纲和答辩提纲
```

## 快速体验

1. 启动 `app_styled.py`；
2. 输入梁长、荷载、材料和截面参数；
3. 点击“开始计算”查看理论结果；
4. 在“图像测量”中上传未加载图和加载图；
5. 在“荷载—挠度数据分析”中上传 `sample_data/load_deflection_example.csv`；
6. 下载 CSV、PNG 或 Markdown/PDF 报告。

![简支梁挠度实验装置参考图](sample_data/reference_beam_deflection_apparatus.jpg)

图片仅作实验装置参考，来源和使用说明见 [sample_data/README.md](sample_data/README.md)。

## 输入单位

程序内部统一换算为：

- 长度：mm；
- 力：N；
- 均布荷载：N/mm；
- 弹性模量：MPa，即 N/mm²；
- 截面惯性矩：mm⁴；
- 挠度：mm。

界面会自动换算 `m`、`kN`、`GPa` 等可选单位，并拒绝非数值、无穷大、零或负数等非法输入。

## 截面惯性矩

在 `app_styled.py` 中选择截面类型：

- 矩形截面：`I = b × h³ / 12`；
- 圆形截面：`I = π × d⁴ / 64`；
- 自定义：直接输入 `I`，单位为 mm⁴。

矩形宽度 `b`、高度 `h` 和圆形直径 `d` 均以 mm 输入。

## 报告导出

完成理论计算后，点击结果区的“导出报告”弹窗，可选择 Markdown 或 PDF 格式。报告包含输入参数、截面信息、支座反力、最大剪力、弯矩和挠度结果；用户不点击生成时不会创建文件。

## 图像测量

在结果页面的“图像测量”区域上传未加载图片和加载后图片，可以：

- 识别高对比度跨中标记点；
- 输入标定物实际长度和像素长度；
- 计算跨中实测挠度；
- 选择 ROI 提取完整挠度曲线；
- 查看理论/实测曲线和误差指标。

实验搭建和拍摄要求见 [experiment_guide.md](docs/experiment_guide.md)。

## 数据导出

理论结果、剪力图、弯矩图、理论挠度图、实测曲线和理论/实测对比 CSV 均可从界面下载。Markdown/PDF 报告也会在识别实测数据后包含实测摘要和误差结果。


## 荷载—挠度数据分析

在理论计算完成后，可展开“荷载—挠度数据分析”，上传包含以下字段的 CSV：

```csv
load_n,measured_deflection_mm
0,0.0
20,-0.0021
40,-0.0042
```

程序会按荷载排序，计算当前梁参数下的理论跨中挠度，显示荷载—挠度曲线、绝对误差和相对误差，并提供对比 CSV 下载。示例文件位于 `sample_data/load_deflection_example.csv`。示例数据只用于演示，不能替代真实实验数据。
## 当前模型适用条件

两端为理想简支，梁为均匀等截面，材料处于线弹性和小挠度范围。不考虑剪切变形、塑性、自重、动态荷载和复杂组合荷载。

## 验算示例

给定 `L=1000 mm`、`P=100 N`、`E=200000 MPa`、`I=1000000 mm⁴`：

- 左右支座反力：`50 N`；
- 最大剪力绝对值：`50 N`；
- 最大弯矩：`25000 N·mm`；
- 最大挠度位置：跨中 `500 mm`；
- 跨中挠度：`-0.0104167 mm`（负号表示向下）。
