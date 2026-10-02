# 教材梁题示例

## 交付范围

- 新增 `sample_data/textbook_examples.json`：三个内部单位（mm/N/MPa/mm⁴）教材梁题示例。
- 新增 `tests/test_textbook_examples.py`：加载 JSON，调用 `solve_textbook_beam`，验证方法、分类、竖向反力、最大挠度及其位置。
- 更新 `README.md`：教材题模式、支座与荷载录入、符号约定、FEM 分流、启动命令、示例位置和导出能力。

## Task 7 修复记录

### 实现

- 悬臂示例的 `expected` 现包含固定端反力弯矩 `fixed_reaction_moment_n_mm: 100000.0`。
