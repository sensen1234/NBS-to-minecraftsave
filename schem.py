import pynbs
from mcschematic import Version, MCSchematic
from collections import defaultdict

# --------------------------
# 用户配置区 (按需修改)
# --------------------------

# 生成配置 (字典格式)
GENERATE_CONFIG = {
    'data_version': Version.JE_1_21_4,  # Minecraft version
    'input_file': 'test.nbs',  # 输入的.nbs文件路径
    'type': 'schematic',  # schematic -> WorldEdit文件, mcfunction -> 原版函数
    'output_file': 'test'  # 输出的文件 (不包含扩展名)
}

# 轨道组配置 (字典格式)
GROUP_CONFIG = {
    0: {
        'base_coords': ("0", "0", "0"),  # 基准坐标 (x,y,z)
        'layers': [0, 1],  # 包含的轨道ID列表
        'block': {  # 方块配置
            'base': 'minecraft:iron_block',  # 基础平台方块
            'cover': 'minecraft:iron_block'  # 顶部覆盖方块
        }
    },
}

# --------------------------
# 常量映射表 (通常无需修改)
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


# --------------------------
# 静态方法
# --------------------------

def _calculate_pan(note):
    """计算声像偏移值"""
    return int(round(note.panning / 10))


def _get_max_pan(notes, tick, direction):
    """获取当前tick指定方向的最大偏移值"""
    max_pan = 0
    for note in notes:
        if note.tick == tick:
            pan = _calculate_pan(note)
            if pan * direction > 0:
                max_pan = max(max_pan, abs(pan))
    return max_pan * direction


# --------------------------
# 轨道组处理器类
# --------------------------
class GroupProcessor:
    """轨道组处理核心类"""

    def __init__(self, all_notes, global_max_tick):
        """
        初始化轨道组处理器
        :param all_notes: 音符
        :param global_max_tick: 音乐总长度(tick)
        """
        self.all_notes = all_notes
        self.global_max_tick = global_max_tick
        self.base_x = None
        self.base_y = None
        self.base_z = None
        self.notes = None
        self.tick_status = None
        self.group_max_tick = None
        self.layers = None
        self.cover_block = None
        self.base_block = None

    def process(self):
        # 处理每个轨道组
        for group_id, config in GROUP_CONFIG.items():
            print(f"\n>> 处理轨道组 {group_id}:")
            print(f"├─ 包含轨道: {config['layers']}")
            print(f"├─ 基准坐标: {config['base_coords']}")
            print(f"└─ 方块配置: {config['block']}")

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
                print(f"   ├─ 发现音符数量: {len(self.notes)}")
                print(f"   └─ 组内最大tick: {self.group_max_tick}")
            else:
                print("   └─ 警告: 未找到该组的音符")

            self.process_group()

    def load_notes(self, all_notes):
        """加载并预处理属于本组的音符"""
        self.notes = sorted(
            [n for n in all_notes if n.layer in self.layers],
            key=lambda x: x.tick
        )
        if self.notes:
            self.group_max_tick = max(n.tick for n in self.notes)
        else:
            self.group_max_tick = 0

    def process_group(self):
        """处理整个轨道组到全局最大tick"""
        current_tick = 0
        note_ptr = 0

        # 遍历所有tick直到全局最大长度
        while current_tick <= self.global_max_tick:
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
                pan = _calculate_pan(note)
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
                pan = _calculate_pan(note)
                if pan != 0:
                    pan_directions.add(1 if pan > 0 else -1)

            # 优先生成左侧平台
            for direction in sorted(pan_directions, reverse=True):
                self._generate_pan_platform(current_tick, direction)

            # 生成音符命令
            for note in active_notes:
                self._generate_note(note)

            current_tick += 1

    def _generate_base_structures(self, tick):
        raise NotImplementedError('This is a abstract method.')

    def _generate_pan_platform(self, tick, direction):
        raise NotImplementedError('This is a abstract method.')

    def _generate_note(self, note):
        raise NotImplementedError('This is a abstract method.')

    def _write(self, commands):
        raise NotImplementedError('This is a abstract method.')


class McFunctionProcessor(GroupProcessor):
    def _generate_base_structures(self, tick):
        """生成每个tick的基础结构"""
        x = self.base_x + tick * 2
        commands = [
            f"setblock {x} {self.base_y} {self.base_z} {self.cover_block}",
            f"setblock {x} {self.base_y - 1} {self.base_z} {self.base_block}",
            f"setblock {x - 1} {self.base_y} {self.base_z} minecraft:repeater[delay=1,facing=west]",
            f"setblock {x - 1} {self.base_y - 1} {self.base_z} {self.base_block}"
        ]
        self._write(commands)

    def _generate_pan_platform(self, tick, direction):
        """生成声像偏移平台"""
        if self.tick_status[tick]['right' if direction == 1 else 'left']:
            return

        max_pan = _get_max_pan(self.notes, tick, direction)
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
                f"fill {x} {self.base_y} {wire_start} {x} {self.base_y} {wire_end} minecraft:redstone_wire[east=side,west=side]"
            )

        self._write(platform_cmds)
        self.tick_status[tick]['right' if direction == 1 else 'left'] = True

    def _generate_note(self, note):
        """生成单个音符的命令"""
        tick_x = self.base_x + note.tick * 2
        pan = _calculate_pan(note)
        z_pos = self.base_z + pan

        instrument = INSTRUMENT_MAPPING.get(note.instrument, "harp")
        base_block = INSTRUMENT_BLOCK_MAPPING.get(note.instrument, "minecraft:stone")
        note_pitch = NOTEPITCH_MAPPING.get(note.key, "0")

        commands = [
            f"setblock {tick_x} {self.base_y} {z_pos} note_block[note={note_pitch},instrument={instrument}]",
            f"setblock {tick_x} {self.base_y - 1} {z_pos} {base_block}"
        ]

        # 沙子特殊处理
        if base_block == "sand":
            commands.append(f"setblock {tick_x} {self.base_y - 2} {z_pos} barrier")

        self._write(commands)

    def _write(self, commands):
        """将命令写入文件"""
        with open(GENERATE_CONFIG['output_file'] + ".mcfunction", 'a', encoding='utf-8') as f:
            f.write("\n".join(commands) + "\n\n")


class SchematicProcessor(GroupProcessor):
    def __init__(self, all_notes, global_max_tick):
        super().__init__(all_notes, global_max_tick)
        self.schem: MCSchematic = MCSchematic()
        self.regions = {}
        self.region_index = 0
        self.current_region = None

    def process(self):
        self.schem = MCSchematic()
        super().process()
        path = GENERATE_CONFIG['output_file']
        self.schem.save(".", path.rsplit('/', 1)[-1], GENERATE_CONFIG['data_version'])

    def process_group(self):
        super().process_group()
        self._write(None)

    def _generate_base_structures(self, tick):
        """生成每个tick的基础结构"""
        x = self.base_x + tick * 2
        self.schem.setBlock((x, self.base_y, self.base_z), self.cover_block)
        self.schem.setBlock((x, self.base_y - 1, self.base_z), self.base_block)
        self.schem.setBlock((x - 1, self.base_y, self.base_z), "minecraft:repeater[delay=1,facing=west]")
        self.schem.setBlock((x - 1, self.base_y - 1, self.base_z), self.base_block)

    def _generate_pan_platform(self, tick, direction):
        """生成声像偏移平台"""
        if self.tick_status[tick]['right' if direction == 1 else 'left']:
            return

        max_pan = _get_max_pan(self.notes, tick, direction)
        if max_pan == 0:
            return

        x = self.base_x + tick * 2
        z_start = self.base_z
        z_end = self.base_z + max_pan - (1 if direction == 1 else -1)

        for z in range(z_start, z_end, 1):
            self.schem.setBlock((x, self.base_y - 1, z), self.base_block)

        self.schem.setBlock((x, self.base_y, z_start), self.cover_block)

        # 生成红石线路
        if abs(max_pan) > 1:
            wire_start = z_start + direction
            wire_end = z_end
            for z in range(wire_start, wire_end, 1):
                self.schem.setBlock((x, self.base_y, z), "minecraft:redstone_wire[east=side,west=side]")

        self.tick_status[tick]['right' if direction == 1 else 'left'] = True

    def _generate_note(self, note):
        """生成单个音符"""
        tick_x = self.base_x + note.tick * 2
        pan = _calculate_pan(note)
        z_pos = self.base_z + pan

        instrument = INSTRUMENT_MAPPING.get(note.instrument, "harp")
        base_block = INSTRUMENT_BLOCK_MAPPING.get(note.instrument, "minecraft:stone")
        note_pitch = NOTEPITCH_MAPPING.get(note.key, "0")

        self.schem.setBlock((tick_x, self.base_y, z_pos),f"minecraft:note_block[note={note_pitch},instrument={instrument}]")
        self.schem.setBlock((tick_x, self.base_y - 1, z_pos), self.base_block)

        # 沙子特殊处理
        if base_block == "minecraft:sand":
            self.schem.setBlock((tick_x, self.base_y - 2, z_pos), "minecraft:barrier")

    def _write(self, _):
        self.regions[str(self.region_index)] = self.current_region
        self.region_index += 1


# --------------------------
# 主程序
# --------------------------

def main():
    # 初始化
    print(">>> 开始处理NBS文件...")
    try:
        song = pynbs.read(GENERATE_CONFIG['input_file'])
        all_notes = song.notes
        global_max_tick = song.header.song_length

        # 清空输出文件
        with open(GENERATE_CONFIG['output_file'], 'w') as f:
            f.write("\n")

        if GENERATE_CONFIG['type'] == 'schematic':
            processor = SchematicProcessor(all_notes, global_max_tick)
        elif GENERATE_CONFIG['type'] == 'mcfunction':
            processor = McFunctionProcessor(all_notes, global_max_tick)
        else:
            print(f"配置文件错误, 未找到可用的 \"{GENERATE_CONFIG['type']}\" 实现")
            return

        processor.process()

        print(f"\n>>> 处理完成！总音乐长度: {global_max_tick} ticks")
        print(f"输出文件: {GENERATE_CONFIG['output_file']}")

    except Exception as e:
        print(f"\n>>> 处理过程中发生错误:")
        print(f"错误信息: {str(e)}")
        print("程序已终止")


if __name__ == "__main__":
    main()
