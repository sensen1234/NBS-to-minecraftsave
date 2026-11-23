from PyQt6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QObject,
    pyqtProperty,  # type: ignore[attr-defined]  # PyQt6 的类型桩未声明该符号
    QPointF,
    QParallelAnimationGroup,
)
from PyQt6.QtWidgets import QWidget, QGraphicsItem
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

        setattr(widget, "_fade_in_anim", group)

        # Keep the group alive until its owning widget is destroyed. Clearing
        # the last Python reference inside finished can destroy the group
        # while Qt is still dispatching that signal (a native crash on Windows).
        group.start()


class GraphicsItemAnimWrapper(QObject):
    """QGraphicsItem 的动画包装器"""

    def __init__(self, item: QGraphicsItem):
        super().__init__()
        self.item = item

    def _get_pos(self) -> QPointF:
        return self.item.pos()

    def _set_pos(self, value: QPointF) -> None:
        self.item.setPos(value)

    # 属性名必须是 "pos"（QPropertyAnimation 按名字查找），
    # 使用显式 fget/fset 而不是 @pos.setter，避免被类型检查判为同名方法重复声明。
    pos = pyqtProperty(QPointF, _get_pos, _set_pos)


class ColorAnimWrapper(QObject):
    """
    用于为普通 QWidget 或 QPushButton 的背景色/前景色制作动画
    需要配合 paintEvent 使用
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._color = QColor(0, 0, 0, 0)
        self.widget = parent

    def _get_color(self) -> QColor:
        return self._color

    def _set_color(self, value: QColor) -> None:
        self._color = value
        self.widget.update()  # 触发重绘

    color = pyqtProperty(QColor, _get_color, _set_color)
