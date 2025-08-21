# -*- coding: utf-8 -*-
"""
轨道组处理核心模块
----------------
负责把 Note 列列转换成 Minecraft 命令或 .schem 结构文件。

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
# 输出格式策略接口
# --------------------------
class OutputFormatStrategy(ABC):
    """
    定义输出格式的策略接口
    不同的输出格式（如mcfunction、schematic）需要实现这个接口
    """
    
    @abstractmethod
    def initialize(self, processor: GroupProcessor):
        """
        初始化输出格式
        
        参数:
        processor: GroupProcessor实例
        """
        pass
    
    @abstractmethod
    def write_base_structures(self, processor: GroupProcessor, tick: int):
        """
        写入基础结构
        
        参数:
        processor: GroupProcessor实例
        tick: 当前tick
        """
        pass
    
    @abstractmethod
    def write_pan_platform(self, processor: GroupProcessor, tick: int, direction: int):
        """
        写入声像平台
        
        参数:
        processor: GroupProcessor实例
        tick: 当前tick
        direction: 方向（1=右，-1=左）
        """
        pass
    
    @abstractmethod
    def write_note(self, processor: GroupProcessor, note: Note):
        """
        写入音符
        
        参数:
        processor: GroupProcessor实例
        note: 要写入的音符
        """
        pass
    
    @abstractmethod
    def finalize(self, processor: GroupProcessor):
        """
        完成输出
        
        参数:
        processor: GroupProcessor实例
        """
        pass


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
        self.base_x: int | None = None  # 轨道组基准 X 坐标
        self.base_y: int | None = None  # 轨道组基准 Y 坐标
        self.base_z: int | None = None  # 轨道组基准 Z 坐标
        self.notes: List[Note] | None = None  # 属于本组的音符（按 tick 排序）
        self.tick_status: defaultdict[int, Dict[str, bool]] = None  # tick 级状态缓存
        self.group_max_tick: int = 0  # 本组最大 tick
        self.layers: set[int] = set()  # 本组包含的 layer 编号
        self.cover_block: str = ""  # 走线顶层方块
        self.base_block: str = ""  # 走线/基座方块
        self.log_callback = None  # 日志回调
        self.progress_callback = None  # 进度回调
        self.output_strategy: OutputFormatStrategy = None  # 输出格式策略
        self.generation_mode: str = "default"  # 生成模式（default 或 staircase）

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
    # 输出策略设置
    # ----------------------
    def set_output_strategy(self, strategy: OutputFormatStrategy):
        """
        设置输出格式策略
        
        参数:
        strategy: OutputFormatStrategy实例
        """
        self.output_strategy = strategy
        self.output_strategy.initialize(self)

    # ----------------------
    # 主流程入口
    # ----------------------
    def process(self):
        """遍历所有轨道组，依次处理。"""
        # 检查是否设置了输出策略
        if self.output_strategy is None:
            raise ValueError("未设置输出格式策略，请先调用set_output_strategy方法")
            
        for group_id, config in self.group_config.items():
            self.log(f"\n>> 处理轨道组 {group_id}:")
            self.log(f"├─ 包含轨道: {config['layers']}")
            self.log(f"├─ 基准坐标: {config['base_coords']}")
            self.log(f"├─ 方块配置: {config['block']}")
            self.log(f"└─ 生成模式: {config.get('generation_mode', 'default')}")

            # 初始化本组专属字段
            self.base_x, self.base_y, self.base_z = map(int, config["base_coords"])
            self.base_block = config["block"]["base"]
            self.cover_block = config["block"]["cover"]
            self.generation_mode = config.get("generation_mode", "default")  # 获取生成模式
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
            
        # 完成处理
        self.output_strategy.finalize(self)

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
            key=lambda note: note.tick,
        )
        self.group_max_tick = max(note.tick for note in self.notes) if self.notes else 0

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
        
        参数:
        notes: 音符列表
        tick: 当前tick
        direction: 方向（1=右，-1=左）
        
        返回:
        带符号的最大偏移值
        """
        max_pan = 0
        for note in notes:
            if note.tick == tick:
                pan = GroupProcessor._calculate_pan(note)
                # 检查音符方向是否与指定方向一致
                if pan * direction > 0:
                    max_pan = max(max_pan, abs(pan))
        return max_pan * direction  # 带符号

    # ----------------------
    # 坐标计算（可被子类重写）
    # ----------------------
    def get_note_position(self, note: Note) -> tuple[int, int, int]:
        """
        计算音符在Minecraft世界中的坐标位置
        子类可以重写此方法以实现不同的坐标计算逻辑
        
        参数:
        note: 要计算坐标的音符
        
        返回:
        (x, y, z) 三元组，表示音符在Minecraft世界中的坐标
        """
        tick_x = self.base_x + note.tick * 2
        pan_offset = self._calculate_pan(note)
        z_pos = self.base_z + pan_offset
        return tick_x, self.base_y, z_pos

    def get_platform_start_z(self) -> int:
        """
        获取平台起始Z坐标（主干道位置）
        
        返回:
        平台起始Z坐标
        """
        return self.base_z

    def calculate_platform_end_z(self, max_pan_offset: int, direction: int) -> int:
        """
        计算平台结束Z坐标
        
        参数:
        max_pan_offset: 最大偏移量
        direction: 方向（1=右，-1=左）
        
        返回:
        平台结束Z坐标
        """
        platform_start_z = self.get_platform_start_z()
        if direction == 1:  # 右侧
            return platform_start_z + max_pan_offset - 1
        else:  # 左侧
            return platform_start_z + max_pan_offset + 1

    def get_wire_start_z(self, direction: int) -> int:
        """
        获取红石线起始Z坐标（从主干道旁边开始）
        
        参数:
        direction: 方向（1=右，-1=左）
        
        返回:
        红石线起始Z坐标
        """
        platform_start_z = self.get_platform_start_z()
        return platform_start_z + direction

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
        note_index = 0  # 已处理到的音符索引

        while current_tick <= self.global_max_tick:
            # 1. 更新进度
            progress = (
                int((current_tick / self.global_max_tick) * 100)
                if self.global_max_tick
                else 0
            )
            self.update_progress(progress)

            # 2. 基础结构（时钟、走线）
            self.output_strategy.write_base_structures(self, current_tick)

            # 3. 收集当前 tick 的音符
            active_notes: List[Note] = []
            while note_index < len(self.notes) and self.notes[note_index].tick == current_tick:
                active_notes.append(self.notes[note_index])
                note_index += 1

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
                self.output_strategy.write_pan_platform(self, current_tick, direction)

            # 6. 生成音符
            for note in active_notes:
                self.output_strategy.write_note(self, note)

            current_tick += 1