# 荷载—挠度 CSV 数据与曲线 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为简支梁系统增加多组荷载—挠度 CSV 导入、理论/实测曲线、误差统计和 Streamlit 展示。

**Architecture:** 使用独立的 `utils/load_deflection.py` 负责 CSV 解析、校验、理论值计算和误差统计；使用 `vision/load_deflection_ui.py` 负责上传、表格、图表和下载按钮；`app_styled.py` 仅负责传入当前理论结果并渲染区域。所有数据保持 N、mm 和 MPa 内部单位，不抓取在线数据。

**Tech Stack:** Python 3.11、csv、NumPy、Matplotlib、Streamlit、pytest。

## Global Constraints

- CSV 必须包含 `load_n` 和 `measured_deflection_mm` 两列。
- `load_n` 必须为有限非负数；挠度必须为有限数；至少两行且荷载不能重复。
- 向下挠度为负；理论值接近零时相对误差为空，避免除零。
- 网上资料只作为参考，不能替代真实实验结论。
- 原有 67 项测试必须保持通过。

---

### Task 1: CSV 数据解析与误差计算

**Files:**
- Create: `utils/load_deflection.py`
- Create: `tests/test_load_deflection.py`

**Interfaces:**
- Produces `load_deflection_from_csv(data: str) -> dict[str, object]`。
- Produces `calculate_load_deflection_comparison(load_n, measured_deflection_mm, theoretical_deflection_mm, relative_floor=1e-9) -> dict[str, object]`。

- [ ] **Step 1: Write failing tests**

测试合法 CSV 排序、缺列、空值、重复荷载、负荷载、长度不一致、相同曲线零误差和零理论值相对误差为空。

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_load_deflection.py -q`

Expected: FAIL because `utils.load_deflection` does not exist.

- [ ] **Step 3: Implement minimal parser and comparison**

使用 `csv.DictReader` 读取文本；将必需字段转换为 `float`；按荷载升序排序；返回 NumPy 数组和列名。比较函数计算理论值、误差、绝对误差、相对误差、最大绝对误差、平均绝对误差和合理范围布尔值。

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_load_deflection.py -q`

Expected: all tests PASS。

- [ ] **Step 5: Commit**

Run: `git add utils/load_deflection.py tests/test_load_deflection.py; git commit -m "feat: add load-deflection CSV processing"`

### Task 2: 示例数据与 CSV 导出

**Files:**
- Create: `sample_data/load_deflection_example.csv`
- Modify: `utils/export.py`
- Modify: `tests/test_export.py`

**Interfaces:**
- Produces `build_load_deflection_csv(comparison: dict[str, object]) -> str`。

- [ ] **Step 1: Write failing export test**

验证 CSV 表头包含荷载、实测、理论、误差和相对误差字段，输出可被 `csv.DictReader` 读取。

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/test_export.py -q`

Expected: FAIL because the exporter is not defined.

- [ ] **Step 3: Implement exporter and example**

使用当前示例梁参数生成 0—100 N 的演示数据，并在导出函数中按行写入比较结果；示例文件标注为演示数据，不作为真实实验结论。

- [ ] **Step 4: Run export tests**

Run: `python -m pytest tests/test_export.py -q`

Expected: all tests PASS。

- [ ] **Step 5: Commit**

Run: `git add sample_data/load_deflection_example.csv utils/export.py tests/test_export.py; git commit -m "feat: add load-deflection CSV export"`

### Task 3: Streamlit 荷载—挠度分析区域

**Files:**
- Create: `vision/load_deflection_ui.py`
- Modify: `app_styled.py`

**Interfaces:**
- Produces `render_load_deflection_analysis(theory_result: dict[str, object] | None) -> None`。
- Consumes `theory_result["max_deflection"]`, `theory_result["load"]` where available, and current beam result fields.

- [ ] **Step 1: Add UI smoke test expectations**

保持 `python -m py_compile app_styled.py vision/load_deflection_ui.py` 作为界面入口验收；纯计算测试继续放在 Task 1，不依赖 Streamlit 会话。

- [ ] **Step 2: Implement upload and rendering**

添加 `st.file_uploader` 接收 CSV；成功读取后显示 `st.dataframe`、理论/实测荷载—挠度曲线、最大/平均绝对误差、合理性提示和对比 CSV 下载按钮；错误通过 `st.error` 显示中文信息。

- [ ] **Step 3: Integrate into app**

在 `app_styled.py` 的理论结果和图像测量区域之后调用 `render_load_deflection_analysis(st.session_state.get("theory_result"))`；没有理论结果时显示提示且不计算。

- [ ] **Step 4: Compile and startup check**

Run: `python -m py_compile app_styled.py vision/load_deflection_ui.py`

Expected: exit code 0；短暂启动 Streamlit 后无启动错误。

- [ ] **Step 5: Commit**

Run: `git add app_styled.py vision/load_deflection_ui.py; git commit -m "feat: add load-deflection analysis UI"`

### Task 4: 全量验证、文档和远端同步

**Files:**
- Modify: `README.md`
- Modify: `docs/experiment_guide.md`

- [ ] **Step 1: Update documentation**

补充 CSV 必需字段、示例文件路径、演示数据与真实实验数据的区别，以及荷载—挠度曲线入口说明。

- [ ] **Step 2: Run full tests**

Run: `python -m pytest -q`

Expected: 原有 67 项加新增测试全部 PASS。

- [ ] **Step 3: Run compile and Streamlit startup checks**

Run: `python -m py_compile app_styled.py utils/load_deflection.py vision/load_deflection_ui.py utils/export.py`

Expected: exit code 0；Streamlit 启动输出本地 URL 且无 traceback。

- [ ] **Step 4: Commit and push**

Run: `git add README.md docs/experiment_guide.md; git commit -m "docs: document load-deflection CSV workflow"; git push origin master`

- [ ] **Step 5: Verify remote**

Run: `git status -sb; git ls-remote origin refs/heads/master`

Expected: 工作区干净，本地 master 与远端 master 同步。
