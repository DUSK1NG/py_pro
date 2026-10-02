# 简支梁力学分析与挠度测量
本项目用 Streamlit 计算简支梁的支座反力、剪力、弯矩和挠度，并用静态图片或 CSV 实验数据与理论结果对比。

## 快速开始

需要 Python 和项目依赖。Windows PowerShell 从仓库根目录执行：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app_styled.py
```

启动输出片段：

```text
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

## 使用

在侧栏选择“基础理论分析”或“教材题求解器”，输入梁、材料、截面和荷载后计算。基础分析支持跨中集中力、任意位置集中力和满跨均布荷载；结果可与静态图片测量或 CSV 荷载—挠度数据比较，并导出图表和报告。CSV 数据需包含 `load_n`、`measured_deflection_mm` 两列，可从 [样例文件](examples/load_deflection_example.csv) 开始。图片测量使用未加载与加载后的两张图片，不采集视频或实时摄像头画面。

教材题求解器只计算竖向弯曲，支持多个支座、集中力和区间均布荷载。输入单位为 mm、N、MPa 和 mm⁴；向上力为正，向下挠度为负。教材题输入、单位、模型条件与报告说明见[使用指南](docs/usage.md)。实验拍摄说明和样例说明见 [实验指南](docs/experiment_guide.md)、[教材题示例](examples/textbook_examples.json) 与 [样例图片说明](examples/README.md)。


## 开发

在仓库根目录安装依赖后运行测试：

```powershell
.venv\Scripts\python.exe -m pytest -q
```

一次实测输出：

```text
154 passed in 45.22s
```
