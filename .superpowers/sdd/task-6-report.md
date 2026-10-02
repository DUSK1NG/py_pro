# Task 6: 教材题报告、CSV 和图表导出

## Delivered

- Added `utils.textbook_export.build_textbook_markdown(problem, solution)` with input summary, solver method/static classification, reactions, equilibrium checks, segment summary, deflection summary, steps, and warnings.
- Added `utils.textbook_export.build_textbook_csv(solution)` with the stable UTF-8 text header `x_mm,deflection_mm,reaction_vertical_n`; non-reaction curve rows have an empty reaction cell.
- Re-exported `build_textbook_csv` from `utils.export`.
- Added `utils.report.build_textbook_pdf_report(problem, solution)`. It lays out the textual report directly and deliberately does not require chart image embedding.
- Extended `vision.report_ui.render_report_exports` with optional textbook problem/solution arguments, without changing legacy call sites. Textbook Markdown/PDF is generated only after clicking `生成报告`; textbook CSV is shown only while both cached textbook objects exist.
- Wired the textbook solver branch in `app_styled.py` to the report popover using cached session values. Existing theory/measurement Markdown and PDF paths are unchanged.

## Task 6 修复记录

### 实现

- 每个剪力/弯矩分段现在包含起止位置、剪力端点值、弯矩端点值和采样数；教材题 PDF 复用该报告结构。
- 展示缓存与导出缓存分离：失败保留上一次成功解的显示数据并使导出缓存失效；成功重新建立导出缓存；模板和清空输入一并清除。
- 报告入口仅使用独立导出缓存；新增可观察测试覆盖无教材解时隐藏下载、未点击生成不构建 Markdown/PDF、点击后按选择格式构建，以及理论报告旧分支。
