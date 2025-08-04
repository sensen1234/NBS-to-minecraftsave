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

from nbs2save.core.core import GroupProcessor

from .constants import INSTRUMENT_MAPPING, INSTRUMENT_BLOCK_MAPPING, NOTEPITCH_MAPPING
from .config import GENERATE_CONFIG, GROUP_CONFIG

# --------------------------
# 命令文件生成器
# --------------------------
class McFunctionProcessor(GroupProcessor):
    """输出为 .mcfunction 命令文件。"""

    def _generate_base_structures(self, tick: int):
        """
        每 tick 生成 2 格宽的基础走线：
        (x, base_y, base_z)     -> cover_block（遮蔽）
        (x, base_y-1, base_z)   -> base_block（基座）
        (x-1, ...)              -> repeater 延时 1 tick 向西
        """
        x = self.base_x + tick * 2
        commands = [
            f"setblock {x} {self.base_y} {self.base_z} {self.cover_block}",
            f"setblock {x} {self.base_y - 1} {self.base_z} {self.base_block}",
            f"setblock {x - 1} {self.base_y} {self.base_z} minecraft:repeater[delay=1,facing=west]",
            f"setblock {x - 1} {self.base_y - 1} {self.base_z} {self.base_block}",
        ]
        self._write(commands)

    def _generate_pan_platform(self, tick: int, direction: int):
        """声像平台：fill + setblock 实现可延伸的基座与红石线。"""
        if self.tick_status[tick]["right" if direction == 1 else "left"]:
            return  # 已生成

        max_pan = self._get_max_pan(self.notes, tick, direction)
        if max_pan == 0:
            return

        x = self.base_x + tick * 2
        z_start = self.base_z
        z_end = self.base_z + max_pan - (1 if direction == 1 else -1)

        platform_cmds = [
            f"fill {x} {self.base_y - 1} {z_start} {x} {self.base_y - 1} {z_end} {self.base_block}",
            f"setblock {x} {self.base_y} {z_start} {self.cover_block}",
        ]

        # 如果长度 > 1，再铺红石线
        if abs(max_pan) > 1:
            wire_start = z_start + direction
            wire_end = z_end
            platform_cmds.append(
                f"fill {x} {self.base_y} {wire_start} {x} {self.base_y} {wire_end} "
                "minecraft:redstone_wire[north=side,south=side]"
            )

        self._write(platform_cmds)
        self.tick_status[tick]["right" if direction == 1 else "left"] = True

    def _generate_note(self, note: Note):
        """生成单个音符方块及其基座（沙子额外加 barrier 防落）。"""
        tick_x, y, z_pos = self.get_note_position(note)
        instrument, base_block, note_pitch = self.get_note_block_info(note)

        commands = [
            f"setblock {tick_x} {y} {z_pos} note_block[note={note_pitch},instrument={instrument}]",
            f"setblock {tick_x} {y - 1} {z_pos} {base_block}",
        ]

        if self.is_sand_block(base_block):
            commands.append(f"setblock {tick_x} {y - 2} {z_pos} barrier")

        self._write(commands)

    def _write(self, commands: List[str]):
        """把命令追加写入 .mcfunction 文件。"""
        output_file = self.config["output_file"] + ".mcfunction"
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n".join(commands) + "\n\n")

