# 满跨均布荷载 Implementation Plan

**Goal:** 新增满跨均布荷载简支梁的反力、剪力、弯矩、挠度与采样计算。

**Files:** 创建 `mechanics/uniform_load.py`、`tests/test_uniform_load.py`。

1. 先写失败测试：对 `L=1000`、`q=1`、`E=200000`、`I=1000000` 验证反力各 `500 N`、跨中剪力 `0`、最大弯矩 `125000 N·mm`、最大挠度 `-5qL⁴/(384EI)`，并验证两端边界与非法参数。
2. 运行 `python -m pytest tests/test_uniform_load.py -v`，确认失败源于模块不存在。
3. 实现 `support_reactions(length, load_intensity)`、`shear_force(x, length, load_intensity)`、`bending_moment(x, length, load_intensity)`、`deflection(x, length, load_intensity, elastic_modulus, inertia_moment)` 和 `sample_beam(...)`。采样结果使用现有绘图键。
4. 运行 `python -m pytest -v`，确认全量通过后提交并推送草稿 PR。
