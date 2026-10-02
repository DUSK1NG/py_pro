# Task 2 报告：静定解析求解器

## 交付内容

- 新建 `mechanics/analytical_beam.py`，提供 `supports_analytical()`、`solve_simply_supported()` 与 `solve_cantilever()`。
- 支持任意多个集中力和部分均布荷载；反力由整体平衡求得，固定端反力包含力矩。
- 使用 Macaulay 括号式计算剪力、弯矩、转角和挠度，并按简支或悬臂边界条件确定积分常数。
- 结果包含分段采样、`x_mm`、`deflection_mm`、极值挠度、平衡校核、教学步骤、假设警告，以及可查询的 `shear_at()`、`moment_at()`、`theta_at()`。

## 范围与假设

仅考虑 mm/N/MPa/mm⁴ 内部单位、竖向荷载与 Euler–Bernoulli 小挠度弯曲；不计算轴向/水平反力、扭转、剪切变形或大挠度。Task 1 模型未扩展字段，因此将统一结果字段附加在 `BeamSolution` 实例上，未修改 Task 1 文件。

## 审查修复（Task 2）

### 根因与修复

- 原最大挠度逻辑在全梁固定扫描 2000 个区间内寻找转角变号；短荷载区间或正负荷载组合可使同一扫描格内存在多个零点，从而遗漏内部候选点。现按荷载与支座断点分段，利用每段三次转角式的驻点划分单调区间，再二分定位每个零点；所有分段端点也纳入比较。
- 原分段采样把集中力断点以右侧定义的剪力同时写入左段末端。现对含集中力断点的相邻段分别采用 `nextafter(a, left)` 与 `nextafter(a, right)`，使结果保留 `V(a-)` 和 `V(a+)`，且不改变 `SegmentResult` 或公开求解接口。
