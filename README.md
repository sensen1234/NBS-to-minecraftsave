# NBS-to-minecraftsave

一个将NBS（Note Block Studio）音乐文件转换为Minecraft可用格式的工具，支持生成WorldEdit schematic文件和Minecraft数据包函数。
## 严禁使用本程序用于生成与《花之舞》(Flower Dance）有关的nbs!!!! 如需生成，请联系我获取授权。
## 严禁将本程序用于商业用途（如有需要需授权）

## 功能特点

### 已实现功能
- 将NBS文件转换为**Minecraft数据包（.mcfunction）**
- 将NBS文件转换为**WorldEdit schematic（.schem）文件**
- 提供直观的GUI操作界面
  - 支持左右声相偏移设置
  - 支持多轨道组管理
  - 可设置偏移位置音符判断规则
  - 自由配置每个轨道组的基础方块、覆盖方块及坐标位置
  - 支持两种生成模式：默认模式和阶梯向下模式

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
   举个例子我进入声道模式，对某个**音符**进行了声道设置，我设置的为左声道，20  
   那么程序生成结果如下（空方块为音符盒）  
```
│       ■  
│       ■  
│   □ ■ ■  
│       ■        ↑↑↑（中继器朝向）
```
   也就是会相对于主干结构的左边2格，生成音符盒  
   如果声道设置为30 那么会为左边三格，若为31，则会四舍五入为30，以此类推  
   ⚠ nbs左边设置的，整个轨道的声像偏移，本程序无法识别  
 
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
  - `generation_mode`：生成模式（`default`默认模式或`staircase`阶梯向下模式）

## 生成模式说明

### 默认模式（default）
在默认模式下，所有音符平台和红石线都保持在同一水平高度上，适用于大多数情况。

### 阶梯向下模式（staircase）
阶梯向下模式是一种增强的生成方式，当左右偏移大于等于3时，会启用阶梯效果：
- 左右偏移>=3的音符平台将逐级向下阶梯式生成
- 左右偏移为1、2的音符平台保持与默认模式一致

这种模式可以创建更立体的视觉效果，特别适用于大型音乐作品，能更好地展示音符的声像分布。

## 核心变量说明

在本项目中，有几个关键变量用于确定音符在Minecraft世界中的位置：

### tick_x 变量
`tick_x` 是用于计算音符在Minecraft世界中X坐标位置的变量。它的计算公式是：
```python
tick_x = self.base_x + tick * 2
```

这个变量的含义是：
- `self.base_x`：轨道组的基准X坐标，即整个轨道组在Minecraft世界中的起始X位置
- `tick`：当前音符的时间点（以游戏刻度为单位）
- `tick * 2`：每个时间点（tick）在X轴上占用2格空间，这样设计是为了给每个音符留出足够的空间放置红石中继器等组件

因此，`tick_x` 表示在特定时间点（tick）上，音符应该放置的X坐标位置。

### 其他相关变量
- `base_x, base_y, base_z`：轨道组的基准坐标，定义了整个轨道组在Minecraft世界中的起始位置
- `pan_offset`：声像偏移量，表示音符在Z轴上的偏移，用于实现立体声效果
- `z_pos`：音符在Z轴上的最终位置，计算公式为 `z_pos = self.base_z + pan_offset`
- `cover_block`：覆盖方块，通常用于隐藏红石线路
- `base_block`：基础方块，构成平台的主体部分

## 工作原理

在Minecraft中播放音乐时，需要按照时间顺序激活音符盒。这个系统通过以下方式工作：

1. 每个tick（游戏刻）在X轴方向上占据2格空间
2. 在每个tick位置上，构建一个基础结构，包括：
   - 红石中继器（用于时钟信号）
   - 覆盖方块和基础方块（构成平台）
3. 根据音符的声像偏移（panning）在Z轴方向上进行偏移
4. 当多个音符在同一tick但不同声像位置时，会生成延伸的平台

这种设计使得音乐可以在Minecraft中以可视化的方式播放，每个音符在正确的时间和位置被激活。

## 许可证

本项目采用Apache License 2.0开源许可证，详情见[LICENSE](LICENSE)文件了解详情。

## 注意事项

- 小白小白版用户建议等待后续简化版本（已经有了，GUI，但是不太好用）
- 生成大型音乐文件可能需要较长时间（毕竟是一个一个音符来生成，大型推荐使用schem）
- 使用前请确保已备份你的Minecraft存档

## 反馈与贡献

欢迎提交issue和PR来帮助改进这个项目！由于作者是新人，代码可能存在不足，敬请谅解。
