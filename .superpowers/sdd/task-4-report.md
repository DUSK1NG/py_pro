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

## 修复记录

### 根因

公共分流器直接复用底层解析求解器的宽松支座识别：只要存在一个 `pin` 和一个 `roller` 即判为解析构型。因此左端 `roller`/右端 `pin` 及内部两支座也会错误进入解析分支。
