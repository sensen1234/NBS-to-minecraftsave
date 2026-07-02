"""
实用工具界面 - 音量/距离速查表 + 双向计算器
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

from qfluentwidgets import (
    ScrollArea,
    CardWidget,
    TitleLabel,
    SubtitleLabel,
    StrongBodyLabel,
    BodyLabel,
    CaptionLabel,
    TableWidget,
    DoubleSpinBox,
    FluentIcon,
)

from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView


# ── 音量-距离原始数据 (音符盒音量 → 玩家可听距离) ──
# 来源: Minecraft Java Edition 音符盒声学模型 (仅供参考)
_RAW_DATA = [
    (100, 0),
    (90, 14),
    (80, 22),
    (70, 28),
    (60, 32),
    (50, 38),
    (40, 40),
    (30, 42),
    (20, 44),
    (10, 46),
]

# ── 拟合函数: 分段线性插值 ──
# 在已知数据点之间做线性插值，提供任意音量↔距离的互查


def _lerp(x, x0, y0, x1, y1):
    """线性插值"""
    if x1 == x0:
        return y0
    return y0 + (y - y0) * (x - x0) / (x1 - x0) if (y := y0) is not None else 0


def volume_to_distance(vol_pct: float) -> float:
    """
    音量百分比 (0-100) → 玩家可听距离 (格)
    使用分段线性插值，边界外推。
    """
    if vol_pct >= 100:
        return 0.0
    if vol_pct <= 10:
        # 低于 10% 时线性外推 (斜率约 0.2 格/%)
        return 46.0 + (10.0 - vol_pct) * 0.2

    # 在数据点间插值
    for i in range(len(_RAW_DATA) - 1):
        v0, d0 = _RAW_DATA[i]
        v1, d1 = _RAW_DATA[i + 1]
        if v1 <= vol_pct <= v0:
            t = (vol_pct - v1) / (v0 - v1)
            return d1 + t * (d0 - d1)

    return 0.0


def distance_to_volume(dist: float) -> float:
    """
    玩家可听距离 (格) → 音量百分比 (0-100)
    使用分段线性插值，边界外推。
    """
    if dist <= 0:
        return 100.0
    if dist >= 46:
        # 超出最大距离时线性外推
        return max(0.0, 10.0 - (dist - 46.0) * 0.2)

    # 在数据点间插值 (距离是递增的)
    for i in range(len(_RAW_DATA) - 1):
        v0, d0 = _RAW_DATA[i]
        v1, d1 = _RAW_DATA[i + 1]
        if d0 <= dist <= d1:
            t = (dist - d0) / (d1 - d0) if d1 != d0 else 0
            return v0 + t * (v1 - v0)

    return 100.0


class UtilitiesInterface(ScrollArea):
    """实用工具界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("utilitiesInterface")
        self.setWidgetResizable(True)
        self.enableTransparentBackground()

        self.scrollWidget = QWidget(self)
        self.scrollWidget.setObjectName("scrollWidget")

        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(16)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 标题
        header = TitleLabel("实用工具", self)
        header.setStyleSheet("font-size: 26px; font-weight: 700;")
        self.vBoxLayout.addWidget(header)

        desc = BodyLabel("常用参考数据与速查工具", self)
        desc.setStyleSheet("color: #888; font-size: 13px; margin-bottom: 8px;")
        self.vBoxLayout.addWidget(desc)

        self._initVolumeTable()
        self._initCalculator()

        self.vBoxLayout.addStretch(1)
        self.setWidget(self.scrollWidget)

    # ── 参考表 ──

    def _initVolumeTable(self):
        card = CardWidget(self.scrollWidget)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 24)
        cl.setSpacing(12)

        title = SubtitleLabel("音量与玩家可听距离", card)
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        cl.addWidget(title)

        note = CaptionLabel(
            "Minecraft Java Edition 音符盒声学模型参考数据，仅供参考。",
            card,
        )
        note.setStyleSheet("color: #888; font-size: 12px;")
        cl.addWidget(note)

        table = TableWidget(card)
        table.setColumnCount(2)
        table.setRowCount(len(_RAW_DATA))
        table.setHorizontalHeaderLabels(["音量", "玩家可听距离"])

        hv = table.horizontalHeader()
        hv.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hv.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        for row, (vol, dist) in enumerate(_RAW_DATA):
            volItem = QTableWidgetItem(f"{vol}%")
            distItem = QTableWidgetItem(f"{dist} 格")
            volItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            distItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, volItem)
            table.setItem(row, 1, distItem)

        table.verticalHeader().setVisible(False)
        table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(TableWidget.SelectionMode.NoSelection)
        table.setFixedHeight(420)

        cl.addWidget(table)
        self.vBoxLayout.addWidget(card)

    # ── 双向计算器 (单行) ──

    def _initCalculator(self):
        from qfluentwidgets import TransparentToolButton

        card = CardWidget(self.scrollWidget)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 24)
        cl.setSpacing(12)

        title = SubtitleLabel("音量 ↔ 距离 计算器", card)
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        cl.addWidget(title)

        # 单行: [音量 SpinBox] [→ 或 ←] [距离 SpinBox] [交换按钮]
        row = QHBoxLayout()
        row.setSpacing(10)

        lbl_vol = StrongBodyLabel("音量", card)
        lbl_vol.setStyleSheet("font-size: 13px;")
        self.spin_vol = DoubleSpinBox(card)
        self.spin_vol.setRange(0, 100)
        self.spin_vol.setDecimals(1)
        self.spin_vol.setSuffix(" %")
        self.spin_vol.setValue(100)
        self.spin_vol.setFixedHeight(32)

        self.arrowLabel = BodyLabel("→", card)
        self.arrowLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arrowLabel.setFixedWidth(32)
        self.arrowLabel.setStyleSheet("font-size: 20px; font-weight: 700; color: #0078d4;")

        lbl_dist = StrongBodyLabel("距离", card)
        lbl_dist.setStyleSheet("font-size: 13px;")
        self.spin_dist = DoubleSpinBox(card)
        self.spin_dist.setRange(0, 100)
        self.spin_dist.setDecimals(1)
        self.spin_dist.setSuffix(" 格")
        self.spin_dist.setValue(0)
        self.spin_dist.setFixedHeight(32)

        swapBtn = TransparentToolButton(FluentIcon.SYNC, card)
        swapBtn.setFixedSize(32, 32)
        swapBtn.setToolTip("交换音量与距离")
        swapBtn.clicked.connect(self._swapValues)

        row.addWidget(lbl_vol)
        row.addWidget(self.spin_vol, 1)
        row.addWidget(self.arrowLabel)
        row.addWidget(lbl_dist)
        row.addWidget(self.spin_dist, 1)
        row.addWidget(swapBtn)

        cl.addLayout(row)

        # 信号 (防循环)
        self._updating = False
        self._mode = "vol2dist"  # vol2dist 或 dist2vol
        self.spin_vol.valueChanged.connect(self._onVolChanged)
        self.spin_dist.valueChanged.connect(self._onDistChanged)

        self.vBoxLayout.addWidget(card)

    def _onVolChanged(self, val):
        if self._updating:
            return
        self._updating = True
        self._mode = "vol2dist"
        self.arrowLabel.setText("→")
        dist = volume_to_distance(val)
        self.spin_dist.blockSignals(True)
        self.spin_dist.setValue(dist)
        self.spin_dist.blockSignals(False)
        self._updating = False

    def _onDistChanged(self, val):
        if self._updating:
            return
        self._updating = True
        self._mode = "dist2vol"
        self.arrowLabel.setText("←")
        vol = distance_to_volume(val)
        self.spin_vol.blockSignals(True)
        self.spin_vol.setValue(vol)
        self.spin_vol.blockSignals(False)
        self._updating = False

    def _swapValues(self):
        """交换音量和距离的值"""
        if self._updating:
            return
        self._updating = True
        vol = self.spin_vol.value()
        dist = self.spin_dist.value()
        self.spin_vol.blockSignals(True)
        self.spin_dist.blockSignals(True)
        self.spin_vol.setValue(dist)  # 距离值放到音量栏
        self.spin_dist.setValue(vol)  # 音量值放到距离栏
        self.spin_vol.blockSignals(False)
        self.spin_dist.blockSignals(False)
        # 触发重新计算
        self._updating = False
        self._onVolChanged(self.spin_vol.value())
