"""
坐标选择对话框 - QFluentWidgets 原生组件
二维坐标规划和基于实际导出结构的三维预览。
"""

from copy import deepcopy

from PyQt6.QtWidgets import (
    QDialog,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsItem,
    QLabel,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QFrame,
    QGraphicsTextItem,
    QStackedWidget,
    QAbstractItemView,
    QHeaderView,
    QTableWidgetItem,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt, QPointF, QPropertyAnimation, QEasingCurve, QRectF, QTimer, QEvent,
    QObject, QRunnable, QThreadPool, pyqtSignal,
)
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QKeyEvent, QShortcut, QKeySequence

from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    ToolButton,
    TransparentToolButton,
    CardWidget,
    HeaderCardWidget,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    SpinBox,
    ComboBox,
    FluentIcon,
    SegmentedWidget,
    isDarkTheme,
    ScrollArea,
    HorizontalSeparator,
    TableWidget,
    TransparentPushButton,
)

from .animations import AnimationUtils, GraphicsItemAnimWrapper
from .preview_3d import MinecraftPreviewWidget
from .layout_tools import LayoutHistory, arrange_along_z, copy_layout, translate_all, validate_layout


class _PreviewSignals(QObject):
    finished = pyqtSignal(int, object, str)


class _PreviewWorker(QRunnable):
    """文件读取和结构生成放在工作线程，避免拖动坐标时阻塞界面。"""

    def __init__(self, revision, input_file, song, groups, config, start, span):
        super().__init__()
        self.signals = _PreviewSignals()
        self.revision = revision
        self.input_file = input_file
        self.song = song
        self.groups = groups
        self.config = config
        self.start = start
        self.span = span

    def run(self):
        try:
            import pynbs
            from ..core.preview import build_preview

            song = self.song if self.song is not None else pynbs.read(self.input_file)
            last_tick = max(0, song.header.song_length)
            start = min(self.start, last_tick)
            data = build_preview(
                song.notes, self.groups, self.config,
                start_tick=start, end_tick=min(start + self.span - 1, last_tick),
                global_max_tick=last_tick,
            )
            self.signals.finished.emit(self.revision, (song, data), "")
        except Exception as exc:
            self.signals.finished.emit(self.revision, None, str(exc))


def _accent():
    """返回当前主题的 accent 色"""
    return QColor(0, 120, 216) if not isDarkTheme() else QColor(96, 205, 255)


def _border():
    return "#e0e0e0" if not isDarkTheme() else "#404040"


def _surface():
    return "#f5f5f5" if not isDarkTheme() else "#2b2b2b"


def _muted(label):
    label.setTextColor(QColor("#657387"), QColor("#a4afbf"))
    return label


def _section_title(text):
    label = BodyLabel(text)
    font = label.font()
    font.setWeight(QFont.Weight.DemiBold)
    label.setFont(font)
    return label


def get_color_by_id(group_id, is_active=False):
    if is_active:
        return QColor(0, 120, 255, 230)
    hue = (group_id * 137.508) % 360
    return QColor.fromHsl(int(hue), 200, 140, 180)


# ── 图形组件 ──


class CrosshairItem(QGraphicsItem):
    """十字准星"""

    def __init__(self, size=24):
        super().__init__()
        self._size = size
        self._color = QColor(0, 255, 128, 200)
        self.setZValue(200)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.anim_wrapper = GraphicsItemAnimWrapper(self)
        self.pos_anim = QPropertyAnimation(self.anim_wrapper, b"pos")
        self.pos_anim.setDuration(250)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def boundingRect(self):
        return QRectF(-self._size, -self._size, self._size * 2, self._size * 2)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._color, 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(-self._size, 0), QPointF(self._size, 0))
        painter.drawLine(QPointF(0, -self._size), QPointF(0, self._size))
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), 3, 3)

    def move_smoothly_to(self, x, y):
        if self.pos_anim.state() == QPropertyAnimation.State.Running:
            self.pos_anim.stop()
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPointF(float(x), float(y)))
        self.pos_anim.start()


class TrackGroupItem(QGraphicsRectItem):
    """轨道组位置图元"""

    def __init__(
        self, x, y, group_id, is_active=True, on_move_callback=None, invert_y=True,
        on_select_callback=None, on_drag_finished=None, on_drag_started=None,
    ):
        size = 12
        super().__init__(-size / 2, -size / 2, size, size)

        self.is_active = is_active
        self.on_move_callback = on_move_callback
        self.on_select_callback = on_select_callback
        self.on_drag_finished = on_drag_finished
        self.on_drag_started = on_drag_started
        self._drag_tracking = False
        self.group_id = group_id
        self.invert_y = invert_y

        if invert_y:
            self.setPos(float(x), -float(y))
        else:
            self.setPos(float(x), float(y))

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.anim_wrapper = GraphicsItemAnimWrapper(self)
        self.pos_anim = QPropertyAnimation(self.anim_wrapper, b"pos")
        self.pos_anim.setDuration(150)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.set_active(is_active)

        # 标签
        self.text_item = QGraphicsTextItem(f"ID:{group_id}", self)
        font = QFont("Segoe UI", 8)
        font.setBold(True)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor("#e9eef7" if isDarkTheme() else "#263448"))
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(-text_rect.width() / 2, -size / 2 - 15)
        self.text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def set_active(self, active):
        self.is_active = active
        self.setBrush(QBrush(get_color_by_id(self.group_id, active)))
        self.setPen(QPen(Qt.GlobalColor.white if active else QColor(220, 220, 220), 2 if active else 1))
        self.setZValue(100 if active else 10)

    def move_smoothly_to(self, x, y):
        if self.anim_wrapper:
            if self.pos_anim.state() == QPropertyAnimation.State.Running:
                self.pos_anim.stop()
            self.pos_anim.setStartValue(self.pos())
            if self.invert_y:
                self.pos_anim.setEndValue(QPointF(float(x), -float(y)))
            else:
                self.pos_anim.setEndValue(QPointF(float(x), float(y)))
            self.pos_anim.start()
        else:
            if self.invert_y:
                self.setPos(float(x), -float(y))
            else:
                self.setPos(float(x), float(y))

    def itemChange(self, change, value):
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
        ):
            if self.scene() and self.scene().mouseGrabberItem() == self:
                value = QPointF(
                    max(-30000000, min(30000000, round(value.x()))),
                    max(-320, min(64, round(value.y()))),
                )
                if self.on_move_callback:
                    if self.invert_y:
                        self.on_move_callback(self.group_id, round(value.x()), round(-value.y()))
                    else:
                        self.on_move_callback(self.group_id, round(value.x()), round(value.y()))
                value = QPointF(round(value.x()), round(value.y()))
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if self.scene():
            # Editing is per group. Qt's Ctrl multiselection would otherwise
            # move additional points without sending their coordinate callbacks.
            for item in self.scene().selectedItems():
                if item is not self:
                    item.setSelected(False)
        if self.on_select_callback:
            self.on_select_callback(self.group_id)
        self._drag_tracking = event.button() == Qt.MouseButton.LeftButton
        if self._drag_tracking and self.on_drag_started:
            self.on_drag_started(self.group_id)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if self.pos_anim.state() == QPropertyAnimation.State.Running:
            self.pos_anim.stop()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
        if self._drag_tracking and self.on_drag_finished:
            self._drag_tracking = False
            self.on_drag_finished(self.group_id)


class GridScene(QGraphicsScene):
    """带网格背景和坐标标注的场景"""

    def __init__(self, parent=None, show_labels=True,
                 h_axis_label="X", v_axis_label="Y"):
        super().__init__(parent)
        self.grid_size = 10
        self._show_labels = show_labels
        self.h_axis_label = h_axis_label
        self.v_axis_label = v_axis_label
        self._dark = isDarkTheme()
        self.update_theme()

    def update_theme(self):
        self._dark = isDarkTheme()
        if self._dark:
            self._bg = QColor(30, 30, 30)
            self._grid_minor = QColor(50, 50, 50)
            self._grid_major = QColor(70, 70, 70)
            self._axis_x = QColor(100, 255, 100, 100)
            self._axis_y = QColor(100, 100, 255, 100)
            self._label_color = QColor(100, 100, 100)
            self._axis_label_color_x = QColor(100, 255, 100, 180)
            self._axis_label_color_y = QColor(100, 100, 255, 180)
        else:
            self._bg = QColor(245, 245, 245)
            self._grid_minor = QColor(220, 220, 220)
            self._grid_major = QColor(190, 190, 190)
            self._axis_x = QColor(80, 200, 80, 120)
            self._axis_y = QColor(80, 80, 200, 120)
            self._label_color = QColor(120, 120, 120)
            self._axis_label_color_x = QColor(50, 160, 50, 200)
            self._axis_label_color_y = QColor(50, 50, 180, 200)
        self.setBackgroundBrush(QBrush(self._bg))

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)

        # 细网格
        lines = []
        for x in range(left, int(rect.right()), self.grid_size):
            lines.append(QPointF(x, rect.top()))
            lines.append(QPointF(x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self.grid_size):
            lines.append(QPointF(rect.left(), y))
            lines.append(QPointF(rect.right(), y))

        pen = QPen(self._grid_minor)
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawLines(lines)

        # 大网格 (每50格)
        big_grid_lines = []
        big_step = 50
        big_left = int(rect.left()) - (int(rect.left()) % big_step)
        big_top = int(rect.top()) - (int(rect.top()) % big_step)

        for x in range(big_left, int(rect.right()), big_step):
            big_grid_lines.append(QPointF(x, rect.top()))
            big_grid_lines.append(QPointF(x, rect.bottom()))
        for y in range(big_top, int(rect.bottom()), big_step):
            big_grid_lines.append(QPointF(rect.left(), y))
            big_grid_lines.append(QPointF(rect.right(), y))

        pen_big = QPen(self._grid_major)
        pen_big.setWidth(1)
        painter.setPen(pen_big)
        painter.drawLines(big_grid_lines)

        # 轴线
        painter.setPen(QPen(self._axis_x, 2))
        painter.drawLine(int(rect.left()), 0, int(rect.right()), 0)
        painter.setPen(QPen(self._axis_y, 2))
        painter.drawLine(0, int(rect.top()), 0, int(rect.bottom()))

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if not self._show_labels:
            return

        # 数值坐标标注
        painter.setPen(QPen(self._label_color, 1))
        font = QFont("Consolas", 7)
        painter.setFont(font)
        big_step = 50
        big_left = int(rect.left()) - (int(rect.left()) % big_step)
        for x in range(big_left, int(rect.right()), big_step):
            if x != 0:
                label = str(x)
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(label)
                painter.drawText(QPointF(x - tw / 2, 12), label)
        big_top = int(rect.top()) - (int(rect.top()) % big_step)
        for y in range(big_top, int(rect.bottom()), big_step):
            if y != 0:
                label = str(y)
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(label)
                painter.drawText(QPointF(-tw - 4, y + 4), label)

        # 轴向方向标注 (在轴末端)
        label_font = QFont("Segoe UI", 8)
        label_font.setBold(True)
        painter.setFont(label_font)

        # 水平轴: 标注在视口右边缘
        painter.setPen(QPen(self._axis_label_color_x, 1))
        if self.h_axis_label == "X":
            h_label = "X (\u2192\u4e1c)"   # →东
        else:
            h_label = "Z (\u2192\u5357)"   # →南
        painter.drawText(
            QPointF(rect.right() - 30, -6),
            h_label,
        )

        # 垂直轴: 标注在视口上边缘
        painter.setPen(QPen(self._axis_label_color_y, 1))
        v_label = f"{self.v_axis_label} (\u2191\u4e0a)"  # ↑上
        painter.drawText(
            QPointF(6, rect.top() + 12),
            v_label,
        )


class PickerGraphicsView(QGraphicsView):
    """支持键盘微调 + 滚轮缩放"""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._on_key_nudge = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_key_nudge_callback(self, callback):
        self._on_key_nudge = callback

    def keyPressEvent(self, event: QKeyEvent):
        if self._on_key_nudge:
            step = 10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            handled = True
            if event.key() == Qt.Key.Key_Left:
                self._on_key_nudge(-step, 0)
            elif event.key() == Qt.Key.Key_Right:
                self._on_key_nudge(step, 0)
            elif event.key() == Qt.Key.Key_Up:
                self._on_key_nudge(0, step)
            elif event.key() == Qt.Key.Key_Down:
                self._on_key_nudge(0, -step)
            elif event.key() == Qt.Key.Key_R:
                self._on_key_nudge(0, 0, reset_view=True)
            elif event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.scale(1.25, 1.25)
                handled = False
            elif event.key() == Qt.Key.Key_Minus:
                self.scale(1 / 1.25, 1 / 1.25)
                handled = False
            else:
                handled = False
            if handled:
                return
        super().keyPressEvent(event)


class LayoutToolsDialog(QDialog):
    """Preview a whole-layout operation before returning one atomic edit."""

    def __init__(self, coords, parent=None):
        super().__init__(parent)
        self.setObjectName("LayoutToolsDialog")
        self.setWindowTitle("批量布局")
        self.resize(660, 540)
        self.setMinimumWidth(580)
        self.setStyleSheet(
            f"QDialog#LayoutToolsDialog {{ background: {'#20252e' if isDarkTheme() else '#f6f8fb'}; }}"
        )
        self._source = {gid: tuple(xyz) for gid, xyz in coords.items()}
        self._proposal = None
        self.description = "批量平移"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(12)
        layout.addWidget(SubtitleLabel("批量布局"))
        layout.addWidget(_muted(CaptionLabel("预览全部组的新坐标，应用后可一步撤销。")))
        self.mode = SegmentedWidget()
        self.mode.addItem("translate", "整体平移")
        self.mode.addItem("arrange", "沿 Z 等距排列")
        self.mode.setCurrentItem("translate")
        layout.addWidget(self.mode)
        self.options = QStackedWidget()
        translation = QWidget()
        grid = QGridLayout(translation)
        grid.setContentsMargins(0, 6, 0, 6)
        grid.setHorizontalSpacing(12)
        self.delta_spins = []
        for column, (axis, limit) in enumerate(zip("XYZ", (60_000_000, 384, 60_000_000))):
            grid.addWidget(BodyLabel(f"Δ{axis} · 平移格数"), 0, column)
            spin = SpinBox()
            spin.setRange(-limit, limit)
            spin.setValue(0)
            spin.valueChanged.connect(self.update_proposal)
            grid.addWidget(spin, 1, column)
            self.delta_spins.append(spin)
        self.options.addWidget(translation)
        arrangement = QWidget()
        arrange_grid = QGridLayout(arrangement)
        arrange_grid.setContentsMargins(0, 6, 0, 6)
        arrange_grid.setHorizontalSpacing(16)
        arrange_grid.addWidget(BodyLabel("首组 Z 坐标"), 0, 0)
        arrange_grid.addWidget(BodyLabel("组起点间隔 · 格"), 0, 1)
        self.start_z = SpinBox()
        self.start_z.setRange(-30_000_000, 30_000_000)
        self.start_z.setValue(next(iter(self._source.values()), (0, 64, 0))[2])
        self.spacing = SpinBox()
        self.spacing.setRange(1, 60_000_000)
        self.spacing.setValue(16)
        self.start_z.valueChanged.connect(self.update_proposal)
        self.spacing.valueChanged.connect(self.update_proposal)
        arrange_grid.addWidget(self.start_z, 1, 0)
        arrange_grid.addWidget(self.spacing, 1, 1)
        self.options.addWidget(arrangement)
        layout.addWidget(self.options)
        self.hint = _muted(CaptionLabel("所有组保持相对位置，一起移动。"))
        layout.addWidget(self.hint)
        self.table = TableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["组", "当前起点 · X, Y, Z", "预览起点 · X, Y, Z"])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setWordWrap(False)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        self.summary = CaptionLabel("")
        self.summary.setWordWrap(True)
        self.summary.setMinimumHeight(34)
        layout.addWidget(self.summary)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button = PrimaryPushButton("应用布局")
        self.apply_button.clicked.connect(self.accept)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.apply_button)
        layout.addLayout(buttons)
        self.mode.currentItemChanged.connect(self._mode_changed)
        self.update_proposal()

    def _mode_changed(self, key):
        self.options.setCurrentIndex(0 if key == "translate" else 1)
        self.hint.setText("所有组保持相对位置，一起移动。" if key == "translate"
                          else "保留 X、Y；按照组列表顺序设置 Z 起点。")
        self.update_proposal()

    def update_proposal(self, *_):
        self._proposal = None
        self.table.setRowCount(len(self._source))
        error = ""
        try:
            if self.options.currentIndex() == 0:
                self.description = "整体平移全部组"
                self._proposal = translate_all(self._source, tuple(spin.value() for spin in self.delta_spins))
            else:
                self.description = "沿 Z 等距排列"
                self._proposal = arrange_along_z(self._source, self.start_z.value(), self.spacing.value())
        except ValueError as exc:
            error = str(exc)
        for row, (gid, xyz) in enumerate(self._source.items()):
            after = self._proposal.get(gid) if self._proposal is not None else None
            for column, text in enumerate((str(gid), ", ".join(map(str, xyz)),
                                            ", ".join(map(str, after)) if after else "—")):
                self.table.setItem(row, column, QTableWidgetItem(text))
        changed = sum(self._proposal[gid] != xyz for gid, xyz in self._source.items()) if self._proposal is not None else 0
        self.summary.setText(error or (f"将调整 {changed} 个组的起点。应用后可用 Ctrl+Z 撤销。"
                                      if changed else "调整上方参数，预览将同步更新。"))
        if error:
            self.summary.setTextColor(QColor("#b42318"), QColor("#ffb4a2"))
        else:
            _muted(self.summary)
        self.apply_button.setEnabled(bool(changed) and not error)

    def proposed_coords(self):
        return {gid: tuple(xyz) for gid, xyz in self._proposal.items()} if self._proposal is not None else None


# ── 主对话框 ──


class CoordinatePickerDialog(QDialog):
    """坐标选择对话框 - QFluentWidgets 原生组件"""

    previewReady = pyqtSignal(object, object)
    selectedGroupChanged = pyqtSignal(object)
    coordinatesChanged = pyqtSignal(object)

    VIEW_SOUTH = "south"   # 从南向北看: 水平=X(东), 垂直=Y(上)
    VIEW_WEST = "west"     # 从西向东看: 水平=Z(南), 垂直=Y(上)

    def __init__(self, target_group_id, all_groups_data, parent=None, *,
                 input_file="", preview_config=None):
        super().__init__(parent)
        self.setWindowTitle("轨道布局工作台")
        self.resize(1120, 780)

        self.target_id = target_group_id
        self.all_groups = all_groups_data
        self._working_groups = deepcopy(all_groups_data)
        self.selected_group_id = target_group_id
        self._closing = False
        self._preview_dragging = False
        self._layout_dragging = False
        self._history = LayoutHistory(self.get_all_coords())
        self._history_merge_timer = QTimer(self)
        self._history_merge_timer.setSingleShot(True)
        self._history_merge_timer.setInterval(850)
        self._history_merge_timer.timeout.connect(self._history.break_merge)
        self._view_mode = "west"
        self._groups_items = {}
        self._target_item = None
        self._crosshair = None
        self._confirmed = False
        self._input_file = input_file.strip()
        self._preview_config = dict(preview_config or {})
        self._preview_song = None
        self._preview_data = None
        self._preview_dirty = True
        self._preview_busy = False
        self._preview_revision = 0
        self._preview_worker = None
        self._preview_fit_pending = True
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(180)
        self._preview_timer.timeout.connect(self._rebuild_preview)

        target_data = self.all_groups.get(target_group_id, {})
        coords = target_data.get("base_coords", ("0", "64", "0"))
        try:
            self.x, self.y, self.z = int(coords[0]), int(coords[1]), int(coords[2])
        except Exception:
            self.x, self.y, self.z = 0, 64, 0

        self._build_ui()
        self._refresh_group_selector()
        self._refresh_scene()
        self._update_history_ui()
        self._undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self._undo_shortcut.activated.connect(self.undo_layout)
        self._redo_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self._redo_shortcut.activated.connect(self.redo_layout)
        # QLineEdit claims its own Ctrl+Z before a window shortcut can run.
        # Coordinate inputs must use the same complete-layout history as the canvas.
        for spin in (self.spin_x, self.spin_y, self.spin_z):
            spin.installEventFilter(self)
            spin.lineEdit().installEventFilter(self)
        QTimer.singleShot(50, self._fade_in_entry)

    def _fade_in_entry(self):
        if not self._closing and self.isVisible():
            AnimationUtils.fade_in_entry(self)

    def _build_ui(self):
        dark = isDarkTheme()
        self.setObjectName("CoordinateWorkbench")
        self.setStyleSheet(f"QDialog#CoordinateWorkbench {{ background-color: {'#191e26' if dark else '#f3f6fa'}; }}")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        main = QHBoxLayout()
        main.setContentsMargins(14, 14, 14, 10)
        main.setSpacing(12)

        # ── 左侧控制面板 ──
        ctrl = CardWidget(self)
        ctrl.setMinimumWidth(260)
        cl = QVBoxLayout(ctrl)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(9)

        cl.addWidget(_muted(CaptionLabel("布局工作台")))
        self.edit_title = SubtitleLabel(f"轨道组 {self.selected_group_id}")
        cl.addWidget(self.edit_title)
        self.group_hint = _muted(CaptionLabel("选择组，或直接点击预览中的方块。"))
        self.group_hint.setWordWrap(True)
        cl.addWidget(self.group_hint)
        self.group_selector = ComboBox()
        self.group_selector.currentIndexChanged.connect(self._on_group_selected)
        cl.addWidget(self.group_selector)
        cl.addSpacing(4)
        cl.addWidget(_section_title("世界坐标"))

        # 坐标输入 (SpinBox)
        coord_group = QWidget()
        coord_grid = QGridLayout(coord_group)
        coord_grid.setContentsMargins(0, 0, 0, 0)
        coord_grid.setSpacing(8)

        self.spin_x = self._make_spin("X", "左右", (-30000000, 30000000), self.x)
        self.spin_y = self._make_spin("Y", "高度", (-64, 320), self.y)
        self.spin_z = self._make_spin("Z", "深度", (-30000000, 30000000), self.z)

        for row, (spin, label, tip) in enumerate([
            (self.spin_x, "X", "东 +"),
            (self.spin_y, "Y", "上 +"),
            (self.spin_z, "Z", "南 +"),
        ]):
            lbl = BodyLabel(f"{label}  ·  {tip}")
            coord_grid.addWidget(lbl, row, 0)
            coord_grid.addWidget(spin, row, 1)
            spin.setToolTip(f"轨道组起点的 Minecraft 世界 {label} 坐标；单位为方块")
            spin.editingFinished.connect(self._finish_history_merge)

        self.spin_x.valueChanged.connect(self._on_spinbox_changed)
        self.spin_y.valueChanged.connect(self._on_spinbox_changed)
        self.spin_z.valueChanged.connect(self._on_z_changed)

        cl.addWidget(coord_group)
        self.layout_state = _muted(CaptionLabel(""))
        self.layout_state.setWordWrap(True)
        cl.addWidget(self.layout_state)
        cl.addWidget(HorizontalSeparator())
        cl.addWidget(_section_title("结构预览"))

        # 视图切换 (SegmentedWidget)
        self.segWidget = SegmentedWidget(self)
        self.segWidget.addItem("south", "南视图")
        self.segWidget.addItem("west", "西视图")
        self.segWidget.addItem("3d", "3D 预览")
        self.segWidget.setCurrentItem("west")
        self.segWidget.currentItemChanged.connect(self._switch_view)
        cl.addWidget(self.segWidget)

        self.preview_controls = QWidget()
        pc = QVBoxLayout(self.preview_controls)
        pc.setContentsMargins(0, 2, 0, 2)
        pc.setSpacing(7)
        range_row = QHBoxLayout()
        range_row.addWidget(_muted(CaptionLabel("起始 tick")))
        self.preview_start = SpinBox()
        self.preview_start.setRange(0, 2147483647)
        range_row.addWidget(self.preview_start, 1)
        pc.addLayout(range_row)
        span_row = QHBoxLayout()
        span_row.addWidget(_muted(CaptionLabel("显示长度")))
        self.preview_span = ComboBox()
        self.preview_span.addItems(["16 tick", "32 tick", "64 tick", "128 tick", "256 tick"])
        self.preview_span.setCurrentIndex(2)
        span_row.addWidget(self.preview_span, 1)
        pc.addLayout(span_row)
        page_row = QHBoxLayout()
        self.preview_previous = PushButton("上一段")
        self.preview_next = PushButton("下一段")
        self.preview_previous.clicked.connect(lambda: self._step_preview(-1))
        self.preview_next.clicked.connect(lambda: self._step_preview(1))
        page_row.addWidget(self.preview_previous)
        page_row.addWidget(self.preview_next)
        pc.addLayout(page_row)
        self.preview_summary = _muted(CaptionLabel("选择 NBS 文件后查看实际结构"))
        self.preview_summary.setWordWrap(True)
        self.preview_summary.setToolTip("显示所选时间段的真实世界位置，并计入跨段覆盖；材质为示意。")
        pc.addWidget(self.preview_summary)
        reload_btn = TransparentPushButton(FluentIcon.SYNC, "重新读取 NBS")
        reload_btn.clicked.connect(self._reload_preview)
        pc.addWidget(reload_btn)
        self.preview_start.valueChanged.connect(self._preview_range_changed)
        self.preview_span.currentIndexChanged.connect(self._preview_range_changed)
        self.preview_controls.hide()
        cl.addWidget(self.preview_controls)

        cl.addWidget(HorizontalSeparator())
        cl.addWidget(_section_title("布局工具"))
        history_row = QHBoxLayout()
        self.undo_button = PushButton("撤销")
        self.redo_button = PushButton("重做")
        self.undo_button.clicked.connect(self.undo_layout)
        self.redo_button.clicked.connect(self.redo_layout)
        history_row.addWidget(self.undo_button)
        history_row.addWidget(self.redo_button)
        cl.addLayout(history_row)
        self.layout_tools_button = PushButton(FluentIcon.MOVE, "批量布局…")
        self.layout_tools_button.setToolTip("整体平移全部组，或沿 Z 轴等距排列；应用前可预览坐标。")
        self.layout_tools_button.clicked.connect(self.open_layout_tools)
        cl.addWidget(self.layout_tools_button)
        self.restore_button = TransparentPushButton(FluentIcon.HISTORY, "恢复最初布局")
        self.restore_button.setToolTip("恢复打开工作台时的全部起点坐标；此操作也可撤销。")
        self.restore_button.clicked.connect(self.restore_initial_layout)
        cl.addWidget(self.restore_button)
        self.help_toggle = TransparentPushButton(FluentIcon.HELP, "操作与快捷键")
        self.help_toggle.setCheckable(True)
        cl.addWidget(self.help_toggle)
        self.help_label = _muted(CaptionLabel(""))
        self.help_label.setWordWrap(True)
        self.help_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.help_label.hide()
        self.help_toggle.toggled.connect(self.help_label.setVisible)
        cl.addWidget(self.help_label)
        self._update_help_text()
        cl.addStretch(1)

        ctrl_scroll = ScrollArea(self)
        ctrl_scroll.setFixedWidth(284)
        ctrl_scroll.setWidget(ctrl)
        # QScrollArea.setWidget() enables an opaque palette fill on its child.
        # Keep the Fluent card translucent over the dialog's themed background.
        ctrl.setAutoFillBackground(False)
        ctrl_scroll.setWidgetResizable(True)
        ctrl_scroll.setFrameShape(QFrame.Shape.NoFrame)
        ctrl_scroll.viewport().setAutoFillBackground(False)
        ctrl_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main.addWidget(ctrl_scroll)

        # ── 右侧视图区域 ──
        vc = QWidget()
        vc.setObjectName("previewSurface")
        vc.setStyleSheet(f"QWidget#previewSurface {{ background-color: {'#202630' if dark else '#ffffff'}; border-radius: 10px; }}")
        vl = QVBoxLayout(vc)
        vl.setContentsMargins(4, 4, 4, 4)
        vl.setSpacing(4)

        # 工具栏 (TransparentToolButton)
        tbw = QWidget()
        tbw.setObjectName("previewToolbar")
        tbw.setStyleSheet(f"QWidget#previewToolbar {{ background-color: {'#29313d' if dark else '#edf2f7'}; border-radius: 7px; }}")
        tbh = QHBoxLayout(tbw)
        tbh.setContentsMargins(8, 4, 8, 4)
        tbh.setSpacing(4)

        self._add_tb_btn(tbh, FluentIcon.FIT_PAGE, "适应全部", self._fit_all)
        self._add_tb_btn(tbh, FluentIcon.BACK_TO_WINDOW, "重置视图", self._reset_view)
        self.status_view = _muted(CaptionLabel("西视图 · Z / Y"))
        tbh.addWidget(self.status_view)
        tbh.addStretch()
        self._add_tb_btn(tbh, FluentIcon.ZOOM_IN, "放大", lambda: self._zoom(1.25))
        self._add_tb_btn(tbh, FluentIcon.ZOOM_OUT, "缩小", lambda: self._zoom(1 / 1.25))
        vl.addWidget(tbw)

        # 图形视图
        self.scene = GridScene(h_axis_label="Z", v_axis_label="Y")
        self.view = PickerGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.scale(3.0, 3.0)
        self.view.set_key_nudge_callback(self._on_key_nudge)
        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.view)
        self.preview3d = MinecraftPreviewWidget()
        self.preview3d.groupSelected.connect(lambda gid: self.select_group(gid, center=False))
        self.preview3d.groupMoved.connect(self._on_3d_group_moved)
        self.preview3d.groupDragStarted.connect(self._on_3d_drag_started)
        self.preview3d.groupDragFinished.connect(self._on_3d_drag_finished)
        self.view_stack.addWidget(self.preview3d)
        vl.addWidget(self.view_stack, 1)
        self.hover_label = CaptionLabel("")
        self.hover_label.setWordWrap(True)
        self.hover_label.setMinimumHeight(36)
        self.hover_label.hide()
        self.preview3d.hoverInfoChanged.connect(self.hover_label.setText)
        vl.addWidget(self.hover_label)
        # External listening controls can occupy the wide viewport column.
        self.listen_panel_host = QWidget()
        self.listen_panel_host.setMinimumWidth(620)
        self.listen_panel_layout = QVBoxLayout(self.listen_panel_host)
        self.listen_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.listen_panel_layout.setSpacing(4)
        self.listen_panel_scroll = ScrollArea()
        self.listen_panel_scroll.setWidgetResizable(True)
        self.listen_panel_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.listen_panel_scroll.setWidget(self.listen_panel_host)
        self.listen_panel_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.listen_panel_scroll.setMinimumHeight(100)
        self.listen_panel_scroll.setMaximumHeight(280)
        self.listen_panel_host.setAutoFillBackground(False)
        self.listen_panel_scroll.viewport().setAutoFillBackground(False)
        vl.addWidget(self.listen_panel_scroll)
        main.addWidget(vc, 1)
        outer.addLayout(main)

        # ── 底部状态栏 ──
        sb = QWidget()
        sb.setObjectName("workbenchFooter")
        sb.setStyleSheet(f"QWidget#workbenchFooter {{ background-color: {'#202630' if dark else '#ffffff'}; border-top: 1px solid {_border()}; }}")
        sl = QHBoxLayout(sb)
        sl.setContentsMargins(22, 12, 18, 12)
        sl.setSpacing(10)
        footer_info = QVBoxLayout()
        footer_info.setSpacing(3)
        self.status_coord = CaptionLabel(
            f"X: {self.x}  |  Y: {self.y}  |  Z: {self.z}"
        )
        font = self.status_coord.font()
        font.setWeight(QFont.Weight.DemiBold)
        self.status_coord.setFont(font)
        footer_info.addWidget(self.status_coord)
        self._confirm_label = CaptionLabel("")
        self._confirm_label.hide()
        footer_info.addWidget(self._confirm_label)
        sl.addLayout(footer_info)
        sl.addStretch()
        self.cancel_button = PushButton("取消所有修改", self)
        self.cancel_button.clicked.connect(self.reject)
        sl.addWidget(self.cancel_button)
        self._btn_ok = PushButton("确认当前布局", self)
        self._btn_ok.setToolTip("标记当前布局已确认，可继续查看；应用全部后才写入项目。")
        self._btn_ok.clicked.connect(self._confirm_position)
        sl.addWidget(self._btn_ok)
        self.apply_button = PrimaryPushButton("应用全部并关闭", self)
        self.apply_button.clicked.connect(self._apply_all)
        sl.addWidget(self.apply_button)
        outer.addWidget(sb)

    # ── 辅助 UI 方法 ──

    def _make_spin(self, label, tip, range_, default):
        """创建 Fluent 风格的 SpinBox"""
        spin = SpinBox()
        spin.setRange(*range_)
        spin.setValue(default)
        spin.setFixedHeight(32)
        return spin

    def _add_tb_btn(self, layout, icon, tooltip, slot):
        """添加工具栏按钮 (TransparentToolButton)"""
        btn = TransparentToolButton(icon, self)
        btn.setFixedSize(28, 28)
        btn.setToolTip(tooltip)
        btn.clicked.connect(slot)
        layout.addWidget(btn)

    def _update_help_text(self):
        shared = "Ctrl+Z 撤销 · Ctrl+Shift+Z 重做\n滚轮缩放 · R 重置视图"
        if self._view_mode == "3d":
            text = ("点击方块或组起点选择轨道组。\n"
                    "拖动起点 / Alt+左拖：移动 XZ\n"
                    "Shift+拖动起点：调整 Y 高度\n"
                    "左拖旋转 · 右拖 / 中拖平移\nF 适应全部 · 悬停查看方块属性\n")
        else:
            text = ("南视图：X / Y · 西视图：Z / Y\n"
                    "拖动任意组点位调整坐标。\n"
                    "拖动空白处平移 · 方向键微调\nShift+方向键：每次移动 10 格\n")
        self.help_label.setText(text + shared)

    # ── 坐标历史与创作工具 ──

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            modifiers = event.modifiers()
            if (event.key() == Qt.Key.Key_Z
                    and modifiers & Qt.KeyboardModifier.ControlModifier
                    and not modifiers & (Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier)):
                event.accept()
                if event.type() == QEvent.Type.KeyPress:
                    if modifiers & Qt.KeyboardModifier.ShiftModifier:
                        self.redo_layout()
                    else:
                        self.undo_layout()
                return True
        return super().eventFilter(watched, event)

    def _finish_history_merge(self):
        self._history_merge_timer.stop()
        self._history.break_merge()

    def _update_history_ui(self):
        coords = self.get_all_coords()
        initial = self._history.initial
        changed = sum(xyz != initial.get(gid) for gid, xyz in coords.items())
        self.layout_state.setText(f"已调整 {changed} / {len(coords)} 个组" if changed
                                  else f"{len(coords)} 个组 · 布局未修改")
        self.undo_button.setEnabled(not self._layout_dragging and self._history.undo_count > 0)
        self.redo_button.setEnabled(not self._layout_dragging and self._history.redo_count > 0)
        self.undo_button.setToolTip(f"撤销：{self._history.undo_label}\nCtrl+Z" if self._history.undo_count else "暂无可撤销的坐标修改 · Ctrl+Z")
        self.redo_button.setToolTip(f"重做：{self._history.redo_label}\nCtrl+Shift+Z" if self._history.redo_count else "暂无可重做的坐标修改 · Ctrl+Shift+Z")
        self.restore_button.setEnabled(not self._layout_dragging and changed > 0)
        self.layout_tools_button.setEnabled(not self._layout_dragging and bool(coords))

    def _begin_layout_drag(self, _group_id):
        self._finish_history_merge()
        self._layout_dragging = True
        self._update_history_ui()

    def _finish_layout_drag(self, group_id):
        self._layout_dragging = False
        self._history.record(self.get_all_coords(), f"移动组 {group_id}")
        self._update_history_ui()

    def _mark_layout_modified(self):
        if self._confirmed:
            self._confirmed = False
            self._btn_ok.setText("确认当前布局")
            self._confirm_label.hide()

    def _apply_layout_coordinates(self, coords, description, *, record=True):
        coords = validate_layout(coords) if record else copy_layout(coords)
        if coords.keys() != self._working_groups.keys():
            raise ValueError("布局必须包含全部轨道组")
        if coords == self.get_all_coords():
            return False
        self._finish_history_merge()
        for gid, xyz in coords.items():
            self._working_groups[gid]["base_coords"] = tuple(map(str, xyz))
        if record:
            self._history.record(coords, description)
        self.select_group(self.selected_group_id, center=False)
        for gid, item in self._groups_items.items():
            item.pos_anim.stop()
            xyz = coords[gid]
            item.setPos(xyz[0] if self._view_mode == "south" else xyz[2], -xyz[1])
        if self._crosshair and self._target_item:
            self._crosshair.pos_anim.stop()
            self._crosshair.setPos(self._target_item.pos())
        self._mark_layout_modified()
        self._update_history_ui()
        self._preview_fit_pending = True
        self.coordinatesChanged.emit(self.get_all_coords())
        self._invalidate_preview()
        if self._view_mode != "3d":
            self._fit_all()
        return True

    def undo_layout(self):
        if self._layout_dragging or not self._history.undo_count:
            return
        self._apply_layout_coordinates(self._history.undo(), "撤销", record=False)

    def redo_layout(self):
        if self._layout_dragging or not self._history.redo_count:
            return
        self._apply_layout_coordinates(self._history.redo(), "重做", record=False)

    def restore_initial_layout(self):
        if not self._layout_dragging:
            self._apply_layout_coordinates(self._history.initial, "恢复最初布局")

    def open_layout_tools(self):
        if self._layout_dragging:
            return
        self._finish_history_merge()
        dialog = LayoutToolsDialog(self.get_all_coords(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            coords = dialog.proposed_coords()
            if coords is not None:
                self._apply_layout_coordinates(coords, dialog.description)

    # ── 场景刷新 ──

    def _refresh_group_selector(self):
        self.group_selector.blockSignals(True)
        self.group_selector.clear()
        for gid, xyz in self.get_all_coords().items():
            self.group_selector.addItem(f"组 {gid} · ({xyz[0]}, {xyz[1]}, {xyz[2]})", userData=gid)
            if gid == self.selected_group_id:
                self.group_selector.setCurrentIndex(self.group_selector.count() - 1)
        self.group_selector.blockSignals(False)

    def _on_group_selected(self, index):
        if index >= 0:
            self.select_group(self.group_selector.itemData(index))

    def select_group(self, group_id, *, center=True):
        """Switch the editor without committing or discarding any group edits."""
        if group_id not in self._working_groups:
            return
        self._finish_history_merge()
        changed = group_id != self.selected_group_id
        self.selected_group_id = group_id
        coords = self.get_all_coords()[group_id]
        for spin, value in zip((self.spin_x, self.spin_y, self.spin_z), coords):
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        self.edit_title.setText(f"轨道组 {group_id}")
        self._refresh_group_selector()
        for gid, item in self._groups_items.items():
            item.set_active(gid == group_id)
        self._target_item = self._groups_items.get(group_id)
        if self._crosshair and self._target_item:
            self._crosshair.pos_anim.stop()
            self._crosshair.setPos(self._target_item.pos())
        if center and self._target_item and self._view_mode != "3d":
            self.view.centerOn(self._target_item.pos())
        self.preview3d.set_selected_group(group_id)
        self._update_status()
        if changed:
            self.selectedGroupChanged.emit(group_id)

    def _refresh_scene(self):
        # Scene.clear deletes C++ items immediately. Stop wrappers first so a
        # pending animation cannot write to a deleted item after switching views.
        for item in [*self._groups_items.values(), self._crosshair]:
            if item is not None:
                item.pos_anim.stop()
        self.scene.clear()
        self._groups_items = {}
        is_south = self._view_mode == "south"

        self._target_item = None
        self._crosshair = None
        for g_id, coords in self.get_all_coords().items():
            gx, gy, gz = coords

            # 南视图: 水平=X, 垂直=-Y | 西视图: 水平=Z, 垂直=-Y
            vx = float(gx if is_south else gz)
            vy = -float(gy)

            item = TrackGroupItem(
                vx, vy, g_id, is_active=g_id == self.selected_group_id,
                on_move_callback=self._on_group_point_dragged, invert_y=False,
                on_select_callback=lambda gid: self.select_group(gid, center=False),
                on_drag_finished=self._on_2d_drag_finished,
                on_drag_started=self._begin_layout_drag,
            )
            self.scene.addItem(item)
            self._groups_items[g_id] = item
            if g_id == self.selected_group_id:
                self._target_item = item

        if self._target_item:
            self._crosshair = CrosshairItem(size=22)
            self._crosshair.setPos(self._target_item.pos())
            self.scene.addItem(self._crosshair)
            self.view.centerOn(self._target_item.pos())
        else:
            self.view.centerOn(QPointF(0, 0))

        # centerOn 使用 bitblt 滚动视口, 不会重绘已移位的像素(含轴向标签)。
        # 显式 update() 标记整个场景为脏, 强制 drawForeground 用最新标签重绘。
        self.scene.update()

    # ── 视图切换 ──

    def _switch_view(self, key):
        if self._view_mode == key:
            return
        self._view_mode = key
        self._finish_history_merge()
        self._update_help_text()
        is_3d = key == "3d"
        self.view_stack.setCurrentIndex(1 if is_3d else 0)
        self.preview_controls.setVisible(is_3d)
        self.hover_label.setVisible(is_3d)
        if is_3d:
            self.status_view.setText("3D · 实际结构")
            if self._preview_dirty:
                self._rebuild_preview()
            return
        is_south = key == "south"
        name = "南视图 (X-Y)" if is_south else "西视图 (Z-Y)"
        self.status_view.setText(name)
        self.scene.h_axis_label = "X" if is_south else "Z"
        self.scene.v_axis_label = "Y"
        self._refresh_scene()

    # ── 坐标更新 ──

    def _on_coords_modified(self, *, merge_key=None):
        self._working_groups[self.selected_group_id]["base_coords"] = tuple(
            str(spin.value()) for spin in (self.spin_x, self.spin_y, self.spin_z)
        )
        self._refresh_group_selector()
        self._mark_layout_modified()
        if not self._layout_dragging:
            self._history.record(self.get_all_coords(), f"调整组 {self.selected_group_id} 坐标", merge_key)
            if merge_key is not None:
                self._history_merge_timer.start()
        self._update_history_ui()
        self.coordinatesChanged.emit(self.get_all_coords())
        self._invalidate_preview()

    def _on_group_point_dragged(self, group_id, view_x, view_y):
        if group_id != self.selected_group_id:
            self.select_group(group_id, center=False)
        self._on_point_dragged(view_x, view_y)

    def _on_2d_drag_finished(self, group_id):
        coords = self.get_all_coords()[group_id]
        item = self._groups_items[group_id]
        item.setPos(coords[0] if self._view_mode == "south" else coords[2], -coords[1])
        self._sync_crosshair()
        self._finish_layout_drag(group_id)

    def _on_point_dragged(self, view_x, view_y):
        mc_h = int(view_x)
        mc_v = int(-view_y)
        if self._view_mode == "south":
            # 南视图: 水平=X, 垂直=Y
            self.spin_x.blockSignals(True)
            self.spin_x.setValue(mc_h)
            self.spin_x.blockSignals(False)
            self.spin_y.blockSignals(True)
            self.spin_y.setValue(mc_v)
            self.spin_y.blockSignals(False)
        else:
            # 西视图: 水平=Z, 垂直=Y
            self.spin_z.blockSignals(True)
            self.spin_z.setValue(mc_h)
            self.spin_z.blockSignals(False)
            self.spin_y.blockSignals(True)
            self.spin_y.setValue(mc_v)
            self.spin_y.blockSignals(False)
        if self._crosshair:
            self._crosshair.pos_anim.stop()
            self._crosshair.setPos(mc_h, -mc_v)
        self._update_status()
        self._on_coords_modified()

    def _on_spinbox_changed(self):
        source = self.sender()
        axis = next((axis for axis, spin in zip("XYZ", (self.spin_x, self.spin_y, self.spin_z))
                     if spin is source), None)
        merge_key = ("spin", self.selected_group_id, axis) if axis else None
        if self._view_mode == "3d":
            self._update_status()
            self._on_coords_modified(merge_key=merge_key)
            return
        if self._view_mode == "south":
            # 南视图: 水平=X, 垂直=Y
            h = self.spin_x.value()
            v = self.spin_y.value()
        else:
            # 西视图: 水平=Z, 垂直=Y
            h = self.spin_z.value()
            v = self.spin_y.value()
        if self._target_item:
            self._target_item.pos_anim.stop()
            self._target_item.setPos(float(h), -float(v))
        self._sync_crosshair()
        self._update_status()
        self._on_coords_modified(merge_key=merge_key)

    def _on_z_changed(self):
        self._on_spinbox_changed()

    def _on_3d_drag_started(self, group_id):
        self.select_group(group_id, center=False)
        self._begin_layout_drag(group_id)
        self._preview_dragging = True
        self._preview_timer.stop()

    def _on_3d_group_moved(self, group_id, coords):
        if group_id != self.selected_group_id:
            self.select_group(group_id, center=False)
        for spin, value in zip((self.spin_x, self.spin_y, self.spin_z), coords):
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        self._update_status()
        self._on_coords_modified()

    def _on_3d_drag_finished(self, group_id, changed):
        self._preview_dragging = False
        self._finish_layout_drag(group_id)
        if changed:
            self._invalidate_preview()

    # ── 真实结构预览 ──

    def _preview_groups(self):
        # Coordinates belong to the transaction; other settings come from the
        # caller's current group configuration and are never rewritten here.
        groups = deepcopy(self.all_groups)
        for gid, coords in self.get_all_coords().items():
            if gid in groups:
                groups[gid]["base_coords"] = tuple(str(value) for value in coords)
        return groups

    def load_preview_song(self):
        """Return the current song, loading it once for preview/listening tools."""
        if self._preview_song is None:
            if not self._input_file:
                raise ValueError("请先在基础设置中选择 NBS 文件")
            import pynbs
            self._preview_song = pynbs.read(self._input_file)
        return self._preview_song

    def get_preview_song(self):
        return self._preview_song

    def _preview_anchors(self):
        anchors = {}
        for gid, cfg in self._preview_groups().items():
            try:
                anchors[gid] = tuple(map(int, cfg.get("base_coords", (0, 0, 0))))
            except (ValueError, TypeError):
                continue
        return anchors

    def _invalidate_preview(self):
        self._preview_revision += 1
        self._preview_dirty = True
        self._preview_data = None
        if self._preview_dragging:
            self.preview_summary.setText("正在移动轨道组；松开后更新实际结构")
            return
        # 也清除隐藏的三维场景，切回 3D 时不会短暂显示修改前的位置。
        self.preview3d.set_preview(None, self._preview_anchors(), self.selected_group_id)
        if self._view_mode == "3d":
            # 旧结构不再代表当前坐标，立即清除，避免生成期间误读位置。
            self.preview3d.set_message("正在更新实际结构…")
            self.preview_summary.setText("正在更新实际结构…")
            self._preview_timer.start()

    def _preview_range_changed(self, *_):
        self._preview_fit_pending = True
        self._invalidate_preview()

    def _step_preview(self, direction):
        span = int(self.preview_span.currentText().split()[0])
        self.preview_start.setValue(self.preview_start.value() + direction * span)

    def _reload_preview(self):
        self._preview_song = None
        self._preview_fit_pending = True
        self._invalidate_preview()

    def _rebuild_preview(self):
        if self._closing or self._preview_dragging or self._preview_busy or not self._preview_dirty or self._view_mode != "3d":
            return
        self._preview_timer.stop()
        self._preview_dirty = False
        if not self._input_file:
            self._preview_data = None
            self.preview3d.set_preview(None, self._preview_anchors(), self.selected_group_id,
                                       reset_camera=True)
            self.preview3d.set_message("请在基础设置中选择 NBS 文件\n当前仅显示各轨道组的基准坐标")
            self.preview_summary.setText("未加载 NBS · 仅显示组起点")
            return
        self._preview_busy = True
        self.preview_summary.setText("正在生成实际结构…")
        self.preview3d.set_message("正在生成实际结构…")
        span = int(self.preview_span.currentText().split()[0])
        worker = _PreviewWorker(
            self._preview_revision, self._input_file, self._preview_song,
            self._preview_groups(), self._preview_config,
            self.preview_start.value(), span,
        )
        self._preview_worker = worker
        worker.signals.finished.connect(self._preview_finished)
        QThreadPool.globalInstance().start(worker)

    def _preview_finished(self, revision, result, error):
        self._preview_busy = False
        self._preview_worker = None
        if self._closing:
            return
        if revision != self._preview_revision:
            if self._view_mode == "3d":
                self._preview_timer.start()
            return
        if error:
            self._preview_data = None
            self.preview3d.set_preview(None, self._preview_anchors(), self.selected_group_id)
            self.preview3d.set_message(f"无法生成实际结构\n{error}")
            self.preview_summary.setText(f"预览失败：{error}")
            return
        self._preview_song, self._preview_data = result
        data = self._preview_data
        self.preview_start.blockSignals(True)
        self.preview_start.setMaximum(data.global_max_tick)
        self.preview_start.setValue(data.start_tick)
        self.preview_start.blockSignals(False)
        self.preview_previous.setEnabled(data.start_tick > 0)
        self.preview_next.setEnabled(data.end_tick < data.global_max_tick)
        self.preview3d.set_preview(data, self._preview_anchors(), self.selected_group_id,
                                   reset_camera=self._preview_fit_pending)
        self._preview_fit_pending = False
        self.preview3d.set_message("")
        note_blocks = sum(block.blockstate.startswith("minecraft:note_block[")
                          for block in data.blocks)
        self.preview_summary.setText(
            f"Tick {data.start_tick}–{data.end_tick} / {data.global_max_tick}\n"
            f"{len(data.blocks):,} 方块 · {note_blocks:,} 音符盒"
        )
        self.previewReady.emit(self._preview_song, data)

    def _sync_crosshair(self):
        if self._crosshair and self._target_item:
            p = self._target_item.pos()
            self._crosshair.move_smoothly_to(p.x(), p.y())

    def _update_status(self):
        self.status_coord.setText(
            f"组 {self.selected_group_id}  |  X: {self.spin_x.value()}  |  Y: {self.spin_y.value()}  |  Z: {self.spin_z.value()}"
        )

    # ── 键盘微调 ──

    def _on_key_nudge(self, dx, dy, reset_view=False):
        if reset_view:
            self._reset_view()
            return
        self._finish_history_merge()
        horizontal = self.spin_x if self._view_mode == "south" else self.spin_z
        horizontal.blockSignals(True)
        self.spin_y.blockSignals(True)
        horizontal.setValue(horizontal.value() + dx)
        self.spin_y.setValue(self.spin_y.value() + dy)
        horizontal.blockSignals(False)
        self.spin_y.blockSignals(False)
        self._on_spinbox_changed()

    # ── 确认与关闭 ──

    def _confirm_position(self):
        self._finish_history_merge()
        self._confirmed = True
        self._confirm_label.setTextColor(QColor("#18794e"), QColor("#8bd5ad"))
        self._confirm_label.setText(f"\u2713 全部 {len(self._working_groups)} 组位置已确认，可继续查看")
        self._confirm_label.setVisible(True)
        self._btn_ok.setText("\u2713 已确认")

    def _try_close(self):
        if self._confirmed:
            self.accept()
        else:
            self._confirm_label.setText("\u26a0 请先点击「确认当前布局」")
            self._confirm_label.setTextColor(QColor("#b54708"), QColor("#ffcf8a"))
            self._confirm_label.setVisible(True)

    def reject(self):
        # Cancel always discards the transaction, even after confirming a layout.
        super().reject()

    def _apply_all(self):
        self._confirm_position()
        self.accept()

    def done(self, result):
        self._closing = True
        self._preview_timer.stop()
        self._history_merge_timer.stop()
        self._preview_revision += 1
        super().done(result)

    # ── 视图控制 ──

    def _fit_all(self):
        if self._view_mode == "3d":
            self.preview3d.fit_all()
            return
        if not self._groups_items:
            return
        rect = QRectF()
        for item in self._groups_items.values():
            rect = rect.united(QRectF(item.pos(), item.boundingRect().size()))
        if not rect.isEmpty():
            rect.adjust(-50, -50, 50, 50)
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def _reset_view(self):
        if self._view_mode == "3d":
            self.preview3d.reset_view()
            return
        self.view.resetTransform()
        self.view.scale(3.0, 3.0)
        if self._target_item:
            self.view.centerOn(self._target_item.pos())

    def _zoom(self, factor):
        if self._view_mode == "3d":
            self.preview3d.zoom(factor)
        else:
            self.view.scale(factor, factor)

    # ── 输出 ──

    def get_coords(self):
        """Original entry group's coordinates, retained for existing callers."""
        return self.get_all_coords().get(self.target_id, (0, 64, 0))

    def get_all_coords(self):
        result = {}
        for gid, data in self._working_groups.items():
            try:
                coords = tuple(int(value) for value in data.get("base_coords", (0, 64, 0)))
                if len(coords) != 3:
                    raise ValueError("invalid coordinate count")
            except (TypeError, ValueError):
                coords = (0, 64, 0)
            result[gid] = coords
        return result

    def get_groups_data(self):
        return self._preview_groups()

    def wheelEvent(self, event):
        if self._view_mode != "3d" and self.view.underMouse():
            zoom_in = event.angleDelta().y() > 0
            factor = 1.15 if zoom_in else 1 / 1.15
            self.view.scale(factor, factor)
        else:
            super().wheelEvent(event)
