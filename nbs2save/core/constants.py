from mcschematic import Version

# ==============================================================================
# NBS到Minecraft结构转换工具常量定义文件
# ==============================================================================
# 该文件定义了程序运行所需的各种常量映射表和配置参数
# 包括乐器映射、音高映射、支持的Minecraft版本等
# 通常情况下这些参数无需修改，除非需要添加自定义音色或支持新版本

# --------------------------
# 常量映射表 (通常无需修改)
# --------------------------
# 除非你要加一些自定义音色，那就在下面的INSTRUMENT_MAPPING和INSTRUMENT_BLOCK_MAPPING中添加上你需要的音色和对应方块

# --------------------------
# 乐器到音符盒音色映射
# --------------------------
# INSTRUMENT_MAPPING 定义了NBS中的乐器ID到Minecraft音符盒instrument值的映射关系
# NBS文件中的每个音符都有一个instrument属性，表示该音符使用的乐器类型
# Minecraft中的音符盒方块也有对应的instrument属性，用于指定播放的音色
# 该映射表确保NBS中的乐器能够正确转换为Minecraft中的对应音色
# 
# 映射说明:
# 0  -> "harp"           钢琴(竖琴)音色，Minecraft默认音色
# 1  -> "bass"           贝斯音色
# 2  -> "basedrum"       底鼓音色
# 3  -> "snare"          小军鼓音色
# 4  -> "hat"            铜钹音色
# 5  -> "guitar"         吉他音色
# 6  -> "flute"          长笛音色
# 7  -> "bell"           钟琴音色
# 8  -> "chime"          风铃音色
# 9  -> "xylophone"      木琴音色
# 10 -> "iron_xylophone" 铁木琴音色
# 11 -> "cow_bell"       牛铃音色
# 12 -> "didgeridoo"     迪吉里杜管音色
# 13 -> "bit"            比特音色
# 14 -> "banjo"          班卓琴音色
# 15 -> "pling"          电钢琴音色
INSTRUMENT_MAPPING = {
    0: "harp", 1: "bass", 2: "basedrum", 3: "snare", 4: "hat",
    5: "guitar", 6: "flute", 7: "bell", 8: "chime", 9: "xylophone",
    10: "iron_xylophone", 11: "cow_bell", 12: "didgeridoo", 13: "bit",
    14: "banjo", 15: "pling"
}

# --------------------------
# 乐器对应下方块类型映射
# --------------------------
# INSTRUMENT_BLOCK_MAPPING 定义了不同乐器需要放置在什么方块上才能发出对应音色
# 在Minecraft中，音符盒播放的声音会根据其下方方块的类型而改变音色
# 该映射表确保每种乐器都能放置在正确的方块上以产生预期的音色效果
#
# 映射说明:
# 0  -> "minecraft:dirt"          钢琴(竖琴)音色对应泥土方块
# 1  -> "minecraft:oak_planks"    贝斯音色对应橡木木板
# 2  -> "minecraft:stone"         底鼓音色对应石头方块
# 3  -> "minecraft:sand"          小军鼓音色对应沙子方块
# 4  -> "minecraft:glass"         铜钹音色对应玻璃方块
# 5  -> "minecraft:white_wool"    吉他音色对应白色羊毛方块
# 6  -> "minecraft:clay"          长笛音色对应粘土方块
# 7  -> "minecraft:gold_block"    钟琴音色对应金块
# 8  -> "minecraft:packed_ice"    风铃音色对应浮冰方块
# 9  -> "minecraft:bone_block"    木琴音色对应骨块
# 10 -> "minecraft:iron_block"    铁木琴音色对应铁块
# 11 -> "minecraft:soul_sand"     牛铃音色对应灵魂沙方块
# 12 -> "minecraft:pumpkin"       迪吉里杜管音色对应南瓜方块
# 13 -> "minecraft:emerald_block" 比特音色对应绿宝石块
# 14 -> "minecraft:hay_block"     班卓琴音色对应干草块
# 15 -> "minecraft:glowstone"     电钢琴音色对应荧石方块
INSTRUMENT_BLOCK_MAPPING = {
    0: "minecraft:dirt", 1: "minecraft:oak_planks", 2: "minecraft:stone", 3: "minecraft:sand",
    4: "minecraft:glass", 5: "minecraft:white_wool", 6: "minecraft:clay", 7: "minecraft:gold_block",
    8: "minecraft:packed_ice", 9: "minecraft:bone_block", 10: "minecraft:iron_block", 11: "minecraft:soul_sand",
    12: "minecraft:pumpkin", 13: "minecraft:emerald_block", 14: "minecraft:hay_block", 15: "minecraft:glowstone"
}

# --------------------------
# 音高映射表 (MIDI键到游戏音高)
# --------------------------
# NOTEPITCH_MAPPING 定义了NBS中的MIDI键值到Minecraft音符盒音高值的映射关系
# NBS文件中的每个音符都有一个key属性，表示该音符的音高(MIDI键值)
# Minecraft中的音符盒方块有note属性，用于指定播放的音高(0-24)
# 该映射表将MIDI键值(33-57)映射到Minecraft音高值(0-24)
# 
# MIDI键值范围说明:
# - MIDI标准中，中央C的键值为60
# - NBS文件中常用的键值范围大约在33-57之间
# - Minecraft音符盒支持的音高范围为0-24(对应F#3到F#5)
#
# 映射逻辑:
# 将MIDI键值33-57映射到Minecraft音高值0-24
# 即: 音高值 = MIDI键值 - 33
NOTEPITCH_MAPPING = {k: str(v) for v, k in enumerate(range(33, 58))}


# --------------------------
# Minecraft版本列表
# --------------------------
# MINECRAFT_VERSIONS 定义了程序支持的Minecraft Java Edition版本列表
# 用于生成schematic文件时指定目标Minecraft版本
# 版本按从新到旧的顺序排列，确保兼容性
# 当生成schematic文件时，程序会使用配置中指定的版本
MINECRAFT_VERSIONS = [
    Version.JE_1_21_5,
    Version.JE_1_21_4,
    Version.JE_1_21_3,
    Version.JE_1_21_2,
    Version.JE_1_21_1,
    Version.JE_1_21,
    Version.JE_1_20_6,
    Version.JE_1_20_5,
    Version.JE_1_20_4,
    Version.JE_1_20_3,
    Version.JE_1_20_2,
    Version.JE_1_20_1,
    Version.JE_1_20,
    Version.JE_1_19_4,
    Version.JE_1_19_3,
    Version.JE_1_19_2,
    Version.JE_1_19_1,
    Version.JE_1_19,
    Version.JE_1_18_2,
    Version.JE_1_18_1,
    Version.JE_1_18,
    Version.JE_1_17_1,
    Version.JE_1_17,
    Version.JE_1_16_5,
    Version.JE_1_16_4,
    Version.JE_1_16_3,
    Version.JE_1_16_2,
    Version.JE_1_16_1,
    Version.JE_1_16,
    Version.JE_1_15_2,
    Version.JE_1_15_1,
    Version.JE_1_15,
    Version.JE_1_14_4,
    Version.JE_1_14_3,
    Version.JE_1_14_2,
    Version.JE_1_14_1,
    Version.JE_1_14,
    Version.JE_1_13_2
]