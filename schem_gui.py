import sys
import os
import json
import pynbs
import traceback
from mcschematic import Version, MCSchematic
from collections import defaultdict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QFileDialog,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QProgressBar, QFrame, QSizePolicy, QStyle
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QLinearGradient, QBrush

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

# Minecraft版本列表
MINECRAFT_VERSIONS = [
    Version.JE_1_21_5,
    Version.JE_1_21_4,
    Version.JE_1_21_3,
    Version.JE_1_21_2,
    Version.JE_1_21_1,
    Version.JE_1_21,
    Version.JE_1_20_6,
    Version.JE_1_20_5,
    Version.JE_1_20_4,
    Version.JE_1_20_3,
    Version.JE_1_20_2,
    Version.JE_1_20_1,
    Version.JE_1_20,
    Version.JE_1_19_4,
    Version.JE_1_19_3,
    Version.JE_1_19_2,
    Version.JE_1_19_1,
    Version.JE_1_19,
    Version.JE_1_18_2,
    Version.JE_1_18_1,
    Version.JE_1_18,
    Version.JE_1_17_1,
    Version.JE_1_17,
    Version.JE_1_16_5,
    Version.JE_1_16_4,
    Version.JE_1_16_3,
    Version.JE_1_16_2,
    Version.JE_1_16_1,
    Version.JE_1_16,
    Version.JE_1_15_2,
    Version.JE_1_15_1,
    Version.JE_1_15,
    Version.JE_1_14_4,
    Version.JE_1_14_3,
    Version.JE_1_14_2,
    Version.JE_1_14_1,
    Version.JE_1_14,
    Version.JE_1_13_2
]


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

    def __init__(self, all_notes, global_max_tick, config, group_config):
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
            # 更新进度
            progress = int((current_tick / self.global_max_tick) * 100) if self.global_max_tick > 0 else 0
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
        self.schem = MCSchematic()
        super().process()
        path = self.config['output_file']
        self.schem.save(".", path.rsplit('/', 1)[-1], self.config['data_version'])

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

        self.schem.setBlock((tick_x, self.base_y, z_pos),
                            f"minecraft:note_block[note={note_pitch},instrument={instrument}]")
        self.schem.setBlock((tick_x, self.base_y - 1, z_pos), self.base_block)

        # 沙子特殊处理
        if base_block == "minecraft:sand":
            self.schem.setBlock((tick_x, self.base_y - 2, z_pos), "minecraft:barrier")

    def _write(self, _):
        self.regions[str(self.region_index)] = self.current_region
        self.region_index += 1


# --------------------------
# 美化样式
# --------------------------

def create_fluent_style():
    """创建Fluent Design样式表"""
    return """
    /* 全局样式 */
    QWidget {
        font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
        font-size: 11pt;
        background-color: #f6f6f6;
    }

    /* 主窗口 */
    QMainWindow {
        background-color: #f6f6f6;
    }

    /* 标题栏 */
    QMainWindow::title {
        color: #333333;
        font-weight: 600;
        padding: 100px;
    }

    /* 分组框 */
    QGroupBox {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-top: 13px;
        padding-top: 20px;
        font-weight: 600;
        color: #333333;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        top: 30px;
        padding: 0 8px;
        background-color: transparent;
    }

    /* 标签 */
    QLabel {
        color: #333333;
        font-weight: 500;
        background-color: #ffffff;
    }

    /* 按钮 */
    QPushButton {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        color: #333333;
        padding: 8px 16px;
        min-height: 32px;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #f0f0f0;
        border-color: #d0d0d0;
    }

    QPushButton:pressed {
        background-color: #e0e0e0;
    }

    QPushButton:checked {
        background-color: #e0e0e0;
    }

    /* 特殊按钮 */
    QPushButton#runButton {
        background-color: #0078d7;
        color: #ffffff;
        border: 1px solid #0066b4;
        font-weight: 600;
    }

    QPushButton#runButton:hover {
        background-color: #0066b4;
    }

    QPushButton#runButton:pressed {
        background-color: #005a9e;
    }

    /* 输入框 */
    QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 8px;
        color: #333333;
    }

    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
        border: 1px solid #0078d7;
    }

    /* 表格 */
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        gridline-color: #e0e0e0;
        alternate-background-color: #f9f9f9;
    }

    QHeaderView::section {
        background-color: #f0f0f0;
        color: #333333;
        font-weight: 600;
        padding: 0px;
        border: none;
    }

    QTableWidget::item {
        padding: -1px;
    }

    /* 标签页 */
    QTabWidget::pane {
        border: none;
        margin-top: -1px;
    }

    QTabBar::tab {
        background-color: #f0f0f0;
        border: 1px solid #e0e0e0;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 16px;
        margin-right: 2px;
    }

    QTabBar::tab:selected {
        background-color: #ffffff;
        border-color: #e0e0e0;
        border-bottom: 2px solid #0078d7;
        font-weight: 600;
    }

    QTabBar::tab:hover {
        background-color: #e0e0e0;
    }

    /* 进度条 */
    QProgressBar {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        text-align: center;
        background-color: #ffffff;
    }

    QProgressBar::chunk {
        background-color: #0078d7;
        border-radius: 4px;
    }

    /* 状态栏 */
    QStatusBar {
        background-color: #f0f0f0;
        border-top: 1px solid #e0e0e0;
        padding: 4px;
    }

    /* 分隔线 */
    QFrame[frameShape="4"] { /* HLine */
        border: none;
        border-top: 1px solid #e0e0e0;
    }
    """


# --------------------------
# 美化控件类
# --------------------------

class FluentButton(QPushButton):
    """Fluent风格的按钮"""

    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon:
            self.setIcon(icon)

        # 设置固定高度
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


class FluentLineEdit(QLineEdit):
    """Fluent风格的输入框"""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class FluentComboBox(QComboBox):
    """Fluent风格的下拉框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


# 修改 FluentGroupBox 类
class FluentGroupBox(QGroupBox):
    """Fluent风格的分组框"""

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # 创建内部布局
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(12)
        inner_layout.setContentsMargins(16, 24, 16, 16)
        self.setLayout(inner_layout)


class FluentTabWidget(QTabWidget):
    """Fluent风格的标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


# --------------------------
# GUI 主窗口
# --------------------------




class NBSConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NBS-to-Minecraft")
        self.setGeometry(100, 100, 1000, 750)

        # 初始化配置
        self.config = {
            'data_version': MINECRAFT_VERSIONS[0],
            'input_file': '',
            'type': 'schematic',
            'output_file': 'output'
        }

        self.group_config = {
            0: {
                'base_coords': ("0", "0", "0"),
                'layers': [0],
                'block': {
                    'base': 'minecraft:iron_block',
                    'cover': 'minecraft:iron_block'
                }
            }
        }

        # 应用样式
        self.setStyleSheet(create_fluent_style())

        self.init_ui()
        self.load_last_config()

    def init_ui(self):
        # 创建主布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 8)
        main_layout.setSpacing(16)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 创建标题栏
        title_layout = QHBoxLayout()
        #title_icon = QLabel()
        #try:
           # pixmap = QPixmap("note_block.png").scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                                                      #Qt.TransformationMode.SmoothTransformation)
            #title_icon.setPixmap(pixmap)
        #except:
            #pass
        #title_icon.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        title_label = QLabel("NBS-to-Minecraft")
        title_label.setStyleSheet("font-size: 20pt; font-weight: 600; color: #333333; background-color: #f6f6f6;")

        #title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        main_layout.addLayout(title_layout)

        # 创建分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(separator)

        # 创建标签页
        tabs = FluentTabWidget()
        main_layout.addWidget(tabs)

        # 基本设置标签页
        basic_tab = QWidget()
        basic_layout = QVBoxLayout()
        basic_layout.setContentsMargins(0, 8, 0, 0)
        basic_layout.setSpacing(16)
        basic_tab.setLayout(basic_layout)
        tabs.addTab(basic_tab, "基本设置")

        # 轨道组设置标签页
        groups_tab = QWidget()
        groups_layout = QVBoxLayout()
        groups_layout.setContentsMargins(0, 8, 0, 0)
        groups_layout.setSpacing(16)
        groups_tab.setLayout(groups_layout)
        tabs.addTab(groups_tab, "轨道组设置")

        # 日志标签页
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(0, 8, 0, 0)
        log_layout.setSpacing(8)
        log_tab.setLayout(log_layout)
        tabs.addTab(log_tab, "处理日志")

        # 基本设置标签页内容
        # 输入文件选择
        # 基本设置标签页内容
        # 输入文件选择
        file_group = FluentGroupBox("输入文件设置")
        file_layout = QVBoxLayout()
        file_layout.setSpacing(12)
        file_group.layout().addLayout(file_layout)
        basic_layout.addWidget(file_group)

        self.input_file_edit = FluentLineEdit("请选择NBS文件...")
        browse_btn = FluentButton("浏览...")
        browse_btn.clicked.connect(self.browse_input_file)

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("NBS文件:"))
        file_row.setObjectName("fileLabel")
        file_row.addWidget(self.input_file_edit, 1)
        file_row.addWidget(browse_btn)
        file_layout.addLayout(file_row)

        # 输出设置
        output_group = FluentGroupBox("输出设置")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(12)
        output_group.layout().addLayout(output_layout)
        basic_layout.addWidget(output_group)

        # Minecraft版本
        version_layout = QHBoxLayout()
        version_layout.setSpacing(12)
        version_layout.addWidget(QLabel("Minecraft版本:"))
        self.version_combo = FluentComboBox()
        for version in MINECRAFT_VERSIONS:
            self.version_combo.addItem(str(version), version)
        version_layout.addWidget(self.version_combo, 1)
        output_layout.addLayout(version_layout)

        # 输出类型
        type_layout = QHBoxLayout()
        type_layout.setSpacing(12)
        type_layout.addWidget(QLabel("输出类型:"))
        self.type_combo = FluentComboBox()
        self.type_combo.addItem("WorldEdit Schematic (.schem)", "schematic")
        self.type_combo.addItem("Minecraft函数 (.mcfunction)", "mcfunction")
        type_layout.addWidget(self.type_combo, 1)
        output_layout.addLayout(type_layout)

        # 输出文件
        output_file_layout = QHBoxLayout()
        output_file_layout.setSpacing(12)
        output_file_layout.addWidget(QLabel("输出文件名:"))
        self.output_file_edit = FluentLineEdit("输出文件名...")
        output_file_btn = FluentButton("浏览...")
        output_file_btn.clicked.connect(self.browse_output_file)
        output_file_layout.addWidget(self.output_file_edit, 1)
        output_file_layout.addWidget(output_file_btn)
        output_layout.addLayout(output_file_layout)

        # 轨道组设置标签页内容
        # 轨道组表格
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(7)
        self.groups_table.setHorizontalHeaderLabels(["ID", "基准X", "基准Y", "基准Z", "轨道ID", "基础方块", "覆盖方块"])
        self.groups_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.groups_table.verticalHeader().setDefaultSectionSize(36)
        groups_layout.addWidget(self.groups_table)

        # 按钮行
        group_btn_layout = QHBoxLayout()
        group_btn_layout.setSpacing(12)
        add_group_btn = FluentButton("添加轨道组")
        add_group_btn.clicked.connect(self.add_group)
        remove_group_btn = FluentButton("删除轨道组")
        remove_group_btn.clicked.connect(self.remove_group)
        group_btn_layout.addWidget(add_group_btn)
        group_btn_layout.addWidget(remove_group_btn)
        group_btn_layout.addStretch()
        groups_layout.addLayout(group_btn_layout)

        # 日志标签页内容
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 10pt;")
        log_layout.addWidget(self.log_text)

        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("color: #666666;")
        self.status_bar.showMessage("就绪")

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        run_btn = FluentButton("开始转换", self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        run_btn.setObjectName("runButton")
        run_btn.setMinimumWidth(120)
        run_btn.clicked.connect(self.start_conversion)

        save_btn = FluentButton("保存配置")
        save_btn.clicked.connect(self.save_config)

        load_btn = FluentButton("加载配置")
        load_btn.clicked.connect(self.load_config)

        exit_btn = FluentButton("退出", )
        exit_btn.clicked.connect(self.close)

        btn_layout.addStretch()
        btn_layout.addWidget(run_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(exit_btn)
        main_layout.addLayout(btn_layout)

        # 初始化轨道组表格
        self.update_groups_table()

    def browse_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择NBS文件", "", "Note Block Studio Files (*.nbs)"
        )
        if file_path:
            self.input_file_edit.setText(file_path)
            # 自动设置输出文件名
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.output_file_edit.setText(base_name)

    def browse_output_file(self):
        output_type = self.type_combo.currentData()
        ext = ".schem" if output_type == "schematic" else ".mcfunction"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存输出文件", "", f"{ext[1:].upper()} Files (*{ext})"
        )
        if file_path:
            # 确保文件扩展名正确
            if not file_path.endswith(ext):
                file_path += ext
            self.output_file_edit.setText(file_path)

    def add_group(self):
        # 先保存当前表格的所有修改
        self.save_table_to_config()

        # 添加新轨道组
        group_id = max(self.group_config.keys()) + 1 if self.group_config else 0
        self.group_config[group_id] = {
            'base_coords': ("0", "0", "0"),
            'layers': [0],
            'block': {
                'base': 'minecraft:iron_block',
                'cover': 'minecraft:iron_block'
            }
        }
        self.update_groups_table()

    def remove_group(self):
        if len(self.group_config) <= 1:
            QMessageBox.warning(self, "警告", "至少需要保留一个轨道组！")
            return

        # 先保存当前表格的所有修改
        self.save_table_to_config()

        selected = self.groups_table.currentRow()
        if selected >= 0:
            group_id = list(self.group_config.keys())[selected]
            del self.group_config[group_id]
            self.update_groups_table()

    def save_table_to_config(self):
        """从表格保存配置到内存"""
        # 清除当前配置，从表格重建
        new_group_config = {}

        for row in range(self.groups_table.rowCount()):
            try:
                group_id = int(self.groups_table.item(row, 0).text())
            except:
                # 如果ID列无效，使用行号作为ID
                group_id = row

            # 获取坐标值
            x = self.groups_table.item(row, 1).text().strip() or "0"
            y = self.groups_table.item(row, 2).text().strip() or "0"
            z = self.groups_table.item(row, 3).text().strip() or "0"

            # 获取轨道ID
            layers_str = self.groups_table.item(row, 4).text().strip()
            layers = []
            if layers_str:
                try:
                    layers = [int(l.strip()) for l in layers_str.split(",") if l.strip()]
                except:
                    layers = [0]  # 默认值
            else:
                layers = [0]  # 默认值

            # 获取方块配置
            base_block = self.groups_table.item(row, 5).text().strip() or "minecraft:iron_block"
            cover_block = self.groups_table.item(row, 6).text().strip() or "minecraft:iron_block"

            new_group_config[group_id] = {
                'base_coords': (x, y, z),
                'layers': layers,
                'block': {
                    'base': base_block,
                    'cover': cover_block
                }
            }

        # 更新内存中的配置
        self.group_config = new_group_config

    def update_groups_table(self):
        """从内存配置更新表格显示"""
        self.groups_table.setRowCount(len(self.group_config))

        for row, (group_id, config) in enumerate(self.group_config.items()):
            # ID列
            id_item = QTableWidgetItem(str(group_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.groups_table.setItem(row, 0, id_item)

            # 坐标列
            self.groups_table.setItem(row, 1, QTableWidgetItem(config['base_coords'][0]))
            self.groups_table.setItem(row, 2, QTableWidgetItem(config['base_coords'][1]))
            self.groups_table.setItem(row, 3, QTableWidgetItem(config['base_coords'][2]))

            # 轨道ID列
            layers_str = ",".join(map(str, config['layers']))
            self.groups_table.setItem(row, 4, QTableWidgetItem(layers_str))

            # 方块列
            self.groups_table.setItem(row, 5, QTableWidgetItem(config['block']['base']))
            self.groups_table.setItem(row, 6, QTableWidgetItem(config['block']['cover']))

    def log(self, message):
        """向日志窗口添加消息"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def start_conversion(self):
        """开始转换过程"""
        # 保存表格数据到配置
        self.save_table_to_config()

        # 从UI获取配置
        self.config['data_version'] = self.version_combo.currentData()
        self.config['input_file'] = self.input_file_edit.text()
        self.config['type'] = self.type_combo.currentData()
        self.config['output_file'] = self.output_file_edit.text()

        # 验证输入
        if not self.config['input_file']:
            QMessageBox.critical(self, "错误", "请选择输入NBS文件！")
            return

        if not os.path.exists(self.config['input_file']):
            QMessageBox.critical(self, "错误", "输入文件不存在！")
            return

        if not self.config['output_file']:
            QMessageBox.critical(self, "错误", "请设置输出文件名！")
            return

        # 清空日志
        self.log_text.clear()

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 在后台线程中运行转换
        self.log(">>> 开始处理NBS文件...")

        try:
            song = pynbs.read(self.config['input_file'])
            all_notes = song.notes
            global_max_tick = song.header.song_length

            # 清空输出文件（如果是mcfunction）
            if self.config['type'] == 'mcfunction':
                with open(self.config['output_file'] + ".mcfunction", 'w') as f:
                    f.write("\n")

            # 创建处理器
            if self.config['type'] == 'schematic':
                processor = SchematicProcessor(all_notes, global_max_tick, self.config, self.group_config)
            elif self.config['type'] == 'mcfunction':
                processor = McFunctionProcessor(all_notes, global_max_tick, self.config, self.group_config)
            else:
                raise ValueError(f"无效的输出类型: {self.config['type']}")

            # 设置回调
            processor.set_log_callback(self.log)
            processor.set_progress_callback(self.update_progress)

            # 执行处理
            processor.process()

            self.log(f"\n>>> 处理完成！总音乐长度: {global_max_tick} ticks")
            self.log(f"输出文件: {self.config['output_file']}")
            self.status_bar.showMessage("转换成功完成！")

            # 保存当前配置
            self.save_last_config()

        except Exception as e:
            self.log(f"\n>>> 处理过程中发生错误:")
            self.log(f"错误信息: {str(e)}")
            self.log(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"处理过程中发生错误:\n{str(e)}")
            self.status_bar.showMessage("转换失败！")
        finally:
            self.progress_bar.setValue(100)

    def save_config(self):
        """保存配置到文件"""
        self.save_table_to_config()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置", "", "JSON Files (*.json)"
        )

        if file_path:
            config = {
                'app_config': self.config,
                'group_config': self.group_config
            }

            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                self.log(f"配置已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存配置失败:\n{str(e)}")

    def load_config(self):
        """从文件加载配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载配置", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)

                # 更新配置
                self.config = config['app_config']
                self.group_config = config['group_config']

                # 更新UI
                self.update_ui_from_config()
                self.update_groups_table()

                self.log(f"配置已从 {file_path} 加载")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载配置失败:\n{str(e)}")

    def save_last_config(self):
        """保存最后一次成功的配置"""
        config = {
            'app_config': self.config,
            'group_config': self.group_config
        }

        try:
            with open('last_config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def load_last_config(self):
        """加载最后一次成功的配置"""
        try:
            if os.path.exists('last_config.json'):
                with open('last_config.json', 'r') as f:
                    config = json.load(f)

                self.config = config['app_config']
                self.group_config = config['group_config']
                self.update_ui_from_config()
        except Exception:
            pass

    def update_ui_from_config(self):
        """从配置更新UI元素"""
        # 输入文件
        self.input_file_edit.setText(self.config.get('input_file', ''))

        # 输出文件
        self.output_file_edit.setText(self.config.get('output_file', 'output'))

        # Minecraft版本
        version = self.config.get('data_version', MINECRAFT_VERSIONS[0])
        for i in range(self.version_combo.count()):
            if self.version_combo.itemData(i) == version:
                self.version_combo.setCurrentIndex(i)
                break

        # 输出类型
        output_type = self.config.get('type', 'schematic')
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == output_type:
                self.type_combo.setCurrentIndex(i)
                break


# --------------------------
# 主程序入口
# --------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle("Fusion")

    # 设置应用调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(246, 246, 246))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(249, 249, 249))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.Text, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)

    # 创建并显示主窗口
    window = NBSConverterGUI()
    window.show()

    sys.exit(app.exec())
