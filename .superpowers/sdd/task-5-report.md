# Task 5 report: Streamlit textbook solver UI

## Delivered

- Added `ui.textbook_solver_ui.render_textbook_solver()` with a batched `st.form`.
- Added dynamic editors for supports, point loads, and distributed loads, plus simply-supported, cantilever, and clear-input templates.
- Converts submitted editor rows to Task 1 dataclasses, reports invalid input with `st.error`, and retains the last successful session solution on failure.
- Renders solver classification/method, input and reaction summaries, equilibrium checks, response charts, segment results, FEM metadata, and collapsible steps/warnings.
- Added a top-level mode switch in `app_styled.py`; the existing base-theory flow remains on its original rendering path.

## TDD evidence

1. Added `tests/test_textbook_ui_import.py` before UI production code.
2. Confirmed RED: `ModuleNotFoundError: No module named 'ui'`.
3. Implemented the UI module and confirmed GREEN.

## Verification

- `python -m pytest tests/test_textbook_ui_import.py tests/test_app.py -q` — 4 passed.
- `python -m py_compile app_styled.py ui/textbook_solver_ui.py ui/__init__.py` — passed.
- `python -m pytest -q` — 117 passed.
- `git diff --check` — no patch errors (Git emitted only the repository's CRLF advisory for `app_styled.py`).
- New UI code does not add `use_container_width`; pre-existing occurrences remain in the unchanged base-theory path.

## Fix follow-up

### Root cause and compatibility

- The template and clear branches changed editor values without removing the cached `textbook_solution` and `textbook_problem`, so a previous result remained visible for new input.
- `清空输入` also left the length, elastic modulus, and inertia fields unchanged.
- The new UI uses Streamlit string `width` values such as `"stretch"`; the dependency floor is now `streamlit>=1.51.0`, which explicitly supports that API rather than relying on `>=1.36`.

### TDD evidence

1. Added behavior-level tests for both templates and clear input invalidating cached results, clear input resetting scalar/table defaults, failed conversion retaining the old result, and the styled entrypoint importing the solver mode.
2. Confirmed RED with `python -m pytest tests/test_textbook_ui_import.py -q`: 3 failed, 2 passed. The failures were the missing state-transition/submit helpers (`apply_simply_supported_template`, `apply_clear_input`, and `submit_textbook_problem`).
3. Implemented minimal side-effect-free state helpers and used them from the Streamlit button and submit paths. Confirmed GREEN: 6 passed.

### Final verification

- `python -m pytest tests/test_textbook_ui_import.py tests/test_app.py -q` — 8 passed.
- `python -m py_compile app_styled.py ui/textbook_solver_ui.py` — passed.
- `python -m pytest -q` — 121 passed.
