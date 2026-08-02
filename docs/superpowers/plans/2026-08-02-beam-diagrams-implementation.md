# 简支梁内力与挠度图绘制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为跨中集中力简支梁生成可显示或保存的剪力图、弯矩图和理论挠度曲线。

**Architecture:** `visualization.plotting` 仅消费 `sample_beam()` 的结果字典，不修改或复制力学计算。三个公共绘图函数分别返回 Matplotlib Figure，并用一组共享校验函数保证输入数据完整、一致且为有限数值。

**Tech Stack:** Python 3.11+、Matplotlib、pytest。

## Global Constraints

- 仅使用 `sample_beam()` 的 `x`、`shear`、`moment`、`deflection` 结果，不重新计算力学公式。
- 图形单位固定为 mm、N、N·mm、mm；挠度向下为负。
- 图形函数不调用 `plt.show()`；`save_path=None` 时不写文件。
- 禁止引入 Streamlit、OpenCV、任意位置集中力和均布荷载。
- 使用 Matplotlib `Agg` 后端测试，且所有新增行为先有失败测试。

---

### Task 1: 绘图输入校验与剪力图

**Files:**
- Create: `visualization/__init__.py`
- Create: `visualization/plotting.py`
- Create: `tests/test_plotting.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: `dict[str, object]`，含等长有限数值列表 `x`、`shear`、`moment`、`deflection`。
- Produces: `plot_shear_force(result: dict[str, object], save_path: str | None = None) -> matplotlib.figure.Figure`。

- [ ] **Step 1: 写入失败测试**

```python
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from mechanics.central_point_load import sample_beam
from visualization.plotting import plot_shear_force

def test_shear_plot_returns_figure_and_uses_sample_data():
    result = sample_beam(1000, 100, 200000, 1000000)
    figure = plot_shear_force(result)
    assert isinstance(figure, Figure)
    assert list(figure.axes[0].lines[0].get_xdata()) == result["x"]
    assert list(figure.axes[0].lines[0].get_ydata()) == result["shear"]

def test_shear_plot_rejects_missing_or_inconsistent_data():
    import pytest
    with pytest.raises(ValueError):
        plot_shear_force({"x": [0, 1], "shear": [1]})
```

- [ ] **Step 2: 确认测试失败**

Run: `python -m pytest tests/test_plotting.py -v`

Expected: FAIL，`visualization.plotting` 尚不存在。

- [ ] **Step 3: 写入最小实现**

```python
import math
from pathlib import Path
import matplotlib.pyplot as plt

def _validate_result(result, curve_name):
    required = ("x", curve_name)
    if not isinstance(result, dict) or any(key not in result for key in required):
        raise ValueError("绘图结果缺少必要数据。")
    x_values, y_values = result["x"], result[curve_name]
    if not isinstance(x_values, list) or not isinstance(y_values, list) or not x_values:
        raise ValueError("绘图数据必须为非空列表。")
    if len(x_values) != len(y_values):
        raise ValueError("横坐标和曲线数据长度必须一致。")
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in x_values + y_values):
        raise ValueError("绘图数据必须为有限数值。")
    return x_values, y_values

def _save_if_requested(figure, save_path):
    if save_path is not None:
        figure.savefig(Path(save_path), dpi=150, bbox_inches="tight")

def plot_shear_force(result, save_path=None):
    x_values, shear_values = _validate_result(result, "shear")
    figure, axis = plt.subplots()
    axis.step(x_values, shear_values, where="post", label="剪力")
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(title="剪力图", xlabel="位置 x（mm）", ylabel="剪力 V（N）")
    axis.grid(True, alpha=0.3)
    axis.legend()
    _save_if_requested(figure, save_path)
    return figure
```

- [ ] **Step 4: 确认测试通过并提交**

Run: `python -m pytest tests/test_plotting.py -v`

Expected: PASS，2 项测试通过。

Run: `git add visualization tests/test_plotting.py requirements.txt && git commit -m "feat: add shear force plotting"`

### Task 2: 弯矩图、挠度图与 PNG 保存

**Files:**
- Modify: `visualization/plotting.py`
- Modify: `tests/test_plotting.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `plot_bending_moment(result: dict[str, object], save_path: str | None = None) -> matplotlib.figure.Figure`。
- Produces: `plot_deflection(result: dict[str, object], save_path: str | None = None) -> matplotlib.figure.Figure`。

- [ ] **Step 1: 写入失败测试**

```python
from pathlib import Path
from visualization.plotting import plot_bending_moment, plot_deflection

def test_moment_and_deflection_plots_use_sample_data_and_save_png(tmp_path):
    result = sample_beam(1000, 100, 200000, 1000000)
    moment_path = tmp_path / "moment.png"
    deflection_path = tmp_path / "deflection.png"
    moment_figure = plot_bending_moment(result, moment_path)
    deflection_figure = plot_deflection(result, deflection_path)
    assert list(moment_figure.axes[0].lines[0].get_ydata()) == result["moment"]
    assert list(deflection_figure.axes[0].lines[0].get_ydata()) == result["deflection"]
    assert moment_path.is_file() and moment_path.stat().st_size > 0
    assert deflection_path.is_file() and deflection_path.stat().st_size > 0
```

- [ ] **Step 2: 确认测试失败**

Run: `python -m pytest tests/test_plotting.py -v`

Expected: FAIL，两个新增公共函数尚不存在。

- [ ] **Step 3: 写入最小实现**

```python
def _plot_curve(result, curve_name, title, y_label, save_path):
    x_values, y_values = _validate_result(result, curve_name)
    figure, axis = plt.subplots()
    axis.plot(x_values, y_values, label=title)
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(title=title, xlabel="位置 x（mm）", ylabel=y_label)
    axis.grid(True, alpha=0.3)
    axis.legend()
    _save_if_requested(figure, save_path)
    return figure

def plot_bending_moment(result, save_path=None):
    return _plot_curve(result, "moment", "弯矩图", "弯矩 M（N·mm）", save_path)

def plot_deflection(result, save_path=None):
    return _plot_curve(result, "deflection", "理论挠度曲线", "挠度 v（mm）", save_path)
```

README 增加使用 `sample_beam()` 和三个绘图函数保存 PNG 的示例。

- [ ] **Step 4: 确认完整测试通过并提交**

Run: `python -m pytest -v`

Expected: PASS，第一阶段和第二阶段全部测试通过。

Run: `git add visualization/plotting.py tests/test_plotting.py README.md && git commit -m "feat: add moment and deflection plotting"`
