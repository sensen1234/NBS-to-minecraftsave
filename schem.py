

import pynbs
from collections import defaultdict

# --------------------------
# 用户配置区 (按需修改)
# --------------------------

# 文件路径配置
NBS_FILE_PATH = 'D:/Code/NBS-to-minecraftsave/test.nbs'               # 输入的.nbs文件路径
OUTPUT_FUNCTION = 'D:/Code/NBS-to-minecraftsave/test.mcfunction'    # 输出的mcfunction路径

# 轨道组配置 (字典格式)
GROUP_CONFIG = {
    # 格式：组ID: {配置字典}
    0: {
        'base_coords': ("0", "0", "0"),  # 基准坐标 (x,y,z)
        'layers': [0, 1, 2],             # 包含的轨道ID列表
        'block': {                       # 方块配置
            'base': 'iron_block',        # 基础平台方块
            'cover': 'iron_block'             # 顶部覆盖方块
        }
    },
    1: {
        'base_coords': ("0", "0", "20"),
        'layers': [3, 4, 5],
        'block': {
            'base': 'iron_block',
            'cover': 'iron_block'
        }
    }
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
    0: "dirt", 1: "oak_planks", 2: "stone", 3: "sand", 4: "glass",
    5: "white_wool", 6: "clay", 7: "gold_block", 8: "packed_ice",
    9: "bone_block", 10: "iron_block", 11: "soul_sand", 12: "pumpkin",
    13: "emerald_block", 14: "hay_block", 15: "glowstone"
}

# 音高映射表 (MIDI键到游戏音高)
NOTEPITCH_MAPPING = {k: str(v) for v, k in enumerate(range(33, 58))}

# --------------------------
# 轨道组处理器类
# --------------------------

class GroupProcessor:
    """轨道组处理核心类"""
    
    def __init__(self, config):
        """
        初始化轨道组处理器
        :param config: 组配置字典，包含：
            - base_coords: 基准坐标 (x,y,z)
            - layers: 轨道ID列表
            - block: 方块配置 {base: 基础方块, cover: 顶部方块}
        """
        self.base_x, self.base_y, self.base_z = map(int, config['base_coords'])
        self.layers = set(config['layers'])
        self.base_block = config['block']['base']
        self.cover_block = config['block']['cover']
        
        # 预处理数据
        self.notes = []          # 本组所有音符（按tick排序）
        self.max_tick = 0        # 本组最大tick值
        self.tick_status = defaultdict(lambda: {'left': False, 'right': False})  # 记录平台生成状态

    def load_notes(self, all_notes):
        """加载并预处理属于本组的音符"""
        self.notes = sorted(
            [n for n in all_notes if n.layer in self.layers],
            key=lambda x: x.tick
        )
        if self.notes:
            self.max_tick = max(n.tick for n in self.notes)

    def process_group(self):
        """处理整个轨道组的生成逻辑"""
        current_tick = 0
        note_ptr = 0  # 音符指针
        
        while current_tick <= self.max_tick:
            # 步骤1：生成基础结构
            self._generate_base_structures(current_tick)
            
            # 步骤2：处理当前tick的所有音符
            active_notes = []
            while note_ptr < len(self.notes) and self.notes[note_ptr].tick == current_tick:
                active_notes.append(self.notes[note_ptr])
                note_ptr += 1
            
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
                self._generate_note_commands(note)
            
            current_tick += 1

    def _calculate_pan(self, note):
        """计算声像偏移值"""
        return int(round(note.panning / 10))

    def _generate_base_structures(self, tick):
        """生成每个tick的基础结构"""
        x = self.base_x + tick * 2
        commands = [
            f"setblock {x} {self.base_y} {self.base_z} {self.cover_block}",
            f"setblock {x} {self.base_y-1} {self.base_z} {self.base_block}",
            f"setblock {x-1} {self.base_y} {self.base_z} repeater[delay=1,facing=west]",
            f"setblock {x-1} {self.base_y-1} {self.base_z} {self.base_block}"
        ]
        self._write_commands(commands)

    def _generate_pan_platform(self, tick, direction):
        """生成声像偏移平台 (direction: 1=右, -1=左)"""
        if self.tick_status[tick]['right' if direction == 1 else 'left']:
            return  # 已生成
        
        x = self.base_x + tick * 2
        pan = self._get_max_pan(tick, direction)
        if pan == 0:
            return
        
        # 计算平台参数
        z_start = self.base_z
        z_end = self.base_z + pan - (1 if direction == 1 else -1)
        platform_cmds = [
            f"fill {x} {self.base_y-1} {z_start} {x} {self.base_y-1} {z_end} {self.base_block}",
            f"setblock {x} {self.base_y} {z_start} {self.cover_block}"
        ]
        
        # 生成红石线路（长度大于1时）
        if abs(pan) > 1:
            wire_start = z_start + direction
            wire_end = z_end - direction
            platform_cmds.append(
                f"fill {x} {self.base_y} {wire_start} {x} {self.base_y} {wire_end} redstone_wire[east=side]"
            )
        
        self._write_commands(platform_cmds)
        self.tick_status[tick]['right' if direction ==1 else 'left'] = True

    def _get_max_pan(self, tick, direction):
        """获取当前tick指定方向的最大偏移值"""
        max_pan = 0
        for note in self.notes:
            if note.tick == tick:
                pan = self._calculate_pan(note)
                if pan * direction > 0:  # 同方向
                    max_pan = max(max_pan, abs(pan))
        return max_pan * direction

    def _generate_note_commands(self, note):
        """生成单个音符的命令"""
        # 计算坐标
        tick_x = self.base_x + note.tick * 2
        pan = self._calculate_pan(note)
        z_pos = self.base_z + pan
        
        # 获取音色配置
        instrument = INSTRUMENT_MAPPING.get(note.instrument, "harp")
        base_block = INSTRUMENT_BLOCK_MAPPING.get(note.instrument, "stone")
        note_pitch = NOTEPITCH_MAPPING.get(note.key, "0")
        
        # 构建命令
        commands = [
            f"setblock {tick_x} {self.base_y} {z_pos} note_block[note={note_pitch},instrument={instrument}]",
            f"setblock {tick_x} {self.base_y-1} {z_pos} {base_block}"
        ]
        
        # 沙子特殊处理
        if base_block == "sand":
            commands.append(f"setblock {tick_x} {self.base_y-2} {z_pos} barrier")
        
        self._write_commands(commands)

    def _write_commands(self, commands):
        """将命令写入文件"""
        with open(OUTPUT_FUNCTION, 'a', encoding='utf-8') as f:
            f.write("\n".join(commands) + "\n\n")

# --------------------------
# 主程序
# --------------------------

def main():
    # 初始化
    print(">>> 开始处理NBS文件...")
    song = pynbs.read(NBS_FILE_PATH)
    all_notes = song.notes
    
    # 清空输出文件
    with open(OUTPUT_FUNCTION, 'w') as f:
        f.write("\n")
    
    # 处理每个轨道组
    for group_id, config in GROUP_CONFIG.items():
        print(f"\n>> 正在处理轨道组 {group_id}：{config['layers']}")
        
        # 初始化处理器
        processor = GroupProcessor(config)
        processor.load_notes(all_notes)
        
        # 执行处理
        if processor.notes:
            print(f"├─ 发现 {len(processor.notes)} 个音符")
            print(f"└─ 最大tick值：{processor.max_tick}")
            processor.process_group()
        else:
            print("└─ 警告：未找到该组的音符")
    
    print("\n>>> 处理完成！输出文件：" + OUTPUT_FUNCTION)

if __name__ == "__main__":
    main()
