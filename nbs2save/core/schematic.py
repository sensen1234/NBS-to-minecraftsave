# -*- coding: utf-8 -*-
"""
轨道组处理核心模块
----------------
负责把 Note 列表转换成 Minecraft 命令或 .schem 结构文件。

主要流程
1. 根据 group_config 把 Note 划分到不同轨道组。
2. 每个轨道组内部：
   2.1 生成 tick 级基础结构（时钟、走线）。
   2.2 根据 panning 生成左右声像平台。
   2.3 在准确坐标生成音符方块及其基座。
3. 输出：
   - McFunctionProcessor → .mcfunction 命令文件
   - SchematicProcessor  → .schem 结构文件
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from mcschematic import MCSchematic
from collections import defaultdict
from pynbs import Note

from .constants import INSTRUMENT_MAPPING, INSTRUMENT_BLOCK_MAPPING, NOTEPITCH_MAPPING
from .config import GENERATE_CONFIG, GROUP_CONFIG
from .core import GroupProcessor

# --------------------------
# 结构文件生成器
# --------------------------
class SchematicProcessor(GroupProcessor):

    """输出为 .schem 结构文件。"""

    def __init__(self, all_notes, global_max_tick, config, group_config):
        super().__init__(all_notes, global_max_tick, config, group_config)
        self.schem: MCSchematic = MCSchematic()  # 内存中的结构对象
        self.regions: dict[str, any] = {}  # 预留多区域支持
        self.region_index = 0
        self.current_region = None

    # ----------------------
    # 覆写主流程
    # ----------------------
    def process(self):
        """前置校验 + 父类流程 + 最终保存。"""
        self.validate_config()
        self.schem = MCSchematic()  # 重新初始化
        super().process()
        path = self.config["output_file"]
        # 保存到本地 .schem
        self.schem.save(".", path.rsplit("/", 1)[-1], self.config["data_version"])

    # ----------------------
    # 生成逻辑（与 McFunctionProcessor 类似，但直接操作 MCSchematic）
    # ----------------------
    def _generate_base_structures(self, tick: int):
        x = self.base_x + tick * 2
        self.schem.setBlock((x, self.base_y, self.base_z), self.cover_block)
        self.schem.setBlock((x, self.base_y - 1, self.base_z), self.base_block)
        self.schem.setBlock((x - 1, self.base_y, self.base_z), "minecraft:repeater[delay=1,facing=west]")
        self.schem.setBlock((x - 1, self.base_y - 1, self.base_z), self.base_block)

    def _generate_pan_platform(self, tick: int, direction: int):
        if self.tick_status[tick]["right" if direction == 1 else "left"]:
            return

        max_pan = self._get_max_pan(self.notes, tick, direction)
        if max_pan == 0:
            return

        x = self.base_x + tick * 2
        z_start = self.base_z
        z_end = self.base_z + max_pan - (1 if direction == 1 else -1)
        step = 1 if direction == 1 else -1
        for z in range(z_start, z_end + step, step):
            self.schem.setBlock((x, self.base_y - 1, z), self.base_block)

        self.schem.setBlock((x, self.base_y, z_start), self.cover_block)

        if abs(max_pan) > 1:
            wire_start = z_start + direction
            wire_end = z_end
            for z in range(wire_start, wire_end + step, step):
                self.schem.setBlock(
                    (x, self.base_y, z),
                    "minecraft:redstone_wire[north=side,south=side]"
                )

        self.tick_status[tick]["right" if direction == 1 else "left"] = True

    def _generate_note(self, note: Note):
        tick_x, y, z_pos = self.get_note_position(note)
        instrument, base_block, note_pitch = self.get_note_block_info(note)

        self.schem.setBlock(
            (tick_x, y, z_pos),
            f"minecraft:note_block[note={note_pitch},instrument={instrument}]"
        )
        self.schem.setBlock((tick_x, y - 1, z_pos), base_block)

        if self.is_sand_block(base_block):
            self.schem.setBlock((tick_x, y - 2, z_pos), "minecraft:barrier")

    def _write(self, _: List[str]):
        """
        空实现：SchematicProcessor 直接操作 MCSchematic，无需收集命令。
        预留接口用于未来多区域拆分。
        """
        self.regions[str(self.region_index)] = self.current_region
        self.region_index += 1

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

    def get_note_position(self, note: Note):
        """统一计算音符坐标：x 轴随 tick 延伸，z 轴随 pan 偏移。"""
        tick_x = self.base_x + note.tick * 2
        pan = self._calculate_pan(note)
        z_pos = self.base_z + pan
        return tick_x, self.base_y, z_pos

    # ----------------------
    # 配置校验
    # ----------------------
    def validate_config(self):
        """确保 config 包含必需的键。"""
        required_keys = ["output_file", "data_version"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"配置缺失: {key}")
            