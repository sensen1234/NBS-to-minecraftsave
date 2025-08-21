# -*- coding: utf-8 -*-
"""
Minecraft阶梯向下结构文件生成器
----------------------
负责将Note列表转换成Minecraft .schem结构文件，采用阶梯向下布局。

主要流程
1. 根据group_config把Note划分到不同轨道组。
2. 每个轨道组内部：
   2.1 生成tick级基础结构（时钟、走线）。
   2.2 根据panning生成左右声像平台（偏移>=3时启用阶梯效果）。
   2.3 在准确坐标生成音符方块及其基座（偏移>=3时启用阶梯效果）。
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
# 阶梯结构文件生成策略
# --------------------------
class StaircaseSchematicOutputStrategy(OutputFormatStrategy):
    """输出为 .schem 结构文件的阶梯向下策略实现。"""

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
        写入声像平台（阶梯向下模式）
        
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
        
        # 判断是否需要启用阶梯效果（偏移量>=3）
        use_staircase = abs(max_pan_offset) >= 3
        base_y = processor.base_y
        
        # 生成平台基座方块
        if use_staircase:
            # 阶梯向下模式：主干道保持在base_y层，也就是中继器下面的那一层，之后每增加一个偏移单位下降一格
            for z in range(platform_start_z, platform_end_z + step, step):
                if z == platform_start_z:
                    # 主干道位置保持在base_y层（与默认模式一致）
                    self.schem.setBlock((tick_x, base_y, z), processor.base_block)
                else:
                    # 偏移位置每增加一个偏移单位下降一格
                    # 计算距离主干道的偏移量
                    distance = abs(z - platform_start_z)
                    self.schem.setBlock((tick_x, base_y - distance, z), processor.base_block)
        else:
            # 默认模式
            for z in range(platform_start_z, platform_end_z + step, step):
                self.schem.setBlock((tick_x, base_y - 1, z), processor.base_block)

        # 在主干道位置放置覆盖方块（始终在base_y层）（这里好像写乱了，我也不知道咋改，能跑就行）
        self.schem.setBlock((tick_x, processor.base_y, platform_start_z), processor.cover_block)

        # 如果偏移量大于1，需要铺设红石线连接
        if abs(max_pan_offset) > 1:
            # 红石线的起始位置应该是从主干道旁边开始
            wire_start_z = processor.get_wire_start_z(direction)
            wire_end_z = platform_end_z
            
            if use_staircase:   #这里的use_staircase，是看是否启用阶梯效果，如果偏移量大于等于3，则为启动，2和1为普通模式
                # 阶梯向下模式：红石线从主干道开始，每增加一个偏移单位下降一格
                for z in range(wire_start_z, wire_end_z + step, step):
                    # 计算距离主干道的偏移量
                    distance = abs(z - platform_start_z)
                    # 红石线高度：主干道位置在base_y+1层，也就是cover层，之后每增加一个偏移单位下降一格
                    y_pos = base_y +1 - distance
                    self.schem.setBlock(
                        (tick_x, y_pos, z),
                        "minecraft:redstone_wire[north=side,south=side]"
                    )
            else:
                # 默认模式：红石线与cover层同高
                for z in range(wire_start_z, wire_end_z + step, step):
                    self.schem.setBlock(
                        (tick_x, processor.base_y, z),
                        "minecraft:redstone_wire[north=side,south=side]"
                    )

        processor.tick_status[tick]["right" if direction == 1 else "left"] = True

    def write_note(self, processor: GroupProcessor, note: Note):
        """
        写入音符（阶梯向下模式）
        
        参数:
        processor: GroupProcessor实例
        note: 要写入的音符
        """
        # 计算音符的位置坐标
        tick_x, base_y, z_pos = processor.get_note_position(note)
        pan_offset = processor._calculate_pan(note)
        
        # 获取当前tick、当前方向上的最大偏移量
        direction = 1 if pan_offset > 0 else -1 if pan_offset < 0 else 0
        max_pan_offset = 0
        if direction != 0:
            max_pan_offset = processor._get_max_pan(processor.notes, note.tick, direction)
        
        # 判断是否需要启用阶梯效果
        use_staircase = abs(max_pan_offset) >= 3
        
        # 计算音符高度
        if use_staircase and abs(pan_offset) >= 3:  # 只有当偏移量>=3时才应用阶梯效果
            # 主干道保持在base_y层，偏移位置每增加一个偏移单位下降一格
            # 需要加1来补偿音符方块自身的高度
            y_level = abs(pan_offset) - 1
            y_pos = base_y - y_level
        else:
            # 主干道或其他情况保持在base_y层
            y_pos = base_y
            
        # 获取音符方块的信息
        instrument, base_block, note_pitch = self.get_note_block_info(note)

        # 设置音符方块
        self.schem.setBlock(
            (tick_x, y_pos, z_pos),
            f"minecraft:note_block[note={note_pitch},instrument={instrument}]"
        )
        # 设置基座方块
        self.schem.setBlock((tick_x, y_pos - 1, z_pos), base_block)

        # 如果基座是沙子类方块，需要在下方添加屏障防止掉落
        if self.is_sand_block(base_block):
            self.schem.setBlock((tick_x, y_pos - 2, z_pos), "minecraft:barrier")

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

    # ----------------------
    # 配置校验
    # ----------------------
    def validate_config(self, processor: GroupProcessor):
        """确保 config 包含必需的键。"""
        required_keys = ["output_file", "data_version"]
        for key in required_keys:
            if key not in processor.config:
                raise ValueError(f"配置缺失: {key}")