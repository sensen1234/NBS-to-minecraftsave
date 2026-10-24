# NBS-to-minecraftsave

> 🎵 将 Note Block Studio 制作的音乐文件（`.nbs`）转换为 Minecraft 中可播放格式的强大工具

<span align="center">

[![Version](https://img.shields.io/github/v/release/sensen1234/NBS-to-minecraftsave?label=Version&color=blue)](https://github.com/sensen1234/NBS-to-minecraftsave/releases)
[![Python Version](https://img.shields.io/badge/Python-3.10--3.13-brightgreen?logo=python)](https://www.python.org/downloads/)
[![Minecraft Version](https://img.shields.io/badge/Minecraft-JE%201.13--26.1.1-5C2D91?logo=minecraft)](https://github.com/sensen1234/NBS-to-minecraftsave)
[![License](https://img.shields.io/github/license/sensen1234/NBS-to-minecraftsave?color=yellow)](https://github.com/sensen1234/NBS-to-minecraftsave/blob/master/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/sensen1234/NBS-to-minecraftsave?color=important)](https://github.com/sensen1234/NBS-to-minecraftsave/issues)
[![GitHub stars](https://img.shields.io/github/stars/sensen1234/NBS-to-minecraftsave?style=social)](https://github.com/sensen1234/NBS-to-minecraftsave/stargazers)

</span>

---

## 声明

**严禁使用本程序用于生成与《花之舞》(Flower Dance) 有关的 nbs。如需生成，请联系[sensen1234](https://github.com/sensen1234)获取授权。**  
**严禁将本程序用于商业用途（如有需要需授权）**  
**使用本程序生成的作品如发布到视频平台（如 BiliBili Youtube 抖音 Acfun 快手 等等）需要在视频简介标注使用本程序生成**

## 功能特点

### 已实现功能

- [x] 将 NBS 文件转换为**Minecraft 数据包（.mcfunction）**
- [x] 将 NBS 文件转换为**WorldEdit schematic（.schem）文件**
- [x] 提供直观的 GUI 操作界面
  - [x] 支持左右声相偏移设置
  - [x] 支持多轨道组管理
  - [x] 可设置偏移位置音符判断规则
  - [x] 自由配置每个轨道组的基础方块、覆盖方块及坐标位置
  - [x] 支持水平布局、阶梯向下、阶梯向上三种生成模式

### 创作与预览

- [x] GUI 选点功能
  - [x] 二维双视角切换：南视图 (X-Y) 和西视图 (Z-Y)
  - [x] 拖拽选点 + 数值精确输入
  - [x] 键盘方向键微调 (±1 / Shift+±10)
  - [x] 十字准星实时位置指示
  - [x] 自适应视图 (适应全部) 和重置视图
  - [x] 坐标轴刻度标注
  - [x] 底部状态栏实时坐标显示
  - [x] 3D 实际结构预览：音符盒、基座、红石、中继器及上下阶梯布局
  - [x] 旋转、平移、缩放及方块坐标／属性查看，修改组坐标后自动更新
  - [x] 多组坐标工作台，切组、拖动、精确输入、统一应用或取消
  - [x] NoteBetter 自定义音色、下垫块、OGG 样本及一键导出安装包
  - [x] 根据实际音符盒位置进行双耳空间试听，并可保存 WAV
  - [x] 自动显示歌曲概览，检查未分配轨道、音域和缺失采样
  - [x] 坐标撤销 / 重做、批量平移、等距排列和恢复初始布局
  - [x] 复制轨道组与音色、直接试听 OGG 采样、监听位置快捷定位

### 推荐创作流程

1. **创作项目**：选择 NBS，查看曲名、节奏、音符与轨道概览，设置输出位置和格式。
2. **轨道布局**：为每组填写 NBS 轨道 ID（从 0 开始，逗号分隔），设置方块和生成方式。复制组可快速搭建相似声部。
3. **创作工作台**：调整全部组的位置，切换 2D / 3D 检查结构，设置监听点试听。布局工具可批量平移或按 Z 轴等距排列；坐标修改支持撤销、重做。
4. **自定义音色**（可选）：从 NBS 导入音色，关联独立底座和单声道 OGG，先试听采样，再导出 NoteBetter 安装包。
5. **创作检查与导出**：运行「创作检查」处理提示，保存项目 JSON，再导出结构。

左侧「外观」可切换浅色、深色或跟随系统，程序会记住选择。常用快捷键：`Ctrl+S` 保存项目、`Ctrl+O` 打开项目、`Ctrl+Shift+P` 打开工作台、`Ctrl+Shift+K` 创作检查；工作台中 `Ctrl+Z` 撤销、`Ctrl+Shift+Z` 重做。

### 坐标与试听工作台

在「创作项目」选择 NBS 文件后，打开「轨道布局 → 打开创作工作台」，或使用首页快捷入口。左侧选择任意组，输入 XYZ 或拖动二维点位；所有组的修改会保留在同一份草稿中。点击「应用全部并关闭」统一写回，点击取消丢弃本次编辑。布局工具会先展示修改前后的坐标，确认后一起应用；撤销可回退整次批量修改。

切换「3D 预览」可查看实际音符盒、垫块、红石及阶梯布局。点击方块或组原点选组，拖动选中组原点可移动 XZ，Shift 拖动修改高度，Alt+左键可在空白处移动当前组。普通左键拖动旋转，右键或中键平移，滚轮缩放，悬停查看世界坐标及方块属性。预览复用导出逻辑；材质为示意，不模拟红石运行。长曲目可调整起始 tick 和显示长度，显示区计入跨 tick 及跨组覆盖。阶梯布局需选择 schematic 输出。

试听面板输入监听双耳的世界坐标和朝向（0° 朝南 +Z，90° 朝西 −X），点击「生成并试听」。推荐使用耳机；试听使用最终结构中的音符盒位置，模拟距离衰减、方向、双耳时差及头部遮挡。可选择 NBS 原曲速度或红石 10 tick/秒，并将结果保存为双声道 WAV。每次最多试听 120 秒，修改位置或监听参数后需重新生成。

自定义音色使用指定 OGG；原版音色可通过「Minecraft 音色目录」选择含 `harp.ogg` 等文件的 `note` 目录或资源包根目录。程序不分发游戏音频，未提供本地原版采样时会明确标为合成参考音色。试听用于空间布局参考，未模拟房间反射、方块遮音、个体 HRTF 或红石故障，不保证与游戏录音完全一致。

### NoteBetter 自定义音色

在「自定义音色」新增条目，或从当前 NBS 导入其自定义乐器。每个条目指定 NBS 乐器 ID、名称、下垫块、声音 ID、样本原音键和单声道 OGG Vorbis 文件。NBS 自定义 ID 通常从 16 开始，也可覆盖 0–15 的原版乐器。原音键采用 NBS key（默认 45），导出映射会校正样本音高；结构沿用原有的 key 33–57 音域，超出时沿用 note=0 的处理。

每种音色须使用不同的下垫块。NoteBetter 按底座方块 ID 匹配，配置会影响所有使用该底座的音符盒，请避免与其他乐器共享底座。结构导出、3D 预览与试听共用这些配置；保存项目 JSON 会保存音色设置及文件路径，后续再次导出仍需原 OGG 文件。

点击音色页的导出按钮，程序校验样本后生成一个 NoteBetter 安装包，包含：

- `config/notebetterfabric.json`：真实的 NoteBetter 底座映射。
- `resourcepacks/nbs2save-custom-instruments.zip`：可直接启用的音效资源包，含 `sounds.json` 和 OGG。
- `README.txt`：对应游戏版本的安装步骤及模组下载链接。

每位听众需安装兼容的 [NoteBetter Fabric 维护版](https://github.com/chsbuffer/NoteBetter)，将配置放入客户端 `config`（已有配置请合并 `mappings`），将内层 ZIP 放入 `resourcepacks` 并启用，然后重启游戏。外层 ZIP 是安装包。资源包格式默认跟随目标游戏版本，也可手动指定；生成资源包不代表模组已验证兼容该游戏版本。自定义映射默认听距 16 格，原版音符盒为 48 格。

## 安装说明

1. 确保已安装 uv(0.11 及以上版本)
2. 安装依赖库：

```sh
uv sync
```

## 使用方法

详细使用请见[wiki.md](/documents/wiki.md)

### 基本流程

1. 运行程序：
   - GUI 模式：`uv run src/app.py`
   - 命令行模式：`uv run src/cli.py`（需修改配置文件后使用）

2. GUI 版本直接在 GUI 里按提示操作即可
   命令行请修改`src/nbs2save/core/config.py`  
   nbs 里单个音符的左右声道偏移为音符相对于轨道组单直轨的左右偏移
   举个例子我进入声道模式，对某个**音符**进行了声道设置，我设置的为左声道，20  
   那么程序生成结果如下（空方块为音符盒）

```txt
│       ■
│       ■
│   □ ■ ■
│       ■        ↑↑↑（中继器朝向）
```

也就是会相对于主干结构的左边 2 格，生成音符盒  
 如果声道设置为 30 那么会为左边三格，若为 31，则会四舍五入为 30，以此类推  
 ⚠ nbs 左边设置的，整个轨道的声像偏移，本程序无法识别

1. 输出文件使用：
   - **Schematic 文件**：通过 WorldEdit 导入到游戏中
   - **mcfunction 文件**：
     1. 创建一个空的数据包
     2. 将数据包解压到你的存档文件夹`save/存档名/datapack`下
     3. 将生成的`.mcfunction`文件放入`functions`文件夹
     4. 在游戏中使用`/function <命名空间>:<文件名>`命令执行（如`/function test:test`）

## 配置说明

配置文件位于`nbs2save/core/config.py`，可手动修改以下参数：

- `GENERATE_CONFIG`：全局生成配置
  - `data_version`：Minecraft 版本（如`Version.JE_1_21_4`）
  - `input_file`：输入 NBS 文件路径
  - `type`：输出类型（`schematic`或`mcfunction`）
  - `output_file`：输出文件名（不含扩展名）
  - `custom_instruments`：自定义音色列表，每项包含 `nbs_id`、`name`、`base_block`、`sound_id`、`sound_file`、`root_key`

- `GROUP_CONFIG`：轨道组配置
  - `base_coords`：基准坐标 (x, y, z)
  - `layers`：包含的轨道 ID 列表
  - `block`：方块配置（`base`基础方块，`cover`覆盖方块）
  - `generation_mode`：生成模式（`default` 水平布局、`staircase` 阶梯向下、`staircase_up` 阶梯向上）

## 生成模式说明

### 默认模式（default）

在默认模式下，所有音符平台和红石线都保持在同一水平高度上，适用于大多数情况。

### 阶梯向下模式（staircase）

阶梯向下模式是一种增强的生成方式，当左右偏移大于等于 3 时，会启用阶梯效果：

- 左右偏移>=3 的音符平台将逐级向下阶梯式生成
- 左右偏移为 1、2 的音符平台保持与默认模式一致

这种模式可以创建更立体的视觉效果，特别适用于大型音乐作品，能更好地展示音符的声像分布。

### 阶梯向上模式（staircase_up）

与阶梯向下相对应，音符平台向上延伸。两种阶梯模式均需选择 Schematic 输出；mcfunction 仅支持水平布局。

## 核心变量说明

在本项目中，有几个关键变量用于确定音符在 Minecraft 世界中的位置：

### tick_x 变量

`tick_x` 是用于计算音符在 Minecraft 世界中 X 坐标位置的变量。它的计算公式是：

```python
tick_x = self.base_x + tick * 2
```

这个变量的含义是：

- `self.base_x`：轨道组的基准 X 坐标，即整个轨道组在 Minecraft 世界中的起始 X 位置
- `tick`：当前音符的 NBS 时间刻，时长由歌曲的 NBS tick/秒决定；它与 Minecraft 的游戏刻不同
- `tick * 2`：每个时间点（tick）在 X 轴上占用 2 格空间，这样设计是为了给每个音符留出足够的空间放置红石中继器等组件

因此，`tick_x` 表示在特定时间点（tick）上，音符应该放置的 X 坐标位置。

### 其他相关变量

- `base_x, base_y, base_z`：轨道组的基准坐标，定义了整个轨道组在 Minecraft 世界中的起始位置
- `pan_offset`：声像偏移量，表示音符在 Z 轴上的偏移，用于实现立体声效果
- `z_pos`：音符在 Z 轴上的最终位置，计算公式为 `z_pos = self.base_z + pan_offset`
- `cover_block`：覆盖方块，通常用于隐藏红石线路
- `base_block`：基础方块，构成平台的主体部分

## 工作原理

在 Minecraft 中播放音乐时，需要按照时间顺序激活音符盒。这个系统通过以下方式工作：

1. 每个 NBS tick 在 X 轴方向上占据 2 格空间；当前红石线路按 10 个 NBS tick/秒推进
2. 在每个 tick 位置上，构建一个基础结构，包括：
   - 红石中继器（用于时钟信号）
   - 覆盖方块和基础方块（构成平台）
3. 根据音符的声像偏移（panning）在 Z 轴方向上进行偏移
4. 当多个音符在同一 tick 但不同声像位置时，会生成延伸的平台

这种设计使得音乐可以在 Minecraft 中以可视化的方式播放，每个音符在正确的时间和位置被激活。

## 许可证

本项目采用 Apache License 2.0 开源许可证，详情见[LICENSE](LICENSE)文件了解详情。

## 注意事项

- 建议先在 GUI 中完成轨道分组、布局与试听，再导出到游戏验证。
- 大型曲目生成时间较长，推荐使用 Schematic；预览和试听可先选择短片段。
- 使用前请确保已备份你的 Minecraft 存档

## 反馈与贡献

欢迎提交 issue 和 PR 来帮助改进这个项目！由于作者是新人，代码可能存在不足，敬请谅解。
