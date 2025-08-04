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


# --------------------------
# 轨道组处理器抽象基类
# --------------------------
class GroupProcessor(ABC):
    """
    抽象基类：处理单个轨道组（Group）内部的所有音符。
    子类决定最终输出格式：命令文件 或 结构文件。
    """

    def __init__(
        self,
        all_notes: List[Note],
        global_max_tick: int,
        config: Dict,
        group_config: Dict,
    ):
        """
        参数
        ----
        all_notes : List[Note]
            整首曲子的全部音符。
        global_max_tick : int
            曲子总长度（tick），用于计算进度。
        config : Dict
            全局生成配置，如输出路径、版本号等。
        group_config : Dict
            轨道组配置，格式见 GROUP_CONFIG。
        """
        self.all_notes: List[Note] = all_notes
        self.global_max_tick: int = global_max_tick
        self.config: Dict = config
        self.group_config: Dict = group_config

        # 以下字段在 process() 中动态填充
        self.base_x: int | None = None  # 轨道组基准 X
        self.base_y: int | None = None  # 轨道组基准 Y
        self.base_z: int | None = None  # 轨道组基准 Z
        self.notes: List[Note] | None = None  # 属于本组的音符（按 tick 排序）
        self.tick_status: defaultdict[int, Dict[str, bool]] = None  # tick 级状态缓存
        self.group_max_tick: int = 0  # 本组最大 tick
        self.layers: set[int] = set()  # 本组包含的 layer 编号
        self.cover_block: str = ""  # 走线顶层方块
        self.base_block: str = ""  # 走线/基座方块
        self.log_callback = None  # 日志回调
        self.progress_callback = None  # 进度回调

    # ----------------------
    # 回调注册
    # ----------------------
    def set_log_callback(self, callback):
        """设置日志输出回调，供前端 UI 实时显示信息。"""
        self.log_callback = callback

    def set_progress_callback(self, callback):
        """设置进度更新回调，参数为 0-100 整数。"""
        self.progress_callback = callback

    def log(self, message: str):
        """内部统一日志接口。"""
        if self.log_callback:
            self.log_callback(message)

    def update_progress(self, value: int):
        """内部统一进度接口。"""
        if self.progress_callback:
            self.progress_callback(value)

    # ----------------------
    # 主流程入口
    # ----------------------
    def process(self):
        """遍历所有轨道组，依次处理。"""
        for group_id, config in self.group_config.items():
            self.log(f"\n>> 处理轨道组 {group_id}:")
            self.log(f"├─ 包含轨道: {config['layers']}")
            self.log(f"├─ 基准坐标: {config['base_coords']}")
            self.log(f"└─ 方块配置: {config['block']}")

            # 初始化本组专属字段
            self.base_x, self.base_y, self.base_z = map(int, config["base_coords"])
            self.base_block = config["block"]["base"]
            self.cover_block = config["block"]["cover"]
            self.layers = set(config["layers"])
            self.tick_status = defaultdict(lambda: {"left": False, "right": False})

            # 加载本组音符
            self.load_notes(self.all_notes)
            if self.notes:
                self.log(f"   ├─ 发现音符数量: {len(self.notes)}")
                self.log(f"   └─ 组内最大tick: {self.group_max_tick}")
            else:
                self.log("   └─ 警告: 未找到该组的音符")

            # 核心生成
            self.process_group()

    # ----------------------
    # 音符加载 & 工具方法
    # ----------------------
    def load_notes(self, all_notes: List[Note]):
        """
        过滤出属于本组的音符，并按 tick 升序排序。
        同时计算组内最大 tick。
        """
        self.notes = sorted(
            (n for n in all_notes if n.layer in self.layers),
            key=lambda n: n.tick,
        )
        self.group_max_tick = max(n.tick for n in self.notes) if self.notes else 0

    @staticmethod
    def _calculate_pan(note: Note) -> int:
        """
        把 Note.panning（-100~100）映射到整数格偏移：
        - 0 表示中央
        - 正数向右，负数向左
        """
        return int(round(note.panning / 10))

    @staticmethod
    def _get_max_pan(notes: List[Note], tick: int, direction: int) -> int:
        """
        在指定 tick 内，找出给定方向（1=右，-1=左）的最大绝对偏移值。
        用于决定声像平台长度。
        """
        max_pan = 0
        for note in notes:
            if note.tick == tick:
                pan = GroupProcessor._calculate_pan(note)
                if pan * direction > 0:
                    max_pan = max(max_pan, abs(pan))
        return max_pan * direction  # 带符号

    # ----------------------
    # 逐 tick 处理
    # ----------------------
    def process_group(self):
        """
        从 tick 0 到 global_max_tick，每一步：
        1. 生成基础时钟结构；
        2. 收集当前 tick 的所有音符；
        3. 检测位置冲突；
        4. 生成声像平台；
        5. 生成音符方块。
        """
        current_tick = 0
        note_ptr = 0  # 已处理到的音符下标

        while current_tick <= self.global_max_tick:
            # 1. 更新进度
            progress = (
                int((current_tick / self.global_max_tick) * 100)
                if self.global_max_tick
                else 0
            )
            self.update_progress(progress)

            # 2. 基础结构（时钟、走线）
            self._generate_base_structures(current_tick)

            # 3. 收集当前 tick 的音符
            active_notes: List[Note] = []
            while note_ptr < len(self.notes) and self.notes[note_ptr].tick == current_tick:
                active_notes.append(self.notes[note_ptr])
                note_ptr += 1

            # 4. 检测坐标冲突：同一 tick 同一 z 不允许重复
            occupied_positions = set()
            for note in active_notes:
                pan = self._calculate_pan(note)
                z_pos = self.base_z + pan
                position = (current_tick, z_pos)
                if position in occupied_positions:
                    raise Exception(
                        f"位置冲突! Tick {current_tick}, Z={z_pos} 位置已有音符\n"
                        f"冲突音符: Layer={note.layer}, Key={note.key}, Instrument={note.instrument}"
                    )
                occupied_positions.add(position)

            # 5. 生成声像平台（左优先）
            pan_directions = set()
            for note in active_notes:
                pan = self._calculate_pan(note)
                if pan != 0:
                    pan_directions.add(1 if pan > 0 else -1)

            for direction in sorted(pan_directions, reverse=True):  # 左(-1) > 右(1)
                self._generate_pan_platform(current_tick, direction)

            # 6. 生成音符
            for note in active_notes:
                self._generate_note(note)

            current_tick += 1

    # ----------------------
    # 子类必须实现的抽象方法
    # ----------------------
    @abstractmethod
    def _generate_base_structures(self, tick: int):
        """生成当前 tick 的基础时钟结构。"""
        pass

    @abstractmethod
    def _generate_pan_platform(self, tick: int, direction: int):
        """
        根据方向生成声像偏移平台。
        direction: 1=右, -1=左
        """
        pass

    @abstractmethod
    def _generate_note(self, note: Note):
        """根据 Note 对象生成单个音符方块及其基座。"""
        pass

    @abstractmethod
    def _write(self, commands: List[str]):
        """
        把命令写入最终输出。
        在 McFunctionProcessor 里写入 .mcfunction；
        在 SchematicProcessor 里直接操作 MCSchematic。
        """
        pass




