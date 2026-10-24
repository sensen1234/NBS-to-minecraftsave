"""
轨道组管理界面
"""

from copy import deepcopy
import math

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QHeaderView,
    QFrame,
    QTableWidgetItem,
    QSizePolicy,
)

from qfluentwidgets import (
    ScrollArea,
    CardWidget,
    TableWidget,
    SubtitleLabel,
    PrimaryPushButton,
    PushButton,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    ComboBox,
)

from .coordinate_picker import CoordinatePickerDialog
from .studio_style import PageHeader, apply_page_style, muted_label
from qfluentwidgets import CaptionLabel


# 生成模式选项: (显示文本, 配置值) — 决定结构生成方式
_GEN_MODE_ITEMS = [
    ("水平布局", "default"),
    ("阶梯向下", "staircase"),
    ("阶梯向上", "staircase_up"),
]

# 偏移模式选项: (显示文本, 配置值) — 决定音符Z轴偏移量计算方式，与生成模式独立
_OFFSET_MODE_ITEMS = [
    ("按声像偏移", "pan"),
    ("按音量偏移", "volume"),
]


class GroupsInterface(ScrollArea):
    """轨道组管理界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("groupsInterface")
        self._main_window = None  # 引用主窗口以访问 group_config

        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName("scrollWidget")
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(12)

        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self._initTitle()
        self._initToolbar()
        self._initTable()
        apply_page_style(self)
        self.table.itemSelectionChanged.connect(self._update_selection)
        self.table.itemChanged.connect(lambda _: self._update_summary())
        self._update_selection()

    # ── 标题 ──

    def _initTitle(self):
        header = PageHeader("轨道与布局", "把音轨组织成独立的结构，在工作台中安排它们的位置与听感。", "ARRANGEMENT", self.scrollWidget)
        self.titleLabel = header.titleLabel
        self.vBoxLayout.addWidget(header)

    # ── 工具栏 ──

    def _initToolbar(self):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.addBtn = PushButton("添加组", self)
        self.addBtn.setIcon(FluentIcon.ADD)

        self.duplicateBtn = PushButton("复制组", self)
        self.duplicateBtn.setIcon(FluentIcon.COPY)
        self.duplicateBtn.setToolTip("复制当前组及其轨道设置，新组向南移动 24 格；可在工作台调整。")
        self.duplicateBtn.clicked.connect(self.duplicateGroup)
        self.removeBtn = PushButton("删除组", self)
        self.removeBtn.setIcon(FluentIcon.DELETE)

        self.workbenchBtn = PrimaryPushButton("打开创作工作台", self)
        self.workbenchBtn.setIcon(FluentIcon.TILES)
        self.workbenchBtn.clicked.connect(self.openWorkbench)

        toolbar.addWidget(self.addBtn)
        toolbar.addWidget(self.duplicateBtn)
        toolbar.addWidget(self.removeBtn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.workbenchBtn)

        self.vBoxLayout.addLayout(toolbar)
        info = QHBoxLayout()
        self.summaryLabel = muted_label(CaptionLabel("轨道 ID 从 0 开始；多个 ID 用英文逗号分隔。", self))
        info.addWidget(self.summaryLabel, 1)
        self.checkBtn = PushButton("创作检查", self)
        self.checkBtn.setToolTip("检查未分配轨道、音域、缺失采样和输出格式。快捷键 Ctrl+Shift+K。")
        info.addWidget(self.checkBtn)
        self.vBoxLayout.addLayout(info)

    # ── 表格 ──

    def _initTable(self):
        self.tableCard = CardWidget(self.scrollWidget)
        self.tableCard.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        cardLayout = QVBoxLayout(self.tableCard)
        cardLayout.setContentsMargins(0, 0, 0, 0)

        self.table = TableWidget(self.tableCard)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "起点 X",
                "起点 Y",
                "起点 Z",
                "位置",
                "NBS 轨道 ID",
                "基础方块",
                "覆盖方块",
                "生成模式",
                "偏移模式",
            ]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(48)
        for column, width in enumerate((48, 80, 80, 80, 88, 130, 190, 190, 136, 136)):
            self.table.setColumnWidth(column, width)
        header.setStretchLastSection(False)
        tips = {1: "世界坐标 X，正方向为东。", 2: "世界坐标 Y，正方向为上。", 3: "世界坐标 Z，正方向为南。", 5: "对应 NBS 的轨道序号，从 0 开始；例如 0,1,3。", 6: "红石线路的基础方块。音符盒下垫块由乐器或自定义音色决定。", 7: "线路覆盖方块；音符盒上方会留空以便发声。", 8: "阶梯布局需要 Schematic 格式。", 9: "声像模式使用音符 panning；音量模式根据音量调整距离。"}
        for column, tip in tips.items():
            self.table.horizontalHeaderItem(column).setToolTip(tip)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.setSelectionBehavior(
            TableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(TableWidget.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(300)

        cardLayout.addWidget(self.table)
        self.vBoxLayout.addWidget(self.tableCard, 1)

    # ── 公开接口 ──

    def setMainWindow(self, mw):
        self._main_window = mw

    def refreshTable(self):
        """从主窗口的 group_config 刷新表格"""
        if not self._main_window:
            return
        gc = self._main_window.group_config
        self.table.blockSignals(True)
        self.table.setRowCount(len(gc))
        for r, (gid, cfg) in enumerate(gc.items()):
            id_item = QTableWidgetItem(str(gid))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, 0, id_item)

            coords = cfg.get("base_coords", ("0", "0", "0"))
            self.table.setItem(r, 1, QTableWidgetItem(str(coords[0])))
            self.table.setItem(r, 2, QTableWidgetItem(str(coords[1])))
            self.table.setItem(r, 3, QTableWidgetItem(str(coords[2])))

            # 坐标规划按钮
            pick_btn = PushButton("定位", self.table)
            pick_btn.setToolTip(f"在工作台编辑组 {gid}，所有组的修改可以一起应用。")
            pick_btn.setFixedHeight(28)
            f = pick_btn.font()
            f.setPointSize(9)
            pick_btn.setFont(f)
            pick_btn.clicked.connect(lambda _, row=r: self._openCoordinatePicker(row))
            self.table.setCellWidget(r, 4, pick_btn)

            l_str = ",".join(map(str, cfg.get("layers", [0])))
            self.table.setItem(r, 5, QTableWidgetItem(l_str))
            self.table.setItem(
                r, 6, QTableWidgetItem(cfg["block"].get("base", ""))
            )
            self.table.setItem(
                r, 7, QTableWidgetItem(cfg["block"].get("cover", ""))
            )
            # 生成模式: 下拉框选择
            combo = ComboBox(self.table)
            combo.addItems([label for label, _ in _GEN_MODE_ITEMS])
            cur_mode = cfg.get("generation_mode", "default")
            for idx, (_, val) in enumerate(_GEN_MODE_ITEMS):
                if val == cur_mode:
                    combo.setCurrentIndex(idx)
                    break
            self.table.setCellWidget(r, 8, combo)

            # 偏移模式: 下拉框选择
            off_combo = ComboBox(self.table)
            off_combo.addItems([label for label, _ in _OFFSET_MODE_ITEMS])
            cur_off = cfg.get("offset_mode", "pan")
            for idx, (_, val) in enumerate(_OFFSET_MODE_ITEMS):
                if val == cur_off:
                    off_combo.setCurrentIndex(idx)
                    break
            self.table.setCellWidget(r, 9, off_combo)
        self.table.blockSignals(False)
        self._update_summary()
        self._update_selection()

    def _update_summary(self):
        count = self.table.rowCount()
        self.summaryLabel.setText(f"{count} 个轨道组 · NBS 轨道从 0 编号，多个 ID 用英文逗号分隔")

    def _update_selection(self):
        selected = self.table.currentRow() >= 0 and bool(self.table.selectedItems())
        self.duplicateBtn.setEnabled(selected)
        self.removeBtn.setEnabled(selected and self.table.rowCount() > 1)

    def _save_edits(self):
        try:
            self.saveTableToConfig()
            return True
        except (ValueError, TypeError) as error:
            self._main_window._settings_error(error)
            return False

    def duplicateGroup(self):
        row = self.table.currentRow()
        if row < 0 or not self._save_edits():
            return
        gc = self._main_window.group_config
        original_id = int(self.table.item(row, 0).text())
        gid = max(gc, default=-1) + 1
        draft = deepcopy(gc[original_id])
        x, y, z = map(int, draft["base_coords"])
        draft["base_coords"] = tuple(map(str, (x, y, z + 24 if z <= 29_999_976 else z - 24)))
        gc[gid] = draft
        self.refreshTable()
        self.table.selectRow(self.table.rowCount() - 1)

    def saveTableToConfig(self):
        """将表格内容写回主窗口的 group_config"""
        if not self._main_window:
            return
        new_config = {}
        for r in range(self.table.rowCount()):
            try:
                gid = int(self.table.item(r, 0).text())
            except Exception:
                gid = r

            if gid in new_config:
                raise ValueError(f"组 ID {gid} 重复，请为每个组使用独立 ID。")
            try:
                x, y, z = (str(int(self.table.item(r, column).text().strip() or "0")) for column in (1, 2, 3))
            except ValueError as exc:
                raise ValueError(f"组 {gid} 的 XYZ 坐标需填写整数。") from exc
            layers_str = self.table.item(r, 5).text().strip()
            try:
                layers = list(dict.fromkeys(int(value) for value in layers_str.replace("，", ",").split(",") if value.strip())) if layers_str else [0]
                if any(layer < 0 for layer in layers):
                    raise ValueError
            except ValueError as exc:
                raise ValueError(f"组 {gid} 的轨道 ID 需为非负整数；多个 ID 用逗号分隔，例如 0,1,3。") from exc
            b_base = (
                self.table.item(r, 6).text().strip() or "minecraft:iron_block"
            )
            b_cover = (
                self.table.item(r, 7).text().strip() or "minecraft:iron_block"
            )
            mode = "default"
            if self.table.columnCount() >= 9:
                combo = self.table.cellWidget(r, 8)
                if isinstance(combo, ComboBox):
                    idx = combo.currentIndex()
                    mode = (
                        _GEN_MODE_ITEMS[idx][1]
                        if 0 <= idx < len(_GEN_MODE_ITEMS)
                        else "default"
                    )
                elif self.table.item(r, 8) is not None:
                    # 兼容旧式 QTableWidgetItem
                    mode = self.table.item(r, 8).text().strip() or "default"

            # 偏移模式
            offset_mode = "pan"
            if self.table.columnCount() >= 10:
                off_combo = self.table.cellWidget(r, 9)
                if isinstance(off_combo, ComboBox):
                    idx = off_combo.currentIndex()
                    offset_mode = (
                        _OFFSET_MODE_ITEMS[idx][1]
                        if 0 <= idx < len(_OFFSET_MODE_ITEMS)
                        else "pan"
                    )

            new_config[gid] = deepcopy(self._main_window.group_config.get(gid, {}))
            new_config[gid].update({
                "base_coords": (x, y, z),
                "layers": layers,
                "block": {"base": b_base, "cover": b_cover},
                "generation_mode": mode,
                "offset_mode": offset_mode,
            })
        self._main_window.group_config = new_config

    def addGroup(self):
        """添加新分组"""
        if not self._save_edits():
            return
        gc = self._main_window.group_config
        gid = max(gc.keys()) + 1 if gc else 0
        gc[gid] = {
            "base_coords": ("0", "0", "0"),
            "layers": [0],
            "block": {
                "base": "minecraft:iron_block",
                "cover": "minecraft:iron_block",
            },
            "generation_mode": "default",
            "offset_mode": "pan",
        }
        self.refreshTable()

    def removeGroup(self):
        """删除选中分组"""
        if not self._main_window:
            return
        # 先检查数量（用当前表格行数，避免 saveTableToConfig 重赋值后引用失效）
        if self.table.rowCount() <= 1:
            InfoBar.warning(
                title="提示",
                content="至少保留一个轨道组",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            return
        curr = self.table.currentRow()
        if curr < 0:
            return
        # 先保存当前表格到 config，再重新获取引用（saveTableToConfig 会重赋值 group_config）
        if not self._save_edits():
            return
        gc = self._main_window.group_config
        gid = list(gc.keys())[curr]
        del gc[gid]
        self.refreshTable()

    def openWorkbench(self):
        if self.table.rowCount():
            self._openCoordinatePicker(max(0, self.table.currentRow()))

    def _openCoordinatePicker(self, row):
        try:
            self._main_window.collect_settings()
        except (ValueError, TypeError) as error:
            self._main_window._settings_error(error)
            return
        gc = self._main_window.group_config
        try:
            gid = int(self.table.item(row, 0).text())
        except Exception:
            gid = row
        home = self._main_window.homeInterface
        preview_config = deepcopy(self._main_window.config)
        preview_config["data_version"] = home.getVersion()
        preview_config["type"] = home.getType()
        if "position" not in preview_config.get("listening", {}):
            try:
                x, y, z = (int(value) for value in gc[gid]["base_coords"])
            except (ValueError, TypeError):
                x, y, z = 0, 64, 0
            preview_config["listening"] = {
                **preview_config.get("listening", {}),
                "position": (x + .5, y + 1.62, z - 6), "yaw": 0,
            }
        dlg = CoordinatePickerDialog(
            gid, gc, self, input_file=home.getInputFile(),
            preview_config=preview_config,
        )
        from .listening_panel import ListeningPanel

        listening = ListeningPanel(
            song_provider=dlg.load_preview_song,
            groups_provider=dlg.get_groups_data,
            config_provider=lambda: preview_config,
            parent=dlg,
        )
        dlg.listen_panel_layout.addWidget(listening)
        listening.listenerChanged.connect(dlg.preview3d.set_listener)
        def selected_origin():
            return dlg.get_all_coords()[dlg.selected_group_id]
        def place_near_group():
            x, y, z = selected_origin()
            listening.set_listener((x + .5, y + 1.62, z - 6), 0)
        def face_group():
            x, _, z = selected_origin()
            lx, _, lz = listening.listener
            dx, dz = x + .5 - lx, z + .5 - lz
            if math.hypot(dx, dz) > 1e-8:
                listening.set_listener(listening.listener, math.degrees(math.atan2(-dx, dz)))
        listening.placeNearGroupRequested.connect(place_near_group)
        listening.faceGroupRequested.connect(face_group)
        dlg.preview3d.set_listener(listening.listener, listening.yaw)
        def preview_ready(song, data):
            listening.invalidate()
            listening.set_range(data.start_tick, data.end_tick)
        dlg.previewReady.connect(preview_ready)
        # The panel only retains audio rendered from the current draft layout.
        dlg.coordinatesChanged.connect(lambda _: listening.invalidate())
        dlg.finished.connect(lambda _: listening.shutdown())
        if dlg.exec():
            self._main_window.group_config = dlg.get_groups_data()
            for key in ("listening", "minecraft_assets_dir"):
                if key in preview_config:
                    self._main_window.config[key] = deepcopy(preview_config[key])
            self.refreshTable()
        listening.shutdown()
        dlg.deleteLater()
