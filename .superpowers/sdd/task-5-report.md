# Task 5 report: Streamlit textbook solver UI

## Delivered

- Added `ui.textbook_solver_ui.render_textbook_solver()` with a batched `st.form`.
- Added dynamic editors for supports, point loads, and distributed loads, plus simply-supported, cantilever, and clear-input templates.
- Converts submitted editor rows to Task 1 dataclasses, reports invalid input with `st.error`, and retains the last successful session solution on failure.
- Renders solver classification/method, input and reaction summaries, equilibrium checks, response charts, segment results, FEM metadata, and collapsible steps/warnings.
- Added a top-level mode switch in `app_styled.py`; the existing base-theory flow remains on its original rendering path.

## Fix follow-up

### Root cause and compatibility

- The template and clear branches changed editor values without removing the cached `textbook_solution` and `textbook_problem`, so a previous result remained visible for new input.
- `清空输入` also left the length, elastic modulus, and inertia fields unchanged.
- The new UI uses Streamlit string `width` values such as `"stretch"`; the dependency floor is now `streamlit>=1.51.0`, which explicitly supports that API rather than relying on `>=1.36`.
