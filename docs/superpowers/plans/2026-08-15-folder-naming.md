# 项目目录命名重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将公开项目目录 `sample_data` 重命名为 `examples`，将 `visualization` 重命名为 `plots`，并同步所有运行、测试和用户文档引用。

**Architecture:** 使用 Git 目录移动保留文件历史；Python 包导入由 `visualization` 统一切换为 `plots`；示例素材路径由 `sample_data` 统一切换为 `examples`。开发记录目录 `.superpowers`、`.worktrees`、`.venv` 和缓存目录不改动。

**Tech Stack:** Python、pytest、Streamlit、Git、GitHub Actions。

## Global Constraints

- 目录名保持小写，使用简洁英文单词，不使用空格或中文。
- 不修改 `mechanics`、`vision`、`ui`、`utils`、`tests` 的名称。
- 不修改历史开发报告和评审补丁中的原始路径记录。
- 完成后 `python -m pytest -q` 必须全部通过。
- 完成后 GitHub Actions 的 `compileall` 路径必须指向 `plots` 和 `examples`。

---

### Task 1: 移动目录并同步 Python 导入

**Files:**
- Rename: `sample_data/` → `examples/`
- Rename: `visualization/` → `plots/`
- Modify: `app.py`
- Modify: `app_styled.py`
- Modify: `vision/export_ui.py`
- Modify: `tests/test_plotting.py`
- Modify: `tests/test_plotting_curves.py`
- Modify: `tests/test_plotting_fonts.py`

**Interfaces:**
- `plots.plotting` 保持原有公开函数名和签名不变。
- `examples/` 中的数据文件内容和文件名保持不变。

- [ ] **Step 1: 移动目录**

```powershell
git mv sample_data examples
git mv visualization plots
```

- [ ] **Step 2: 更新绘图模块导入**

将所有 `from visualization...` 和 `import visualization...` 改为 `from plots...` 或 `import plots...`；不修改函数调用。

- [ ] **Step 3: 更新示例路径**

将代码和测试中的 `sample_data/` 路径改为 `examples/`，保留示例文件名不变。

- [ ] **Step 4: 编译检查**

运行：

```powershell
python -m compileall -q app.py app_styled.py mechanics utils vision plots
```

预期：命令退出码为 0。

- [ ] **Step 5: 提交代码目录变更**

```powershell
git add app.py app_styled.py vision tests examples plots
git commit -m "refactor: rename project data and plot folders"
```

### Task 2: 同步用户文档和 CI 配置

**Files:**
- Modify: `README.md`
- Modify: `docs/experiment_guide.md`
- Modify: `docs/project_report_outline.md`
- Modify: `.github/workflows/tests.yml`

**Interfaces:**
- README 中的目录树、示例数据链接和图片链接必须指向 `examples/` 与 `plots/`。
- CI 编译命令必须检查 `plots`。

- [ ] **Step 1: 更新 README 路径和目录说明**

将所有用户可见的 `sample_data` 替换为 `examples`，将 `visualization` 替换为 `plots`。

- [ ] **Step 2: 更新实验说明和项目报告大纲**

同步示例 CSV、参考图片和目录说明路径；不改变实验步骤和数据含义。

- [ ] **Step 3: 更新 GitHub Actions**

将 `compileall` 命令中的 `visualization` 改为 `plots`，并确认不再检查不存在的旧目录。

- [ ] **Step 4: 检查活动文件中的旧路径**

运行：

```powershell
rg -n --hidden --glob '!**/.git/**' --glob '!**/.venv/**' 'sample_data|visualization' README.md docs .github app.py app_styled.py mechanics vision ui utils tests examples plots
```

预期：无旧目录路径命中；历史 `.superpowers` 报告和 `docs/superpowers/reviews/final-review-package.diff` 不纳入活动路径检查。

- [ ] **Step 5: 提交文档和 CI 变更**

```powershell
git add README.md docs/experiment_guide.md docs/project_report_outline.md .github/workflows/tests.yml
git commit -m "docs: update paths after folder rename"
```

### Task 3: 全量验收

**Files:**
- Test: all files under `tests/`

- [ ] **Step 1: 运行完整测试**

```powershell
python -m pytest -q
```

预期：所有测试通过，失败数为 0。

- [ ] **Step 2: 检查 Git 状态和路径**

```powershell
git status --short --branch
Test-Path examples
Test-Path plots
Test-Path sample_data
Test-Path visualization
```

预期：`examples` 和 `plots` 为 `True`，旧目录为 `False`；除明确保留的既有未跟踪审查资料外，不出现额外临时文件。

- [ ] **Step 3: 记录验收结果**

将测试数量、编译结果和最终目录状态记录到交付说明中。
