from abc import ABC, abstractmethod
from typing import Dict, List

from mcschematic import MCSchematic
from collections import defaultdict
from pynbs import Note

from .constants import INSTRUMENT_MAPPING, INSTRUMENT_BLOCK_MAPPING, NOTEPITCH_MAPPING
from .config import GENERATE_CONFIG, GROUP_CONFIG

# --------------------------
# 轨道组处理器类
# --------------------------


class GroupProcessor(ABC):
    """轨道组处理核心类"""

    def __init__(self, all_notes: List[Note], global_max_tick: int, config: Dict, group_config: Dict):
        """
        初始化轨道组处理器
        :param all_notes: 音符
        :param global_max_tick: 音乐总长度(tick)
        :param config: 生成配置
        :param group_config: 轨道组配置
        """
        self.all_notes = all_notes
        self.global_max_tick = global_max_tick
        self.config = config
        self.group_config = group_config
        self.base_x = None
        self.base_y = None
        self.base_z = None
        self.notes = None
        self.tick_status = None
        self.group_max_tick = None
        self.layers = None
        self.cover_block = None
        self.base_block = None
        self.log_callback = None
        self.progress_callback = None

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def log(self, message):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message)

    def update_progress(self, value):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(value)

    def process(self):
        # 处理每个轨道组
        for group_id, config in self.group_config.items():
            self.log(f"\n>> 处理轨道组 {group_id}:")
            self.log(f"├─ 包含轨道: {config['layers']}")
            self.log(f"├─ 基准坐标: {config['base_coords']}")
            self.log(f"└─ 方块配置: {config['block']}")

            self.base_x, self.base_y, self.base_z = map(int, config['base_coords'])
            self.base_block = config['block']['base']
            self.cover_block = config['block']['cover']

            # 轨道和状态配置
            self.layers = set(config['layers'])
            self.tick_status = defaultdict(lambda: {'left': False, 'right': False})

            # 音符数据
            self.notes = []
            self.group_max_tick = 0

            self.load_notes(self.all_notes)

            if self.notes:
                self.log(f"   ├─ 发现音符数量: {len(self.notes)}")
                self.log(f"   └─ 组内最大tick: {self.group_max_tick}")
            else:
                self.log("   └─ 警告: 未找到该组的音符")

            self.process_group()

    def load_notes(self, all_notes: List[Note]):
        """加载并预处理属于本组的音符"""
        self.notes = sorted(
            [n for n in all_notes if n.layer in self.layers],
            key=lambda x: x.tick
        )
        if self.notes:
            self.group_max_tick = max(n.tick for n in self.notes)
        else:
            self.group_max_tick = 0

    @staticmethod
    def _calculate_pan(note: Note) -> int:
        """计算声像偏移值"""
        return int(round(note.panning / 10))

    @staticmethod
    def _get_max_pan(notes: List[Note], tick: int, direction: int):
        """获取当前tick指定方向的最大偏移值"""
        max_pan = 0
        for note in notes:
            if note.tick == tick:
                pan = GroupProcessor._calculate_pan(note)
                if pan * direction > 0:
                    max_pan = max(max_pan, abs(pan))
        return max_pan * direction

    def process_group(self):
        """处理整个轨道组到全局最大tick"""
        current_tick = 0
        note_ptr = 0

        # 遍历所有tick直到全局最大长度
        while current_tick <= self.global_max_tick:
            # 更新进度
            progress = int((current_tick / self.global_max_tick) *
                           100) if self.global_max_tick > 0 else 0
            self.update_progress(progress)

            # 无论是否有音符都生成基础结构
            self._generate_base_structures(current_tick)

            # 收集当前tick的有效音符
            active_notes = []
            while note_ptr < len(self.notes) and self.notes[note_ptr].tick == current_tick:
                active_notes.append(self.notes[note_ptr])
                note_ptr += 1

            # 检测音符位置冲突
            occupied_positions = set()
            for note in active_notes:
                pan = self._calculate_pan(note)
                z_pos = self.base_z + pan
                position = (current_tick, z_pos)  # 位置标识符 (tick, z坐标)

                if position in occupied_positions:
                    # 发现位置冲突，报错并终止
                    raise Exception(
                        f"位置冲突! Tick {current_tick}, Z={z_pos} 位置已有音符\n"
                        f"冲突音符: Layer={note.layer}, Key={note.key}, Instrument={note.instrument}"
                    )
                occupied_positions.add(position)

            # 协调生成声像平台
            pan_directions = set()
            for note in active_notes:
                pan = self._calculate_pan(note)
                if pan != 0:
                    pan_directions.add(1 if pan > 0 else -1)

            # 优先生成左侧平台
            for direction in sorted(pan_directions, reverse=True):
                self._generate_pan_platform(current_tick, direction)

            # 生成音符命令
            for note in active_notes:
                self._generate_note(note)

            current_tick += 1

    @abstractmethod
    def _generate_base_structures(self, tick: int):
        pass

    @abstractmethod
    def _generate_pan_platform(self, tick: int, direction: int):
        pass
    
    @abstractmethod
    def _generate_note(self, note: Note):
        pass

    @abstractmethod
    def _write(self, commands: List[str]):
        pass


class McFunctionProcessor(GroupProcessor):
    def _generate_base_structures(self, tick: int):
        """生成每个tick的基础结构"""
        x = self.base_x + tick * 2
        commands = [
            f"setblock {x} {self.base_y} {self.base_z} {self.cover_block}",
            f"setblock {x} {self.base_y - 1} {self.base_z} {self.base_block}",
            f"setblock {x - 1} {self.base_y} {self.base_z} minecraft:repeater[delay=1,facing=west]",
            f"setblock {x - 1} {self.base_y - 1} {self.base_z} {self.base_block}"
        ]
        self._write(commands)

    def _generate_pan_platform(self, tick: int, direction: int):
        """生成声像偏移平台"""
        if self.tick_status[tick]['right' if direction == 1 else 'left']:
            return

        max_pan = self._get_max_pan(self.notes, tick, direction)
        if max_pan == 0:
            return

        x = self.base_x + tick * 2
        z_start = self.base_z
        z_end = self.base_z + max_pan - (1 if direction == 1 else -1)

        platform_cmds = [
            f"fill {x} {self.base_y - 1} {z_start} {x} {self.base_y - 1} {z_end} {self.base_block}",
            f"setblock {x} {self.base_y} {z_start} {self.cover_block}"
        ]

        # 生成红石线路
        if abs(max_pan) > 1:
            wire_start = z_start + direction
            wire_end = z_end
            platform_cmds.append(
                f"fill {x} {self.base_y} {wire_start} {x} {self.base_y} {wire_end} minecraft:redstone_wire[north=side,south=side]"
            )

        self._write(platform_cmds)
        self.tick_status[tick]['right' if direction == 1 else 'left'] = True

    def _generate_note(self, note: Note):
        """生成单个音符的命令"""
        tick_x, y, z_pos = self.get_note_position(note)
        instrument, base_block, note_pitch = self.get_note_block_info(note)

        commands = [
            f"setblock {tick_x} {y} {z_pos} note_block[note={note_pitch},instrument={instrument}]",
            f"setblock {tick_x} {y - 1} {z_pos} {base_block}"
        ]

        # 沙子特殊处理
        if self.is_sand_block(base_block):
            commands.append(f"setblock {tick_x} {y - 2} {z_pos} barrier")

        self._write(commands)

    def _write(self, commands: List[str]):
        """将命令写入文件"""
        output_file = self.config['output_file'] + ".mcfunction"
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write("\n".join(commands) + "\n\n")


class SchematicProcessor(GroupProcessor):
    def __init__(self, all_notes, global_max_tick, config, group_config):
        super().__init__(all_notes, global_max_tick, config, group_config)
        self.schem: MCSchematic = MCSchematic()
        self.regions = {}
        self.region_index = 0
        self.current_region = None

    def process(self):
        self.validate_config()
        self.schem = MCSchematic()
        super().process()
        path = self.config['output_file']
        self.schem.save(".", path.rsplit('/', 1)[-1], self.config['data_version'])

    def _generate_base_structures(self, tick: int):
        x = self.base_x + tick * 2
        self.schem.setBlock((x, self.base_y, self.base_z), self.cover_block)
        self.schem.setBlock((x, self.base_y - 1, self.base_z), self.base_block)
        self.schem.setBlock((x - 1, self.base_y, self.base_z),
                            "minecraft:repeater[delay=1,facing=west]")
        self.schem.setBlock((x - 1, self.base_y - 1, self.base_z), self.base_block)

    def _generate_pan_platform(self, tick: int, direction: int):
        if self.tick_status[tick]['right' if direction == 1 else 'left']:
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
                self.schem.setBlock((x, self.base_y, z),
                                    "minecraft:redstone_wire[north=side,south=side]")

        self.tick_status[tick]['right' if direction == 1 else 'left'] = True

    def _generate_note(self, note: Note):
        tick_x, y, z_pos = self.get_note_position(note)
        instrument, base_block, note_pitch = self.get_note_block_info(note)

        self.schem.setBlock((tick_x, y, z_pos),
                            f"minecraft:note_block[note={note_pitch},instrument={instrument}]")
        self.schem.setBlock((tick_x, y - 1, z_pos), base_block)

        if self.is_sand_block(base_block):
            self.schem.setBlock((tick_x, y - 2, z_pos), "minecraft:barrier")

    def _write(self, _: List[str]):
        self.regions[str(self.region_index)] = self.current_region
        self.region_index += 1

    @staticmethod
    def get_note_block_info(note: Note):
        """获取音符方块的所有属性"""
        instrument = INSTRUMENT_MAPPING.get(note.instrument, "harp")
        base_block = INSTRUMENT_BLOCK_MAPPING.get(note.instrument, "minecraft:stone")
        note_pitch = NOTEPITCH_MAPPING.get(note.key, "0")
        return instrument, base_block, note_pitch

    @staticmethod
    def is_sand_block(block: str) -> bool:
        """判断是否为沙子类方块"""
        return block.endswith("sand")

    def get_note_position(self, note: Note):
        """统一音符坐标计算"""
        tick_x = self.base_x + note.tick * 2
        pan = self._calculate_pan(note)
        z_pos = self.base_z + pan
        return tick_x, self.base_y, z_pos

    def validate_config(self):
        """配置校验"""
        required_keys = ['output_file', 'data_version']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"配置缺失: {key}")
