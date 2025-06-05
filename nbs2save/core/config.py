from mcschematic import Version

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
