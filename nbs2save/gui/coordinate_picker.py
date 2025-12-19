import sys
import math
from PyQt6.QtWidgets import (QDialog, QPushButton, QGraphicsView, QGraphicsScene, 
                             QGraphicsRectItem, QGraphicsItem, QLabel, QSpinBox, 
                             QGroupBox, QGridLayout, QHBoxLayout, QGraphicsTextItem)
from PyQt6.QtCore import Qt, QPointF, QRectF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont

# 导入新写的动画工具
from .animations import AnimationUtils, GraphicsItemAnimWrapper

def get_color_by_id(group_id, is_active=False):
    if is_active:
        return QColor(0, 120, 255, 230)
    hue = (group_id * 137.508) % 360
    return QColor.fromHsl(int(hue), 200, 140, 180)

class TrackGroupItem(QGraphicsRectItem):
    """代表轨道组位置的图元"""
    def __init__(self, x, y, group_id, is_active=True, on_move_callback=None):
        size = 12 
        super().__init__(-size/2, -size/2, size, size)
        
        self.is_active = is_active
        self.on_move_callback = on_move_callback
        self.group_id = group_id
        
        self.setPos(float(x), -float(y))
        
        color = get_color_by_id(group_id, is_active)
        self.setBrush(QBrush(color))
        
        if self.is_active:
            self.setPen(QPen(Qt.GlobalColor.white, 2))
            self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                          QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.setZValue(100)
            
            # --- 动画包装器 ---
            self.anim_wrapper = GraphicsItemAnimWrapper(self)
            self.pos_anim = QPropertyAnimation(self.anim_wrapper, b"pos")
            self.pos_anim.setDuration(400) # 动画时长 400ms
            self.pos_anim.setEasingCurve(QEasingCurve.Type.OutBack) # 略微回弹的效果
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
        self.text_item.setPos(-text_rect.width() / 2, -size/2 - 15)
        self.text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def move_smoothly_to(self, x, y):
        """平滑移动到指定位置 (x, -y)"""
        if self.anim_wrapper:
            self.pos_anim.stop()
            self.pos_anim.setStartValue(self.pos())
            self.pos_anim.setEndValue(QPointF(float(x), -float(y)))
            self.pos_anim.start()
        else:
            self.setPos(float(x), -float(y))

    def itemChange(self, change, value):
        # 仅在鼠标拖动引起的位置变化时触发回调
        # 如果是动画引起的变化，我们需要区分（这里简单处理，动画也会触发，但 SpinBox 会暂时 block signal）
        if self.is_active and change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.scene() and self.scene().mouseGrabberItem() == self:
                 if self.on_move_callback:
                    self.on_move_callback(int(value.x()), int(-value.y()))
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if self.is_active:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            # 停止当前可能正在进行的动画，防止冲突
            if(self.pos_anim.state() == QPropertyAnimation.State.Running):
                self.pos_anim.stop()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_active:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

class GridScene(QGraphicsScene):
    """带有网格背景的场景"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 10  
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30))) 

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        # 优化绘制性能，只绘制视野内的
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
        
        # 绘制 大网格 (每50格)
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

class CoordinatePickerDialog(QDialog):
    """坐标选择对话框"""
    def __init__(self, target_group_id, all_groups_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"轨道布局规划 (侧视图 X-Y) - 正在编辑 ID: {target_group_id}")
        self.resize(1100, 750)
        
        self.target_id = target_group_id
        self.all_groups = all_groups_data
        
        target_data = self.all_groups.get(target_group_id, {})
        coords = target_data.get('base_coords', ("0", "64", "0"))
        try:
            self.x = int(coords[0])
            self.y = int(coords[1])
            self.z = int(coords[2])
        except:
            self.x, self.y, self.z = 0, 64, 0
        
        self.init_ui()
        
        # 启动入场动画
        AnimationUtils.fade_in_entry(self)

    def init_ui(self):
        layout = QHBoxLayout(self)

        # === 左侧控制 ===
        control_panel = QGroupBox("坐标调整")
        control_panel.setStyleSheet("QGroupBox { border: none; background-color: #f3f3f3; }")
        control_layout = QGridLayout()
        control_layout.setSpacing(15)
        
        # 标题栏
        color_label = QLabel()
        color_label.setFixedSize(16, 16)
        c = get_color_by_id(self.target_id, True)
        color_label.setStyleSheet(f"background-color: rgb({c.red()},{c.green()},{c.blue()}); border-radius: 4px;")
        
        title_box = QHBoxLayout()
        title_text = QLabel(f"当前编辑: ID {self.target_id}")
        title_text.setStyleSheet("font-weight: bold; font-size: 11pt;")
        title_box.addWidget(color_label)
        title_box.addWidget(title_text)
        title_box.addStretch()
        control_layout.addLayout(title_box, 0, 0, 1, 2)
        
        # 坐标输入
        control_layout.addWidget(QLabel("X (左右):"), 1, 0)
        self.spin_x = QSpinBox()
        self.spin_x.setRange(-30000000, 30000000)
        self.spin_x.setValue(self.x)
        self.spin_x.valueChanged.connect(self.update_from_spinbox)
        control_layout.addWidget(self.spin_x, 1, 1)

        control_layout.addWidget(QLabel("Y (高度):"), 2, 0)
        self.spin_y = QSpinBox()
        self.spin_y.setRange(-64, 320)
        self.spin_y.setValue(self.y)
        self.spin_y.valueChanged.connect(self.update_from_spinbox)
        control_layout.addWidget(self.spin_y, 2, 1)

        control_layout.addWidget(QLabel("Z (深度):"), 3, 0)
        self.spin_z = QSpinBox()
        self.spin_z.setRange(-30000000, 30000000)
        self.spin_z.setValue(self.z)
        # Z轴修改不影响视图
        control_layout.addWidget(self.spin_z, 3, 1)
        
        # 确定按钮
        self.btn_confirm = QPushButton("确定位置")
        # 样式已在 FluentButton 或全局样式中定义，这里微调
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #0078d4; color: white; border-radius: 6px; 
                padding: 10px; font-weight: bold; font-size: 10pt;
            }
            QPushButton:hover { background-color: #1084d0; }
            QPushButton:pressed { background-color: #006abc; }
        """)
        self.btn_confirm.clicked.connect(self.accept)
        control_layout.addWidget(self.btn_confirm, 5, 0, 1, 2)
        
        info_label = QLabel("提示:\n• 修改左侧 X/Y 数值，视图中的方块会平滑移动。\n• 右键拖动平移视图。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; margin-top: 10px; font-size: 9pt;")
        control_layout.addWidget(info_label, 6, 0, 1, 2)

        control_layout.setRowStretch(7, 1) 
        control_panel.setLayout(control_layout)
        control_panel.setFixedWidth(260)

        # === 右侧视图 ===
        self.scene = GridScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.scale(3.0, 3.0) 
        
        self.target_item = None
        
        # 绘制
        for g_id, data in self.all_groups.items():
            coords = data.get('base_coords', ("0", "0", "0"))
            try:
                gx, gy, gz = int(coords[0]), int(coords[1]), int(coords[2])
            except:
                gx, gy, gz = 0, 64, 0
            
            if g_id != self.target_id:
                ref_item = TrackGroupItem(gx, gy, g_id, is_active=False)
                self.scene.addItem(ref_item)
        
        self.target_item = TrackGroupItem(self.x, self.y, self.target_id, is_active=True, on_move_callback=self.on_point_dragged)
        self.scene.addItem(self.target_item)
        
        self.view.centerOn(self.x, -self.y)

        layout.addWidget(control_panel)
        layout.addWidget(self.view)

    def on_point_dragged(self, x, y):
        """鼠标拖动 -> 更新数值 (阻断信号防止循环递归)"""
        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)
        self.spin_x.setValue(x)
        self.spin_y.setValue(y)
        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)

    def update_from_spinbox(self):
        """数值改变 -> 平滑移动图元"""
        x = self.spin_x.value()
        y = self.spin_y.value()
        if self.target_item:
            # 使用平滑移动方法
            self.target_item.move_smoothly_to(x, y)
            # 可选：让视图跟随 (如果希望视野一直锁定目标)
            # self.view.centerOn(float(x), -float(y))

    def get_coords(self):
        return self.spin_x.value(), self.spin_y.value(), self.spin_z.value()

    def wheelEvent(self, event):
        if self.view.underMouse():
            zoom_in = event.angleDelta().y() > 0
            factor = 1.15 if zoom_in else 1 / 1.15
            self.view.scale(factor, factor)
        else:
            super().wheelEvent(event)