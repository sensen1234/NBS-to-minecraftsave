"""
实用工具界面 - 提供常用参考数据
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout

from qfluentwidgets import (
    ScrollArea,
    CardWidget,
    TitleLabel,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    TableWidget,
    FluentIcon,
)

from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QColor


# 音量-距离参考数据 (音符盒音量 vs 玩家可听距离)
VOLUME_DISTANCE_DATA = [
    ("100%", "0 格"),
    ("90%",  "14 格"),
    ("80%",  "22 格"),
    ("70%",  "28 格"),
    ("60%",  "32 格"),
    ("50%",  "38 格"),
    ("40%",  "40 格"),
    ("30%",  "42 格"),
    ("20%",  "44 格"),
    ("10%",  "46 格"),
]


class UtilitiesInterface(ScrollArea):
    """实用工具界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("utilitiesInterface")
        self.setWidgetResizable(True)
        self.enableTransparentBackground()

        self.scrollWidget = TitleLabel("", self)
        self.scrollWidget.setObjectName("scrollWidget")

        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(16)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 标题
        header = TitleLabel("实用工具", self)
        header.setStyleSheet("font-size: 26px; font-weight: 700;")
        self.vBoxLayout.addWidget(header)

        desc = BodyLabel("常用参考数据与速查表", self)
        desc.setStyleSheet("color: #888; font-size: 13px; margin-bottom: 8px;")
        self.vBoxLayout.addWidget(desc)

        self._initVolumeTable()

        self.setWidget(self.scrollWidget)

    def _initVolumeTable(self):
        """音量与玩家距离参考表"""
        card = CardWidget(self.scrollWidget)
        cardLayout = QVBoxLayout(card)
        cardLayout.setContentsMargins(24, 20, 24, 24)
        cardLayout.setSpacing(12)

        # 标题行
        title = SubtitleLabel("音量与玩家可听距离", card)
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        cardLayout.addWidget(title)

        note = CaptionLabel("仅供参考。实际距离可能受游戏版本与环境影响。", card)
        note.setStyleSheet("color: #888; font-size: 12px;")
        cardLayout.addWidget(note)

        # 表格
        table = TableWidget(card)
        table.setColumnCount(2)
        table.setRowCount(len(VOLUME_DISTANCE_DATA))
        table.setHorizontalHeaderLabels(["音量", "玩家可听距离"])

        # 设置列宽
        headerView = table.horizontalHeader()
        headerView.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        headerView.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        for row, (vol, dist) in enumerate(VOLUME_DISTANCE_DATA):
            volItem = QTableWidgetItem(vol)
            distItem = QTableWidgetItem(dist)
            volItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            distItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, volItem)
            table.setItem(row, 1, distItem)

        table.verticalHeader().setVisible(False)
        table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(TableWidget.SelectionMode.NoSelection)
        table.setFixedHeight(420)

        cardLayout.addWidget(table)
        self.vBoxLayout.addWidget(card)
