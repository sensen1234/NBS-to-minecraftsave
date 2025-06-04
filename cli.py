import pynbs
from nbs2save.core.config import GENERATE_CONFIG, GROUP_CONFIG
from nbs2save.core.schem import SchematicProcessor, McFunctionProcessor

# --------------------------
# 命令行测试
# --------------------------


def main():
    print(">>> 开始处理NBS文件...")
    try:
        song = pynbs.read(GENERATE_CONFIG['input_file'])
        all_notes = song.notes
        global_max_tick = song.header.song_length

        # 清空输出文件
        with open(GENERATE_CONFIG['output_file'], 'w') as f:
            f.write("\n")

        if GENERATE_CONFIG['type'] == 'schematic':
            processor = SchematicProcessor(all_notes, global_max_tick,
                                           GENERATE_CONFIG, GROUP_CONFIG)
        elif GENERATE_CONFIG['type'] == 'mcfunction':
            processor = McFunctionProcessor(
                all_notes, global_max_tick, GENERATE_CONFIG, GROUP_CONFIG)
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
