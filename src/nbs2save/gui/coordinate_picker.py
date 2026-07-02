"""
坐标选择对话框 - QFluentWidgets 原生组件
双视图（XY/XZ）、键盘微调、十字准星、拖拽定位
"""

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
)
from PyQt6.QtCore import Qt, QPointF, QPropertyAnimation, QEasingCurve, QRectF, QTimer
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QKeyEvent

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
    FluentIcon,
    SegmentedWidget,
    isDarkTheme,
)

from .animations import AnimationUtils, GraphicsItemAnimWrapper


def _accent():
    """返回当前主题的 accent 色"""
    return QColor(0, 120, 216) if not isDarkTheme() else QColor(96, 205, 255)


def _border():
    return "#e0e0e0" if not isDarkTheme() else "#404040"


def _surface():
    return "#f5f5f5" if not isDarkTheme() else "#2b2b2b"


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
        self, x, y, group_id, is_active=True, on_move_callback=None, invert_y=True
    ):
        size = 12
        super().__init__(-size / 2, -size / 2, size, size)

        self.is_active = is_active
        self.on_move_callback = on_move_callback
        self.group_id = group_id
        self.invert_y = invert_y

        if invert_y:
            self.setPos(float(x), -float(y))
        else:
            self.setPos(float(x), float(y))

        color = get_color_by_id(group_id, is_active)
        self.setBrush(QBrush(color))

        if self.is_active:
            self.setPen(QPen(Qt.GlobalColor.white, 2))
            self.setFlags(
                QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            )
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.setZValue(100)

            self.anim_wrapper = GraphicsItemAnimWrapper(self)
            self.pos_anim = QPropertyAnimation(self.anim_wrapper, b"pos")
            self.pos_anim.setDuration(300)
            self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        else:
            self.setPen(QPen(QColor(220, 220, 220), 1, Qt.PenStyle.SolidLine))
            self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
            self.setZValue(10)
            self.anim_wrapper = None

        # 标签
        self.text_item = QGraphicsTextItem(f"ID:{group_id}", self)
        font = QFont("Segoe UI", 8)
        font.setBold(True)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(-text_rect.width() / 2, -size / 2 - 15)
        self.text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

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
            self.is_active
            and change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
        ):
            if self.scene() and self.scene().mouseGrabberItem() == self:
                if self.on_move_callback:
                    if self.invert_y:
                        self.on_move_callback(int(value.x()), int(-value.y()))
                    else:
                        self.on_move_callback(int(value.x()), int(value.y()))
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if self.is_active:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            if self.pos_anim.state() == QPropertyAnimation.State.Running:
                self.pos_anim.stop()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_active:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)


class GridScene(QGraphicsScene):
    """带网格背景和坐标标注的场景"""

    def __init__(self, parent=None, show_labels=True, v_axis_label="Y"):
        super().__init__(parent)
        self.grid_size = 10
        self._show_labels = show_labels
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
        else:
            self._bg = QColor(245, 245, 245)
            self._grid_minor = QColor(220, 220, 220)
            self._grid_major = QColor(190, 190, 190)
            self._axis_x = QColor(80, 200, 80, 120)
            self._axis_y = QColor(80, 80, 200, 120)
            self._label_color = QColor(120, 120, 120)
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


# ── 主对话框 ──


class CoordinatePickerDialog(QDialog):
    """坐标选择对话框 - QFluentWidgets 原生组件"""

    VIEW_XY = "xy"
    VIEW_XZ = "xz"

    def __init__(self, target_group_id, all_groups_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"轨道布局规划 - ID: {target_group_id}")
        self.resize(1120, 780)

        self.target_id = target_group_id
        self.all_groups = all_groups_data
        self._view_mode = "xy"
        self._groups_items = {}
        self._target_item = None
        self._crosshair = None
        self._confirmed = False

        target_data = self.all_groups.get(target_group_id, {})
        coords = target_data.get("base_coords", ("0", "64", "0"))
        try:
            self.x, self.y, self.z = int(coords[0]), int(coords[1]), int(coords[2])
        except Exception:
            self.x, self.y, self.z = 0, 64, 0

        self._build_ui()
        self._refresh_scene()
        QTimer.singleShot(50, lambda: AnimationUtils.fade_in_entry(self))

    def _build_ui(self):
        dark = isDarkTheme()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        main = QHBoxLayout()
        main.setContentsMargins(12, 10, 12, 10)
        main.setSpacing(12)

        # ── 左侧控制面板 ──
        ctrl = CardWidget(self)
        ctrl.setFixedWidth(280)
        cl = QVBoxLayout(ctrl)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(10)

        # 标题行
        color_lbl = QLabel()
        color_lbl.setFixedSize(14, 14)
        c = get_color_by_id(self.target_id, True)
        color_lbl.setStyleSheet(
            f"background-color: rgb({c.red()},{c.green()},{c.blue()}); border-radius: 7px;"
        )
        title_row = QHBoxLayout()
        tt = SubtitleLabel(f"编辑 ID: {self.target_id}")
        title_row.addWidget(color_lbl)
        title_row.addWidget(tt)
        title_row.addStretch()
        cl.addLayout(title_row)

        # 坐标输入 (SpinBox)
        coord_group = QWidget()
        coord_grid = QGridLayout(coord_group)
        coord_grid.setContentsMargins(0, 0, 0, 0)
        coord_grid.setSpacing(8)

        self.spin_x = self._make_spin("X", "左右", (-30000000, 30000000), self.x)
        self.spin_y = self._make_spin("Y", "高度", (-64, 320), self.y)
        self.spin_z = self._make_spin("Z", "深度", (-30000000, 30000000), self.z)

        for row, (spin, label, tip) in enumerate([
            (self.spin_x, "X", "左右"),
            (self.spin_y, "Y", "高度"),
            (self.spin_z, "Z", "深度"),
        ]):
            lbl = BodyLabel(f"{label} ({tip})")
            lbl.setStyleSheet("font-size: 12px;")
            coord_grid.addWidget(lbl, row, 0)
            coord_grid.addWidget(spin, row, 1)

        self.spin_x.valueChanged.connect(self._on_spinbox_changed)
        self.spin_y.valueChanged.connect(self._on_spinbox_changed)
        self.spin_z.valueChanged.connect(self._on_z_changed)

        cl.addWidget(coord_group)

        # 视图切换 (SegmentedWidget)
        self.segWidget = SegmentedWidget(self)
        self.segWidget.addItem("xy", "侧视图 (X-Y)")
        self.segWidget.addItem("xz", "俯视图 (X-Z)")
        self.segWidget.setCurrentItem("xy")
        self.segWidget.currentItemChanged.connect(self._switch_view)
        cl.addWidget(self.segWidget)

        # 确定按钮
        self._btn_ok = PrimaryPushButton("确定位置", self)
        self._btn_ok.setFixedHeight(38)
        self._btn_ok.clicked.connect(self._confirm_position)
        cl.addWidget(self._btn_ok)

        self._confirm_label = CaptionLabel("")
        self._confirm_label.setStyleSheet("color: #107c10; font-weight: bold;")
        self._confirm_label.setVisible(False)
        cl.addWidget(self._confirm_label)

        # 完成按钮
        btn_done = PushButton("完成", self)
        btn_done.setFixedHeight(34)
        btn_done.clicked.connect(self._try_close)
        cl.addWidget(btn_done)

        # 操作提示
        info = CaptionLabel(
            "拖动方块或修改数值调整坐标\n"
            "滚轮缩放 | 右键拖动平移\n"
            "方向键微调 | Shift+方向键(\u00b110)\n"
            "R 重置视图 | +/- 缩放"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; margin-top: 8px; line-height: 1.5;")
        cl.addWidget(info)
        cl.addStretch(1)

        main.addWidget(ctrl)

        # ── 右侧视图区域 ──
        vc = QWidget()
        vc.setStyleSheet(f"background-color: {'#222' if dark else '#f8f8f8'}; border-radius: 8px;")
        vl = QVBoxLayout(vc)
        vl.setContentsMargins(4, 4, 4, 4)
        vl.setSpacing(4)

        # 工具栏 (TransparentToolButton)
        tbw = QWidget()
        tbw.setStyleSheet(f"background-color: {'#333' if dark else '#e8e8e8'}; border-radius: 6px;")
        tbh = QHBoxLayout(tbw)
        tbh.setContentsMargins(8, 4, 8, 4)
        tbh.setSpacing(4)

        self._add_tb_btn(tbh, FluentIcon.FIT_PAGE, "适应全部", self._fit_all)
        self._add_tb_btn(tbh, FluentIcon.BACK_TO_WINDOW, "重置视图", self._reset_view)
        tbh.addStretch()
        self._add_tb_btn(tbh, FluentIcon.ZOOM_IN, "放大", lambda: self.view.scale(1.25, 1.25))
        self._add_tb_btn(tbh, FluentIcon.ZOOM_OUT, "缩小", lambda: self.view.scale(1 / 1.25, 1 / 1.25))
        vl.addWidget(tbw)

        # 图形视图
        self.scene = GridScene()
        self.view = PickerGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.scale(3.0, 3.0)
        self.view.set_key_nudge_callback(self._on_key_nudge)
        vl.addWidget(self.view)
        main.addWidget(vc, 1)
        outer.addLayout(main)

        # ── 底部状态栏 ──
        sb = QWidget()
        sb.setStyleSheet(f"background-color: {'#f0f0f0' if dark else '#f0f0f0'}; border-top: 1px solid {_border()};")
        sl = QHBoxLayout(sb)
        sl.setContentsMargins(20, 6, 20, 6)
        self.status_coord = CaptionLabel(
            f"X: {self.x}  |  Y: {self.y}  |  Z: {self.z}"
        )
        self.status_coord.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 10pt;"
            " color: #444; font-weight: 600;"
        )
        sl.addWidget(self.status_coord)
        sl.addStretch()
        self.status_view = CaptionLabel("视图: 侧视图 (X-Y)")
        self.status_view.setStyleSheet("color: #888;")
        sl.addWidget(self.status_view)
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

    # ── 场景刷新 ──

    def _refresh_scene(self):
        self.scene.clear()
        self._groups_items = {}
        is_xy = self._view_mode == "xy"

        for g_id, data in self.all_groups.items():
            coords = data.get("base_coords", ("0", "0", "0"))
            try:
                gx, gy, gz = int(coords[0]), int(coords[1]), int(coords[2])
            except Exception:
                gx, gy, gz = 0, 64, 0
            vx = float(gx)
            vy = -float(gy if is_xy else gz)

            if g_id != self.target_id:
                item = TrackGroupItem(
                    vx, vy, g_id, is_active=False, invert_y=False
                )
                self.scene.addItem(item)
                self._groups_items[g_id] = item
            else:
                self._target_item = TrackGroupItem(
                    vx,
                    vy,
                    self.target_id,
                    is_active=True,
                    on_move_callback=self._on_point_dragged,
                    invert_y=False,
                )
                self.scene.addItem(self._target_item)
                self._groups_items[g_id] = self._target_item

        if self._target_item:
            self._crosshair = CrosshairItem(size=22)
            self._crosshair.setPos(self._target_item.pos())
            self.scene.addItem(self._crosshair)
            self.view.centerOn(self._target_item.pos())
        else:
            self.view.centerOn(QPointF(0, 0))

    # ── 视图切换 ──

    def _switch_view(self, key):
        if self._view_mode == key:
            return
        self._view_mode = key
        name = "侧视图 (X-Y)" if key == "xy" else "俯视图 (X-Z)"
        self.status_view.setText(f"视图: {name}")
        self._refresh_scene()

    # ── 坐标更新 ──

    def _on_coords_modified(self):
        if self._confirmed:
            self._confirmed = False
            self._btn_ok.setText("确定位置")
            self._confirm_label.setVisible(False)

    def _on_point_dragged(self, view_x, view_y):
        mc_x = int(view_x)
        mc_v = int(-view_y)
        self.spin_x.blockSignals(True)
        self.spin_x.setValue(mc_x)
        self.spin_x.blockSignals(False)
        if self._view_mode == "xy":
            self.spin_y.blockSignals(True)
            self.spin_y.setValue(mc_v)
            self.spin_y.blockSignals(False)
        else:
            self.spin_z.blockSignals(True)
            self.spin_z.setValue(mc_v)
            self.spin_z.blockSignals(False)
        self._sync_crosshair()
        self._update_status()
        self._on_coords_modified()

    def _on_spinbox_changed(self):
        x = self.spin_x.value()
        v = self.spin_y.value() if self._view_mode == "xy" else self.spin_z.value()
        if self._target_item:
            self._target_item.move_smoothly_to(float(x), -float(v))
        self._sync_crosshair()
        self._update_status()
        self._on_coords_modified()

    def _on_z_changed(self):
        if self._view_mode == "xz":
            self._on_spinbox_changed()
        self._update_status()

    def _sync_crosshair(self):
        if self._crosshair and self._target_item:
            p = self._target_item.pos()
            self._crosshair.move_smoothly_to(p.x(), p.y())

    def _update_status(self):
        self.status_coord.setText(
            f"X: {self.spin_x.value()}  |  Y: {self.spin_y.value()}  |  Z: {self.spin_z.value()}"
        )

    # ── 键盘微调 ──

    def _on_key_nudge(self, dx, dy, reset_view=False):
        if reset_view:
            self._reset_view()
            return
        if not self._target_item:
            return
        cur = self._target_item.pos()
        nx, ny = cur.x() + dx, cur.y() + dy
        self._target_item.move_smoothly_to(nx, ny)
        self._sync_crosshair()
        mc_x, mc_v = int(nx), int(-ny)
        self.spin_x.blockSignals(True)
        self.spin_x.setValue(mc_x)
        self.spin_x.blockSignals(False)
        if self._view_mode == "xy":
            self.spin_y.blockSignals(True)
            self.spin_y.setValue(mc_v)
            self.spin_y.blockSignals(False)
        else:
            self.spin_z.blockSignals(True)
            self.spin_z.setValue(mc_v)
            self.spin_z.blockSignals(False)
        self._update_status()
        self._on_coords_modified()

    # ── 确认与关闭 ──

    def _confirm_position(self):
        self._confirmed = True
        self._confirm_label.setText("\u2713 位置已保存，可切换视角查看")
        self._confirm_label.setVisible(True)
        self._btn_ok.setText("\u2713 已保存")

    def _try_close(self):
        if self._confirmed:
            self.accept()
        else:
            self._confirm_label.setText("\u26a0 请先点击「确定位置」保存坐标")
            self._confirm_label.setStyleSheet(
                "color: #d83b01; font-weight: bold;"
            )
            self._confirm_label.setVisible(True)

    def reject(self):
        if self._confirmed:
            self.accept()
        else:
            super().reject()

    # ── 视图控制 ──

    def _fit_all(self):
        if not self._groups_items:
            return
        rect = QRectF()
        for item in self._groups_items.values():
            rect = rect.united(QRectF(item.pos(), item.boundingRect().size()))
        if not rect.isEmpty():
            rect.adjust(-50, -50, 50, 50)
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def _reset_view(self):
        self.view.resetTransform()
        self.view.scale(3.0, 3.0)
        if self._target_item:
            self.view.centerOn(self._target_item.pos())

    # ── 输出 ──

    def get_coords(self):
        return self.spin_x.value(), self.spin_y.value(), self.spin_z.value()

    def wheelEvent(self, event):
        if self.view.underMouse():
            zoom_in = event.angleDelta().y() > 0
            factor = 1.15 if zoom_in else 1 / 1.15
            self.view.scale(factor, factor)
        else:
            super().wheelEvent(event)
