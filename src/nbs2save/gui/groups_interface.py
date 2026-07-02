"""
轨道组管理界面
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QHeaderView,
    QFrame,
    QTableWidgetItem,
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
)

from .coordinate_picker import CoordinatePickerDialog


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

        self.vBoxLayout.addStretch(1)

    # ── 标题 ──

    def _initTitle(self):
        self.titleLabel = SubtitleLabel("轨道组管理", self)
        self.titleLabel.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)

    # ── 工具栏 ──

    def _initToolbar(self):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.addBtn = PrimaryPushButton("添加分组", self)
        self.addBtn.setFixedWidth(110)
        self.addBtn.setIcon(FluentIcon.ADD)

        self.removeBtn = PushButton("删除选中", self)
        self.removeBtn.setFixedWidth(110)
        self.removeBtn.setIcon(FluentIcon.DELETE)

        toolbar.addWidget(self.addBtn)
        toolbar.addWidget(self.removeBtn)
        toolbar.addStretch(1)

        self.vBoxLayout.addLayout(toolbar)

    # ── 表格 ──

    def _initTable(self):
        self.tableCard = CardWidget(self.scrollWidget)
        cardLayout = QVBoxLayout(self.tableCard)
        cardLayout.setContentsMargins(0, 0, 0, 0)

        self.table = TableWidget(self.tableCard)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "基准X",
                "基准Y",
                "基准Z",
                "坐标规划",
                "轨道ID",
                "基础方块",
                "覆盖方块",
                "生成模式",
            ]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.setSelectionBehavior(
            TableWidget.SelectionBehavior.SelectRows
        )

        cardLayout.addWidget(self.table)
        self.vBoxLayout.addWidget(self.tableCard)

    # ── 公开接口 ──

    def setMainWindow(self, mw):
        self._main_window = mw

    def refreshTable(self):
        """从主窗口的 group_config 刷新表格"""
        if not self._main_window:
            return
        gc = self._main_window.group_config
        self.table.setRowCount(len(gc))
        for r, (gid, cfg) in enumerate(gc.items()):
            self.table.setItem(r, 0, QTableWidgetItem(str(gid)))

            coords = cfg.get("base_coords", ("0", "0", "0"))
            self.table.setItem(r, 1, QTableWidgetItem(str(coords[0])))
            self.table.setItem(r, 2, QTableWidgetItem(str(coords[1])))
            self.table.setItem(r, 3, QTableWidgetItem(str(coords[2])))

            # 坐标规划按钮
            pick_btn = PrimaryPushButton("选点", self.table)
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
            self.table.setItem(
                r, 8, QTableWidgetItem(cfg.get("generation_mode", "default"))
            )

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

            x = self.table.item(r, 1).text().strip() or "0"
            y = self.table.item(r, 2).text().strip() or "0"
            z = self.table.item(r, 3).text().strip() or "0"
            layers_str = self.table.item(r, 5).text().strip()
            layers = (
                [int(x) for x in layers_str.split(",") if x.strip()]
                if layers_str
                else [0]
            )
            b_base = (
                self.table.item(r, 6).text().strip() or "minecraft:iron_block"
            )
            b_cover = (
                self.table.item(r, 7).text().strip() or "minecraft:iron_block"
            )
            mode = "default"
            if self.table.columnCount() >= 9:
                mode = self.table.item(r, 8).text().strip() or "default"

            new_config[gid] = {
                "base_coords": (x, y, z),
                "layers": layers,
                "block": {"base": b_base, "cover": b_cover},
                "generation_mode": mode,
            }
        self._main_window.group_config = new_config

    def addGroup(self):
        """添加新分组"""
        self.saveTableToConfig()
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
        }
        self.refreshTable()

    def removeGroup(self):
        """删除选中分组"""
        if not self._main_window:
            return
        gc = self._main_window.group_config
        if len(gc) <= 1:
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
        self.saveTableToConfig()
        curr = self.table.currentRow()
        if curr >= 0:
            gid = list(gc.keys())[curr]
            del gc[gid]
            self.refreshTable()

    def _openCoordinatePicker(self, row):
        self.saveTableToConfig()
        gc = self._main_window.group_config
        try:
            gid = int(self.table.item(row, 0).text())
        except Exception:
            gid = row
        dlg = CoordinatePickerDialog(gid, gc, self)
        if dlg.exec():
            nx, ny, nz = dlg.get_coords()
            self.table.setItem(row, 1, QTableWidgetItem(str(nx)))
            self.table.setItem(row, 2, QTableWidgetItem(str(ny)))
            self.table.setItem(row, 3, QTableWidgetItem(str(nz)))
            self.saveTableToConfig()
