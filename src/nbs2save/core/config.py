from mcschematic import Version

# ==============================================================================
# NBS到Minecraft结构转换工具配置文件
# ==============================================================================
# 该文件定义了程序运行所需的基本配置参数，包括输入输出设置和轨道组配置
# 用户可以根据需要修改这些参数来定制转换过程

# --------------------------
# 全局生成配置 (字典格式)
# --------------------------
# GENERATE_CONFIG 定义了程序的基本运行参数，控制整个转换过程的行为
# 包括输入文件路径、输出格式、输出文件名等设置
GENERATE_CONFIG = {
    # data_version: 指定生成的schematic文件的Minecraft版本
    # 这个参数只在输出格式为schematic时生效
    # 可选值参考 mcschematic.Version 枚举
    "data_version": Version.JE_1_21_4,
    # input_file: 指定要转换的NBS文件路径
    # 程序将读取该文件并解析其中的音符信息
    "input_file": "test.nbs",
    # type: 指定输出格式类型
    # 可选值:
    #   'schematic'  -> 生成WorldEdit格式的.schem文件
    #   'mcfunction' -> 生成Minecraft原版函数文件(.mcfunction)
    "type": "schematic",
    # output_file: 指定输出文件的名称(不包含扩展名)
    # 程序会根据type参数自动添加相应的扩展名
    # 例如: 如果type为'schematic'且output_file为'test'，则生成'test.schem'
    "output_file": "test",
    # NoteBetter 音色映射；GUI 可编辑并导出对应的配置与资源包。
    # 例如 {"nbs_id": 16, "name": "Piano", "base_block": "minecraft:diamond_block",
    #       "sound_id": "nbs2save:custom.piano", "sound_file": "piano.ogg", "root_key": 45}
    "custom_instruments": [],
}

# --------------------------
# 轨道组配置 (字典格式)
# --------------------------
# GROUP_CONFIG 定义了如何将NBS文件中的音符轨道分组以及每组的生成参数
# 每个轨道组可以有不同的基准坐标、包含的轨道列表和方块配置
# 键为轨道组ID(整数)，值为该组的配置参数
GROUP_CONFIG = {
    # 轨道组0的配置
    0: {
        # base_coords: 轨道组的基准坐标 (x, y, z)
        # 这是该轨道组生成结构的起始坐标位置
        # 所有该组的音符都将基于这个坐标进行定位
        # 注意: 坐标值需要是字符串类型
        "base_coords": ("0", "0", "0"),
        # layers: 该轨道组包含的轨道ID列表
        # NBS文件中的每个音符轨道都有一个唯一的ID
        # 通过这个列表可以指定哪些轨道属于当前轨道组
        "layers": [0, 1, 2, 3, 4, 5, 6],
        # block: 轨道组的方块配置
        # 定义生成结构时使用的方块类型
        "block": {
            # base: 基础平台方块
            # 用于构建音符播放平台的基础方块
            "base": "minecraft:iron_block",
            # cover: 顶部覆盖方块
            # 用于覆盖在基础平台上方的方块，通常是红石相关结构
            "cover": "minecraft:iron_block",
        },
        # generation_mode: 生成模式（决定结构生成方式）
        # 可选值:
        #   'default'       -> 默认生成模式
        #   'staircase'     -> 阶梯向下生成模式（偏移>=3时启用阶梯效果）
        #   'staircase_up'  -> 阶梯向上生成模式（偏移>=3时启用阶梯效果）
        "generation_mode": "default",
        # offset_mode: 偏移计算模式（决定音符Z轴偏移量的计算方式，与 generation_mode 独立）
        # 可选值:
        #   'pan'     -> pan值偏移: offset = panning / 10
        #   'volume'  -> 音量偏移: 量级来自音量经 volume_to_distance 拟合换算为格数,
        #               方向来自 panning 正负; panning==0 时不偏移并 WARN
        "offset_mode": "pan",
    },
}
