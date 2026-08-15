# 项目目录命名规范设计

## 目标

将项目中含义不够直观的公开目录改为更符合 Python 项目习惯、便于新用户理解的名称，同时保持程序功能和导入结构不变。

## 目录变更

| 旧目录 | 新目录 | 说明 |
| --- | --- | --- |
| `sample_data` | `examples` | 示例数据、示例图片和实验参考素材 |
| `visualization` | `plots` | 剪力图、弯矩图和挠度图绘图代码 |

以下目录保持不变：`mechanics`、`vision`、`ui`、`utils`、`tests`。

## 同步范围

- Python 导入路径和包路径；
- GitHub Actions 中的编译检查路径；
- README、实验说明和项目报告中的目录及文件链接；
- 测试中的示例文件路径；
- Git 文件移动记录。

## 兼容性与验收

- 代码继续使用小写目录名，避免空格和中文路径带来的导入问题；
- `python -m pytest -q` 全部通过；
- `python -m compileall -q app.py app_styled.py mechanics utils vision plots` 通过；
- README 中不再出现旧目录路径；
- Git 状态只包含本次重命名及其引用同步变更。
