# Task 7 验收报告

## 交付范围

- 新增 `sample_data/textbook_examples.json`：三个内部单位（mm/N/MPa/mm⁴）教材梁题示例。
- 新增 `tests/test_textbook_examples.py`：加载 JSON，调用 `solve_textbook_beam`，验证方法、分类、竖向反力、最大挠度及其位置。
- 更新 `README.md`：教材题模式、支座与荷载录入、符号约定、FEM 分流、启动命令、示例位置和导出能力。

## TDD 记录

先新增示例回归测试并运行 `python -m pytest tests/test_textbook_examples.py -q`。首次运行因 `sample_data/textbook_examples.json` 不存在而失败（`FileNotFoundError`）；添加 JSON 示例及 README 后，聚焦测试通过。

## 验收结果

- `python -m pytest tests/test_textbook_examples.py -q`：1 passed
- `python -m py_compile app.py app_styled.py mechanics/*.py ui/*.py utils/*.py vision/*.py`：通过（PowerShell 不展开通配符，使用等价的文件列表调用完成检查）
- `python -m pytest -q`：139 passed
