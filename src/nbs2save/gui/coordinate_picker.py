from PyQt6.QtWidgets import (
    QDialog,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsItem,
    QLabel,
    QSpinBox,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QToolButton,
    QFrame,
    QGraphicsTextItem,
)
from PyQt6.QtCore import Qt, QPointF, QPropertyAnimation, QEasingCurve, QRectF, QTimer
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QKeyEvent

# 导入新写的动画工具
from .animations import AnimationUtils, GraphicsItemAnimWrapper


def get_color_by_id(group_id, is_active=False):
    if is_active:
        return QColor(0, 120, 255, 230)
    hue = (group_id * 137.508) % 360
    return QColor.fromHsl(int(hue), 200, 140, 180)


class CrosshairItem(QGraphicsItem):
    """十字准星 �C 指示当前精确位置"""

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
    """代表轨道组位置的图元"""

    def __init__(self, x, y, group_id, is_active=True, on_move_callback=None, invert_y=True):
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

            # --- 动画包装器 ---
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
        """平滑移动到指定位置（视图坐标）"""
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
    """带有网格背景和坐标标注的场景"""

    def __init__(self, parent=None, show_labels=True, v_axis_label="Y"):
        super().__init__(parent)
        self.grid_size = 10
        self._show_labels = show_labels
        self.v_axis_label = v_axis_label
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)

        # 绘制细网格
        lines = []
        for x in range(left, int(rect.right()), self.grid_size):
            lines.append(QPointF(x, rect.top()))
            lines.append(QPointF(x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self.grid_size):
            lines.append(QPointF(rect.left(), y))
            lines.append(QPointF(rect.right(), y))

        pen = QPen(QColor(50, 50, 50))
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawLines(lines)

        # 绘制大网格 (每50格)
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

        pen_big = QPen(QColor(70, 70, 70))
        pen_big.setWidth(1)
        painter.setPen(pen_big)
        painter.drawLines(big_grid_lines)

        # 轴线
        painter.setPen(QPen(QColor(100, 255, 100, 100), 2))
        painter.drawLine(int(rect.left()), 0, int(rect.right()), 0)
        painter.setPen(QPen(QColor(100, 100, 255, 100), 2))
        painter.drawLine(0, int(rect.top()), 0, int(rect.bottom()))

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if not self._show_labels:
            return
        painter.setPen(QPen(QColor(100, 100, 100), 1))
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
                label = str(y)  # 视图垂直轴：Y向下或Z向下（负值）
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(label)
                painter.drawText(QPointF(-tw - 4, y + 4), label)


class PickerGraphicsView(QGraphicsView):
    """支持键盘方向键微调坐标 + 鼠标滚轮缩放"""

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


class CoordinatePickerDialog(QDialog):
    """完善的坐标选择对话框 �C 双视图、键盘微调、十字准星"""

    VIEW_XY = "xy"
    VIEW_XZ = "xz"

    def __init__(self, target_group_id, all_groups_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"轨道布局规划 - 正在编辑 ID: {target_group_id}")
        self.resize(1120, 780)

        self.target_id = target_group_id
        self.all_groups = all_groups_data
        self._view_mode = "xy"
        self._groups_items = {}
        self._target_item = None
        self._crosshair = None
        self._confirmed = False  # 用户是否已确认过位置

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
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        main = QHBoxLayout()
        main.setContentsMargins(12, 10, 12, 10)
        main.setSpacing(12)

        # ── 左侧控制面板 ──
        ctrl = QGroupBox("坐标调整")
        ctrl.setStyleSheet(
            "QGroupBox { border: none; background-color: #f5f5f5; border-radius: 8px; padding: 14px; }"
        )
        cl = QGridLayout()
        cl.setSpacing(8)

        # 标题
        color_lbl = QLabel()
        color_lbl.setFixedSize(14, 14)
        c = get_color_by_id(self.target_id, True)
        color_lbl.setStyleSheet(
            f"background-color: rgb({c.red()},{c.green()},{c.blue()}); border-radius: 3px;"
        )
        tb = QHBoxLayout()
        tt = QLabel(f"编辑 ID: {self.target_id}")
        tt.setStyleSheet("font-weight: bold; font-size: 11pt; color: #333;")
        tb.addWidget(color_lbl)
        tb.addWidget(tt)
        tb.addStretch()
        cl.addLayout(tb, 0, 0, 1, 3)
        cl.addWidget(self._sep(), 1, 0, 1, 3)

        self.spin_x = self._add_coord(cl, 2, "X (左右):", (-30000000, 30000000), self.x)
        self.spin_y = self._add_coord(cl, 3, "Y (高度):", (-64, 320), self.y)
        self.spin_z = self._add_coord(cl, 4, "Z (深度):", (-30000000, 30000000), self.z)

        self.spin_x.valueChanged.connect(self._on_spinbox_changed)
        self.spin_y.valueChanged.connect(self._on_spinbox_changed)
        self.spin_z.valueChanged.connect(self._on_z_changed)

        cl.addWidget(self._sep(), 5, 0, 1, 3)

        self.btn_xy = self._make_view_toggle("侧视图 (X-Y)", "xy")
        self.btn_xz = self._make_view_toggle("俯视图 (X-Z)", "xz")
        self.btn_xy.setChecked(True)
        self._update_view_btn_styles()
        vb = QHBoxLayout()
        vb.setSpacing(6)
        vb.addWidget(self.btn_xy)
        vb.addWidget(self.btn_xz)
        cl.addLayout(vb, 6, 0, 1, 3)

        cl.addWidget(self._sep(), 7, 0, 1, 3)
        btn_ok = QPushButton("确定位置")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setMinimumHeight(38)
        btn_ok.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; border-radius: 6px;"
            " padding: 10px; font-weight: bold; font-size: 10pt; }"
            " QPushButton:hover { background-color: #1084d0; }"
            " QPushButton:pressed { background-color: #006abc; }"
        )
        btn_ok.clicked.connect(self._confirm_position)
        self._btn_ok = btn_ok
        cl.addWidget(btn_ok, 8, 0, 1, 3)

        self._confirm_label = QLabel("")
        self._confirm_label.setStyleSheet(
            "color: #107c10; font-size: 9pt; font-weight: bold;"
            " background: transparent; padding: 2px 0;"
        )
        self._confirm_label.setVisible(False)
        cl.addWidget(self._confirm_label, 9, 0, 1, 3)

        btn_done = QPushButton("完成")
        btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_done.setMinimumHeight(34)
        btn_done.setStyleSheet(
            "QPushButton { background-color: #e0e0e0; color: #333; border-radius: 6px;"
            " padding: 8px; font-size: 9pt; }"
            " QPushButton:hover { background-color: #d0d0d0; }"
            " QPushButton:pressed { background-color: #c0c0c0; }"
        )
        btn_done.clicked.connect(self._try_close)
        cl.addWidget(btn_done, 10, 0, 1, 3)

        info = QLabel(
            "操作提示:\n"
            "\u2022 拖动方块或修改数值调整坐标\n"
            "\u2022 滚轮缩放 | 右键拖动平移\n"
            "\u2022 方向键微调(\u00b11) | Shift+方向键(\u00b110)\n"
            "\u2022 R键重置视图 | +/-缩放"
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "color: #888; margin-top: 10px; font-size: 8pt;"
            " line-height: 1.4; background: transparent;"
        )
        cl.addWidget(info, 11, 0, 1, 3)
        cl.setRowStretch(12, 1)
        ctrl.setLayout(cl)
        ctrl.setFixedWidth(275)
        main.addWidget(ctrl)

        # ── 右侧视图区域 ──
        vc = QWidget()
        vc.setStyleSheet("background-color: #222; border-radius: 8px;")
        vl = QVBoxLayout(vc)
        vl.setContentsMargins(4, 4, 4, 4)
        vl.setSpacing(4)

        # 工具栏
        tbw = QWidget()
        tbw.setStyleSheet("background-color: #333; border-radius: 6px;")
        tbh = QHBoxLayout(tbw)
        tbh.setContentsMargins(8, 4, 8, 4)
        tbh.setSpacing(6)
        tbh.addWidget(self._tb_btn("适应全部", self._fit_all))
        tbh.addWidget(self._tb_btn("重置视图", self._reset_view))
        tbh.addStretch()
        tbh.addWidget(self._tb_btn("+", lambda: self.view.scale(1.25, 1.25)))
        tbh.addWidget(self._tb_btn("-", lambda: self.view.scale(1 / 1.25, 1 / 1.25)))
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
        sb.setStyleSheet(
            "background-color: #f0f0f0; border-top: 1px solid #ddd;"
        )
        sl = QHBoxLayout(sb)
        sl.setContentsMargins(20, 6, 20, 6)
        self.status_coord = QLabel(
            f"X: {self.x}  |  Y: {self.y}  |  Z: {self.z}"
        )
        self.status_coord.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 10pt;"
            " color: #444; font-weight: 600; background: transparent;"
        )
        sl.addWidget(self.status_coord)
        sl.addStretch()
        self.status_view = QLabel("视图: 侧视图 (X-Y)")
        self.status_view.setStyleSheet(
            "font-size: 9pt; color: #888; background: transparent;"
        )
        sl.addWidget(self.status_view)
        outer.addWidget(sb)

    # ── 辅助 UI 方法 ──

    @staticmethod
    def _sep():
        s = QFrame()
        s.setFrameShape(QFrame.Shape.HLine)
        s.setStyleSheet("background-color: #ddd; max-height: 1px;")
        return s

    def _add_coord(self, layout, row, label, sr, dv):
        layout.addWidget(QLabel(label), row, 0)
        spin = QSpinBox()
        spin.setRange(*sr)
        spin.setValue(dv)
        layout.addWidget(spin, row, 1)
        bs = QToolButton(); bs.setText("-")
        bs.clicked.connect(lambda _, s=spin: self._nudge(s, -1))
        ba = QToolButton(); ba.setText("+")
        ba.clicked.connect(lambda _, s=spin: self._nudge(s, 1))
        hl = QHBoxLayout(); hl.setSpacing(2)
        hl.addWidget(bs); hl.addWidget(ba)
        layout.addLayout(hl, row, 2)
        return spin

    def _make_view_toggle(self, text, mode):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._switch_view(mode))
        return btn

    def _tb_btn(self, text, slot):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(26)
        btn.setStyleSheet(
            "QPushButton { background-color: #444; color: #ddd; border: none;"
            " border-radius: 4px; padding: 2px 10px; font-size: 9pt; }"
            " QPushButton:hover { background-color: #555; }"
        )
        btn.clicked.connect(slot)
        return btn

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
                item = TrackGroupItem(vx, vy, g_id, is_active=False, invert_y=False)
                self.scene.addItem(item)
                self._groups_items[g_id] = item
            else:
                self._target_item = TrackGroupItem(
                    vx, vy, self.target_id, is_active=True,
                    on_move_callback=self._on_point_dragged, invert_y=False
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

    def _switch_view(self, mode):
        if self._view_mode == mode:
            return
        self._view_mode = mode
        self._update_view_btn_styles()
        name = "侧视图 (X-Y)" if mode == "xy" else "俯视图 (X-Z)"
        self.status_view.setText(f"视图: {name}")
        self._refresh_scene()

    def _update_view_btn_styles(self):
        act = (
            "QPushButton { background-color: #0078d4; color: white; border: none;"
            " border-radius: 4px; padding: 6px 10px; font-size: 9pt; font-weight: bold; }"
        )
        inact = (
            "QPushButton { background-color: #e0e0e0; color: #555; border: none;"
            " border-radius: 4px; padding: 6px 10px; font-size: 9pt; }"
            " QPushButton:hover { background-color: #d0d0d0; }"
        )
        self.btn_xy.setStyleSheet(act if self._view_mode == "xy" else inact)
        self.btn_xz.setStyleSheet(act if self._view_mode == "xz" else inact)

    # ── 坐标更新 ──

    def _on_coords_modified(self):
        """坐标被修改时重置确认状态"""
        if self._confirmed:
            self._confirmed = False
            self._btn_ok.setStyleSheet(
                "QPushButton { background-color: #0078d4; color: white; border-radius: 6px;"
                " padding: 10px; font-weight: bold; font-size: 10pt; }"
                " QPushButton:hover { background-color: #1084d0; }"
                " QPushButton:pressed { background-color: #006abc; }"
            )
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

    @staticmethod
    def _nudge(spin, delta):
        spin.setValue(spin.value() + delta)

    # ── 确认与关闭 ──

    def _confirm_position(self):
        """保存当前坐标但不关闭对话框"""
        self._confirmed = True
        self._confirm_label.setText("✓ 位置已保存，可切换视角查看")
        self._confirm_label.setVisible(True)
        # 按钮视觉反馈
        self._btn_ok.setStyleSheet(
            "QPushButton { background-color: #107c10; color: white; border-radius: 6px;"
            " padding: 10px; font-weight: bold; font-size: 10pt; }"
        )
        self._btn_ok.setText("✓ 已保存")

    def _try_close(self):
        """尝试关闭对话框：若已确认则保存并关闭"""
        if self._confirmed:
            self.accept()
        else:
            self._confirm_label.setText("⚠ 请先点击「确定位置」保存坐标")
            self._confirm_label.setStyleSheet(
                "color: #d83b01; font-size: 9pt; font-weight: bold;"
                " background: transparent; padding: 2px 0;"
            )
            self._confirm_label.setVisible(True)

    def reject(self):
        """ESC 或点击 X 关闭时的处理"""
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
