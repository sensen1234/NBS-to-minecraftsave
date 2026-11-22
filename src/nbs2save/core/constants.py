from dataclasses import dataclass

from mcschematic import Version

# ==============================================================================
# NBS到Minecraft结构转换工具常量定义文件
# ==============================================================================
# 该文件定义了程序运行所需的各种常量映射表和配置参数
# 包括乐器映射、音高映射、支持的Minecraft版本等
# 通常情况下这些参数无需修改；自定义音色请使用配置中的 custom_instruments

# --------------------------
# 常量映射表 (通常无需修改)
# --------------------------
# 原版默认映射。自定义音色通过 GUI「自定义音色」或 custom_instruments 配置覆盖。

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
# 16 -> "copper_horn"    小号
# 17 -> "copper_horn_exposed" 斑驳小号
# 18 -> "copper_horn_weathered" 锈蚀小号
# 19 -> "copper_horn_oxidized" 氧化小号
INSTRUMENT_MAPPING = {
    0: "harp",
    1: "bass",
    2: "basedrum",
    3: "snare",
    4: "hat",
    5: "guitar",
    6: "flute",
    7: "bell",
    8: "chime",
    9: "xylophone",
    10: "iron_xylophone",
    11: "cow_bell",
    12: "didgeridoo",
    13: "bit",
    14: "banjo",
    15: "pling",
    16: "copper_horn",
    17: "copper_horn_exposed",
    18: "copper_horn_weathered",
    19: "copper_horn_oxidized",
}
VANILLA_INSTRUMENT_COUNT = max(INSTRUMENT_MAPPING) + 1

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
# 16 -> "minecraft:waxed_copper_block" 小号
# 17 -> "minecraft:waxed_exposed_copper" 斑驳小号
# 18 -> "minecraft:waxed_weathered_copper" 锈蚀小号
# 19 -> "minecraft:waxed_oxidized_copper" 氧化小号
INSTRUMENT_BLOCK_MAPPING = {
    0: "minecraft:dirt",
    1: "minecraft:oak_planks",
    2: "minecraft:stone",
    3: "minecraft:sand",
    4: "minecraft:glass",
    5: "minecraft:white_wool",
    6: "minecraft:clay",
    7: "minecraft:gold_block",
    8: "minecraft:packed_ice",
    9: "minecraft:bone_block",
    10: "minecraft:iron_block",
    11: "minecraft:soul_sand",
    12: "minecraft:pumpkin",
    13: "minecraft:emerald_block",
    14: "minecraft:hay_block",
    15: "minecraft:glowstone",
    16: "minecraft:waxed_copper_block",
    17: "minecraft:waxed_exposed_copper",
    18: "minecraft:waxed_weathered_copper",
    19: "minecraft:waxed_oxidized_copper",
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
@dataclass(frozen=True)
class SchematicVersion:
    """A Mojang release represented by its label and numeric DataVersion."""

    name: str
    value: int

    def __str__(self):
        return f"Version.{self.name}"


# Latest stable release in each major/minor line from Mojang's version manifest.
# Source: https://piston-meta.mojang.com/mc/game/version_manifest_v2.json
# DataVersion values are from misode/mcmeta summary/versions/data.json. Releases
# before 1.9 did not define DataVersion and use the legacy sentinel value 0.
_RELEASES = (
    ("26.3", 5023), ("26.2", 4903), ("26.1.2", 4790),
    ("1.21.11", 4671), ("1.20.6", 3839), ("1.19.4", 3337),
    ("1.18.2", 2975), ("1.17.1", 2730), ("1.16.5", 2586),
    ("1.15.2", 2230), ("1.14.4", 1976), ("1.13.2", 1631),
    ("1.12.2", 1343), ("1.11.2", 922), ("1.10.2", 512),
    ("1.9.4", 184), ("1.8.9", 0), ("1.7.10", 0),
    ("1.6.4", 0), ("1.5.2", 0), ("1.4.7", 0),
    ("1.3.2", 0), ("1.2.5", 0), ("1.1", 0), ("1.0", 0),
)


def _schematic_version(release, data_version):
    name = "JE_" + release.replace(".", "_")
    return Version.__members__.get(name, SchematicVersion(name, data_version))


MINECRAFT_VERSIONS = [
    _schematic_version(release, data_version)
    for release, data_version in _RELEASES
]


def schematic_version_from_name(name):
    """Restore a saved version value, including versions absent from the dependency enum."""
    if not isinstance(name, str):
        return None
    normalized = name.removeprefix("Version.")
    member = Version.__members__.get(normalized)
    if member is not None:
        return member
    return next((version for version in MINECRAFT_VERSIONS if version.name == normalized), None)
