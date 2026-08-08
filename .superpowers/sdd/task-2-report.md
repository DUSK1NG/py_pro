# Task 2 报告：静定解析求解器

## 交付内容

- 新建 `mechanics/analytical_beam.py`，提供 `supports_analytical()`、`solve_simply_supported()` 与 `solve_cantilever()`。
- 支持任意多个集中力和部分均布荷载；反力由整体平衡求得，固定端反力包含力矩。
- 使用 Macaulay 括号式计算剪力、弯矩、转角和挠度，并按简支或悬臂边界条件确定积分常数。
- 结果包含分段采样、`x_mm`、`deflection_mm`、极值挠度、平衡校核、教学步骤、假设警告，以及可查询的 `shear_at()`、`moment_at()`、`theta_at()`。

## TDD 记录

1. 先创建 `tests/test_textbook_analytical.py`，覆盖跨中集中力、部分均布荷载平衡、悬臂端点力、集中力剪力跳跃/均布段弯矩积分和支座识别。
2. 实现前运行 `python -m pytest tests/test_textbook_analytical.py -q`：按预期因 `mechanics.analytical_beam` 不存在而在导入阶段失败。
3. 最小实现后，解析测试通过。

## 验证结果

- `python -m pytest tests/test_textbook_analytical.py -q`：`5 passed in 0.05s`
- `python -m pytest -q`：`93 passed in 1.29s`

## 范围与假设

仅考虑 mm/N/MPa/mm⁴ 内部单位、竖向荷载与 Euler–Bernoulli 小挠度弯曲；不计算轴向/水平反力、扭转、剪切变形或大挠度。Task 1 模型未扩展字段，因此将统一结果字段附加在 `BeamSolution` 实例上，未修改 Task 1 文件。

## 审查修复（Task 2）

### 根因与修复

- 原最大挠度逻辑在全梁固定扫描 2000 个区间内寻找转角变号；短荷载区间或正负荷载组合可使同一扫描格内存在多个零点，从而遗漏内部候选点。现按荷载与支座断点分段，利用每段三次转角式的驻点划分单调区间，再二分定位每个零点；所有分段端点也纳入比较。
- 原分段采样把集中力断点以右侧定义的剪力同时写入左段末端。现对含集中力断点的相邻段分别采用 `nextafter(a, left)` 与 `nextafter(a, right)`，使结果保留 `V(a-)` 和 `V(a+)`，且不改变 `SegmentResult` 或公开求解接口。

### TDD 记录

1. 先新增集中力断点相邻分段的单侧剪力测试，运行聚焦套件时按预期失败：左段末端位置仍为 `500.0`。
2. 先新增同一分段双近根测试，运行聚焦套件时按预期失败：`_critical_positions()` 尚不接收断点，也只能执行固定全梁扫描。
3. 最小实现分段根搜索与单侧采样后，聚焦套件通过。
4. 额外覆盖两个不同位置的集中力、两段部分均布荷载、其内部极值根，以及右端固定悬臂的边界和平衡条件。

### 验证结果

- 红灯：`python -m pytest tests/test_textbook_analytical.py -q`：`2 failed, 7 passed`（集中力断点与分段根搜索两项预期缺陷）。
- 绿灯：`python -m pytest tests/test_textbook_analytical.py -q`：`9 passed in 0.04s`。
- 全量：`python -m pytest -q`：`97 passed in 1.26s`。
- `git diff --check`：无空白错误。

### 自审

- 公开接口 `supports_analytical`、`solve_simply_supported`、`solve_cantilever` 未改变；内部仍使用 mm/N/MPa/mm⁴ 和既有向上为正约定。
- 变更范围仅限解析求解器、对应测试和本报告；未回退其他任务的未跟踪文件。
