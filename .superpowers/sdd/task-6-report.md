# Task 6: 教材题报告、CSV 和图表导出

## Delivered

- Added `utils.textbook_export.build_textbook_markdown(problem, solution)` with input summary, solver method/static classification, reactions, equilibrium checks, segment summary, deflection summary, steps, and warnings.
- Added `utils.textbook_export.build_textbook_csv(solution)` with the stable UTF-8 text header `x_mm,deflection_mm,reaction_vertical_n`; non-reaction curve rows have an empty reaction cell.
- Re-exported `build_textbook_csv` from `utils.export`.
- Added `utils.report.build_textbook_pdf_report(problem, solution)`. It lays out the textual report directly and deliberately does not require chart image embedding.
- Extended `vision.report_ui.render_report_exports` with optional textbook problem/solution arguments, without changing legacy call sites. Textbook Markdown/PDF is generated only after clicking `生成报告`; textbook CSV is shown only while both cached textbook objects exist.
- Wired the textbook solver branch in `app_styled.py` to the report popover using cached session values. Existing theory/measurement Markdown and PDF paths are unchanged.

## TDD evidence

1. Added `tests/test_textbook_export.py` before implementation.
2. RED: `python -m pytest tests/test_textbook_export.py -q` failed with `ModuleNotFoundError: No module named 'utils.textbook_export'`.
3. GREEN: implemented Markdown/CSV, then the focused test passed (2 passed).
4. RED: added a PDF behavior test; test collection failed because `build_textbook_pdf_report` was absent.
5. GREEN: implemented textual PDF generation; focused tests passed (3 passed).
6. RED: added public-export and report-UI interface tests; each failed due to the missing interface.
7. GREEN: re-exported CSV and added optional report UI arguments plus the styled-app session wiring; focused tests passed (6 passed).
8. RED/GREEN: changed the report requirement test to require the literal `warnings` heading, observed failure, then updated the export heading and re-ran successfully.

## Verification

- `python -m pytest tests/test_textbook_export.py tests/test_report.py tests/test_report_extended.py tests/test_export.py -q` — 14 passed.
- `python -m py_compile utils/textbook_export.py utils/report.py utils/export.py vision/report_ui.py app_styled.py` — passed.
- `git diff --check` — passed; Git printed only existing CRLF advisories for touched Python files.
- `python -m pytest -q` — 127 passed.
