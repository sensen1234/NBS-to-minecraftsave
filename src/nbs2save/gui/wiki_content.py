#!/usr/bin/env python3
"""
自动生成的 Wiki 结构化数据

此文件由 tools/generate_wiki_ui.py 从 documents/wiki.md 自动生成。
请勿手动修改。修改 wiki.md 后重新运行:

    python tools/generate_wiki_ui.py
"""


def build_wiki_content(el):
    """向 Interpreter 添加 wiki 内容元素"""

    el.add_heading(1, "NBS-to-Minecraftsave 完整使用指南")
    el.add_blockquote("**NBS-to-Minecraftsave** 是一款强大的转换工具，可将 Note Block Studio 制作的音乐文件 (`.nbs`) 转换为 Minecraft 中可播放的格式。")
    el.add_separator()
    el.add_heading(2, "一、环境准备")
    el.add_heading(3, "1.1 系统要求")
    el.add_table(
        headers=["项目", "要求"],
        rows=[
            ["**操作系统**", "Windows 10/11、macOS、Linux 均可 (只要能运行 python 就行)"],
            ["**Python 版本**", "Python 3.8 及以上版本"],
            ["**Minecraft 版本**", "Java Edition 1.13 至 26.1.1"],
        ],
    )
    el.add_heading(3, "1.2 必要软件安装")
    el.add_heading(4, "步骤 1：安装 Python")
    el.add_numbered_list([
        "访问 [Python 官网](https://www.python.org/downloads/)",
        "下载 Python 3.8 或更高版本",
        "安装时**务必勾选 \"Add Python to PATH\"**(添加到环境变量)",
        "打开命令提示符 (PowerShell)，输入以下命令验证安装：",
    ])
    el.add_code_block("sh", "   python --version")
    el.add_paragraph("**若成功安装，应显示版本号**：")
    el.add_code_block("ansi", "   Python 3.x.x")
    el.add_heading(4, "步骤 2：安装 Git(可选)")
    el.add_blockquote("💡 仅在需要通过 Git 克隆仓库时安装")
    el.add_numbered_list([
        "访问 [Git 官网](https://git-scm.com/download/win)",
        "下载并安装 Git",
        "安装完成后验证：",
    ])
    el.add_code_block("sh", "   git --version")
    el.add_separator()
    el.add_heading(2, "二、下载与安装")
    el.add_heading(3, "2.1 方式一：通过 Git 克隆 (推荐)")
    el.add_paragraph("打开 PowerShell，运行以下命令：")
    el.add_code_block("sh", "# 克隆仓库到本地\ngit clone https://github.com/sensen1234/NBS-to-minecraftsave.git\n\n# 进入项目目录\ncd NBS-to-minecraftsave")
    el.add_heading(3, "2.2 方式二：手动下载")
    el.add_numbered_list([
        "访问项目 GitHub 页面 (<https://github.com/sensen1234/NBS-to-minecraftsave>)",
        "点击 Releases",
    ])
    el.add_image("![Releases](img/image.png)", "")
    el.add_numbered_list([
        "找到最新版，点击 Assets 里面的 Source code 进行下载",
    ])
    el.add_image("![Download ZIP](img/efcc02de891be4ea97d4dd1bc111b846.png)", "")
    el.add_numbered_list([
        "解压下载的文件到任意任意目录 (尽量为英文目录)",
    ])
    el.add_heading(3, "2.3 安装依赖")
    el.add_paragraph("程序需要以下 Python 库：")
    el.add_table(
        headers=["库名称", "版本要求", "作用描述"],
        rows=[
            ["`pynbs`", "最新稳定版", "读取和解析 NBS 文件格式"],
            ["`mcschematic`", "最新稳定版", "生成 Minecraft 结构文件"],
            ["`PyQt6`", "最新稳定版", "提供图形用户界面框架"],
        ],
    )
    el.add_paragraph("进入项目目录后，运行以下命令安装所有依赖：")
    el.add_code_block("sh", "uv sync")
    el.add_blockquote("💡 **Tips**：如果下载速度慢，可以使用国内镜像源：  ```sh uv sync -i https://pypi.tuna.tsinghua.edu.cn/simple ```")
    el.add_heading(3, "2.4 验证安装")
    el.add_paragraph("运行以下命令验证安装是否成功：\\ (需要在项目目录下运行)")
    el.add_code_block("sh", "# 测试 GUI 模式\nuv run src/app.py\n\n# 或测试 CLI 模式\nuv run src/cli.py")
    el.add_separator()
    el.add_heading(2, "三、配置说明")
    el.add_blockquote("程序支持两种使用方式：**GUI 图形界面**(推荐新手) 和 **CLI 命令行**(适合高级用户和自动化脚本)。")
    el.add_heading(3, "3.1 GUI 模式配置")
    el.add_heading(4, "启动 GUI")
    el.add_code_block("sh", "uv run src/app.py")
    el.add_heading(4, "界面结构")
    el.add_paragraph("程序界面分为三个主要标签页：")
    el.add_table(
        headers=["标签页", "图标", "功能说明"],
        rows=[
            ["**基础设置**", "⚙️", "文件输入输出、版本选择、格式配置"],
            ["**轨道组**", "🛤️", "轨道分组管理、坐标规划、方块配置"],
            ["**运行日志**", "📝", "实时显示转换进度和错误信息"],
        ],
    )
    el.add_separator()
    el.add_heading(4, "基础设置详解")
    el.add_table(
        headers=["配置项", "说明", "操作方式"],
        rows=[
            ["**文件输入**", "选择要转换的 `.nbs` 文件", "点击\"浏览...\"按钮选择文件"],
            ["**输出路径**", "设置生成文件的保存路径", "自动根据输入文件名填充，可手动修改"],
            ["**目标游戏版本**", "选择 Minecraft Java Edition 版本", "从下拉菜单选择对应版本"],
            ["**输出格式**", "选择生成文件类型", "二选一：Schem 或 Mcfunction"],
        ],
    )
    el.add_paragraph("**输出格式对比**：")
    el.add_table(
        headers=["格式", "文件扩展名", "依赖模组", "适用场景"],
        rows=[
            ["WorldEdit Schematic", "`.schem`", "需要 WorldEdit", "快速导入、可视化编辑"],
            ["Minecraft Function", "`.mcfunction`", "无需模组 (原版支持)", "原版部署"],
        ],
    )
    el.add_separator()
    el.add_heading(4, "轨道组配置详解")
    el.add_blockquote("⭐ **这是程序最核心的配置区域**，用于管理音符轨道的空间布局。")
    el.add_paragraph("**表格列说明**：")
    el.add_table(
        headers=["列名", "说明", "示例值"],
        rows=[
            ["**ID**", "轨道组唯一标识符", "`0`, `1`, `2`..."],
            ["**基准 X**", "该组在 Minecraft 世界中的 X 坐标", "`0`, `100`, `-50`..."],
            ["**基准 Y**", "该组在 Minecraft 世界中的 Y 坐标 (高度)", "`64`, `100`..."],
            ["**基准 Z**", "该组在 Minecraft 世界中的 Z 坐标", "`0`, `200`..."],
            ["**坐标规划**", "打开可视化坐标选择器", "点击 📍 选点 按钮"],
            ["**轨道 ID**", "NBS 文件中的轨道编号 (多个用逗号分隔)", "`0,1,2,3,4,5,6`"],
            ["**基础方块**", "构成平台的主体方块类型", "`minecraft:iron_block`"],
            ["**覆盖方块**", "覆盖在平台顶层的方块", "`minecraft:iron_block`"],
            ["**生成模式**", "生成结构的样式", "`default` 或 `staircase`"],
        ],
    )
    el.add_heading(4, "详细说明")
    el.add_bullet_list([
        "ID：",
    ])
    el.add_paragraph("每个 ID 对应一个`轨道组`，如 0 对应第一个轨道组，2 对应第二个，以此类推")
    el.add_paragraph("通常不需要修改该数值")
    el.add_bullet_list([
        "基准 X、Y、Z：",
    ])
    el.add_paragraph("每个轨道组的**第一个方块 (cover 或音符盒)**在 Minecraft 世界中的坐标，用于确定音符平台和红石线的位置。")
    el.add_bullet_list([
        "若选择的为 schem 模式，**该处对应的为相对于 (0,0,0) 坐标的向量位置**",
    ])
    el.add_paragraph("如：基准X=100,基准Y=64,基准Z=0 表示轨道组的**第一个方块(cover或音符盒)**在(100,64,0)位置生成 其中(0,0,0)为Schematic文件的原点，与Minecraft世界原点不同(也就是你站在地上，输入schem load对应的那个坐标) 推荐0轨道(ID=0)设定为voice(Main Rhythm)轨道，其轨道的坐标设置为(0,0,0)")
    el.add_bullet_list([
        "若选择的为 mcfunction 模式，**该处对应的为 Minecraft 中的坐标**",
    ])
    el.add_paragraph("如：基准 X=100，基准 Y=64，基准 Z=0 表示轨道组的**第一个方块 (cover 或音符盒)**在 (100,64,0) 位置生成 (不难理解，因为 mcfunction 模式为一大堆命令，命令执行的为`setblock x y z 方块类型`，故 XYZ 为 Minecraft 中的坐标，与 Schematic 文件的坐标不同)")
    el.add_bullet_list([
        "坐标规划 (GUI 选点)：",
    ])
    el.add_paragraph("点击\"📍 选点\"按钮，打开可视化界面在网格上拖动选择坐标 (选择的为轨道组的 XY 坐标，不支持 Z 坐标) (PS：程序本身就是默认为向东边生成，所以 GUI 选点不能设定 Z 坐标)")
    el.add_bullet_list([
        "轨道 ID：",
    ])
    el.add_paragraph("每个轨道组包含多个轨道，每个轨道对应一个音符平台和红石线。 该处为 NBS 文件中的轨道编号，多个轨道编号之间用逗号分隔。")
    el.add_paragraph("如：轨道 ID=0,1,2,3,4,5,6 表示轨道组包含 7 个轨道，编号为 0、1、2、3、4、5、6 其中，轨道`ID=0`对应`NBS中的第一个轨道` 1 对应第 2 个 以此类推。")
    el.add_bullet_list([
        "基础方块、覆盖方块：",
    ])
    el.add_paragraph("每个轨道组的音符平台和红石线的方块类型，基础方块用于放置在音符盒下一层中的方块，覆盖方块用于放置在音符盒同层的方块。 该处为 Minecraft 中的方块类型，如`minecraft:iron_block`、`minecraft:stone`等。")
    el.add_bullet_list([
        "生成模式：",
    ])
    el.add_paragraph("生成结构的样式，`default`为默认模式，`staircase`为阶梯向下模式。默认模式为`default`。")
    el.add_bullet_list([
        "`default`模式：所有音符平台和红石线保持在同一水平高度。",
        "`staircase`模式：当左右偏移 ≥ 3 时，音符平台逐级向下阶梯式生成。",
    ])
    el.add_paragraph("**生成模式对比**：")
    el.add_table(
        headers=["模式", "名称", "特点", "适用场景"],
        rows=[
            ["`default`", "默认模式", "所有音符平台和红石线保持在同一水平高度", "大多数情况"],
            ["`staircase`", "阶梯向下模式", "当左右偏移 ≥ 3 时，音符平台逐级向下阶梯式生成", "大型音乐作品、立体视觉效果"],
        ],
    )
    el.add_separator()
    el.add_heading(3, "3.2 命令行模式配置")
    el.add_heading(4, "运行命令 (记得在修改完配置后运行！)")
    el.add_code_block("sh", "uv run src/cli.py")
    el.add_heading(4, "配置文件位置")
    el.add_paragraph("`src/nbs2save/core/config.py`")
    el.add_heading(4, "全局生成配置 (`GENERATE_CONFIG`)")
    el.add_code_block("python", "GENERATE_CONFIG = {\n    # 指定生成的 schematic 文件的 Minecraft 版本\n    # 仅在输出格式为 schematic 时生效\n    # 可选值参考 mcschematic.Version 枚举\n    'data_version': Version.JE_1_21_4,\n\n    # 指定要转换的 NBS 文件路径\n    'input_file': 'test.nbs',\n\n    # 指定输出格式类型\n    # 可选值：'schematic' 或 'mcfunction'\n    'type': 'schematic',\n\n    # 指定输出文件的名称 (不包含扩展名)\n    # 程序会自动添加相应的扩展名\n    'output_file': 'test'\n}")
    el.add_paragraph("**参数详解**：")
    el.add_table(
        headers=["参数名", "数据类型", "说明", "示例值"],
        rows=[
            ["`data_version`", "`Version`", "目标 Minecraft 版本，影响 schematic 文件的兼容性", "`Version.JE_1_21_4`"],
            ["`input_file`", "`str`", "NBS 文件的完整路径 (相对或绝对路径均可)", "`'test.nbs'`"],
            ["`type`", "`str`", "输出格式类型", "`'schematic'` 或 `'mcfunction'`"],
            ["`output_file`", "`str`", "输出文件名 (不包含扩展名)", "`'test'`"],
        ],
    )
    el.add_separator()
    el.add_heading(4, "轨道组配置 (`GROUP_CONFIG`)")
    el.add_code_block("python", "GROUP_CONFIG = {\n    # 轨道组 0 的配置\n    0: {\n        # 基准坐标 (x, y, z)，必须是字符串类型\n        'base_coords': (\"0\", \"0\", \"0\"),\n\n        # 该组包含的轨道 ID 列表\n        'layers': [0, 1, 2, 3, 4, 5, 6],\n\n        # 方块配置\n        'block': {\n            # 基础平台方块\n            'base': 'minecraft:iron_block',\n            # 顶部覆盖方块\n            'cover': 'minecraft:iron_block'\n        },\n\n        # 生成模式：'default' 或 'staircase'\n        'generation_mode': 'default'\n    },\n}")
    el.add_paragraph("**参数详解**：")
    el.add_table(
        headers=["参数名", "数据类型", "说明", "示例值"],
        rows=[
            ["`base_coords`", "`tuple(str, str, str)`", "轨道组的第一个方块 (cover 或音符盒) 在 Minecraft 世界中的起始位置 `(X, Y, Z)`，**字符串类型**", "`(\"0\", \"64\", \"0\")`"],
            ["`layers`", "`list[int]`", "NBS 文件中的轨道 ID 列表，对应 NBS 中的轨道编号如 0 对应 NBS 的第一个轨道", "`[0, 1, 2, 3]`"],
            ["`block.base`", "`str`", "基础平台方块 (放置在音符盒下一层的方块)", "`'minecraft:iron_block'`"],
            ["`block.cover`", "`str`", "顶部覆盖方块 (放置在音符盒同层的方块，用于隐藏红石线路)", "`'minecraft:iron_block'`"],
            ["`generation_mode`", "`str`", "生成模式：`default`(默认，同一水平高度) 或 `staircase`(阶梯向下)", "`'default'` 或 `'staircase'`"],
        ],
    )
    el.add_blockquote("💡 **坐标说明**：  - 若输出格式为 **schematic**：`base_coords` 为相对于 `(0,0,0)` 的向量位置，与 Minecraft 世界原点不同 - 若输出格式为 **mcfunction**：`base_coords` 为 Minecraft 中的绝对坐标  💡 **Y 坐标建议**：设置在 `64` 或更高，避免结构生成在地底。")
    el.add_separator()
    el.add_heading(3, "3.3 常量配置")
    el.add_blockquote("⚠️ 通常无需修改，除非需要添加自定义音色。")
    el.add_paragraph("**文件位置**：`src/nbs2save/core/constants.py`")
    el.add_heading(4, "乐器映射 (`INSTRUMENT_MAPPING`)")
    el.add_paragraph("定义 NBS 乐器 ID 到 Minecraft 音符盒音色的对应关系：")
    el.add_table(
        headers=["ID", "NBS 乐器", "Minecraft 音色标识"],
        rows=[
            ["`0`", "钢琴 (竖琴)", "`harp`"],
            ["`1`", "贝斯", "`bass`"],
            ["`2`", "底鼓", "`basedrum`"],
            ["`3`", "小军鼓", "`snare`"],
            ["`4`", "铜钹", "`hat`"],
            ["`5`", "吉他", "`guitar`"],
            ["`6`", "长笛", "`flute`"],
            ["`7`", "钟琴", "`bell`"],
            ["`8`", "风铃", "`chime`"],
            ["`9`", "木琴", "`xylophone`"],
            ["`10`", "铁木琴", "`iron_xylophone`"],
            ["`11`", "牛铃", "`cow_bell`"],
            ["`12`", "迪吉里杜管", "`didgeridoo`"],
            ["`13`", "比特", "`bit`"],
            ["`14`", "班卓琴", "`banjo`"],
            ["`15`", "电钢琴", "`pling`"],
        ],
    )
    el.add_heading(4, "乐器方块映射 (`INSTRUMENT_BLOCK_MAPPING`)")
    el.add_paragraph("定义不同音色需要放置的方块类型：")
    el.add_table(
        headers=["乐器 ID", "乐器名称", "下方块类型"],
        rows=[
            ["`0`", "钢琴", "`minecraft:dirt`"],
            ["`1`", "贝斯", "`minecraft:oak_planks`"],
            ["`2`", "底鼓", "`minecraft:stone`"],
            ["`3`", "小军鼓", "`minecraft:sand`"],
            ["`4`", "铜钹", "`minecraft:glass`"],
            ["`5`", "吉他", "`minecraft:white_wool`"],
            ["`6`", "长笛", "`minecraft:clay`"],
            ["`7`", "钟琴", "`minecraft:gold_block`"],
            ["`8`", "风铃", "`minecraft:packed_ice`"],
            ["`9`", "木琴", "`minecraft:bone_block`"],
            ["`10`", "铁木琴", "`minecraft:iron_block`"],
            ["`11`", "牛铃", "`minecraft:soul_sand`"],
            ["`12`", "迪吉里杜管", "`minecraft:pumpkin`"],
            ["`13`", "比特", "`minecraft:emerald_block`"],
            ["`14`", "班卓琴", "`minecraft:hay_block`"],
            ["`15`", "电钢琴", "`minecraft:glowstone`"],
        ],
    )
    el.add_heading(4, "音高映射 (`NOTEPITCH_MAPPING`)")
    el.add_paragraph("将 MIDI 键值 (`33-57`) 映射到 Minecraft 音符盒音高 (`0-24`)。")
    el.add_separator()
    el.add_heading(2, "五、生成示例&高级生成")
    el.add_heading(3, "5.1 多轨道组管理")
    el.add_paragraph("该模式适用于制作大型红石音乐，将不同乐器或声部放置在不同位置。 若需要生成多轨则需要配置不同的轨道组。(ID=0,1,2,3,4,5,6 等等)")
    el.add_heading(4, "配置示例 (cil 模式 GUI 同理)")
    el.add_code_block("python", "GROUP_CONFIG = {\n    # 主旋律组\n    0: {\n        'base_coords': (\"0\", \"64\", \"0\"),\n        'layers': [0, 1, 2, 3],\n        'block': {\n            'base': 'minecraft:iron_block',\n            'cover': 'minecraft:gold_block'\n        },\n        'generation_mode': 'default'\n    },\n    # 伴奏组\n    1: {\n        'base_coords': (\"3\", \"64\", \"0\"),\n        'layers': [4, 5, 6],\n        'block': {\n            'base': 'minecraft:stone',\n            'cover': 'minecraft:iron_block'\n        },\n        'generation_mode': 'staircase'\n    }\n}\n\n#比如我这里配置了两个 GROUP\n#0 号 GROUP 是主旋律组，1 号 GROUP 是伴奏组，我可以把 NBS 中的轨道 0,1,2,3,4,5,6 分别对应到 0 号 GROUP 和 1 号 GROUP 中\n#这时候生成出来的就是两条轨道组，来实现大型红石音乐制作")
    el.add_image("![alt text](img/image-1.png)", "")
    el.add_paragraph("通过配置 GROUP 可以实现如上图一样的效果，来实现大型红石音乐制作")
    el.add_separator()
    el.add_heading(3, "5.2 声像偏移 (Panning)")
    el.add_paragraph("NBS 文件中的声像设置会影响音符在 Minecraft 中的 **Z 轴位置**。")
    el.add_heading(4, "工作原理")
    el.add_table(
        headers=["NBS 声像值", "Minecraft Z 轴偏移", "方向"],
        rows=[
            ["`0`", "`0` 格", "中央 (主干道)"],
            ["`30`", "`+3` 格", "右侧"],
            ["`-50`", "`-5` 格", "左侧"],
            ["`-53`", "`-5` 格", "左侧"],
        ],
    )
    el.add_paragraph("**转换公式**：")
    el.add_paragraph("`Z 轴偏移格数 = round(NBS 声像值 ÷ 10)`")
    el.add_paragraph("这里的`round`函数用于四舍五入，确保结果为整数。 声像值并非轨道声像，而是音符的声像值。 (即：同一轨道内的不同音符可以拥有各自独立的声像值，并非整个轨道统一设置)")
    el.add_heading(4, "示例效果")
    el.add_paragraph("如果在 NBS 中设置某个音符的声像为 **左声道 20**：")
    el.add_code_block("txt", "│       ■\n│       ■\n│   □ ■ ■\n│       ■        ↑(中继器朝向)")
    el.add_blockquote("说明：`□` 表示音符盒，会相对于主干结构左边 **第 2 格** 生成。")
    el.add_paragraph("**示例图片**：")
    el.add_image("![alt text](img/image-2.png)", "")
    el.add_paragraph("如上图所示，将 NBS 切换到`声道模式`，这里的两个红色箭头所指的`L40`表示左声道 4 格子，`R40`表示右声道 4 格子。 生成所对应的位置应如下图")
    el.add_image("![alt text](img/image-3.png)", "")
    el.add_heading(4, "⚠️ 重要限制")
    el.add_blockquote("NBS 中**整个轨道的声像偏移设置**无法被程序识别，只能识别**单个音符的声像设置**。 _其实也是个好事，因为这样可以实现更复杂的声像分布效果。_")
    el.add_separator()
    el.add_heading(3, "5.3 生成模式详解")
    el.add_heading(4, "默认模式 (`default`)")
    el.add_table(
        headers=["特点", "说明"],
        rows=[
            ["结构", "所有音符平台和红石线在同一水平高度"],
            ["复杂度", "结构简单，适合大多数情况"],
            ["维护性", "易于观察和修改"],
        ],
    )
    el.add_paragraph("如图所示：")
    el.add_image("![alt text](img/image-4.png)", "")
    el.add_heading(4, "阶梯向下模式 (`staircase`)")
    el.add_paragraph("**启用条件**：当声像偏移 **≥ 3** 时自动启用阶梯效果")
    el.add_paragraph("**效果特点**：")
    el.add_table(
        headers=["层级", "位置", "说明"],
        rows=[
            ["**主干道**", "`base_y` 层", "保持在基准高度"],
            ["**偏移位置**", "每增加 1 个偏移单位下降 1 格", "逐级下降"],
            ["**红石线**", "从主干道开始逐级下降", "跟随阶梯布局"],
        ],
    )
    el.add_paragraph("**适用场景**：")
    el.add_bullet_list([
        "🎶 大型音乐作品",
        "🎨 需要突出声像分布的作品",
        "🏗️ 追求视觉美感的展示项目",
    ])
    el.add_paragraph("**配置方法 (cil 模式 GUI 同理)**：")
    el.add_code_block("python", "'generation_mode': 'staircase'")
    el.add_paragraph("如图所示：")
    el.add_image("![alt text](img/image-5.png)", "")
    el.add_separator()
    el.add_heading(3, "5.4 坐标系统详解 (普通用户无需了解，该处为开发需要用到的)")
    el.add_heading(4, "关键变量")
    el.add_table(
        headers=["变量名", "含义", "计算公式", "说明"],
        rows=[
            ["`tick_x`", "音符的 X 坐标", "`base_x + tick × 2`", "每个 tick 占用 2 格 X 轴空间"],
            ["`base_x, base_y, base_z`", "轨道组基准坐标", "—", "定义整个结构的起始位置"],
            ["`pan_offset`", "声像偏移量", "`panning ÷ 10`", "影响音符的 Z 轴位置"],
            ["`z_pos`", "音符的最终 Z 坐标", "`base_z + pan_offset`", "音符在南北方向的实际位置"],
        ],
    )
    el.add_heading(4, "坐标布局示意")
    el.add_code_block("", "X 轴(东西方向)：\n  时间 → 沿着 X 轴正方向延伸\n  每个 tick 占 2 格\n\nY 轴(高度方向)：\n  base_y 是平台高度\n  音符盒放置在 base_y 层\n\nZ 轴(南北方向)：\n  base_z 是主干道位置\n  声像偏移沿 Z 轴展开")
    el.add_separator()
    el.add_heading(3, "5.5 自定义音色和方块")
    el.add_paragraph("如果需要添加自定义音色，可以修改 `src/nbs2save/core/constants.py`：")
    el.add_code_block("python", "# 在 INSTRUMENT_MAPPING 中添加新乐器\nINSTRUMENT_MAPPING = {\n    # ... 现有映射 ...\n    16: \"custom_sound\",  # 添加新乐器\n}\n\n# 在 INSTRUMENT_BLOCK_MAPPING 中添加对应的方块\nINSTRUMENT_BLOCK_MAPPING = {\n    # ... 现有映射 ...\n    16: \"minecraft:diamond_block\",  # 新乐器对应方块\n}")
    el.add_blockquote("说明：`custom_sound` 是自定义的音色，`minecraft:diamond_block` 是对应的方块。 本人还没了解过新版本的铜号在 NBS 里对应乐器 ID，所以需要自己琢磨下这里的 16 应该改成什么 ((")
    el.add_separator()
    el.add_heading(3, "5.6 配置保存和加载")
    el.add_table(
        headers=["操作", "步骤", "文件格式"],
        rows=[
            ["**保存配置**", "点击\"保存配置\"按钮 → 选择保存位置", "JSON"],
            ["**加载配置**", "点击\"加载配置\"按钮 → 选择 JSON 文件", "JSON"],
            ["**自动保存**", "程序自动保存最后一次配置到 `last_config.json`", "JSON"],
        ],
    )
    el.add_blockquote("💡 **提示**：下次启动程序时，会自动加载 `last_config.json` 中的配置。")
    el.add_separator()
    el.add_heading(2, "六、输出文件使用")
    el.add_heading(3, "6.1 Schematic 文件使用")
    el.add_heading(4, "前提条件")
    el.add_table(
        headers=["项目", "要求"],
        rows=[
            ["**Minecraft 版本**", "Java Edition"],
            ["**必要模组**", "WorldEdit"],
        ],
    )
    el.add_heading(4, "使用步骤")
    el.add_numbered_list([
        "**复制文件**到 WorldEdit 的 schematics 文件夹",
    ])
    el.add_code_block("txt", "   .minecraft/config/worldedit/schematics/")
    el.add_blockquote("这里有可能不是在这个路径，详细见 WorldEdit 的文档。")
    el.add_numbered_list([
        "**加载结构**：在游戏中输入命令",
    ])
    el.add_code_block("txt", "   //schem load 文件名")
    el.add_numbered_list([
        "**选择位置**：选择一个合适的位置作为粘贴起点",
        "**粘贴结构**：",
    ])
    el.add_code_block("txt", "   //paste")
    el.add_separator()
    el.add_heading(3, "6.2 Mcfunction 文件使用")
    el.add_heading(4, "步骤 1：创建数据包文件夹结构")
    el.add_code_block("txt", "save/你的存档名/datapacks/你的数据包名/\n├── pack.mcmeta\n└── data/你的命名空间/\n    └── functions/\n        └── 文件名.mcfunction")
    el.add_heading(4, "步骤 2：创建 `pack.mcmeta` 文件")
    el.add_code_block("json", "{\n  \"pack\": {\n    \"pack_format\": 18,\n    \"description\": \"NBS 音乐数据包\"\n  }\n}")
    el.add_blockquote("⚠️ **注意**：`pack_format` 需要对应你的 Minecraft 版本")
    el.add_table(
        headers=["Minecraft 版本", "pack_format"],
        rows=[
            ["1.21.4", "48"],
            ["1.21.2 - 1.21.3", "46"],
            ["1.21 - 1.21.1", "42"],
            ["1.20.5 - 1.20.6", "32"],
            ["1.20.3 - 1.20.4", "26"],
            ["1.20.2", "18"],
            ["1.20 - 1.20.1", "15"],
        ],
    )
    el.add_blockquote("这里使用了 AI 生成的表格，可能不是完全准确的。")
    el.add_heading(4, "步骤 3：放置文件")
    el.add_paragraph("将生成的 `.mcfunction` 文件放入 `functions` 文件夹。")
    el.add_heading(4, "步骤 4：重新加载数据包")
    el.add_paragraph("在游戏中输入命令：")
    el.add_code_block("txt", "/reload")
    el.add_heading(4, "步骤 5：执行音乐函数")
    el.add_code_block("txt", "/function 命名空间：文件名")
    el.add_paragraph("**示例**：")
    el.add_code_block("txt", "/function mymusic:test")
    el.add_separator()
    el.add_heading(2, "七、故障排除")
    el.add_heading(3, "7.1 常见问题")
    el.add_heading(4, "问题 1：导入模块错误")
    el.add_paragraph("**错误信息**：")
    el.add_code_block("ansi", "ModuleNotFoundError: No module named 'pynbs'")
    el.add_paragraph("**原因分析**：")
    el.add_paragraph("Python 依赖库未安装或安装不完整。")
    el.add_paragraph("**解决方法**：")
    el.add_code_block("sh", "uv sync")
    el.add_separator()
    el.add_heading(4, "问题 2：NBS 文件路径错误")
    el.add_paragraph("**错误信息**：")
    el.add_code_block("ansi", "FileNotFoundError: [Errno 2] No such file or directory: 'test.nbs'")
    el.add_paragraph("**原因分析**：")
    el.add_paragraph("程序无法找到指定的 NBS 文件。")
    el.add_paragraph("**解决方法**：")
    el.add_table(
        headers=["检查项", "说明"],
        rows=[
            ["✅ 路径正确性", "确保 NBS 文件路径正确"],
            ["✅ 使用绝对路径", "优先使用绝对路径而不是相对路径"],
            ["✅ 文件扩展名", "检查文件扩展名是否为 `.nbs`"],
        ],
    )
    el.add_separator()
    el.add_heading(4, "问题 3：位置冲突错误")
    el.add_paragraph("**错误信息**：")
    el.add_code_block("ansi", "Exception: 位置冲突! Tick XXX, Z=XX 位置已有音符")
    el.add_paragraph("**原因分析**：")
    el.add_paragraph("同一时间点，同一 Z 轴位置有多个音符。")
    el.add_paragraph("**解决方法**：")
    el.add_numbered_list([
        "在 NBS 编辑器中检查冲突的音符",
        "调整冲突音符的声像 (Panning) 值",
        "将冲突的轨道分配到不同的轨道组",
    ])
    el.add_separator()
    el.add_heading(4, "问题 4：配置缺失错误")
    el.add_paragraph("**错误信息**：")
    el.add_code_block("ansi", "ValueError: 配置缺失: output_file")
    el.add_paragraph("**原因分析**：")
    el.add_paragraph("配置文件中缺少必需的配置项。")
    el.add_paragraph("**解决方法**：")
    el.add_paragraph("检查 `config.py` 中的 `GENERATE_CONFIG` 是否包含所有必需字段：")
    el.add_table(
        headers=["必需字段", "说明"],
        rows=[
            ["`data_version`", "Minecraft 版本"],
            ["`input_file`", "NBS 文件路径"],
            ["`type`", "输出格式"],
            ["`output_file`", "输出文件名"],
        ],
    )
    el.add_separator()
    el.add_heading(4, "问题 5：GUI 启动失败")
    el.add_paragraph("**错误信息**：")
    el.add_code_block("ansi", "ModuleNotFoundError: No module named 'PyQt6'")
    el.add_paragraph("**原因分析**：")
    el.add_paragraph("图形界面依赖库未安装。")
    el.add_paragraph("**解决方法**：")
    el.add_code_block("sh", "uv pip install PyQt6")
    el.add_separator()
    el.add_heading(4, "问题 6：Schematic 文件在游戏中无法加载")
    el.add_paragraph("**可能原因**：")
    el.add_table(
        headers=["原因", "说明"],
        rows=[
            ["🔴 版本不匹配", "Minecraft 版本与 schematic 版本不一致"],
            ["🔴 模组不兼容", "WorldEdit 版本与 Minecraft 版本不兼容"],
        ],
    )
    el.add_paragraph("**解决方法**：")
    el.add_numbered_list([
        "确认 `data_version` 与你的 Minecraft 版本一致",
        "更新 WorldEdit 到最新版本",
        "尝试使用较低的 Minecraft 版本重新生成",
    ])
    el.add_separator()
    el.add_heading(4, "问题 7：生成的音乐播放不正常")
    el.add_paragraph("**可能原因**：")
    el.add_table(
        headers=["原因", "说明"],
        rows=[
            ["🔴 不支持的乐器", "NBS 文件中使用了程序不支持的乐器"],
            ["🔴 音高超出范围", "音符音高超出 Minecraft 支持范围"],
        ],
    )
    el.add_paragraph("**解决方法**：")
    el.add_numbered_list([
        "检查 NBS 文件使用的乐器是否在支持范围内 (ID `0-15`)",
        "确保音符的 MIDI 键值在 `33-57` 范围内",
        "尝试在 NBS 编辑器中调整不兼容的音符",
    ])
    el.add_separator()
    el.add_heading(3, "7.2 性能优化")
    el.add_heading(4, "场景 A：大型音乐文件生成缓慢")
    el.add_paragraph("**原因**：程序逐个音符生成，大型文件需要较长时间。")
    el.add_paragraph("**解决方法**：")
    el.add_table(
        headers=["方法", "说明"],
        rows=[
            ["🚀 使用 schematic 格式", "生成速度比 mcfunction 更快"],
            ["⏳ 耐心等待", "生成过程中可以查看进度条"],
            ["💻 确保性能", "关闭其他占用资源的程序"],
        ],
    )
    el.add_separator()
    el.add_heading(4, "场景 B：内存占用过高")
    el.add_paragraph("**解决方法**：")
    el.add_bullet_list([
        "将大型音乐分割成多个部分",
        "使用多个轨道组分散处理",
        "关闭其他占用内存的程序",
    ])
    el.add_separator()
    el.add_heading(3, "7.3 日志分析")
    el.add_heading(4, "日志示例")
    el.add_code_block("ansi", ">> 处理轨道组 0:\n├─ 包含轨道: [0, 1, 2, 3, 4, 5, 6]\n├─ 基准坐标: (0, 64, 0)\n├─ 方块配置: {'base': 'minecraft:iron_block', 'cover': 'minecraft:iron_block'}\n└─ 生成模式: default\n   ├─ 发现音符数量: 1234\n   └─ 组内最大tick: 500")
    el.add_heading(4, "日志解读")
    el.add_table(
        headers=["日志标识", "含义"],
        rows=[
            ["`>>`", "开始处理新的轨道组"],
            ["`├─` 和 `└─`", "显示配置信息层级"],
            ["`发现音符数量`", "该组中找到的音符总数"],
            ["`组内最大tick`", "音乐的长度 (以 tick 为单位)"],
            ["进度条", "整体转换进度 (0-100%)"],
        ],
    )
    el.add_separator()
    el.add_heading(2, "八、注意事项")
    el.add_heading(3, "8.1 许可和使用限制")
    el.add_blockquote("⚠️ **重要声明**")
    el.add_table(
        headers=["限制类型", "说明"],
        rows=[
            ["🚫 **花之舞限制**", "**严禁**使用本程序生成与《花之舞》(Flower Dance) 有关的文件，如需使用请联系作者获取授权"],
            ["🚫 **商业用途**", "**严禁**将本程序用于商业用途 (如有需要需获得授权)"],
            ["📝 **发布要求**", "使用本程序生成的作品发布到视频平台时，**必须在视频简介中标注使用本程序生成**"],
        ],
    )
    el.add_separator()
    el.add_heading(3, "8.2 使用建议")
    el.add_heading(4, "备份存档")
    el.add_blockquote("⚠️ **重要**：使用本程序前，请务必备份你的 Minecraft 存档！")
    el.add_paragraph("备份路径：`.minecraft/saves/你的存档名`")
    el.add_paragraph("将存档文件夹复制到安全位置。")
    el.add_separator()
    el.add_heading(4, "合理设置坐标")
    el.add_table(
        headers=["建议", "说明"],
        rows=[
            ["📍 Y 坐标", "建议设置在 `64` 或更高，避免生成在地底"],
            ["📏 轨道组间距", "多个轨道组之间保持足够距离，避免结构重叠"],
            ["🎯 可视化设置", "使用坐标规划器可视化设置位置"],
        ],
    )
    el.add_separator()
    el.add_heading(4, "测试后再部署")
    el.add_table(
        headers=["步骤", "说明"],
        rows=[
            ["1️⃣ 测试世界", "先在测试世界或备份世界中测试生成的结构"],
            ["2️⃣ 确认效果", "确认播放效果无误后再部署到正式存档"],
            ["3️⃣ 分段测试", "对于大型音乐，建议分段测试"],
        ],
    )
    el.add_separator()
    el.add_heading(4, "选择合适的格式")
    el.add_table(
        headers=["格式", "✅ 优点", "❌ 缺点"],
        rows=[
            ["**Schematic**", "生成快、导入方便、可预览和调整", "需要 WorldEdit 模组"],
            ["**Mcfunction**", "原版支持、无需模组", "生成较慢、修改不便"],
        ],
    )
    el.add_separator()
    el.add_heading(3, "8.3 技术限制")
    el.add_table(
        headers=["限制项", "说明"],
        rows=[
            ["🔊 轨道声像", "无法识别 NBS 中整个轨道的声像偏移，只能识别单个音符的声像"],
            ["🎵 音高范围", "Minecraft 音符盒支持的音高范围为 `0-24`(对应 MIDI 键值 `33-57`)"],
            ["⚠️ 位置冲突", "同一时间点同一 Z 轴位置不能有多个音符"],
            ["⏱️ 文件大小", "超大型音乐文件可能需要较长时间生成"],
        ],
    )
    el.add_separator()
    el.add_blockquote("该文档部分内容使用了 AI 生成，但所有内容都经过了手动修改和人工审核，确保了文档的质量准确性和可靠性。 🎵 **祝你使用愉快！**")
