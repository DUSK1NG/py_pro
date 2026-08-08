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

## TDD：RED 证据

### 1. 挠度极值

命令：

```text
python -m pytest tests/test_textbook_final_fixes.py -k 'upward or mixed' -q
```

结果：`4 failed, 5 deselected`。解析/FEM 的纯向上和混合荷载都错误返回支座处 `0.0 mm`。

### 2. 显式结果契约

命令：

```text
python -m pytest tests/test_textbook_final_fixes.py -k 'declares_and_serializes' -q
```

结果：`2 failed, 7 deselected`。`BeamSolution` 仅声明原四个字段，公共字段未进入 dataclass / `asdict()`。

### 3. 教材式输出

命令：

```text
python -m pytest tests/test_textbook_final_fixes.py -k 'textbook_expressions or markdown_and_ui' -q
```

结果：`2 failed, 7 deselected`。缺少分段表达式，报告/UI 缺少极值、简图和 FEM 节点/精度内容。

### 4. CSV

命令：

```text
python -m pytest tests/test_textbook_final_fixes.py tests/test_textbook_export.py -k 'csv' -q
```

结果：`3 failed, 23 deselected`。缺少新增字段与 `row_type`，仍依赖曲线坐标拼接反力。

CSV 转角列补充测试先失败：`1 failed, 8 deselected`（缺少 `rotation_rad`）；新增列后现有反力字段对齐断言再次以 `1 failed, 8 deselected` 捕获错位，再补齐独立反力行空字段。

### 审查补充 RED

提交前只读审查发现固定采样可能遗漏真实剪力/弯矩极值，且直接调用解析/FEM 时分类仍为 `None`。先增加回归：

```text
python -m pytest tests/test_textbook_final_fixes.py -k 'direct_solvers_populate or resultant_extrema' -q
```

结果：`4 failed, 9 deselected`。解析/FEM 分类均为空；部分均布荷载解析漏掉右支座左侧 `-375 N`，粗网格 FEM 漏掉 `x=625 mm` 的 `70312.5 N·mm` 弯矩极值。

## TDD：GREEN 证据

- 挠度极值：`4 passed, 5 deselected`。
- 显式结果契约：`2 passed, 7 deselected`。
- 教材式输出：`2 passed, 7 deselected`。
- CSV 完整契约：`3 passed, 23 deselected`。
- 审查补充的直接分类与真实极值：`4 passed, 9 deselected`。

## 最终验证

聚焦教材题、导出、报告与 Streamlit 回归：

```text
86 passed in 2.57s
```

语法编译：

```text
python -m py_compile mechanics/textbook_models.py mechanics/analytical_beam.py mechanics/beam_fem.py mechanics/textbook_solver.py ui/textbook_solver_ui.py utils/textbook_export.py utils/report.py app_styled.py
```

结果：退出码 `0`。

全量测试：

```text
python -m pytest -q
152 passed in 3.01s
```

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

### TDD：RED → GREEN

新增回归：4 单元、`-1000 N @ 250 mm`、内部固定支座 `@ 500 mm`。

RED：

```text
python -m pytest tests/test_textbook_final_fixes.py -k 'fem_moment_extrema_keep_one_sided_internal_support_endpoints' -q
```

结果：`1 failed, 13 deselected`。旧实现返回 `78125 N·mm @ 250 mm`，
没有报告内部固定支座左侧的 `-93750 N·mm @ 500 mm`。

GREEN：同一命令结果为 `1 passed, 13 deselected`。

### 最终验证

- FEM、教材题与导出聚焦回归：`76 passed in 2.30s`。
- `python -m py_compile mechanics/beam_fem.py`：退出码 `0`。
- 全量 `python -m pytest -q`：`153 passed in 2.69s`。
