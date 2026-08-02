# Section Properties Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add validated rectangular, circular, and user-defined section inertia inputs and integrate them into the styled Streamlit beam-analysis interface.

**Architecture:** Keep section formulas in a small pure module, independent of Streamlit and beam-load calculations. The UI selects one section type, collects only the required dimensions, computes a single internal inertia value in mm⁴, and passes that value to the existing `calculate_beam` function.

**Tech Stack:** Python 3.11+, NumPy-free standard-library math, pytest, Streamlit.

## Global Constraints

- Internal units remain mm, N, MPa, and mm⁴.
- Rectangle inertia uses `I = b * h**3 / 12`.
- Circle inertia uses `I = pi * d**4 / 64`.
- Every dimension and custom inertia must be finite and strictly positive.
- OpenCV and image-processing code are out of scope for this change.
- New behavior must follow test-driven development: a focused test fails before production code is added.

---

### Task 1: Section-property behavior tests

**Files:**
- Create: `tests/test_section_properties.py`
- Create later: `mechanics/section_properties.py`

**Interfaces:**
- Tests will target `rectangle_inertia(width, height)`, `circle_inertia(diameter)`, and `section_inertia(section_type, **values)`.
- Each function returns one positive `float` in mm⁴ and raises `ValueError` for invalid values or unknown section types.

- [ ] **Step 1: Write the failing tests**

```python
import math

import pytest

from mechanics.section_properties import circle_inertia, rectangle_inertia, section_inertia


def test_rectangle_inertia_uses_width_and_height_in_mm():
    assert rectangle_inertia(20, 30) == pytest.approx(20 * 30**3 / 12)


def test_circle_inertia_uses_diameter_in_mm():
    assert circle_inertia(20) == pytest.approx(math.pi * 20**4 / 64)


def test_section_inertia_accepts_custom_inertia():
    assert section_inertia("自定义", inertia=12345) == pytest.approx(12345)


@pytest.mark.parametrize(
    "call",
    [
        lambda: rectangle_inertia(0, 30),
        lambda: rectangle_inertia(20, -1),
        lambda: circle_inertia(float("nan")),
        lambda: section_inertia("自定义", inertia=0),
        lambda: section_inertia("未知"),
    ],
)
def test_section_properties_reject_invalid_inputs(call):
    with pytest.raises(ValueError):
        call()
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```powershell
python -m pytest tests/test_section_properties.py -v
```

Expected: collection fails because `mechanics.section_properties` does not exist yet.

- [ ] **Step 3: Commit the failing test**

```powershell
git add tests/test_section_properties.py
git commit -m "test: specify section inertia calculations"
```

### Task 2: Implement pure section inertia calculations

**Files:**
- Create: `mechanics/section_properties.py`
- Modify: `mechanics/__init__.py` only if the package currently exposes public symbols there
- Test: `tests/test_section_properties.py`

**Interfaces:**

```python
def rectangle_inertia(width: float, height: float) -> float: ...
def circle_inertia(diameter: float) -> float: ...
def section_inertia(section_type: str, **values: float) -> float: ...
```

- [ ] **Step 1: Implement the smallest passing module**

```python
import math


def _positive_finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}必须是有限正数。")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name}必须是有限正数。")
    return number


def rectangle_inertia(width: float, height: float) -> float:
    width_value = _positive_finite(width, "矩形宽度")
    height_value = _positive_finite(height, "矩形高度")
    return width_value * height_value**3 / 12.0


def circle_inertia(diameter: float) -> float:
    diameter_value = _positive_finite(diameter, "圆形直径")
    return math.pi * diameter_value**4 / 64.0


def section_inertia(section_type: str, **values: float) -> float:
    if section_type == "矩形截面":
        return rectangle_inertia(values.get("width"), values.get("height"))
    if section_type == "圆形截面":
        return circle_inertia(values.get("diameter"))
    if section_type == "自定义":
        return _positive_finite(values.get("inertia"), "截面惯性矩")
    raise ValueError("不支持的截面类型。")
```

- [ ] **Step 2: Run the focused tests**

Run:

```powershell
python -m pytest tests/test_section_properties.py -v
```

Expected: all section-property tests pass.

- [ ] **Step 3: Run the full suite**

Run:

```powershell
python -m pytest -v
```

Expected: existing tests and the new section tests pass with no failures.

- [ ] **Step 4: Commit the implementation**

```powershell
git add mechanics/section_properties.py tests/test_section_properties.py
git commit -m "feat: add section inertia calculations"
```

### Task 3: Integrate section selection into BeamLab UI

**Files:**
- Modify: `app_styled.py`
- Test: `tests/test_section_properties.py` remains the pure calculation contract

**Interfaces:**
- `app_styled.py` imports `section_inertia`.
- The sidebar exposes `矩形截面`, `圆形截面`, and `自定义`.
- The existing `calculate_beam(..., inertia_moment=...)` receives the computed mm⁴ value.

- [ ] **Step 1: Add the section controls after the elastic-modulus controls**

Use this logic inside `main()`:

```python
section_type = st.sidebar.selectbox(
    "截面类型",
    ["矩形截面", "圆形截面", "自定义"],
)

if section_type == "矩形截面":
    width_col, height_col = st.sidebar.columns(2)
    section_width = width_col.number_input("宽度 b（mm）", min_value=0.001, value=20.0)
    section_height = height_col.number_input("高度 h（mm）", min_value=0.001, value=30.0)
    inertia_moment = section_inertia(
        section_type,
        width=section_width,
        height=section_height,
    )
elif section_type == "圆形截面":
    section_diameter = st.sidebar.number_input(
        "直径 d（mm）",
        min_value=0.001,
        value=20.0,
    )
    inertia_moment = section_inertia(section_type, diameter=section_diameter)
else:
    custom_inertia = st.sidebar.number_input(
        "截面惯性矩 I（mm⁴）",
        min_value=0.001,
        value=1000000.0,
    )
    inertia_moment = section_inertia(section_type, inertia=custom_inertia)
```

The `try` block around the calculate button should continue to display `ValueError` in Chinese if a calculation input is invalid.

- [ ] **Step 2: Check the UI file compiles**

Run:

```powershell
python -m py_compile app_styled.py
```

Expected: no syntax or indentation errors.

- [ ] **Step 3: Run the full test suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit and push the integration**

```powershell
git add app_styled.py
git commit -m "feat: integrate section type inputs into BeamLab"
git push
```

### Task 4: Update project documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document section input behavior**

Add the three section types, formulas, and the command `streamlit run app_styled.py`; explain that all dimensions are entered in mm and calculated inertia is in mm⁴.

- [ ] **Step 2: Run final verification**

```powershell
git diff --check
python -m py_compile app_styled.py
python -m pytest -q
```

Expected: no whitespace errors, successful compilation, and all tests passing.

- [ ] **Step 3: Commit and push documentation**

```powershell
git add README.md
git commit -m "docs: describe section property inputs"
git push
```
