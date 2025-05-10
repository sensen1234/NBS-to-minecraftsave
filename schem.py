
import pynbs
from collections import defaultdict

# --------------------------
# 用户配置区 (按需修改)
# --------------------------

NBS_FILE_PATH = 'main.nbs'                # 输入的.nbs文件路径
OUTPUT_FUNCTION = 'main.mcfunction'     # 输出的mcfunction路径

# 轨道组配置 (字典格式)
GROUP_CONFIG = {
    0: {
        'base_coords': ("0", "10", "2"),   # 基准坐标 (x,y,z)
        'layers': [0, 1, 2],              # 包含的轨道ID列表
        'block': {                        # 方块配置
            'base': 'iron_block',         # 基础平台方块
            'cover': 'iron_block'              # 顶部覆盖方块
        }
    },
    1: {
        'base_coords': ("0", "10", "6"),   # 基准坐标 (x,y,z)
        'layers': [4, 5, 7],              # 包含的轨道ID列表
        'block': {                        # 方块配置
            'base': 'iron_block',         # 基础平台方块
            'cover': 'iron_block'              # 顶部覆盖方块
        }
    },
    2: {
        'base_coords': ("0", "10", "10"),   # 基准坐标 (x,y,z)
        'layers': [8, 9, 10],              # 包含的轨道ID列表
        'block': {                        # 方块配置
            'base': 'iron_block',         # 基础平台方块
            'cover': 'iron_block'              # 顶部覆盖方块
        }
    },
    3: {
        'base_coords': ("0", "10", "14"),   # 基准坐标 (x,y,z)
        'layers': [12, 14, 15],              # 包含的轨道ID列表
        'block': {                        # 方块配置
            'base': 'iron_block',         # 基础平台方块
            'cover': 'iron_block'              # 顶部覆盖方块
        }
    },
    4: {
        'base_coords': ("0", "10", "18"),   # 基准坐标 (x,y,z)
        'layers': [16, 17, 18],              # 包含的轨道ID列表
        'block': {                        # 方块配置
            'base': 'iron_block',         # 基础平台方块
            'cover': 'iron_block'              # 顶部覆盖方块
        }
    },
    5: {
        'base_coords': ("0", "10", "22"),   # 基准坐标 (x,y,z)
        'layers': [20, 21, 22],              # 包含的轨道ID列表
        'block': {                        # 方块配置
            'base': 'iron_block',         # 基础平台方块
            'cover': 'iron_block'              # 顶部覆盖方块
        }
    },
    6: {
        'base_coords': ("0", "10", "26"),   # 基准坐标 (x,y,z)
        'layers': [24, 25, 26],              # 包含的轨道ID列表
        'block': {                        # 方块配置
            'base': 'iron_block',         # 基础平台方块
            'cover': 'iron_block'              # 顶部覆盖方块
        }
    },
    7: {
        'base_coords': ("0", "10", "30"),   # 基准坐标 (x,y,z)
        'layers': [27, 28, 29],              # 包含的轨道ID列表
        'block': {                        # 方块配置
            'base': 'iron_block',         # 基础平台方块
            'cover': 'iron_block'              # 顶部覆盖方块
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
    
    def __init__(self, config, global_max_tick, output_path):
        self.base_x, self.base_y, self.base_z = map(int, config['base_coords'])
        self.base_block = config['block']['base']
        self.cover_block = config['block']['cover']
        
        self.layers = set(config['layers'])
        self.global_max_tick = global_max_tick
        self.tick_status = defaultdict(lambda: {'left': False, 'right': False})
        
        self.notes = []
        self.group_max_tick = 0
        
        self.output_path = output_path  # <- 추가된 부분
        self.layer_z_offsets = {
            layer: i - len(config['layers']) // 2
            for i, layer in enumerate(sorted(config['layers']))
}



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
        """生成声像偏移平台"""
        if self.tick_status[tick]['right' if direction == 1 else 'left']:
            return
        
        max_pan = self._get_max_pan(tick, direction)
        if max_pan == 0:
            return
        
        x = self.base_x + tick * 2
        z_start = self.base_z
        z_end = self.base_z + max_pan - (1 if direction == 1 else -1)
        
        platform_cmds = [
            f"fill {x} {self.base_y-1} {z_start} {x} {self.base_y-1} {z_end} {self.base_block}",
            f"setblock {x} {self.base_y} {z_start} {self.cover_block}"
        ]
        
        # 生成红石线路
        if abs(max_pan) > 1:
            wire_start = z_start + direction
            wire_end = z_end 
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
                if pan * direction > 0:
                    max_pan = max(max_pan, abs(pan))
        return max_pan * direction

    def _generate_note_commands(self, note):
        tick_x = self.base_x + note.tick * 2
        pan = self._calculate_pan(note)
        
        # ✅ layer 기반 z-offset 적용
        z_layer_offset = self.layer_z_offsets.get(note.layer, 0)
        z_pos = self.base_z + pan + z_layer_offset
        
        instrument = INSTRUMENT_MAPPING.get(note.instrument, "harp")
        base_block = INSTRUMENT_BLOCK_MAPPING.get(note.instrument, "stone")
        note_pitch = NOTEPITCH_MAPPING.get(note.key, "0")
        
        commands = [
            f"setblock {tick_x} {self.base_y} {z_pos} note_block[note={note_pitch},instrument={instrument}]",
            f"setblock {tick_x} {self.base_y-1} {z_pos} {base_block}"
        ]
        
        if base_block == "sand":
            commands.append(f"setblock {tick_x} {self.base_y-2} {z_pos} barrier")
        
        self._write_commands(commands)
        

    def _write_commands(self, commands):
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write("\n".join(commands) + "\n\n")


# --------------------------
# 主程序
# --------------------------

def main():
    # 初始化
    print(">>> 开始处理NBS文件...")
    song = pynbs.read(NBS_FILE_PATH)
    all_notes = song.notes
    global_max_tick = song.header.song_length
    
    # 清空输出文件
    with open(OUTPUT_FUNCTION, 'w') as f:
        f.write("\n")
    
    # 处理每个轨道组
    for group_id, config in GROUP_CONFIG.items():
        output_path = f"group_{group_id}.mcfunction"
    
    # 출력 파일 초기화
        with open(output_path, 'w') as f:
            f.write("\n")
        print(f"\n>> 处理轨道组 {group_id}:")
        print(f"├─ 包含轨道: {config['layers']}")
        print(f"├─ 基准坐标: {config['base_coords']}")
        print(f"└─ 方块配置: {config['block']}")
        
        processor = GroupProcessor(config, global_max_tick, output_path)
        processor.load_notes(all_notes)
        
        if processor.notes:
            print(f"   ├─ 发现音符数量: {len(processor.notes)}")
            print(f"   └─ 组内最大tick: {processor.group_max_tick}")
        else:
            print("   └─ 警告: 未找到该组的音符")
        
        processor.process_group()
    
    print(f"\n>>> 处理完成！总音乐长度: {global_max_tick} ticks")
    print(f"输出文件: {OUTPUT_FUNCTION}")

if __name__ == "__main__":
    main()
