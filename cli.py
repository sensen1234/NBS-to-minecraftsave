#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================================================================
# NBS到Minecraft结构转换工具 命令行接口
# ==============================================================================
# 该文件提供了程序的命令行接口(CLI)
# 用户可以通过命令行运行该脚本，无需图形界面即可完成NBS文件转换
# 适用于服务器环境或自动化处理场景

# --------------------------
# 导入所需模块
# --------------------------
# pynbs: 第三方库，用于解析NBS文件格式
# config: 项目配置模块，包含GENERATE_CONFIG和GROUP_CONFIG配置
# McFunctionProcessor, McFunctionOutputStrategy: 生成mcfunction文件的处理器和策略
# SchematicProcessor, SchematicOutputStrategy: 生成schematic文件的处理器和策略
# GroupProcessor: 核心处理器抽象基类
import pynbs
from nbs2save.core.config import GENERATE_CONFIG, GROUP_CONFIG
from nbs2save.core.mcfunction import McFunctionProcessor, McFunctionOutputStrategy
from nbs2save.core.schematic import SchematicProcessor, SchematicOutputStrategy
from nbs2save.core.core import GroupProcessor

# --------------------------
# 命令行主函数
# --------------------------
# main函数是命令行接口的入口点
# 负责读取配置、解析NBS文件、执行转换过程并输出结果
def main():
    # 打印开始处理信息
    print(">>> 开始处理NBS文件...")
    
    # 使用try-except块捕获可能的异常
    # 确保程序在出现错误时能够给出友好的错误提示而不是直接崩溃
    try:
        # 使用pynbs库读取配置中指定的NBS文件
        # song对象包含了NBS文件的所有信息，包括音符、头部信息等
        song = pynbs.read(GENERATE_CONFIG['input_file'])
        
        # 从song对象中提取所有音符信息
        # all_notes是一个包含所有音符对象的列表
        all_notes = song.notes
        
        # 从song头部信息中获取音乐的总长度(以tick为单位)
        # global_max_tick用于进度计算和循环控制
        global_max_tick = song.header.song_length

        # 根据配置中的输出类型选择相应的处理器
        # 如果配置为'schematic'，则使用SchematicProcessor处理
        if GENERATE_CONFIG['type'] == 'schematic':
            # 创建SchematicProcessor实例
            # 传入音符列表、最大tick数、全局配置和轨道组配置
            processor = SchematicProcessor(all_notes, global_max_tick,
                                           GENERATE_CONFIG, GROUP_CONFIG)
                                           
        # 如果配置为'mcfunction'，则使用McFunctionProcessor处理
        elif GENERATE_CONFIG['type'] == 'mcfunction':
            # 创建McFunctionProcessor实例
            # 传入音符列表、最大tick数、全局配置和轨道组配置
            processor = McFunctionProcessor(
                all_notes, global_max_tick, GENERATE_CONFIG, GROUP_CONFIG)
                
        # 如果配置的类型既不是'schematic'也不是'mcfunction'
        else:
            # 打印错误信息并返回
            print(f"配置文件错误, 未找到可用的 \"{GENERATE_CONFIG['type']}\" 实现")
            return

        # 调用处理器的process方法开始执行转换过程
        # 这是整个转换流程的核心步骤
        processor.process()

        # 打印处理完成信息和统计信息
        print(f"\n>>> 处理完成！总音乐长度: {global_max_tick} ticks")
        # 打印输出文件名
        print(f"输出文件: {GENERATE_CONFIG['output_file']}")

    # 捕获处理过程中可能出现的任何异常
    except Exception as e:
        # 打印错误信息
        print(f"\n>>> 处理过程中发生错误:")
        # 打印具体的异常信息
        print(f"错误信息: {str(e)}")
        # 打印程序终止信息
        print("程序已终止")


# --------------------------
# 程序入口点
# --------------------------
# 当直接运行该脚本时执行main函数
# 这种写法确保了模块既可以被直接运行也可以被其他模块导入
if __name__ == "__main__":
    main()