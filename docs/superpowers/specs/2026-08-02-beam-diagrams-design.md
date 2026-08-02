# 第二阶段设计：简支梁内力与挠度图绘制

## 目标与范围

在已完成的跨中集中力简支梁计算模块基础上，使用 Matplotlib 分别绘制剪力图、弯矩图和理论挠度曲线。函数既可返回图对象供后续 Streamlit 使用，也可选择保存 PNG 文件。

本阶段不修改已有力学公式，不新增界面、OpenCV、任意位置集中力、均布荷载或数据导出功能。

## 模块边界

新增 `visualization/plotting.py`。该模块只消费 `mechanics.central_point_load.sample_beam()` 返回的结果字典，不重新计算反力、剪力、弯矩或挠度。

提供以下函数：

- `plot_shear_force(result, save_path=None)`：返回剪力图 Figure。
- `plot_bending_moment(result, save_path=None)`：返回弯矩图 Figure。
- `plot_deflection(result, save_path=None)`：返回挠度图 Figure。

`save_path` 为 `None` 时不写入文件；传入路径时创建对应 PNG。绘图函数不调用 `plt.show()`，由调用方决定如何展示或关闭图形。

## 图形约定

横坐标均为梁位置 `x`（mm）。剪力图纵坐标为剪力（N），使用阶梯线体现跨中集中力导致的跳变；弯矩图纵坐标为弯矩（N·mm）；挠度图纵坐标为挠度（mm）。

三张图均包含中文标题、坐标轴标签、网格、零线和图例。弯矩图和挠度图以跨中解析极值位置添加标记与数值注释；挠度曲线保留当前力学模块的符号约定，即向下为负。

## 输入校验与错误处理

结果字典缺少 `x` 或相应曲线键、数组长度不一致、数组为空、数据不是有限数值时，绘图函数抛出带中文说明的 `ValueError`。无法保存至给定路径时，让底层的文件异常向调用方显式传递。

## 测试与验收

使用 Matplotlib 非交互式 `Agg` 后端，避免测试时弹出窗口。

1. 对已知 `sample_beam()` 结果，三个绘图函数均返回 `matplotlib.figure.Figure`。
2. 验证每张图的主曲线横、纵数据分别与结果字典中的 `x` 和对应数据一致。
3. 验证剪力图主曲线使用阶梯绘制方式。
4. 传入临时 PNG 路径时验证文件存在且非空。
5. 验证缺少键、空数组和长度不一致的数据会抛出 `ValueError`。

验收标准：所有第一阶段和第二阶段测试通过；保存的 PNG 可打开；无 Streamlit 或 OpenCV 依赖。

## 后续衔接

第三阶段将在不改变本模块接口的前提下扩展任意位置集中力；Streamlit 阶段可直接接收本模块返回的 Figure 对象。
