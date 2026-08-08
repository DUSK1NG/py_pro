# 教材题简支梁求解器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不破坏现有简支梁计算、图片测量和报告功能的前提下，增加面向材料力学教材习题的多荷载、多约束解析/FEM 求解器。

**Architecture:** 新建独立的数据模型、静定解析求解器、Euler–Bernoulli 梁有限元求解器和统一分流器；Streamlit 只负责表格输入、模板和结果呈现。解析分支处理标准简支梁与悬臂梁，其他可解约束进入 FEM，并返回统一的 `BeamSolution` 供图表、CSV 和报告复用。

**Tech Stack:** Python 3.11+, NumPy, Pandas, Matplotlib, Streamlit, pytest；沿用现有单位换算、绘图、报告和导出模块。

## Global Constraints

- 内部单位固定为 mm、N、MPa、mm⁴、mm。
- 只计算平面内竖向 Euler–Bernoulli 梁弯曲，不计算轴向、水平反力、扭转、剪切变形或大挠度。
- 向上外力为正、向下外力为负；挠度向下为负。
- 现有 77 项测试必须保持通过。
- 使用 `st.form` 批量提交输入；新代码不增加已弃用的 `use_container_width` 参数。
- 每个任务完成后运行对应测试并单独提交 Git。

---

## 文件与职责映射

**新增文件**

- `mechanics/textbook_models.py`：输入、结果、支座、荷载和分段表达式的数据类及枚举。
- `mechanics/analytical_beam.py`：标准简支梁和悬臂梁的平衡、分段剪力/弯矩和挠度解析计算。
- `mechanics/beam_fem.py`：Euler–Bernoulli 梁单元、荷载组装、约束处理和反力恢复。
- `mechanics/textbook_solver.py`：输入校验、静定性分类、解析/FEM 分流和统一结果接口。
- `ui/__init__.py`、`ui/textbook_solver_ui.py`：Streamlit 教材题输入表格、模板、结果和错误提示。
- `utils/textbook_export.py`：教材题 Markdown、CSV 和报告附加段落。
- `tests/test_textbook_models.py`、`tests/test_textbook_analytical.py`、`tests/test_beam_fem.py`、`tests/test_textbook_solver.py`、`tests/test_textbook_export.py`：新增测试。

**修改文件**

- `app_styled.py`：增加教材题求解器入口，保存 `BeamSolution`，复用现有主题和图表。
- `utils/report.py`：允许追加教材题输入、步骤、反力、分段和 FEM 节点结果。
- `utils/export.py`：增加教材题结果和曲线 CSV 构建函数的导出入口。
- `vision/report_ui.py`：报告弹窗增加教材题报告选项，但不改变现有理论/实验报告行为。
- `README.md`：补充教材题模式的输入说明、解析/FEM 分流和示例题。

### Task 1: 数据模型与输入校验

**Files:**
- Create: `mechanics/textbook_models.py`
- Create: `tests/test_textbook_models.py`
- Modify: `utils/units.py` only if existing converters lack a required N/mm or MPa conversion

**Interfaces:**
- Consumes: existing unit converters and Python standard-library dataclasses.
- Produces: `Support`, `PointLoad`, `DistributedLoad`, `BeamProblem`, `Reaction`, `SegmentResult`, `BeamSolution`, `ProblemInputError`.

- [ ] **Step 1: Write failing model and validation tests**

```python
def test_beam_problem_rejects_out_of_range_support():
    with pytest.raises(ProblemInputError, match="支座位置"):
        BeamProblem(1000, 200000, 1_000_000,
                    [Support(1200, "roller")], [], []).validate()

def test_beam_problem_rejects_overlapping_distributed_load():
    with pytest.raises(ProblemInputError, match="x1 < x2"):
        BeamProblem(1000, 200000, 1_000_000,
                    [Support(0, "pin"), Support(1000, "roller")], [],
                    [DistributedLoad(800, 700, -1)]).validate()

def test_problem_serializes_signed_loads():
    problem = BeamProblem(1000, 200000, 1_000_000,
                          [Support(0, "pin"), Support(1000, "roller")],
                          [PointLoad(500, -100)], [])
    assert problem.total_vertical_load_n() == pytest.approx(-100)
```

- [ ] **Step 2: Run tests and confirm they fail**

Run: `pytest tests/test_textbook_models.py -q`

Expected: collection failure because `mechanics.textbook_models` does not exist.

- [ ] **Step 3: Implement the typed models and exact validation rules**

Use frozen dataclasses for individual supports/loads and a mutable `BeamProblem` for editor input. `BeamProblem.validate()` must reject `length_mm <= 0`, `elastic_modulus_mpa <= 0`, `inertia_mm4 <= 0`, unsupported support kinds, duplicate support positions, positions outside `[0, L]`, empty support lists, empty loads only when no external load is explicitly allowed by the caller, and `start_mm >= end_mm`. Keep signed values in N and N/mm.

- [ ] **Step 4: Run the model tests**

Run: `pytest tests/test_textbook_models.py -q`

Expected: all model tests pass.

- [ ] **Step 5: Commit**

```text
git add mechanics/textbook_models.py tests/test_textbook_models.py
git commit -m "feat: add textbook beam data models"
```

### Task 2: 静定解析求解器

**Files:**
- Create: `mechanics/analytical_beam.py`
- Create: `tests/test_textbook_analytical.py`

**Interfaces:**
- Consumes: `BeamProblem` and model result types from Task 1.
- Produces: `solve_simply_supported(problem) -> BeamSolution`, `solve_cantilever(problem) -> BeamSolution`, `supports_analytical(problem) -> bool`.

- [ ] **Step 1: Write failing benchmark tests**

```python
def test_midspan_point_load_reactions_and_deflection():
    p = simple_problem(point_loads=[PointLoad(500, -1000)])
    result = solve_simply_supported(p)
    assert result.reactions[0].vertical_n == pytest.approx(500)
    assert result.reactions[1].vertical_n == pytest.approx(500)
    assert result.max_deflection_mm == pytest.approx(-1000 * 1000**3 / (48 * 200000 * 1_000_000))

def test_partial_udl_resultant_is_used_in_reactions():
    p = simple_problem(distributed_loads=[DistributedLoad(200, 800, -2)])
    result = solve_simply_supported(p)
    assert sum(r.vertical_n for r in result.reactions) == pytest.approx(1200)
    assert result.checks["sum_vertical_n"] == pytest.approx(0, abs=1e-8)

def test_cantilever_tip_force_has_fixed_reaction_and_moment():
    p = BeamProblem(1000, 200000, 1_000_000,
                    [Support(0, "fixed"), Support(1000, "free")],
                    [PointLoad(1000, -100)], [])
    result = solve_cantilever(p)
    assert result.reactions[0].vertical_n == pytest.approx(100)
    assert result.reactions[0].moment_n_mm == pytest.approx(100000)
```

- [ ] **Step 2: Run the analytical tests and verify failure**

Run: `pytest tests/test_textbook_analytical.py -q`

Expected: import or missing-function failures.

- [ ] **Step 3: Implement equilibrium and Macaulay-style evaluation**

For each supported load, compute its signed resultant and centroid. For the simple support branch solve `RA + RB + ΣF = 0` and `RB*L + Σ(F*x) = 0`; for the cantilever branch solve the fixed vertical force and fixed reaction moment. Implement `shear_at(x)` and `moment_at(x)` by summing reactions, point-force jumps, and the active portion of each uniform load. Build segment breakpoints from all supports, point-force positions, and distributed-load boundaries.

- [ ] **Step 4: Implement deflection and educational steps**

Integrate `M(x)/(E*I)` over the generated grid and determine the two integration constants from the branch boundary conditions (`v(0)=v(L)=0` for simple support; `v(0)=θ(0)=0` for cantilever). Populate `steps` with the equilibrium equations, substituted values, boundary conditions, and sign convention. Populate `warnings` with the transverse-only assumption.

- [ ] **Step 5: Run analytical tests and regression tests**

Run: `pytest tests/test_textbook_analytical.py tests/test_point_load.py tests/test_uniform_load.py -q`

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```text
git add mechanics/analytical_beam.py tests/test_textbook_analytical.py
git commit -m "feat: add analytical textbook beam solver"
```

### Task 3: Euler–Bernoulli 梁有限元

**Files:**
- Create: `mechanics/beam_fem.py`
- Create: `tests/test_beam_fem.py`

**Interfaces:**
- Consumes: validated `BeamProblem`.
- Produces: `solve_fem(problem, max_elements=200) -> BeamSolution` with node coordinates, displacement/rotation arrays, reactions, element shear/moment samples, mesh metadata, and warnings.

- [ ] **Step 1: Write failing FEM tests**

```python
def test_fem_matches_simple_support_midspan_point_load():
    result = solve_fem(simple_problem(point_loads=[PointLoad(500, -1000)]), max_elements=40)
    assert result.max_deflection_mm == pytest.approx(
        -1000 * 1000**3 / (48 * 200000 * 1_000_000), rel=1e-3
    )

def test_fem_rejects_mechanism():
    p = BeamProblem(1000, 200000, 1_000_000,
                    [Support(500, "free")], [PointLoad(500, -100)], [])
    with pytest.raises(ProblemInputError, match="机构|约束"):
        solve_fem(p)
```

- [ ] **Step 2: Run FEM tests and verify failure**

Run: `pytest tests/test_beam_fem.py -q`

Expected: missing module/function failure.

- [ ] **Step 3: Implement mesh construction and standard beam element matrix**

Create exact nodes at `0`, `L`, every support, every point-load position, and every distributed-load boundary. Subdivide remaining intervals so the total element count is at most `max_elements`. Assemble the standard two-node `[v, θ]` stiffness matrix with `E*I/L_e**3` scaling.

- [ ] **Step 4: Implement load vectors, constraints, solve, and reactions**

Apply point loads to the matching vertical DOF. Apply each uniform load with the consistent element nodal vector, preserving the signed direction. Constrain vertical DOFs for pin/roller and vertical plus rotation DOFs for fixed. Solve the reduced system with `numpy.linalg.solve`; convert `LinAlgError` into `ProblemInputError("机构或约束不足，刚度矩阵不可解")`. Compute reactions from `K @ u - F` and sample element shear/moment from local end forces.

- [ ] **Step 5: Run FEM tests and full mechanics regression**

Run: `pytest tests/test_beam_fem.py tests/test_textbook_analytical.py tests/test_point_load.py tests/test_uniform_load.py -q`

Expected: FEM benchmarks and existing mechanics tests pass.

- [ ] **Step 6: Commit**

```text
git add mechanics/beam_fem.py tests/test_beam_fem.py
git commit -m "feat: add Euler Bernoulli beam FEM solver"
```

### Task 4: 统一分流器、静定性分类和结果契约

**Files:**
- Create: `mechanics/textbook_solver.py`
- Create: `tests/test_textbook_solver.py`

**Interfaces:**
- Consumes: `BeamProblem`, `supports_analytical`, `solve_simply_supported`, `solve_cantilever`, and `solve_fem`.
- Produces: `solve_textbook_beam(problem) -> BeamSolution`, `classify_problem(problem) -> ProblemClassification`.

- [ ] **Step 1: Write failing dispatch and classification tests**

```python
def test_standard_simple_support_uses_analytical_method():
    result = solve_textbook_beam(simple_problem(point_loads=[PointLoad(300, -100)]))
    assert result.method == "analytical"
    assert result.classification == "静定"

def test_extra_internal_support_uses_fem():
    p = BeamProblem(1000, 200000, 1_000_000,
                    [Support(0, "pin"), Support(500, "roller"), Support(1000, "roller")],
                    [PointLoad(500, -100)], [])
    result = solve_textbook_beam(p)
    assert result.method == "fem"
    assert "超静定" in result.classification
```

- [ ] **Step 2: Implement classification and dispatch**

Validate once, classify effective displacement/rotation constraints, call the matching analytical solver for the two canonical cases, and otherwise call FEM. Normalize all result fields, including `reactions`, `shear_segments`, `moment_segments`, `x_mm`, `deflection_mm`, `checks`, `steps`, `warnings`, and `metadata`.

- [ ] **Step 3: Add superposition and error-path tests**

Verify two point loads and two separated uniform-load ranges equal the sum of their individual responses within `1e-8` for analytical cases. Verify invalid positions and singular mechanisms produce user-readable `ProblemInputError` messages.

- [ ] **Step 4: Run all mechanics tests and commit**

Run: `pytest tests/test_textbook_solver.py tests/test_textbook_models.py tests/test_textbook_analytical.py tests/test_beam_fem.py -q`

```text
git add mechanics/textbook_solver.py tests/test_textbook_solver.py
git commit -m "feat: route textbook beam problems to analytical or FEM solver"
```

### Task 5: Streamlit 教材题输入与结果区

**Files:**
- Create: `ui/__init__.py`
- Create: `ui/textbook_solver_ui.py`
- Modify: `app_styled.py`
- Create: `tests/test_textbook_ui_import.py`

**Interfaces:**
- Consumes: `BeamProblem`, `solve_textbook_beam`, existing theme/plot helpers.
- Produces: `render_textbook_solver() -> BeamSolution | None`, session-state key `textbook_solution`.

- [ ] **Step 1: Write import and validation smoke tests**

```python
def test_textbook_ui_module_imports():
    module = importlib.import_module("ui.textbook_solver_ui")
    assert callable(module.render_textbook_solver)
```

- [ ] **Step 2: Implement template and form state helpers**

Add template factories returning the exact rows for “简支梁（左铰右滚）” and “悬臂梁（左固定右自由）”. Use `st.form` and `st.data_editor(num_rows="dynamic")` for supports, point loads, and distributed loads. Convert table rows into the Task 1 dataclasses only after the submit button is pressed.

- [ ] **Step 3: Implement result rendering**

Render method/classification badges, input summary, reaction table, equilibrium checks, shear/moment/deflection plots, segment tables, FEM mesh metadata, and an expander containing `steps` and `warnings`. On validation errors call `st.error` and keep the last successful `st.session_state["textbook_solution"]`.

- [ ] **Step 4: Integrate without changing existing modes**

Add a top-level mode selector in `app_styled.py`; keep current basic theory, image measurement, load-deflection analysis, and report branches unchanged when “教材题求解器” is not selected. Reuse existing plotting functions where their input contract matches; otherwise add small adapters in `ui/textbook_solver_ui.py`.

- [ ] **Step 5: Run compile and app tests**

Run: `python -m py_compile app_styled.py ui/textbook_solver_ui.py mechanics/textbook_models.py mechanics/analytical_beam.py mechanics/beam_fem.py mechanics/textbook_solver.py` and `pytest tests/test_textbook_ui_import.py tests/test_app.py -q`.

- [ ] **Step 6: Commit**

```text
git add ui app_styled.py tests/test_textbook_ui_import.py
git commit -m "feat: add Streamlit textbook beam solver interface"
```

### Task 6: 报告、CSV 和图表导出

**Files:**
- Create: `utils/textbook_export.py`
- Create: `tests/test_textbook_export.py`
- Modify: `utils/report.py`
- Modify: `utils/export.py`
- Modify: `vision/report_ui.py`
- Modify: `app_styled.py`

**Interfaces:**
- Consumes: `BeamSolution` and `BeamProblem`.
- Produces: `build_textbook_markdown(problem, solution) -> str`, `build_textbook_csv(solution) -> str`, and optional PDF story sections.

- [ ] **Step 1: Write failing export tests**

```python
def test_textbook_markdown_contains_method_reactions_and_steps():
    text = build_textbook_markdown(problem, solution)
    assert "求解方法" in text
    assert "支座反力" in text
    assert "解题步骤" in text

def test_textbook_csv_has_curve_and_reaction_columns():
    frame = pd.read_csv(io.StringIO(build_textbook_csv(solution)))
    assert {"x_mm", "deflection_mm", "reaction_vertical_n"}.issubset(frame.columns)
```

- [ ] **Step 2: Implement deterministic Markdown/CSV builders**

Serialize inputs, classification, method, reactions, checks, steps, warnings, segment expressions, and curve arrays. Use UTF-8 CSV with a stable header and blank reaction cells for rows without a reaction.

- [ ] **Step 3: Add optional PDF sections and UI download buttons**

Extend the existing report builders with an optional `textbook_solution` argument defaulting to `None`; when absent, byte-for-byte existing behavior remains. Add Markdown/PDF/CSV download options to the existing report modal only after a solution exists.

- [ ] **Step 4: Run export/report regression tests and commit**

Run: `pytest tests/test_textbook_export.py tests/test_report.py tests/test_report_extended.py tests/test_export.py -q`

```text
git add utils/textbook_export.py utils/report.py utils/export.py vision/report_ui.py app_styled.py tests/test_textbook_export.py
git commit -m "feat: export textbook beam solutions and steps"
```

### Task 7: 文档、示例题与最终验收

**Files:**
- Modify: `README.md`
- Create: `sample_data/textbook_examples.json`
- Create: `tests/test_textbook_examples.py`

**Interfaces:**
- Consumes: public `solve_textbook_beam` API and the two templates.
- Produces: documented, runnable textbook examples and final regression evidence.

- [ ] **Step 1: Add three concrete examples**

Store a 1 m simply supported midspan force, a simply supported partial UDL, and a cantilever tip force with all values in internal units and expected reaction/deflection checks.

- [ ] **Step 2: Add example regression tests**

Load the JSON examples, build `BeamProblem` objects, call `solve_textbook_beam`, and assert the stored reactions, method, and maximum-deflection tolerances.

- [ ] **Step 3: Update README**

Document the new mode, supported support types, signed-load convention, why pin/roller horizontal reactions are omitted, when FEM is selected, and the exact command `streamlit run app_styled.py`.

- [ ] **Step 4: Run the complete acceptance suite**

Run: `pytest -q` and `python -m py_compile app.py app_styled.py mechanics/*.py ui/*.py utils/*.py vision/*.py`.

Expected: all existing and new tests pass; compile command exits with code 0.

- [ ] **Step 5: Commit documentation and examples**

```text
git add README.md sample_data/textbook_examples.json tests/test_textbook_examples.py
git commit -m "docs: add textbook beam examples and usage guide"
```

## Self-Review Checklist

- Spec coverage: input model → Task 1; analytical branches → Task 2; FEM fallback → Task 3; classification/dispatch → Task 4; Streamlit interaction → Task 5; reports/CSV → Task 6; README/examples → Task 7.
- Placeholder scan: no `TODO`, `TBD`, or unspecified “appropriate handling” steps are used; every task names files, interfaces, commands, and expected outcomes.
- Type consistency: all later tasks consume `BeamProblem` and `BeamSolution` from Task 1, and the dispatcher signature is fixed as `solve_textbook_beam(problem) -> BeamSolution`.
- Regression safety: every task ends with focused tests, and Task 7 runs the full existing suite.
