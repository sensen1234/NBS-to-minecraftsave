import os
import json
import traceback

import pynbs
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QTextEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QProgressBar, QFrame, QSizePolicy, QStyle
)
from PyQt6.QtCore import Qt

from ..core.constants import MINECRAFT_VERSIONS
from ..core.core import GroupProcessor
from ..core.schematic import SchematicOutputStrategy
from ..core.mcfunction import McFunctionOutputStrategy
from ..core.staircase_schematic import StaircaseSchematicOutputStrategy  # 新增导入
from .widgets import FluentButton, FluentLineEdit, FluentComboBox, FluentGroupBox, FluentTabWidget


def create_fluent_style():
    """创建Win11风格的Fluent Design样式表 - 兼容PyQt6版本"""
    return """
    /* 全局样式 - Win11设计语言 */
    QWidget {
        font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
        font-size: 10pt;
        color: #323130;
        background-color: #fafafa;
    }

    /* 主窗口 - Win11背景 */
    QMainWindow {
        background-color: #fafafa;
        border: 1px solid #e1dfdd;
    }

    /* 标题区域 */
    #titleLabel {
        font-size: 24px;
        font-weight: 600;
        color: #323130;
        background-color: transparent;
        padding: 8px 16px;
        border-radius: 6px;
    }

    /* 分组框 - Win11圆角卡片设计 */
    QGroupBox {
        background-color: #ffffff;
        border: 1px solid #e1dfdd;
        border-radius: 12px;
        margin-top: 16px;
        padding-top: 20px;
        font-weight: 600;
        color: #323130;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        top: 12px;
        padding: 0 12px 0 8px;
        background-color: #fafafa;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        color: #323130;
    }

    /* 标签 - 清晰层次 */
    QLabel {
        color: #323130;
        font-weight: 500;
        background-color: transparent;
        font-size: 10pt;
    }

    /* 按钮 - Win11 Fluent按钮样式 */
    QPushButton {
        background-color: #ffffff;
        border: 1px solid #e1dfdd;
        border-radius: 8px;
        color: #323130;
        padding: 10px 16px;
        min-height: 20px;
        font-weight: 500;
        font-size: 10pt;
    }

    QPushButton:hover {
        background-color: #f3f2f1;
        border-color: #d0d0d0;
    }

    QPushButton:pressed {
        background-color: #edebe9;
        border-color: #c8c6c4;
    }

    QPushButton:focus {
        outline: none;
        border-color: #0078d4;
    }

    /* 主要按钮 - 强调色 */
    QPushButton#runButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 #0078d4, stop:1 #106ebe);
        color: #ffffff;
        border: 1px solid #005a9e;
        font-weight: 600;
        border-radius: 8px;
    }

    QPushButton#runButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 #1084d0, stop:1 #0078d4);
        border-color: #004578;
    }

    QPushButton#runButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 #106ebe, stop:1 #005a9e);
    }

    /* 输入框 - Win11 Fluent输入框 */
    QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        border: 1px solid #e1dfdd;
        border-radius: 8px;
        padding: 12px 12px;
        color: #323130;
        font-size: 10pt;
    }

    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
        border-color: #0078d4;
        background-color: #ffffff;
        outline: none;
    }

    QLineEdit:hover, QComboBox:hover, QTextEdit:hover {
        border-color: #c8c6c4;
    }

    /* 下拉框特殊样式 */
    QComboBox::drop-down {
        border: none;
        border-radius: 0 8px 8px 0;
        width: 32px;
        background-color: #f3f2f1;
    }

    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid #323130;
        margin-right: 8px;
    }

    /* 表格 - Win11样式 */
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #e1dfdd;
        border-radius: 8px;
        gridline-color: #edebe9;
        alternate-background-color: #faf9f8;
        selection-background-color: #0078d4;
        selection-color: #ffffff;
        padding: 4px;
    }

    QHeaderView::section {
        background-color: #f3f2f1;
        color: #323130;
        font-weight: 600;
        padding: 8px 12px;
        border: none;
        border-right: 1px solid #edebe9;
        border-radius: 4px;
        font-size: 9pt;
    }

    QTableWidget::item {
        padding: 8px 4px;
        border-radius: 4px;
    }

    QTableWidget::item:selected {
        background-color: #0078d4;
        color: #ffffff;
    }

    /* 标签页 - Win11 Fluent标签页 */
    QTabWidget::pane {
        border: 1px solid #e1dfdd;
        border-radius: 12px;
        background-color: #ffffff;
        margin-top: 8px;
    }

    QTabBar::tab {
        background-color: #f3f2f1;
        border: 1px solid #e1dfdd;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 12px 20px;
        margin-right: 2px;
        font-weight: 500;
        font-size: 10pt;
        color: #605e5c;
    }

    QTabBar::tab:selected {
        background-color: #ffffff;
        border-color: #e1dfdd;
        color: #323130;
        font-weight: 600;
        border-bottom: 2px solid #0078d4;
    }

    QTabBar::tab:hover:!selected {
        background-color: #edebe9;
        color: #323130;
    }

    /* 进度条 - Win11样式 */
    QProgressBar {
        border: 1px solid #e1dfdd;
        border-radius: 8px;
        text-align: center;
        background-color: #f3f2f1;
        color: #323130;
        font-weight: 500;
        height: 24px;
    }

    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                   stop:0 #0078d4, stop:1 #106ebe);
        border-radius: 6px;
        margin: 1px;
    }

    /* 状态栏 - Win11 Fluent */
    QStatusBar {
        background-color: #f3f2f1;
        border-top: 1px solid #e1dfdd;
        padding: 8px;
        font-size: 9pt;
        color: #605e5c;
    }

    /* 分隔线 - 柔和设计 */
    QFrame[frameShape="4"] { /* HLine */
        border: none;
        border-top: 1px solid #edebe9;
        margin: 8px 0;
    }

    /* 滚动条 - Win11样式 */
    QScrollBar:vertical {
        background-color: #f3f2f1;
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }

    QScrollBar::handle:vertical {
        background-color: #c8c6c4;
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #a19f9d;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }

    /* 消息框样式 */
    QMessageBox {
        background-color: #ffffff;
    }

    QMessageBox QLabel {
        color: #323130;
        font-size: 10pt;
    }

    QMessageBox QPushButton {
        min-width: 80px;
        padding: 6px 12px;
        border-radius: 6px;
    }
    """


class MainWindow(QMainWindow):
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
        # title_icon = QLabel()
        # try:
        # pixmap = QPixmap("note_block.png").scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
        # Qt.TransformationMode.SmoothTransformation)
        # title_icon.setPixmap(pixmap)
        # except:
        # pass
        # title_icon.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        title_label = QLabel("NBS-to-Minecraft")
        title_label.setObjectName("titleLabel")
        title_label.setStyleSheet(
            "font-size: 24px; font-weight: 600; color: #323130; background-color: transparent; padding: 4px 8px; border-radius: 4px;")

        # title_layout.addWidget(title_icon)
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

        # 基本设置
        basic_group = FluentGroupBox("基本设置")
        settings_layout = QFormLayout()
        settings_layout.setSpacing(12)

        # 基础方块
        self.base_block_input = FluentLineEdit("minecraft:iron_block")
        settings_layout.addRow("基础方块:", self.base_block_input)

        # 覆盖方块
        self.cover_block_input = FluentLineEdit("minecraft:iron_block")
        settings_layout.addRow("覆盖方块:", self.cover_block_input)

        # 生成模式
        self.generation_mode_combo = FluentComboBox()
        self.generation_mode_combo.addItems(["default", "staircase"])
        self.generation_mode_combo.setCurrentText("default")
        settings_layout.addRow("生成模式:", self.generation_mode_combo)

        # 添加到分组框
        basic_group.layout().addLayout(settings_layout)
        basic_layout.addWidget(basic_group)

        # 轨道组设置标签页内容
        # 轨道组表格
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(7)
        self.groups_table.setHorizontalHeaderLabels(
            ["ID", "基准X", "基准Y", "基准Z", "轨道ID", "基础方块", "覆盖方块"])
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
        self.log_text.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 10pt;")
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

        run_btn = FluentButton("开始转换", self.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaPlay))
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
            processor = GroupProcessor(all_notes, global_max_tick, self.config, self.group_config)
            processor.set_log_callback(self.log)
            processor.set_progress_callback(self.update_progress)

            # 根据输出类型设置处理器
            output_type = self.config["type"]
            if output_type == "schematic":
                # 检查是否有轨道组使用阶梯模式
                use_staircase = any(
                    config.get("generation_mode") == "staircase" 
                    for config in self.group_config.values()
                )
                if use_staircase:
                    processor.set_output_strategy(StaircaseSchematicOutputStrategy())
                else:
                    processor.set_output_strategy(SchematicOutputStrategy())
            elif output_type == "mcfunction":
                processor.set_output_strategy(McFunctionOutputStrategy())
            else:
                raise ValueError(f"不支持的输出类型: {output_type}")

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
        except Exception as e:
            print("error when saving last config:", e)

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

    def parse_layers(self, layers_text):
        """解析轨道层配置文本"""
        layers = []
        if layers_text:
            try:
                layers = [int(l.strip()) for l in layers_text.split(",") if l.strip()]
            except ValueError:
                layers = [0]  # 默认值
        return layers if layers else [0]
