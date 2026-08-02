# 单位换算层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将界面输入的长度、力和均布荷载安全转换为内部计算单位。

**Architecture:** `utils.units` 独立于力学与界面层，接受数值和单位字符串，返回内部单位数值。所有转换共享同一有限数值校验。

**Tech Stack:** Python 3.11+、pytest。

## Global Constraints

- 内部单位固定为 mm、N、N/mm。
- 支持 `mm/m`、`N/kN`、`N/mm/N/m/kN/m/kN/mm`。
- 非数值、NaN、无穷大和未知单位抛出中文 `ValueError`。
- 新行为遵循测试先行。

---

### Task 1: 单位换算函数

**Files:**
- Create: `utils/units.py`
- Create: `tests/test_units.py`

**Interfaces:**
- Produces: `convert_length_to_mm(value: object, unit: str) -> float`
- Produces: `convert_force_to_n(value: object, unit: str) -> float`
- Produces: `convert_distributed_load_to_n_per_mm(value: object, unit: str) -> float`

- [ ] **Step 1: 写入失败测试**

```python
import pytest
from utils.units import convert_distributed_load_to_n_per_mm, convert_force_to_n, convert_length_to_mm

def test_converts_supported_units_to_internal_units():
    assert convert_length_to_mm(1, "m") == 1000.0
    assert convert_length_to_mm(10, "mm") == 10.0
    assert convert_force_to_n(1, "kN") == 1000.0
    assert convert_distributed_load_to_n_per_mm(1, "kN/m") == 1.0
    assert convert_distributed_load_to_n_per_mm(1, "N/m") == 0.001

@pytest.mark.parametrize("function,unit", [(convert_length_to_mm, "cm"), (convert_force_to_n, "kg"), (convert_distributed_load_to_n_per_mm, "kN/cm")])
def test_rejects_unknown_units(function, unit):
    with pytest.raises(ValueError):
        function(1, unit)
```

- [ ] **Step 2: 确认失败**

Run: `python -m pytest tests/test_units.py -v`

Expected: FAIL，`utils.units` 尚不存在。

- [ ] **Step 3: 写入最小实现**

```python
import math

def _validate_value(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("换算数值必须是有限数值。")
    return float(value)

def _convert(value, unit, factors, label):
    number = _validate_value(value)
    if unit not in factors:
        raise ValueError(f"不支持的{label}单位：{unit}。")
    return number * factors[unit]

def convert_length_to_mm(value, unit):
    return _convert(value, unit, {"mm": 1, "m": 1000}, "长度")

def convert_force_to_n(value, unit):
    return _convert(value, unit, {"N": 1, "kN": 1000}, "力")

def convert_distributed_load_to_n_per_mm(value, unit):
    return _convert(value, unit, {"N/mm": 1, "N/m": 0.001, "kN/m": 1, "kN/mm": 1000}, "均布荷载")
```

- [ ] **Step 4: 确认完整测试通过并提交**

Run: `python -m pytest -v`

Expected: PASS，全部测试通过。

Run: `git add utils/units.py tests/test_units.py && git commit -m "feat: add unit conversion helpers"`
