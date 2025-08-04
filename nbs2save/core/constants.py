from mcschematic import Version

# --------------------------
# 常量映射表 (通常无需修改)
# 除非你要加一些自定义音色，那就在下面的INSTRUMENT_MAPPING和INSTRUMENT_BLOCK_MAPPING中添加上你需要的音色和对应方块
# --------------------------

# 乐器到音符盒音色映射
INSTRUMENT_MAPPING = {
    0: "harp", 1: "bass", 2: "basedrum", 3: "snare", 4: "hat",
    5: "guitar", 6: "flute", 7: "bell", 8: "chime", 9: "xylophone",
    10: "iron_xylophone", 11: "cow_bell", 12: "didgeridoo", 13: "bit",
    14: "banjo", 15: "pling"
}

# 乐器对应下方块类型
INSTRUMENT_BLOCK_MAPPING = {
    0: "minecraft:dirt", 1: "minecraft:oak_planks", 2: "minecraft:stone", 3: "minecraft:sand",
    4: "minecraft:glass", 5: "minecraft:white_wool", 6: "minecraft:clay", 7: "minecraft:gold_block",
    8: "minecraft:packed_ice", 9: "minecraft:bone_block", 10: "minecraft:iron_block", 11: "minecraft:soul_sand",
    12: "minecraft:pumpkin", 13: "minecraft:emerald_block", 14: "minecraft:hay_block", 15: "minecraft:glowstone"
}

# 音高映射表 (MIDI键到游戏音高)
NOTEPITCH_MAPPING = {k: str(v) for v, k in enumerate(range(33, 58))}


# Minecraft版本列表
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
