from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QPoint, QObject, pyqtProperty, 
    QPointF, QParallelAnimationGroup, QAbstractAnimation
)
from PyQt6.QtWidgets import QWidget, QGraphicsItem, QGraphicsOpacityEffect
from PyQt6.QtGui import QColor

class AnimationUtils:
    """通用动画工具类"""

    @staticmethod
    def fade_in_entry(widget: QWidget, duration=500, scale=True):
        """
        窗口进入动画：
        1. 透明度 0 -> 1
        2. (可选) 缩放 0.95 -> 1.0 (模拟 Windows 11 弹窗效果)
        """
        widget.setWindowOpacity(0)
        
        group = QParallelAnimationGroup(widget)
        
        # 透明度动画
        anim_opacity = QPropertyAnimation(widget, b"windowOpacity")
        anim_opacity.setStartValue(0)
        anim_opacity.setEndValue(1)
        anim_opacity.setDuration(duration)
        anim_opacity.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(anim_opacity)
        
        if scale:
            # 需要在 resizeEvent 中处理 geometry，这里简化处理
            # 对于顶层窗口，直接做透明度通常最稳健，geometry 动画可能导致闪烁
            # 这里的 scale 预留给子控件使用
            pass
            
        group.start()

class GraphicsItemAnimWrapper(QObject):
    """QGraphicsItem 的动画包装器"""
    def __init__(self, item: QGraphicsItem):
        super().__init__()
        self.item = item

    @pyqtProperty(QPointF)
    def pos(self):
        return self.item.pos()

    @pos.setter
    def pos(self, value):
        self.item.setPos(value)

class ColorAnimWrapper(QObject):
    """
    用于为普通 QWidget 或 QPushButton 的背景色/前景色制作动画
    需要配合 paintEvent 使用
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._color = QColor(0, 0, 0, 0)
        self.widget = parent

    @pyqtProperty(QColor)
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.widget.update() # 触发重绘