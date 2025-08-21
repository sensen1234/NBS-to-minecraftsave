# -*- coding: utf-8 -*-
"""
命令行入口
----------
通过命令行方式调用NBS转换工具，适用于自动化处理场景
"""

import pynbs

from nbs2save.core.config import GENERATE_CONFIG, GROUP_CONFIG
from nbs2save.core.core import GroupProcessor
from nbs2save.core.mcfunction import McFunctionOutputStrategy
from nbs2save.core.schematic import SchematicOutputStrategy
from nbs2save.core.staircase_schematic import StaircaseSchematicOutputStrategy  # 新增导入

# --------------------------
# 工具函数
# --------------------------
def log(message: str):
    """简单的日志输出函数"""
    print(message)

def progress(value: int):
    """进度显示函数"""
    print(f"进度: {value}%")

# --------------------------
# 主处理类
# --------------------------
class CLIProcessor(GroupProcessor):
    """CLI版本的轨道组处理器"""
    
    def __init__(self):
        # 读取NBS文件
        nbs = pynbs.read(GENERATE_CONFIG['input_file'])
        all_notes = nbs.notes
        global_max_tick = nbs.header.song_length
        
        # 调用父类初始化
        super().__init__(all_notes, global_max_tick, GENERATE_CONFIG, GROUP_CONFIG)
        
        # 注册回调
        self.set_log_callback(log)
        self.set_progress_callback(progress)

# --------------------------
# 程序入口
# --------------------------
if __name__ == "__main__":
    processor = CLIProcessor()
    
    # 根据配置选择输出策略
    output_type = GENERATE_CONFIG['type']
    if output_type == 'mcfunction':
        processor.set_output_strategy(McFunctionOutputStrategy())
    elif output_type == 'schematic':
        # 检查是否有轨道组使用阶梯模式
        use_staircase = any(config.get('generation_mode') == 'staircase' 
                           for config in GROUP_CONFIG.values())
        if use_staircase:
            processor.set_output_strategy(StaircaseSchematicOutputStrategy())
        else:
            processor.set_output_strategy(SchematicOutputStrategy())
    else:
        raise ValueError(f"不支持的输出类型: {output_type}")
    
    # 执行处理
    processor.process()
    print("处理完成!")