# 任意位置集中力简支梁 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增任意内部位置集中力简支梁的反力、剪力、弯矩、挠度和采样计算。

**Architecture:** 新建 `mechanics.point_load`，不修改跨中专用模块。新模块返回与 `sample_beam()` 相同的绘图数据键，令现有可视化函数无需变化。

**Tech Stack:** Python 3.11+、标准库、pytest。

## Global Constraints

- 输入单位为 mm、N、MPa（N/mm²）、mm⁴；挠度向下为负。
- 荷载位置必须满足 `0 < a < L`。
- 不修改既有跨中集中力接口，不引入均布荷载、组合荷载、OpenCV 或 Streamlit。
- 每项业务行为先有失败测试。

---

### Task 1: 反力、剪力与弯矩

**Files:**
- Create: `mechanics/point_load.py`
- Create: `tests/test_point_load.py`

**Interfaces:**
- Produces: `support_reactions(length, load, position) -> tuple[float, float]`
- Produces: `shear_force(x, length, load, position) -> float`
- Produces: `bending_moment(x, length, load, position) -> float`

- [ ] **Step 1: 写入失败测试**

```python
import pytest
from mechanics.point_load import bending_moment, shear_force, support_reactions

def test_reactions_and_internal_forces_for_off_center_load():
    assert support_reactions(1000, 100, 300) == (70.0, 30.0)
    assert shear_force(300, 1000, 100, 300) == 70.0
    assert shear_force(301, 1000, 100, 300) == -30.0
    assert bending_moment(300, 1000, 100, 300) == 21000.0

@pytest.mark.parametrize("position", [0, 1000, -1, 1001])
def test_load_position_must_be_strictly_inside_beam(position):
    with pytest.raises(ValueError):
        support_reactions(1000, 100, position)
```

- [ ] **Step 2: 确认失败**

Run: `python -m pytest tests/test_point_load.py -v`

Expected: FAIL，`mechanics.point_load` 尚不存在。

- [ ] **Step 3: 写入最小实现**

```python
from utils.validation import validate_position, validate_positive_finite

def _validate_load_position(position, length):
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_position = validate_position(position, checked_length)
    if checked_position in (0, checked_length):
        raise ValueError("荷载位置 a 必须满足 0 < a < L。")
    return checked_length, checked_position

def support_reactions(length, load, position):
    checked_length, checked_position = _validate_load_position(position, length)
    checked_load = validate_positive_finite(load, "集中力 P")
    return checked_load * (checked_length - checked_position) / checked_length, checked_load * checked_position / checked_length

def shear_force(x, length, load, position):
    checked_length, checked_position = _validate_load_position(position, length)
    checked_x = validate_position(x, checked_length)
    left_reaction, _ = support_reactions(checked_length, load, checked_position)
    return left_reaction if checked_x <= checked_position else left_reaction - validate_positive_finite(load, "集中力 P")

def bending_moment(x, length, load, position):
    checked_length, checked_position = _validate_load_position(position, length)
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")
    left_reaction, _ = support_reactions(checked_length, checked_load, checked_position)
    return left_reaction * checked_x if checked_x <= checked_position else left_reaction * checked_x - checked_load * (checked_x - checked_position)
```

- [ ] **Step 4: 确认通过并提交**

Run: `python -m pytest tests/test_point_load.py -v`

Expected: PASS，5 项测试通过。

Run: `git add mechanics/point_load.py tests/test_point_load.py && git commit -m "feat: calculate off-center point load forces"`

### Task 2: 挠度、采样与跨中兼容性

**Files:**
- Modify: `mechanics/point_load.py`
- Modify: `tests/test_point_load.py`

**Interfaces:**
- Produces: `deflection(x, length, load, position, elastic_modulus, inertia_moment) -> float`
- Produces: `sample_beam(length, load, position, elastic_modulus, inertia_moment, sample_count=101) -> dict[str, object]`

- [ ] **Step 1: 写入失败测试**

```python
import math
from mechanics.central_point_load import deflection as midspan_deflection
from mechanics.point_load import deflection, sample_beam

def test_deflection_boundaries_continuity_and_midspan_compatibility():
    assert deflection(0, 1000, 100, 300, 200000, 1000000) == 0.0
    assert deflection(1000, 1000, 100, 300, 200000, 1000000) == 0.0
    assert math.isclose(deflection(500, 1000, 100, 500, 200000, 1000000), midspan_deflection(500, 1000, 100, 200000, 1000000))

def test_sample_result_can_be_drawn_and_contains_load_position():
    result = sample_beam(1000, 100, 300, 200000, 1000000, sample_count=100)
    assert 300.0 in result["x"]
    assert result["max_moment"] == 21000.0
    assert result["max_moment_position"] == 300.0
```

- [ ] **Step 2: 确认失败**

Run: `python -m pytest tests/test_point_load.py -v`

Expected: FAIL，`deflection` 和 `sample_beam` 尚不存在。

- [ ] **Step 3: 写入最小实现**

```python
def deflection(x, length, load, position, elastic_modulus, inertia_moment):
    checked_length, checked_position = _validate_load_position(position, length)
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")
    checked_modulus = validate_positive_finite(elastic_modulus, "弹性模量 E")
    checked_inertia = validate_positive_finite(inertia_moment, "截面惯性矩 I")
    opposite = checked_length - checked_position
    if checked_x <= checked_position:
        return -checked_load * opposite * checked_x * (checked_length**2 - opposite**2 - checked_x**2) / (6 * checked_length * checked_modulus * checked_inertia)
    right_distance = checked_length - checked_x
    return -checked_load * checked_position * right_distance * (checked_length**2 - checked_position**2 - right_distance**2) / (6 * checked_length * checked_modulus * checked_inertia)
```

`sample_beam` 生成等间距位置，额外插入 `a` 后排序去重；使用本模块函数填充 `x`、`shear`、`moment`、`deflection`，并报告 `max_moment=P*a*(L-a)/L` 和解析位置 `a`。

- [ ] **Step 4: 确认完整测试通过并提交**

Run: `python -m pytest -v`

Expected: PASS，全部测试通过。

Run: `git add mechanics/point_load.py tests/test_point_load.py && git commit -m "feat: add off-center point load deflection"`
