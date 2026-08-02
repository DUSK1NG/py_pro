# Streamlit 最小界面 Implementation Plan

**Goal:** 创建可选择荷载类型与单位、展示理论结果和三张图的 Streamlit 页面。

**Files:** 新建 `app.py`、`tests/test_app.py`；更新 `requirements.txt` 与 `README.md`。

1. 先测试纯调度函数 `calculate_beam(...)`：跨中、任意位置、均布三类输入均返回统一结果字典；非法荷载类型抛出 `ValueError`。
2. 实现 `calculate_beam`：调用 `utils.units` 换算输入，分派到相应 `mechanics` 模块。
3. 创建 `app.py`：侧边栏下拉选择单位/荷载类型和数值输入；按钮触发计算；结果区显示指标与三张 Figure；捕获 `ValueError` 并显示中文错误。
4. 将 `streamlit>=1.36` 加入依赖，README 增加 `streamlit run app.py`。
5. 运行完整 pytest 并以 Streamlit 启动检查页面可加载，提交并推送草稿 PR。
