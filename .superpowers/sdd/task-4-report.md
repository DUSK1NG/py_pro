# Task 4 实施报告：统一教材梁题分流器

## 交付内容

- 新增 `mechanics/textbook_solver.py`：
  - `classify_problem(problem) -> ProblemClassification`
  - `solve_textbook_beam(problem) -> BeamSolution`
- 新增 `tests/test_textbook_solver.py`，覆盖解析/FEM 分流、统一结果契约、两类荷载叠加、三支座超静定及机构错误。

## 分流规则

- 标准简支梁与端部固定悬臂梁：静定，调用解析求解器。
- 反力分量多于两个：标为“超静定（数值解）”，调用 FEM。
- 反力分量少于两个：标为“机构/约束不足”，抛出可读的 `ProblemInputError`。
- 其余静定但不属于标准解析构型的问题：调用 FEM。

公共入口首先执行 `BeamProblem.validate()`，并将底层解析/FEM 异常统一为可读的 `ProblemInputError`。输出会补齐 `classification`、剪力/弯矩分段别名和包含单位、符号约定的 `metadata`，保持内部 mm/N/MPa/mm⁴ 与向下挠度为负。

## TDD 记录

1. 先新增 `tests/test_textbook_solver.py`。
2. RED：运行 `python -m pytest tests/test_textbook_solver.py -q`，因 `mechanics.textbook_solver` 不存在而失败（`ModuleNotFoundError`）。
3. 实现最小公共分流器及结果归一化。
4. GREEN：修正测试中的手算反力顺序后，聚焦测试通过。

## 验证

- `python -m pytest tests/test_textbook_solver.py -q`：7 passed
- `python -m pytest -q`：113 passed
- `git diff --check`：通过，无空白错误。

## 修复记录

### 根因

公共分流器直接复用底层解析求解器的宽松支座识别：只要存在一个 `pin` 和一个 `roller` 即判为解析构型。因此左端 `roller`/右端 `pin` 及内部两支座也会错误进入解析分支。

### TDD

1. 新增两个回归测试：
   - 参数化的非标准两支座布局测试，覆盖左滚右铰和内部两支座，要求走 FEM。
   - 三支座 FEM 统一结果契约测试，断言 `method`、`classification`、`shear_segments`、`moment_segments`、`metadata`、`x_mm`、`deflection_mm`、`checks` 均存在且形状合理。
2. RED：`python -m pytest tests/test_textbook_solver.py -q` → `2 failed, 7 passed`。两个非标准两支座参数均得到错误的 `analytical` 方法。
3. GREEN：公共入口改为仅在 `pin@0`、`roller@L`（或端部 `fixed` 且其余为 `free` 的悬臂）时选择解析分支。
4. GREEN：`python -m pytest tests/test_textbook_solver.py -q` → `9 passed`。
5. 修复后的全量验证：`python -m pytest -q` → `115 passed`。
