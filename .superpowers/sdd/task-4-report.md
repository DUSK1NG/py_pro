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
