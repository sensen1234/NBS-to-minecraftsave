"""
Minecraft函数文件生成器
----------------------
负责将Note列表转换成Minecraft .mcfunction命令文件。

主要流程
1. 根据group_config把Note划分到不同轨道组。
2. 每个轨道组内部：
   2.1 生成tick级基础结构（时钟、走线）。
   2.2 根据panning生成左右声像平台。
   2.3 在准确坐标生成音符方块及其基座。
3. 输出为.mcfunction命令文件
"""

from __future__ import annotations

from typing import Dict, List

from pynbs import Note

from .core import GroupProcessor, OutputFormatStrategy
from .constants import INSTRUMENT_MAPPING, INSTRUMENT_BLOCK_MAPPING, NOTEPITCH_MAPPING

# --------------------------
# 命令文件生成策略
# --------------------------
class McFunctionOutputStrategy(OutputFormatStrategy):
    """输出为 .mcfunction 命令文件的策略实现。"""
    
    def __init__(self):
        self.commands = []  # 存储生成的命令

    def initialize(self, processor: GroupProcessor):
        """
        初始化输出格式，清空命令列表
        
        参数:
        processor: GroupProcessor实例
        """
        self.commands = []
        # 清空输出文件
        output_file = processor.config["output_file"] + ".mcfunction"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("")  # 创建空文件或清空已有文件

    def write_base_structures(self, processor: GroupProcessor, tick: int):
        """
        写入基础结构
        
        参数:
        processor: GroupProcessor实例
        tick: 当前tick
        """
        # 计算当前tick在X轴上的位置（每个tick占2格）
        tick_x = processor.base_x + tick * 2
        commands = [
            f"setblock {tick_x} {processor.base_y} {processor.base_z} {processor.cover_block}",
            f"setblock {tick_x} {processor.base_y - 1} {processor.base_z} {processor.base_block}",
            f"setblock {tick_x - 1} {processor.base_y} {processor.base_z} minecraft:repeater[delay=1,facing=west]",
            f"setblock {tick_x - 1} {processor.base_y - 1} {processor.base_z} {processor.base_block}",
        ]
        self._write_commands(processor, commands)

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
            return  # 已生成

        # 获取该方向上的最大偏移量
        max_pan_offset = processor._get_max_pan(processor.notes, tick, direction)
        if max_pan_offset == 0:
            return

        # 计算平台的起始和结束坐标
        tick_x = processor.base_x + tick * 2
        platform_start_z = processor.get_platform_start_z()  # 平台起始Z坐标（主干道）
        platform_end_z = processor.calculate_platform_end_z(max_pan_offset, direction)

        # 生成平台基础结构命令
        platform_commands = [
            f"fill {tick_x} {processor.base_y - 1} {platform_start_z} {tick_x} {processor.base_y - 1} {platform_end_z} {processor.base_block}",
            f"setblock {tick_x} {processor.base_y} {platform_start_z} {processor.cover_block}",
        ]

        # 如果偏移量大于1，需要铺设红石线连接
        if abs(max_pan_offset) > 1:
            # 红石线的起始位置应该是从主干道旁边开始
            wire_start_z = processor.get_wire_start_z(direction)
            wire_end_z = platform_end_z
            platform_commands.append(
                f"fill {tick_x} {processor.base_y} {wire_start_z} {tick_x} {processor.base_y} {wire_end_z} "
                "minecraft:redstone_wire[north=side,south=side]"
            )

        self._write_commands(processor, platform_commands)
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

        # 生成音符方块和基座方块的命令
        commands = [
            f"setblock {tick_x} {y} {z_pos} note_block[note={note_pitch},instrument={instrument}]",
            f"setblock {tick_x} {y - 1} {z_pos} {base_block}",
        ]

        # 如果基座是沙子类方块，需要在下方添加屏障防止掉落
        if self.is_sand_block(base_block):
            commands.append(f"setblock {tick_x} {y - 2} {z_pos} barrier")

        self._write_commands(processor, commands)

    def finalize(self, processor: GroupProcessor):
        """
        完成输出，将所有命令写入文件
        
        参数:
        processor: GroupProcessor实例
        """
        output_file = processor.config["output_file"] + ".mcfunction"
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n".join(self.commands) + "\n\n")

    def _write_commands(self, processor: GroupProcessor, commands: List[str]):
        """
        将命令添加到命令列表中
        
        参数:
        processor: GroupProcessor实例
        commands: 要添加的命令列表
        """
        self.commands.extend(commands)

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


# --------------------------
# 兼容性类（为了保持向后兼容）
# --------------------------
class McFunctionProcessor(GroupProcessor):
    """向后兼容的 McFunctionProcessor 类。"""

    def __init__(self, all_notes, global_max_tick, config, group_config):
        super().__init__(all_notes, global_max_tick, config, group_config)
        self.set_output_strategy(McFunctionOutputStrategy())

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