# Task 1：数据模型与输入校验报告

## 改动

- 新增 `mechanics/textbook_models.py`，提供 `Support`、`PointLoad`、`DistributedLoad`、`BeamProblem`、`Reaction`、`SegmentResult`、`BeamSolution` 和 `ProblemInputError`。
- `BeamProblem.validate()` 校验梁长、弹性模量和惯性矩为正；检查支座列表、类型、位置和重复位置；检查集中力与均布荷载的位置范围，以及均布荷载区间方向。
- `total_vertical_load_n()` 保持竖向荷载的代数符号，合并集中力与均布荷载的等效竖向力。
- 新增 `tests/test_textbook_models.py`，覆盖简报要求的越界支座、反向均布区间、带符号合计，并补充其余明确规定的拒绝条件。
- 未修改既有单荷载模块或单位换算模块。

## 测试先行记录

1. 新建测试后，在模型模块不存在时运行 `python -m pytest tests/test_textbook_models.py -q`，按预期以 `ModuleNotFoundError: mechanics.textbook_models` 失败。
2. 扩展所有简报列出的校验测试后，再次在模块不存在时运行同一命令，仍按预期以相同缺失模块错误失败。
3. 再实现最小模型与校验逻辑。

## 提交

- 实现与测试提交：`8846843a8564672d4b07b418c2da938ec5403222`（`Add textbook beam data models`）

## 测试结果

- `python -m pytest tests/test_textbook_models.py -q`：11 passed in 0.03s
- `python -m pytest -q`：88 passed in 1.31s

## 自审

- 数据模型内部单位保持为 mm、N、MPa、mm⁴；荷载不强制为正，符合向上正、向下负的约定。
- 每个位置均按闭区间 `[0, length_mm]` 校验；均布荷载另要求 `start_mm < end_mm`。
- 新逻辑独立于现有 `mechanics.point_load` 和 `mechanics.uniform_load`，全量测试通过。

## 疑问

- 简报仅要求提供 `SegmentResult` 与 `BeamSolution` 名称，未规定它们的字段契约；当前采用后续求解器可直接填充的最小通用字段。若后续任务需要不同的结果字段，应在其任务中明确后再扩展。
