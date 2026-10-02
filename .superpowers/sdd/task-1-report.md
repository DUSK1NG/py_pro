# Task 1：数据模型与输入校验报告

## 改动

- 新增 `mechanics/textbook_models.py`，提供 `Support`、`PointLoad`、`DistributedLoad`、`BeamProblem`、`Reaction`、`SegmentResult`、`BeamSolution` 和 `ProblemInputError`。
- `BeamProblem.validate()` 校验梁长、弹性模量和惯性矩为正；检查支座列表、类型、位置和重复位置；检查集中力与均布荷载的位置范围，以及均布荷载区间方向。
- `total_vertical_load_n()` 保持竖向荷载的代数符号，合并集中力与均布荷载的等效竖向力。
- 新增 `tests/test_textbook_models.py`，覆盖简报要求的越界支座、反向均布区间、带符号合计，并补充其余明确规定的拒绝条件。
- 未修改既有单荷载模块或单位换算模块。
