from PyQt6.QtWidgets import (
    QPushButton, QLineEdit, QComboBox, QGroupBox, QWidget, QSizePolicy, 
    QVBoxLayout, QHBoxLayout, QApplication, QGraphicsDropShadowEffect, QStyle,
    QStackedWidget, QLabel
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, 
    QParallelAnimationGroup, QPoint, QObject, pyqtProperty, QRectF
)
from PyQt6.QtGui import (
    QPalette, QColor, QPainter, QBrush, QPen, QIcon, QFont, QTextOption
)

from .animations import ColorAnimWrapper

# ==========================================
# 🎨 配色方案 (UI 优化版)
# ==========================================

# 1. 主题色 (Primary - 亮蓝)
# 用于 "开始转换", "选点", "添加"
PRIMARY_BG    = QColor(0, 120, 212)
PRIMARY_HOVER = QColor(20, 135, 230)
PRIMARY_PRESS = QColor(0, 90, 180)

# 2. 浅灰色系 (Standard - 优化版)
# 用于 "加载配置", "保存配置" -> 调整为 #f0f0f0 风格
STD_BG_NORMAL = QColor(240, 240, 240)  # #f0f0f0 浅灰基底
STD_BG_HOVER  = QColor(232, 232, 232)  # 悬停稍深
STD_BG_PRESS  = QColor(220, 220, 220)  # 按下更深
STD_BORDER    = QColor(210, 210, 210)  # 边框
STD_TEXT      = QColor(30, 30, 30)     # 深灰文字

# 3. 危险色 (Danger - 红)
# 用于 "退出", "删除"
DANGER_BG     = QColor(215, 45, 45)
DANGER_HOVER  = QColor(235, 60, 60)
DANGER_PRESS  = QColor(180, 30, 30)

class FluentButton(QPushButton):
    """
    Q弹动画按钮 v3.1
    - 优化了浅灰色按钮的视觉表现
    - 平滑的 Color Fade + Scale Bounce 动画
    """
    def __init__(self, text, icon=None, parent=None, is_primary=False, is_danger=False):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon: self.setIcon(icon)

        self.setMinimumHeight(36) 
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # 字体设置
        font = QFont("Segoe UI", 9)
        if is_primary or is_danger: 
            font.setBold(True)
        self.setFont(font)
        
        self.is_primary = is_primary
        self.is_danger = is_danger
        
        self._scale_val = 1.0
        
        # --- 动画系统 ---
        
        # 1. 颜色过渡动画 (Smooth Fade)
        self.color_wrapper = ColorAnimWrapper(self)
        self.bg_anim = QPropertyAnimation(self.color_wrapper, b"color")
        self.bg_anim.setDuration(200) # 200ms 平滑过渡
        self.bg_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # 2. 缩放回弹动画 (Scale Bounce)
        self.scale_anim = QPropertyAnimation(self, b"scale_prop")
        self.scale_anim.setDuration(350)
        self.scale_anim.setEasingCurve(QEasingCurve.Type.OutBack) # Q弹回馈

        # 初始化颜色
        self._update_target_colors()
        self.color_wrapper.color = self.bg_normal

        # 阴影 (浅灰色按钮加一点点立体感)
        if not (self.is_primary or self.is_danger):
            self.shadow = QGraphicsDropShadowEffect(self)
            self.shadow.setBlurRadius(8)
            self.shadow.setColor(QColor(0, 0, 0, 8)) # 极淡阴影
            self.shadow.setOffset(0, 1)
            self.setGraphicsEffect(self.shadow)

    def _update_target_colors(self):
        """定义三态颜色"""
        if self.is_primary:
            self.bg_normal = PRIMARY_BG
            self.bg_hover = PRIMARY_HOVER
            self.bg_press = PRIMARY_PRESS
            self.text_color = Qt.GlobalColor.white
            self.border_color = PRIMARY_BG
        elif self.is_danger:
            self.bg_normal = DANGER_BG
            self.bg_hover = DANGER_HOVER
            self.bg_press = DANGER_PRESS
            self.text_color = Qt.GlobalColor.white
            self.border_color = DANGER_BG
        else:
            # 应用浅灰色系
            self.bg_normal = STD_BG_NORMAL
            self.bg_hover = STD_BG_HOVER
            self.bg_press = STD_BG_PRESS
            self.text_color = STD_TEXT
            self.border_color = STD_BORDER

    @pyqtProperty(float)
    def scale_prop(self):
        return self._scale_val

    @scale_prop.setter
    def scale_prop(self, val):
        self._scale_val = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. 应用缩放 (以中心为锚点)
        w, h = self.width(), self.height()
        painter.translate(w / 2, h / 2)
        painter.scale(self._scale_val, self._scale_val)
        painter.translate(-w / 2, -h / 2)

        rect = self.rect().adjusted(1, 1, -1, -1)
        
        # 2. 绘制背景
        current_bg = self.color_wrapper.color
        painter.setBrush(QBrush(current_bg))
        
        # 绘制边框
        if self.is_primary or self.is_danger:
            painter.setPen(Qt.PenStyle.NoPen)
        else:
            painter.setPen(QPen(self.border_color, 1))
            
        painter.drawRoundedRect(rect, 6, 6)

        # 3. 底部立体线 (仅浅灰按钮)
        if not self.is_primary and not self.is_danger and not self.isDown():
            # 颜色加深一点点做立体感
            darker_line = QColor(0,0,0, 15)
            painter.setPen(QPen(darker_line, 1))
            painter.drawLine(rect.left()+6, rect.bottom(), rect.right()-6, rect.bottom())

        # 4. 手动绘制文字 (防止遮挡)
        painter.setPen(self.text_color)
        
        icon = self.icon()
        text = self.text()
        
        if not icon.isNull():
            icon_size = 16
            # 简单估算宽度以居中
            fm = self.fontMetrics()
            text_w = fm.horizontalAdvance(text)
            content_w = icon_size + 8 + text_w
            start_x = (w - content_w) / 2
            
            icon_rect = QRect(int(start_x), int((h - icon_size)/2), icon_size, icon_size)
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
            
            text_rect = QRect(int(start_x + icon_size + 8), 0, int(text_w + 10), h)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def enterEvent(self, event):
        # 颜色变深 (Hover)
        self.bg_anim.stop()
        self.bg_anim.setEndValue(self.bg_hover)
        self.bg_anim.start()
        
        # 微微放大 (Scale Up)
        self.scale_anim.stop()
        self.scale_anim.setEndValue(1.02)
        self.scale_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # 颜色恢复
        self.bg_anim.stop()
        self.bg_anim.setEndValue(self.bg_normal)
        self.bg_anim.start()
        
        # 大小恢复
        self.scale_anim.stop()
        self.scale_anim.setEndValue(1.0)
        self.scale_anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        # 颜色按下 (Press)
        self.bg_anim.stop()
        self.bg_anim.setEndValue(self.bg_press)
        self.bg_anim.start()
        
        # 明显缩小 (Click Feedback)
        self.scale_anim.stop()
        self.scale_anim.setDuration(100)
        self.scale_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.scale_anim.setEndValue(0.94)
        self.scale_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # 颜色回 Hover
        self.bg_anim.stop()
        self.bg_anim.setEndValue(self.bg_hover)
        self.bg_anim.start()
        
        # Q弹回位
        self.scale_anim.stop()
        self.scale_anim.setDuration(400)
        self.scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.scale_anim.setEndValue(1.02)
        self.scale_anim.start()
        super().mouseReleaseEvent(event)


class FluentCard(QWidget):
    """ 圆角卡片容器 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            FluentCard {
                background-color: #ffffff;
                border: 1px solid #eaeaea; 
                border-radius: 10px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 6))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

class SmoothStackedWidget(QStackedWidget):
    """ 滑动切换容器 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_direction = Qt.Orientation.Horizontal
        self.m_speed = 300 
        self.m_animationtype = QEasingCurve.Type.OutCubic
        self.m_now = 0
        self.m_next = 0
        self.m_active = False

    def setCurrentIndex(self, index):
        if self.m_active or self.currentIndex() == index:
            super().setCurrentIndex(index)
            return
        self.m_now = self.currentIndex()
        self.m_next = index
        self.m_active = True
        offset_x = self.frameRect().width()
        if index > self.m_now: offset_x = -offset_x
        
        w_next = self.widget(index)
        w_now = self.widget(self.m_now)
        w_next.setGeometry(0, 0, self.width(), self.height())
        
        p_now = w_now.grab()
        p_next = w_next.grab()

        self.l_now = QLabel(self)
        self.l_now.setPixmap(p_now)
        self.l_now.setGeometry(0, 0, self.width(), self.height())
        self.l_now.show()

        self.l_next = QLabel(self)
        self.l_next.setPixmap(p_next)
        self.l_next.setGeometry(0, 0, self.width(), self.height())
        self.l_next.hide()

        start_next = QPoint(-offset_x, 0)
        end_next = QPoint(0, 0)
        start_now = QPoint(0, 0)
        end_now = QPoint(offset_x, 0)

        self.l_next.move(start_next)
        self.l_next.show()

        self.anim_group = QParallelAnimationGroup()
        anim_now = QPropertyAnimation(self.l_now, b"pos")
        anim_now.setDuration(self.m_speed)
        anim_now.setEasingCurve(self.m_animationtype)
        anim_now.setStartValue(start_now)
        anim_now.setEndValue(end_now)

        anim_next = QPropertyAnimation(self.l_next, b"pos")
        anim_next.setDuration(self.m_speed)
        anim_next.setEasingCurve(self.m_animationtype)
        anim_next.setStartValue(start_next)
        anim_next.setEndValue(end_next)

        self.anim_group.addAnimation(anim_now)
        self.anim_group.addAnimation(anim_next)
        self.anim_group.finished.connect(self.animationDone)
        self.anim_group.start()
        w_now.hide()
        w_next.hide()

    def animationDone(self):
        self.setCurrentIndex_original(self.m_next)
        self.widget(self.m_next).show()
        self.l_now.deleteLater()
        self.l_next.deleteLater()
        self.m_active = False

    def setCurrentIndex_original(self, index):
        super().setCurrentIndex(index)

class NavButton(QPushButton):
    """ 顶部导航按钮 (Tab) """
    def __init__(self, text, icon_char=None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFont(QFont("Segoe UI", 10))
        self.icon_char = icon_char
        
        # 颜色定义
        self.bg_normal = QColor(0,0,0,0)
        self.bg_hover = QColor(0,0,0,10)
        self.bg_checked = QColor(255, 255, 255)
        
        self.text_normal = QColor(100, 100, 100)
        self.text_checked = PRIMARY_BG

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        
        if self.isChecked():
            painter.setBrush(QBrush(self.bg_checked))
            painter.setPen(QPen(QColor(0,0,0,20), 1))
            painter.drawRoundedRect(rect, 6, 6)
        elif self.underMouse():
            painter.setBrush(QBrush(self.bg_hover))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
            
        if self.isChecked():
            painter.setPen(self.text_checked)
            font = self.font()
            font.setBold(True)
            painter.setFont(font)
        else:
            painter.setPen(self.text_normal)
            
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())

class FluentTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(16)

        # 导航栏容器
        self.nav_container = QWidget()
        self.nav_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.5); 
            border-radius: 8px;
        """)
        self.nav_layout = QHBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(4, 4, 4, 4)
        self.nav_layout.setSpacing(8)
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.stacked_widget = SmoothStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent;")

        self.layout.addWidget(self.nav_container)
        self.layout.addWidget(self.stacked_widget)
        self.buttons = []

    def addTab(self, widget, text, icon_char=None):
        index = self.stacked_widget.addWidget(widget)
        display_text = f"{icon_char}  {text}" if icon_char else text
        btn = NavButton(display_text, icon_char)
        btn.clicked.connect(lambda: self.switch_tab(index))
        self.nav_layout.addWidget(btn)
        self.buttons.append(btn)
        if index == 0:
            btn.setChecked(True)

    def switch_tab(self, index):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        self.stacked_widget.setCurrentIndex(index)


class FluentLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(34)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

class FluentComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(34)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

class FluentGroupBox(QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(16)
        inner_layout.setContentsMargins(24, 36, 24, 24)
        self.setLayout(inner_layout)