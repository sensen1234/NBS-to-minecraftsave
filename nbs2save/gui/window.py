import os
import json
import traceback

import pynbs
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QProgressBar, QFrame, QSizePolicy, QStyle, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from ..core.constants import MINECRAFT_VERSIONS
from ..core.core import GroupProcessor
from ..core.schematic import SchematicOutputStrategy
from ..core.mcfunction import McFunctionOutputStrategy
from ..core.staircase_schematic import StaircaseSchematicOutputStrategy

from .widgets import (
    FluentButton, FluentLineEdit, FluentComboBox, FluentTabWidget, FluentCard
)
from .coordinate_picker import CoordinatePickerDialog
from .animations import AnimationUtils 

def create_fluent_style():
    """
    Revised Style: Warm Light Gray + Consistent Radius
    """
    return """
    /* 全局设置 */
    QWidget {
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        font-size: 10pt;
        color: #2a2a2a;
        background-color: transparent; 
    }
    
    QMainWindow {
        background-color: #f7f7f7; /* 浅灰偏暖 */
    }
    
    /* 标题 */
    #titleLabel {
        font-size: 28px;
        font-weight: 700;
        color: #111111;
        margin-left: 4px;
        font-family: 'Segoe UI Variable Display', 'Segoe UI';
    }
    
    QLabel#sectionTitle {
        font-size: 10pt;
        font-weight: 600;
        color: #605e5c;
        margin-bottom: 6px;
    }

    /* 输入框: 6px 圆角 */
    QLineEdit, QSpinBox {
        background-color: #ffffff;
        border: 1px solid #dcdcdc;
        border-bottom: 2px solid #c0c0c0;
        border-radius: 6px; 
        padding: 5px 10px;
        color: #333;
    }
    QLineEdit:hover, QSpinBox:hover {
        background-color: #fcfcfc;
        border-color: #b0b0b0;
    }
    QLineEdit:focus, QSpinBox:focus {
        border-color: #0078d4;
        border-bottom: 2px solid #0078d4;
    }

    /* 下拉框 */
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #dcdcdc;
        border-bottom: 2px solid #c0c0c0;
        border-radius: 6px; 
        padding: 4px 10px;
    }
    QComboBox:hover {
        background-color: #fcfcfc;
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    
    /* 表格 */
    QTableWidget {
        border: 1px solid #e5e5e5;
        border-radius: 10px; 
        background-color: #ffffff;
        gridline-color: transparent; 
        selection-background-color: #e0effb; 
        selection-color: #000000;
    }
    QHeaderView::section {
        background-color: #ffffff;
        padding: 10px 8px;
        border: none;
        border-bottom: 2px solid #f0f0f0;
        font-weight: 600;
        color: #605e5c;
        text-align: left;
    }
    QTableWidget::item {
        border-bottom: 1px solid #fafafa;
        padding-left: 8px;
    }

    /* 进度条 */
    QProgressBar {
        border: none;
        background-color: #edebe9;
        border-radius: 3px;
        height: 6px;
        text-align: right;
    }
    QProgressBar::chunk {
        background-color: #0078d4;
        border-radius: 3px;
    }
    
    /* 滚动条 */
    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #d0d0d0;
        min-height: 20px;
        border-radius: 4px;
    }
    """

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NBS-to-Minecraft")
        self.setGeometry(100, 100, 1200, 850)

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
                'block': {'base': 'minecraft:iron_block', 'cover': 'minecraft:iron_block'}
            }
        }

        self.setStyleSheet(create_fluent_style())
        self.init_ui()
        self.load_last_config()
        
        AnimationUtils.fade_in_entry(self, duration=600)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 32, 40, 32)
        main_layout.setSpacing(24)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 1. 顶部栏
        header_layout = QHBoxLayout()
        title_label = QLabel("NBS-to-minecraftsave")
        title_label.setObjectName("titleLabel")
        

        header_layout.addWidget(title_label)
        header_layout.addSpacing(8)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)

        # 2. 导航 Tab
        tabs = FluentTabWidget()
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 8)) 
        shadow.setOffset(0, 6)
        tabs.setGraphicsEffect(shadow)
        
        main_layout.addWidget(tabs)

        # --- Tab 内容 ---
        basic_tab = QWidget()
        groups_tab = QWidget()
        log_tab = QWidget()

        for tab in [basic_tab, groups_tab, log_tab]:
            layout = QVBoxLayout()
            layout.setContentsMargins(4, 12, 4, 12)
            layout.setSpacing(24)
            tab.setLayout(layout)

        tabs.addTab(basic_tab, "基础设置", "⚙️")
        tabs.addTab(groups_tab, "轨道组", "🛤️")
        tabs.addTab(log_tab, "运行日志", "📝")

        # === A. 基础设置 ===
        file_card = FluentCard()
        card_layout1 = QVBoxLayout(file_card)
        card_layout1.setSpacing(16)
        card_layout1.setContentsMargins(28, 28, 28, 28)
        
        lbl_f1 = QLabel("文件输入")
        lbl_f1.setObjectName("sectionTitle")
        card_layout1.addWidget(lbl_f1)

        row1 = QHBoxLayout()
        self.input_file_edit = FluentLineEdit("选择 .nbs 文件...")
        # 浅灰按钮
        browse_in = FluentButton("浏览...", is_primary=False)
        browse_in.clicked.connect(self.browse_input_file)
        row1.addWidget(self.input_file_edit, 1)
        row1.addWidget(browse_in)
        card_layout1.addLayout(row1)
        
        card_layout1.addSpacing(12)
        
        lbl_f2 = QLabel("输出路径")
        lbl_f2.setObjectName("sectionTitle")
        card_layout1.addWidget(lbl_f2)
        
        row2 = QHBoxLayout()
        self.output_file_edit = FluentLineEdit("设置保存路径...")
        browse_out = FluentButton("浏览...", is_primary=False)
        browse_out.clicked.connect(self.browse_output_file)
        row2.addWidget(self.output_file_edit, 1)
        row2.addWidget(browse_out)
        card_layout1.addLayout(row2)
        
        basic_tab.layout().addWidget(file_card)

        # 参数配置
        param_card = FluentCard()
        card_layout2 = QVBoxLayout(param_card)
        card_layout2.setSpacing(16)
        card_layout2.setContentsMargins(28, 28, 28, 28)
        
        lbl_p = QLabel("转换参数")
        lbl_p.setObjectName("sectionTitle")
        card_layout2.addWidget(lbl_p)

        grid = QHBoxLayout()
        
        self.version_combo = FluentComboBox()
        for version in MINECRAFT_VERSIONS:
            self.version_combo.addItem(str(version), version)
            
        self.type_combo = FluentComboBox()
        self.type_combo.addItem("WorldEdit Schematic (.schem)", "schematic")
        self.type_combo.addItem("Minecraft Function (.mcfunction)", "mcfunction")
        
        v_layout = QVBoxLayout()
        v_layout.addWidget(QLabel("目标游戏版本", styleSheet="color:#666; font-size:9pt;"))
        v_layout.addWidget(self.version_combo)
        
        t_layout = QVBoxLayout()
        t_layout.addWidget(QLabel("输出格式", styleSheet="color:#666; font-size:9pt;"))
        t_layout.addWidget(self.type_combo)
        
        grid.addLayout(v_layout, 1)
        grid.addSpacing(40)
        grid.addLayout(t_layout, 1)
        
        card_layout2.addLayout(grid)
        basic_tab.layout().addWidget(param_card)
        basic_tab.layout().addStretch()

        # === B. 轨道组 ===
        toolbar = QHBoxLayout()
        lbl_g = QLabel("布局管理")
        lbl_g.setObjectName("sectionTitle")
        toolbar.addWidget(lbl_g)
        toolbar.addStretch()
        
        # 蓝色添加按钮
        add_btn = FluentButton("添加分组", is_primary=True)
        add_btn.setMinimumWidth(100)
        add_btn.clicked.connect(self.add_group)
        # 红色删除按钮 (is_danger=True)
        del_btn = FluentButton("删除选中", is_danger=True)
        del_btn.setMinimumWidth(100)
        del_btn.clicked.connect(self.remove_group)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(del_btn)
        groups_tab.layout().addLayout(toolbar)

        table_card = FluentCard()
        card_layout_t = QVBoxLayout(table_card)
        card_layout_t.setContentsMargins(0, 0, 0, 0)
        
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(9)
        self.groups_table.setHorizontalHeaderLabels(
            ["ID", "基准X", "基准Y", "基准Z", "坐标规划", "轨道ID", "基础方块", "覆盖方块", "生成模式"])
        
        header = self.groups_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.groups_table.verticalHeader().setDefaultSectionSize(54)
        self.groups_table.verticalHeader().setVisible(False)
        self.groups_table.setShowGrid(False)
        self.groups_table.setFrameShape(QFrame.Shape.NoFrame)
        
        card_layout_t.addWidget(self.groups_table)
        groups_tab.layout().addWidget(table_card)

        # === C. 日志 ===
        log_card = FluentCard()
        card_layout_l = QVBoxLayout(log_card)
        card_layout_l.setContentsMargins(0, 0, 0, 0)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit { 
                border: none; 
                font-family: 'Consolas', monospace; 
                color: #555; 
                padding: 16px; 
                background-color: transparent;
            }
        """)
        card_layout_l.addWidget(self.log_text)
        log_tab.layout().addWidget(log_card)

        # === 底部操作栏 ===
        action_bar = QWidget()
        action_bar.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-top: 1px solid #f0efed;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(28, 20, 28, 20)
        
        self.status_bar_label = QLabel("就绪")
        self.status_bar_label.setStyleSheet("border: none; color: #888; font-weight: 500;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(240)

        # ====== 按钮颜色调整区域 ======
        
        # 加载按钮 -> 浅灰色 (Standard, is_primary=False)
        load_btn = FluentButton("加载配置", is_primary=False)
        load_btn.setMinimumWidth(120)
        load_btn.clicked.connect(self.load_config)
        
        # 保存按钮 -> 浅灰色 (Standard, is_primary=False)
        save_btn = FluentButton("保存配置", is_primary=False)
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self.save_config)
        
        # 退出按钮 -> 红色 (Danger)
        exit_btn = FluentButton("退出", is_danger=True)
        exit_btn.setMinimumWidth(120)
        exit_btn.clicked.connect(self.close)

        # 开始转换 -> 蓝色 (Primary)
        run_btn = FluentButton("开始转换", is_primary=True)
        run_btn.setMinimumHeight(44)
        run_btn.setMinimumWidth(180)
        run_btn.clicked.connect(self.start_conversion)
        
        action_layout.addWidget(self.status_bar_label)
        action_layout.addWidget(self.progress_bar)
        action_layout.addStretch()
        
        action_layout.addWidget(load_btn)
        action_layout.addWidget(save_btn)
        action_layout.addWidget(exit_btn)
        action_layout.addSpacing(20)
        action_layout.addWidget(run_btn)

        main_layout.addWidget(action_bar)

        self.update_groups_table()

    # --- Logic (保持不变) ---

    def log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        if len(message) < 50 and ">>>" not in message:
             self.status_bar_label.setText(message)

    def update_progress(self, value):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        if value >= 100: self.status_bar_label.setText("任务完成")

    def browse_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择NBS文件", "", "Note Block Studio (*.nbs)")
        if file_path:
            self.input_file_edit.setText(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.output_file_edit.setText(base_name)

    def browse_output_file(self):
        output_type = self.type_combo.currentData()
        ext = ".schem" if output_type == "schematic" else ".mcfunction"
        file_path, _ = QFileDialog.getSaveFileName(self, "保存输出文件", "", f"Files (*{ext})")
        if file_path:
            if not file_path.endswith(ext): file_path += ext
            self.output_file_edit.setText(file_path)

    def add_group(self):
        self.save_table_to_config()
        gid = max(self.group_config.keys()) + 1 if self.group_config else 0
        self.group_config[gid] = {
            'base_coords': ("0", "0", "0"), 'layers': [0],
            'block': {'base': 'minecraft:iron_block', 'cover': 'minecraft:iron_block'},
            'generation_mode': 'default'
        }
        self.update_groups_table()

    def remove_group(self):
        if len(self.group_config) <= 1:
            QMessageBox.warning(self, "提示", "至少保留一个轨道组")
            return
        self.save_table_to_config()
        curr = self.groups_table.currentRow()
        if curr >= 0:
            gid = list(self.group_config.keys())[curr]
            del self.group_config[gid]
            self.update_groups_table()

    def save_table_to_config(self):
        new_config = {}
        for r in range(self.groups_table.rowCount()):
            try:
                gid = int(self.groups_table.item(r, 0).text())
            except:
                gid = r
            
            x = self.groups_table.item(r, 1).text().strip() or "0"
            y = self.groups_table.item(r, 2).text().strip() or "0"
            z = self.groups_table.item(r, 3).text().strip() or "0"
            layers_str = self.groups_table.item(r, 5).text().strip()
            layers = [int(x) for x in layers_str.split(',') if x.strip()] if layers_str else [0]
            b_base = self.groups_table.item(r, 6).text().strip() or "minecraft:iron_block"
            b_cover = self.groups_table.item(r, 7).text().strip() or "minecraft:iron_block"
            mode = "default"
            if self.groups_table.columnCount() >= 9:
                mode = self.groups_table.item(r, 8).text().strip() or "default"
            
            new_config[gid] = {
                'base_coords': (x,y,z), 'layers': layers,
                'block': {'base': b_base, 'cover': b_cover},
                'generation_mode': mode
            }
        self.group_config = new_config

    def update_groups_table(self):
        self.groups_table.setRowCount(len(self.group_config))
        for r, (gid, cfg) in enumerate(self.group_config.items()):
            self.groups_table.setItem(r, 0, QTableWidgetItem(str(gid)))
            
            coords = cfg.get('base_coords', ('0','0','0'))
            self.groups_table.setItem(r, 1, QTableWidgetItem(str(coords[0])))
            self.groups_table.setItem(r, 2, QTableWidgetItem(str(coords[1])))
            self.groups_table.setItem(r, 3, QTableWidgetItem(str(coords[2])))
            
            # 蓝色选点按钮
            pick_btn = FluentButton("📍 选点", is_primary=True)
            pick_btn.setMinimumHeight(28)
            f = pick_btn.font()
            f.setPointSize(9)
            pick_btn.setFont(f)
            
            pick_btn.clicked.connect(lambda _, row=r: self.open_coordinate_picker(row))
            self.groups_table.setCellWidget(r, 4, pick_btn)
            
            l_str = ','.join(map(str, cfg.get('layers', [0])))
            self.groups_table.setItem(r, 5, QTableWidgetItem(l_str))
            
            self.groups_table.setItem(r, 6, QTableWidgetItem(cfg['block'].get('base', '')))
            self.groups_table.setItem(r, 7, QTableWidgetItem(cfg['block'].get('cover', '')))
            self.groups_table.setItem(r, 8, QTableWidgetItem(cfg.get('generation_mode', 'default')))

    def open_coordinate_picker(self, row):
        self.save_table_to_config()
        try:
            gid = int(self.groups_table.item(row, 0).text())
        except:
            gid = row
        dlg = CoordinatePickerDialog(gid, self.group_config, self)
        if dlg.exec():
            nx, ny, nz = dlg.get_coords()
            self.groups_table.setItem(row, 1, QTableWidgetItem(str(nx)))
            self.groups_table.setItem(row, 2, QTableWidgetItem(str(ny)))
            self.groups_table.setItem(row, 3, QTableWidgetItem(str(nz)))
            self.save_table_to_config()

    def start_conversion(self):
        self.save_table_to_config()
        self.config['data_version'] = self.version_combo.currentData()
        self.config['input_file'] = self.input_file_edit.text()
        self.config['type'] = self.type_combo.currentData()
        self.config['output_file'] = self.output_file_edit.text()

        if not self.config['input_file'] or not os.path.exists(self.config['input_file']):
            QMessageBox.critical(self, "错误", "请输入有效的NBS文件路径")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar_label.setText("正在分析...")
        self.log(">>> 开始转换任务...")
        
        try:
            song = pynbs.read(self.config['input_file'])
            if self.config['type'] == 'mcfunction':
                 with open(self.config['output_file']+".mcfunction", 'w') as f: f.write("\n")
            
            proc = GroupProcessor(song.notes, song.header.song_length, self.config, self.group_config)
            proc.set_log_callback(self.log)
            proc.set_progress_callback(self.update_progress)
            
            if self.config['type'] == 'schematic':
                stair = any(c.get('generation_mode')=='staircase' for c in self.group_config.values())
                proc.set_output_strategy(StaircaseSchematicOutputStrategy() if stair else SchematicOutputStrategy())
            else:
                proc.set_output_strategy(McFunctionOutputStrategy())
            
            proc.process()
            self.log(">>> ✅ 转换成功!")
            self.status_bar_label.setText("就绪")
            self.save_last_config()
            
        except Exception as e:
            self.log(f">>> ❌ 错误: {e}")
            self.log(traceback.format_exc())
            QMessageBox.critical(self, "错误", str(e))
        finally:
            self.progress_bar.setValue(100)

    def save_config(self):
        self.save_table_to_config()
        path, _ = QFileDialog.getSaveFileName(self, "保存配置", "", "JSON (*.json)")
        if path:
            with open(path, 'w') as f:
                json.dump({'app_config': self.config, 'group_config': self.group_config}, f, indent=2)

    def load_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载配置", "", "JSON (*.json)")
        if path:
            with open(path, 'r') as f:
                d = json.load(f)
            self.config = d['app_config']
            self.group_config = d['group_config']
            self.input_file_edit.setText(self.config['input_file'])
            self.output_file_edit.setText(self.config['output_file'])
            self.update_groups_table()
            self.log(f"已加载配置: {path}")

    def save_last_config(self):
        try:
            with open('last_config.json', 'w') as f:
                json.dump({'app_config': self.config, 'group_config': self.group_config}, f)
        except: pass

    def load_last_config(self):
        try:
            if os.path.exists('last_config.json'):
                with open('last_config.json', 'r') as f:
                    d = json.load(f)
                self.config = d['app_config']
                self.group_config = d['group_config']
                self.input_file_edit.setText(self.config.get('input_file', ''))
                self.output_file_edit.setText(self.config.get('output_file', ''))
                self.update_groups_table()
        except: pass