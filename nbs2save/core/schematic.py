# -*- coding: utf-8 -*-
"""
Minecraft结构文件生成器
----------------------
负责将Note列表转换成Minecraft .schem结构文件。

主要流程
1. 根据group_config把Note划分到不同轨道组。
2. 每个轨道组内部：
   2.1 生成tick级基础结构（时钟、走线）。
   2.2 根据panning生成左右声像平台。
   2.3 在准确坐标生成音符方块及其基座。
3. 输出为.schem结构文件
"""

from __future__ import annotations

from typing import Dict, List

from mcschematic import MCSchematic
from collections import defaultdict
from pynbs import Note

from .constants import INSTRUMENT_MAPPING, INSTRUMENT_BLOCK_MAPPING, NOTEPITCH_MAPPING
from .config import GENERATE_CONFIG, GROUP_CONFIG
from .core import GroupProcessor, OutputFormatStrategy

# --------------------------
# 结构文件生成策略
# --------------------------
class SchematicOutputStrategy(OutputFormatStrategy):
    """输出为 .schem 结构文件的策略实现。"""

    def __init__(self):
        self.schem: MCSchematic = None  # 内存中的结构对象

    def initialize(self, processor: GroupProcessor):
        """
        初始化输出格式
        
        参数:
        processor: GroupProcessor实例
        """
        self.schem = MCSchematic()  # 重新初始化
        # 验证配置
        self.validate_config(processor)

    def write_base_structures(self, processor: GroupProcessor, tick: int):
        """
        写入基础结构
        
        参数:
        processor: GroupProcessor实例
        tick: 当前tick
        """
        # 计算当前tick在X轴上的位置（每个tick占2格）
        tick_x = processor.base_x + tick * 2
        # 设置基础平台方块
        self.schem.setBlock((tick_x, processor.base_y, processor.base_z), processor.cover_block)
        self.schem.setBlock((tick_x, processor.base_y - 1, processor.base_z), processor.base_block)
        # 设置红石中继器（用于时钟信号）
        self.schem.setBlock((tick_x - 1, processor.base_y, processor.base_z), "minecraft:repeater[delay=1,facing=west]")
        self.schem.setBlock((tick_x - 1, processor.base_y - 1, processor.base_z), processor.base_block)

    def write_pan_platform(self, processor: GroupProcessor, tick: int, direction: int):
        """
        写入声像平台
        
        参数:
        processor: GroupProcessor实例
        tick: 当前tick
        direction: 方向（1=右，-1=左）
        """
        # 检查该tick该方向的平台是否已生成
        if processor.tick_status[tick]["right" if direction == 1 else "left"]:
            return

        # 获取该方向上的最大偏移量
        max_pan_offset = processor._get_max_pan(processor.notes, tick, direction)
        if max_pan_offset == 0:
            return

        # 计算平台的起始和结束坐标
        tick_x = processor.base_x + tick * 2
        platform_start_z = processor.get_platform_start_z()  # 平台起始Z坐标（主干道）
        platform_end_z = processor.calculate_platform_end_z(max_pan_offset, direction)
        step = 1 if direction == 1 else -1
        
        # 生成平台基座方块
        for z in range(platform_start_z, platform_end_z + step, step):
            self.schem.setBlock((tick_x, processor.base_y - 1, z), processor.base_block)

        # 在主干道位置放置覆盖方块
        self.schem.setBlock((tick_x, processor.base_y, platform_start_z), processor.cover_block)

        # 如果偏移量大于1，需要铺设红石线连接
        if abs(max_pan_offset) > 1:
            # 红石线的起始位置应该是从主干道旁边开始
            wire_start_z = processor.get_wire_start_z(direction)
            wire_end_z = platform_end_z
            for z in range(wire_start_z, wire_end_z + step, step):
                self.schem.setBlock(
                    (tick_x, processor.base_y, z),
                    "minecraft:redstone_wire[north=side,south=side]"
                )

        processor.tick_status[tick]["right" if direction == 1 else "left"] = True

    def write_note(self, processor: GroupProcessor, note: Note):
        """
        写入音符
        
        参数:
        processor: GroupProcessor实例
        note: 要写入的音符
        """
        # 计算音符的位置坐标
        tick_x, y, z_pos = processor.get_note_position(note)
        # 获取音符方块的信息
        instrument, base_block, note_pitch = self.get_note_block_info(note)

        # 设置音符方块
        self.schem.setBlock(
            (tick_x, y, z_pos),
            f"minecraft:note_block[note={note_pitch},instrument={instrument}]"
        )
        # 设置基座方块
        self.schem.setBlock((tick_x, y - 1, z_pos), base_block)

        # 如果基座是沙子类方块，需要在下方添加屏障防止掉落
        if self.is_sand_block(base_block):
            self.schem.setBlock((tick_x, y - 2, z_pos), "minecraft:barrier")

    def finalize(self, processor: GroupProcessor):
        """
        完成输出，保存结构文件
        
        参数:
        processor: GroupProcessor实例
        """
        path = processor.config["output_file"]
        # 保存到本地 .schem
        self.schem.save(".", path.rsplit("/", 1)[-1], processor.config["data_version"])

    # ----------------------
    # 工具方法
    # ----------------------
    @staticmethod
    def get_note_block_info(note: Note):
        """根据 instrument 获取音符方块属性。"""
        instrument = INSTRUMENT_MAPPING.get(note.instrument, "harp")
        base_block = INSTRUMENT_BLOCK_MAPPING.get(note.instrument, "minecraft:stone")
        note_pitch = NOTEPITCH_MAPPING.get(note.key, "0")
        return instrument, base_block, note_pitch

    @staticmethod
    def is_sand_block(block: str) -> bool:
        """简单规则：以 'sand' 结尾即视为沙子类方块。"""
        return block.endswith("sand")

    @staticmethod
    def validate_config(processor: GroupProcessor):
        """确保 config 包含必需的键。"""
        required_keys = ["output_file", "data_version"]
        for key in required_keys:
            if key not in processor.config:
                raise ValueError(f"配置缺失: {key}")


# --------------------------
# 兼容性类（为了保持向后兼容）
# --------------------------
class SchematicProcessor(GroupProcessor):
    """向后兼容的 SchematicProcessor 类。"""

    def __init__(self, all_notes, global_max_tick, config, group_config):
        super().__init__(all_notes, global_max_tick, config, group_config)
        self.set_output_strategy(SchematicOutputStrategy())

    def _generate_base_structures(self, tick: int):
        """向后兼容的方法。"""
        pass

    def _generate_pan_platform(self, tick: int, direction: int):
        """向后兼容的方法。"""
        pass

    def _generate_note(self, note: Note):
        """向后兼容的方法。"""
        pass

    def _write(self, commands: List[str]):
        """向后兼容的方法。"""
        pass

    def process(self):
        """前置校验 + 父类流程 + 最终保存。"""
        # 验证配置
        SchematicOutputStrategy.validate_config(self)
        super().process()