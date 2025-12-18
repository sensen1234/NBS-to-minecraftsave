import sys
import math
from PyQt6.QtWidgets import (QDialog, QPushButton, QGraphicsView, QGraphicsScene, 
                             QGraphicsRectItem, QGraphicsItem, QLabel, QSpinBox, 
                             QGroupBox, QGridLayout, QHBoxLayout, QGraphicsTextItem)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont

def get_color_by_id(group_id, is_active=False):
    """
    根据ID生成固定颜色
    使用黄金角度近似算法，确保相邻ID颜色差异明显
    """
    if is_active:
        # 当前选中项：使用特殊的亮蓝色，或者保留ID色但加高亮
        # 这里为了突出，当前选中项统一使用高亮蓝，方便寻找
        return QColor(0, 120, 255, 230)
    
    # 黄金角度生成色相，确保颜色分布均匀
    hue = (group_id * 137.508) % 360
    # 饱和度中等，亮度中等，防止太刺眼
    return QColor.fromHsl(int(hue), 200, 140, 180) # Alpha=180 半透明

class TrackGroupItem(QGraphicsRectItem):
    """
    代表轨道组位置的图元 (在 X-Y 平面上)
    """
    def __init__(self, x, y, group_id, is_active=True, on_move_callback=None):
        # [修改] 尺寸缩小，方便精准操作 (从40改为12)
        size = 12 
        super().__init__(-size/2, -size/2, size, size)
        
        self.is_active = is_active
        self.on_move_callback = on_move_callback
        self.group_id = group_id
        
        # 坐标映射：Minecraft Y -> Graphics -Y
        self.setPos(float(x), -float(y))
        
        # [修改] 颜色逻辑
        color = get_color_by_id(group_id, is_active)
        self.setBrush(QBrush(color))
        
        if self.is_active:
            # 当前编辑点：加粗白色边框
            self.setPen(QPen(Qt.GlobalColor.white, 2))
            self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                          QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.setZValue(100) # 最上层
        else:
            # 参照点：细虚线边框
            self.setPen(QPen(QColor(220, 220, 220), 1, Qt.PenStyle.SolidLine))
            self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable) 
            self.setZValue(10)

        # [修改] ID 标签显示在方块上方，避免遮挡方块本体
        self.text_item = QGraphicsTextItem(f"ID:{group_id}", self)
        font = QFont()
        font.setPixelSize(12) # 字体调小
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        
        # 计算文字位置：放在方块上方 15 像素处
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(-text_rect.width() / 2, -size/2 - 15)
        
        # 禁用文字响应鼠标，防止误触文字拖不动方块
        self.text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def itemChange(self, change, value):
        if self.is_active and change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.on_move_callback:
                # 实时回调
                self.on_move_callback(int(value.x()), int(-value.y()))
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if self.is_active:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_active:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

class GridScene(QGraphicsScene):
    """带有网格背景的场景 (X-Y视图)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # [修改] 网格间距缩小到 10，适应 20-100 格的排版需求
        self.grid_size = 10  
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30))) 

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        
        lines = []
        # 普通网格线
        for x in range(left, int(rect.right()), self.grid_size):
            lines.append(QPointF(x, rect.top()))
            lines.append(QPointF(x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self.grid_size):
            lines.append(QPointF(rect.left(), y))
            lines.append(QPointF(rect.right(), y))

        # 绘制深色细网格
        pen = QPen(QColor(50, 50, 50))
        pen.setWidth(0) # Cosmetic pen (1 pixel)
        painter.setPen(pen)
        painter.drawLines(lines)
        
        # 绘制 大网格 (每50格一条粗线，方便计数)
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
        
        # 绘制轴线
        pen_origin = QPen(QColor(100, 255, 100, 100)) # 绿色 X轴
        pen_origin.setWidth(2)
        painter.setPen(pen_origin)
        painter.drawLine(int(rect.left()), 0, int(rect.right()), 0) 
        
        pen_y = QPen(QColor(100, 100, 255, 100)) # 蓝色 Y轴
        pen_y.setWidth(2)
        painter.setPen(pen_y)
        painter.drawLine(0, int(rect.top()), 0, int(rect.bottom())) 

class CoordinatePickerDialog(QDialog):
    """坐标选择对话框 (X-Y 平面视图)"""
    def __init__(self, target_group_id, all_groups_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"轨道布局规划 (侧视图 X-Y) - 正在编辑 ID: {target_group_id}")
        self.resize(1100, 750)
        
        self.target_id = target_group_id
        self.all_groups = all_groups_data
        
        # 获取数据
        target_data = self.all_groups.get(target_group_id, {})
        coords = target_data.get('base_coords', ("0", "64", "0"))
        try:
            self.x = int(coords[0])
            self.y = int(coords[1])
            self.z = int(coords[2])
        except:
            self.x, self.y, self.z = 0, 64, 0
        
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # === 左侧：控制面板 ===
        control_panel = QGroupBox("坐标调整")
        control_layout = QGridLayout()
        
        # 显示当前颜色的色块（可选）
        color_label = QLabel()
        color_label.setFixedSize(20, 20)
        c = get_color_by_id(self.target_id, True)
        color_label.setStyleSheet(f"background-color: rgb({c.red()},{c.green()},{c.blue()}); border: 1px solid white;")
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel(f"当前编辑: ID {self.target_id}"))
        title_layout.addWidget(color_label)
        title_layout.addStretch()
        
        control_layout.addLayout(title_layout, 0, 0, 1, 2)
        
        # X
        control_layout.addWidget(QLabel("X (左右):"), 1, 0)
        self.spin_x = QSpinBox()
        self.spin_x.setRange(-30000000, 30000000)
        self.spin_x.setValue(self.x)
        self.spin_x.valueChanged.connect(self.update_from_spinbox)
        control_layout.addWidget(self.spin_x, 1, 1)

        # Y
        control_layout.addWidget(QLabel("Y (高度):"), 2, 0)
        self.spin_y = QSpinBox()
        self.spin_y.setRange(-64, 320)
        self.spin_y.setValue(self.y)
        self.spin_y.valueChanged.connect(self.update_from_spinbox)
        control_layout.addWidget(self.spin_y, 2, 1)

        # Z
        control_layout.addWidget(QLabel("Z (深度):"), 3, 0)
        self.spin_z = QSpinBox()
        self.spin_z.setRange(-30000000, 30000000)
        self.spin_z.setValue(self.z)
        self.spin_z.valueChanged.connect(self.update_z_only) 
        control_layout.addWidget(self.spin_z, 3, 1)
        
        self.btn_confirm = QPushButton("确定位置")
        self.btn_confirm.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        self.btn_confirm.clicked.connect(self.accept)
        control_layout.addWidget(self.btn_confirm, 5, 0, 1, 2)
        
        info_label = QLabel("操作提示:\n• 不同ID拥有不同颜色\n• 小方块代表起始点(12px)\n• 网格间距: 10格\n• 滚轮缩放，右键平移")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888888; margin-top: 20px; font-size: 9pt;")
        control_layout.addWidget(info_label, 6, 0, 1, 2)

        control_layout.setRowStretch(7, 1) 
        control_panel.setLayout(control_layout)
        control_panel.setFixedWidth(240)

        # === 右侧：视图 ===
        self.scene = GridScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # [修改] 默认放大视图，使1个方块看起来足够大
        # 3.0倍缩放，配合10px的网格，视觉效果清晰
        self.view.scale(3.0, 3.0) 
        
        self.target_item = None
        
        # 绘制其他组
        for g_id, data in self.all_groups.items():
            coords = data.get('base_coords', ("0", "0", "0"))
            try:
                gx, gy, gz = int(coords[0]), int(coords[1]), int(coords[2])
            except:
                gx, gy, gz = 0, 64, 0
            
            if g_id == self.target_id:
                continue
            else:
                ref_item = TrackGroupItem(gx, gy, g_id, is_active=False)
                self.scene.addItem(ref_item)
        
        # 绘制当前组
        self.target_item = TrackGroupItem(self.x, self.y, self.target_id, is_active=True, on_move_callback=self.on_point_dragged)
        self.scene.addItem(self.target_item)
        
        # 聚焦
        self.view.centerOn(self.x, -self.y)

        layout.addWidget(control_panel)
        layout.addWidget(self.view)

    def on_point_dragged(self, x, y):
        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)
        self.spin_x.setValue(x)
        self.spin_y.setValue(y)
        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)

    def update_from_spinbox(self):
        x = self.spin_x.value()
        y = self.spin_y.value()
        if self.target_item:
            self.target_item.setPos(float(x), -float(y))
            self.view.ensureVisible(self.target_item)

    def update_z_only(self):
        pass

    def get_coords(self):
        return self.spin_x.value(), self.spin_y.value(), self.spin_z.value()

    def wheelEvent(self, event):
        if self.view.underMouse():
            zoom_in = event.angleDelta().y() > 0
            factor = 1.15 if zoom_in else 1 / 1.15
            self.view.scale(factor, factor)
        else:
            super().wheelEvent(event)