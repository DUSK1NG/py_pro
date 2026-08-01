# 跨中集中力简支梁计算模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为跨中承受集中力的简支梁提供经单元测试验证的反力、剪力、弯矩及挠度计算。

**Architecture:** 校验和力学公式分离；力学模块不依赖绘图或界面。它包含单点函数以及等间距采样汇总，供之后的可视化阶段复用。

**Tech Stack:** Python 3.11+、标准库、pytest。

## Global Constraints

- 输入单位固定为 mm、N、MPa（N/mm²）和 mm⁴，不自动换算 kN、m。
- 仅支持跨中集中力、线弹性小挠度 Euler–Bernoulli 理想简支梁。
- 向下挠度为负；不开发 OpenCV、绘图、Streamlit、任意位置荷载或均布荷载。
- 每项业务行为先运行失败测试，再写最小实现。

---

### Task 1: 输入校验

**Files:**
- Create: `mechanics/__init__.py`
- Create: `utils/__init__.py`
- Create: `utils/validation.py`
- Create: `tests/test_validation.py`
- Create: `requirements.txt`

**Interfaces:** `validate_positive_finite(value: object, name: str) -> float`、`validate_position(position: object, length: object) -> float`、`validate_sample_count(sample_count: object) -> int`。

- [ ] **Step 1: 写入失败测试**

```python
import pytest
from utils.validation import validate_positive_finite, validate_sample_count

@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), "100"])
def test_positive_finite_validator_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        validate_positive_finite(value, "梁长 L")

def test_sample_count_validator_accepts_three_or_more_integer_points():
    assert validate_sample_count(3) == 3

def test_sample_count_validator_rejects_too_few_or_non_integer_points():
    for value in (2, 3.5, True):
        with pytest.raises(ValueError):
            validate_sample_count(value)
```

- [ ] **Step 2: 确认测试失败**

Run: `python -m pytest tests/test_validation.py -v`

Expected: FAIL，`utils.validation` 尚不存在。

- [ ] **Step 3: 写入最小实现**

```python
import math

def validate_positive_finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}必须是有限正数。")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name}必须是有限正数。")
    return number

def validate_position(position: object, length: object) -> float:
    checked_length = validate_positive_finite(length, "梁长 L")
    if isinstance(position, bool) or not isinstance(position, (int, float)):
        raise ValueError("位置 x 必须是有限数值。")
    checked_position = float(position)
    if not math.isfinite(checked_position) or not 0 <= checked_position <= checked_length:
        raise ValueError("位置 x 必须位于梁长范围 [0, L] 内。")
    return checked_position

def validate_sample_count(sample_count: object) -> int:
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 3:
        raise ValueError("采样点数量必须是不小于 3 的整数。")
    return sample_count
```

- [ ] **Step 4: 确认测试通过并提交**

Run: `python -m pytest tests/test_validation.py -v`

Expected: PASS，3 项测试通过。

Run: `git add mechanics/__init__.py utils/__init__.py utils/validation.py tests/test_validation.py requirements.txt && git commit -m "feat: add mechanics input validation"`

### Task 2: 力学计算和汇总

**Files:**
- Create: `mechanics/central_point_load.py`
- Create: `tests/test_central_point_load.py`

**Interfaces:** `support_reactions(length: object, load: object) -> tuple[float, float]`、`shear_force(x: object, length: object, load: object) -> float`、`bending_moment(x: object, length: object, load: object) -> float`、`deflection(x: object, length: object, load: object, elastic_modulus: object, inertia_moment: object) -> float`、`sample_beam(length: object, load: object, elastic_modulus: object, inertia_moment: object, sample_count: object = 101) -> dict[str, object]`。

- [ ] **Step 1: 写入失败测试**

```python
import math
import pytest
from mechanics.central_point_load import bending_moment, deflection, sample_beam, shear_force, support_reactions

def test_classic_midspan_load_results():
    assert support_reactions(1000, 100) == (50.0, 50.0)
    assert shear_force(499, 1000, 100) == 50.0
    assert shear_force(501, 1000, 100) == -50.0
    assert bending_moment(0, 1000, 100) == 0.0
    assert bending_moment(500, 1000, 100) == 25000.0
    assert bending_moment(1000, 1000, 100) == 0.0
    expected = -100 * 1000**3 / (48 * 200000 * 1000000)
    assert math.isclose(deflection(500, 1000, 100, 200000, 1000000), expected)

def test_deflection_has_supported_boundaries_and_symmetry():
    assert deflection(0, 1000, 100, 200000, 1000000) == 0.0
    assert deflection(1000, 1000, 100, 200000, 1000000) == 0.0
    assert math.isclose(deflection(200, 1000, 100, 200000, 1000000), deflection(800, 1000, 100, 200000, 1000000))

def test_sample_summary_reports_midspan_extrema():
    result = sample_beam(1000, 100, 200000, 1000000)
    assert result["max_shear"] == 50.0
    assert result["max_moment"] == 25000.0
    assert result["max_moment_position"] == 500.0
    assert result["max_deflection_position"] == 500.0

def test_invalid_position_and_stiffness_are_rejected():
    with pytest.raises(ValueError):
        shear_force(1001, 1000, 100)
    with pytest.raises(ValueError):
        deflection(500, 1000, 100, 0, 1000000)
```

- [ ] **Step 2: 确认测试失败**

Run: `python -m pytest tests/test_central_point_load.py -v`

Expected: FAIL，力学模块尚不存在。

- [ ] **Step 3: 写入最小实现**

```python
from utils.validation import validate_position, validate_positive_finite, validate_sample_count

def support_reactions(length: object, load: object) -> tuple[float, float]:
    validate_positive_finite(length, "梁长 L")
    checked_load = validate_positive_finite(load, "集中力 P")
    return checked_load / 2, checked_load / 2

def shear_force(x: object, length: object, load: object) -> float:
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    reaction, _ = support_reactions(checked_length, load)
    return reaction if checked_x <= checked_length / 2 else -reaction

def bending_moment(x: object, length: object, load: object) -> float:
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")
    return checked_load * (checked_x if checked_x <= checked_length / 2 else checked_length - checked_x) / 2

def deflection(x: object, length: object, load: object, elastic_modulus: object, inertia_moment: object) -> float:
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_x = validate_position(x, checked_length)
    checked_load = validate_positive_finite(load, "集中力 P")
    checked_modulus = validate_positive_finite(elastic_modulus, "弹性模量 E")
    checked_inertia = validate_positive_finite(inertia_moment, "截面惯性矩 I")
    distance = min(checked_x, checked_length - checked_x)
    return -checked_load * distance * (3 * checked_length**2 - 4 * distance**2) / (48 * checked_modulus * checked_inertia)

def sample_beam(length: object, load: object, elastic_modulus: object, inertia_moment: object, sample_count: object = 101) -> dict[str, object]:
    checked_length = validate_positive_finite(length, "梁长 L")
    checked_count = validate_sample_count(sample_count)
    positions = [checked_length * i / (checked_count - 1) for i in range(checked_count)]
    shears = [shear_force(x, checked_length, load) for x in positions]
    moments = [bending_moment(x, checked_length, load) for x in positions]
    values = [deflection(x, checked_length, load, elastic_modulus, inertia_moment) for x in positions]
    midpoint = positions.index(checked_length / 2)
    return {"x": positions, "shear": shears, "moment": moments, "deflection": values, "max_shear": validate_positive_finite(load, "集中力 P") / 2, "max_moment": max(moments), "max_moment_position": positions[moments.index(max(moments))], "max_deflection": values[midpoint], "max_deflection_magnitude": abs(values[midpoint]), "max_deflection_position": positions[midpoint]}
```

- [ ] **Step 4: 确认全部测试通过并提交**

Run: `python -m pytest -v`

Expected: PASS，所有测试通过。

Run: `git add mechanics/central_point_load.py tests/test_central_point_load.py && git commit -m "feat: calculate beam mechanics"`

### Task 3: 初学者运行说明

**Files:**
- Create: `README.md`

- [ ] **Step 1: 写入 README**

README 必须提供虚拟环境、`python -m pip install -r requirements.txt`、`python -m pytest -v`、统一单位、适用条件，以及示例 `L=1000`、`P=100`、`E=200000`、`I=1000000`，其反力为 `50 N`、最大弯矩为 `25000 N·mm`、跨中挠度为 `-0.0104167 mm`。

- [ ] **Step 2: 运行测试并提交**

Run: `python -m pytest -v`

Expected: PASS，所有自动化测试通过，README 满足 Step 1。

Run: `git add README.md && git commit -m "docs: add first phase usage guide"`
