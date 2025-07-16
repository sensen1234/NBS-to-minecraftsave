# NBS-to-minecraftsave

一个将NBS（Note Block Studio）音乐文件转换为Minecraft可用格式的工具，支持生成WorldEdit schematic文件和Minecraft数据包函数。

## 功能特点

### 已实现功能
- 将NBS文件转换为**Minecraft数据包（.mcfunction）**
- 将NBS文件转换为**WorldEdit schematic（.schem）文件**
- 提供直观的GUI操作界面
  - 支持左右声相偏移设置
  - 支持多轨道组管理
  - 可设置偏移位置音符判断规则
  - 自由配置每个轨道组的基础方块、覆盖方块及坐标位置

### 待实现功能
- 更完善的GUI选点功能

## 安装说明

1. 确保已安装Python 3.8及以上版本
2. 安装依赖库：
```bash
pip install pynbs mcschematic PyQt6
```

## 使用方法

### 基本流程
1. 运行程序：
   - GUI模式：`python app.py`
   - 命令行模式：`python cli.py`（需修改配置文件后使用）

2. GUI版本直接在GUI里按提示操作即可
   命令行请修改config.py
   nbs里单个音符的左右声道偏移为音符相对于轨道组单直轨的左右偏移

4. 输出文件使用：
   - **Schematic文件**：通过WorldEdit导入到游戏中
   - **mcfunction文件**：
     1. 创建一个空的数据包
     2. 将数据包解压到你的存档文件夹`save/存档名/datapack`下
     3. 将生成的`.mcfunction`文件放入`functions`文件夹
     4. 在游戏中使用`/function <命名空间>:<文件名>`命令执行（如`/function test:test`）

## 配置说明

配置文件位于`nbs2save/core/config.py`，可手动修改以下参数：
- `GENERATE_CONFIG`：全局生成配置
  - `data_version`：Minecraft版本（如`Version.JE_1_21_4`）
  - `input_file`：输入NBS文件路径
  - `type`：输出类型（`schematic`或`mcfunction`）
  - `output_file`：输出文件名（不含扩展名）

- `GROUP_CONFIG`：轨道组配置
  - `base_coords`：基准坐标(x, y, z)
  - `layers`：包含的轨道ID列表
  - `block`：方块配置（`base`基础方块，`cover`覆盖方块）

## 许可证

本项目采用Apache License 2.0开源许可证，详情见[LICENSE](LICENSE)文件了解详情。

## 注意事项

- 小白小白版用户建议等待后续简化版本（已经有了，GUI，但是不太好用）
- 生成大型音乐文件可能需要较长时间（毕竟是一个一个音符来生成，大型推荐使用schem）
- 使用前请确保已备份你的Minecraft存档

## 反馈与贡献

欢迎提交issue和PR来帮助改进这个项目！由于作者是新人，代码可能存在不足，敬请谅解。
