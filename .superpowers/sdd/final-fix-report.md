# 最终整分支修复报告

## 范围

按 `final-fix-brief.md` 修复最终审查的四项 Important，保持既有教材题 UI、Markdown/PDF、CSV 和基础理论流程兼容。未处理审查中的 Minor 或其他范围外需求。

## 改动摘要

1. **向上及混合荷载挠度极值**
   - 解析解由“最小代数挠度”改为“最大绝对挠度候选点”，返回值保留正负号。
   - FEM 对采样挠度按绝对值选极值，返回值保留正负号。
   - 覆盖解析/FEM 的纯向上跨中荷载及正负混合荷载。

2. **显式统一结果契约**
   - `BeamSolution` 显式声明方法、分类、曲线、反力、分段、校核、步骤、警告、元数据、FEM 节点结果、曲线查询函数、剪力/弯矩极值和 `diagram_data` 等公共字段。
   - `SegmentResult` 显式声明 `shear_expression`、`moment_expression`。
   - `ProblemClassification` 移入模型层；解析和 FEM 公开求解器直接构造分类完整的 `BeamSolution`。
   - 解析/FEM 不再动态挂载字段；公共分流器用 `dataclasses.replace()` 归一化分类、别名和元数据。
   - 测试用 `dataclasses.fields()` / `dataclasses.asdict()` 检查声明字段和序列化字典。

3. **教材式核心输出**
   - 解析分段给出局部坐标形式的可读 `V(x)`、`M(x)`；FEM 分段明确标记“数值采样（FEM）”。
   - 剪力极值比较每段单侧端点；弯矩极值额外比较每段/单元内部 `V=0` 的驻点，避免固定采样遗漏真实极值。
   - 统一结果提供带符号的 `max_shear`、`max_moment` 及位置，并提供梁、支座、荷载、反力的 `diagram_data`。
   - FEM 元数据增加网格范围、边界保留说明、插值模型和收敛/精度说明。
   - Streamlit 显示分段表达式、三类极值、受力简图数据和 FEM 节点挠度；Markdown/PDF 同步显示这些内容及 FEM 网格/精度说明。

4. **CSV 完整记录契约**
   - 保留前三列 `x_mm,deflection_mm,reaction_vertical_n` 的顺序。
   - 增加 `row_type,shear_n,moment_n,rotation_rad,reaction_moment_n,method,classification,check_sum_vertical_n,check_sum_moment_about_0_n_mm`。
   - 曲线使用 `row_type=curve`，反力使用独立 `row_type=reaction`；不再按浮点坐标把反力拼接到曲线点。
   - 集中力与支座同位时仍导出精确支座坐标和反力。

## 提交范围

- `mechanics/textbook_models.py`
- `mechanics/analytical_beam.py`
- `mechanics/beam_fem.py`
- `mechanics/textbook_solver.py`
- `ui/textbook_solver_ui.py`
- `utils/textbook_export.py`
- `tests/test_textbook_final_fixes.py`
- `tests/test_textbook_export.py`
- `tests/test_textbook_solver.py`
- `.superpowers/sdd/final-fix-report.md`

## 最终边界修复（final-fix2）

### 根因与最小修复

FEM 的 `_curve_extrema()` 已经为剪力候选保留各单元端点的左右极限，
但弯矩候选仍以精确节点坐标查询。内部节点按右侧单元定位，导致
`pin@0 + fixed@500 + roller@1000` 的固定支座左侧弯矩被右侧的零弯矩覆盖。

弯矩端点候选现与剪力一致，使用 `math.nextafter()` 查询每个单元的起、终点
单侧极限，同时仍把实际节点坐标作为报告的位置。
