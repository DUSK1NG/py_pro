# 满跨均布荷载设计

新增 `mechanics/uniform_load.py`，处理全长均匀向下荷载 `q`。内部单位为 `L`（mm）、`q`（N/mm）、`E`（MPa）、`I`（mm⁴）；挠度向下为负。未来界面先用 `convert_distributed_load_to_n_per_mm()` 统一单位。

公共函数与现有模块一致：反力、剪力、弯矩、挠度和 `sample_beam()`。采样结果继续使用 `x`、`shear`、`moment`、`deflection`，可直接调用现有绘图函数。

公式：`RA=RB=qL/2`，`V(x)=qL/2-qx`，`M(x)=qx(L-x)/2`，`v(x)=-q*x*(L³-2Lx²+x³)/(24EI)`。跨中最大弯矩为 `qL²/8`，最大挠度为 `-5qL⁴/(384EI)`。

测试验证反力、两端弯矩/挠度、跨中经典极值、剪力跨中为零、非法参数拒绝，以及采样结果能直接绘图。本阶段不支持部分均布荷载或组合荷载。
