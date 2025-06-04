from PyQt6.QtWidgets import (
    QPushButton, QLineEdit, QComboBox, QGroupBox, QTabWidget, QSizePolicy, QVBoxLayout, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor


class FluentButton(QPushButton):
    """Fluent风格的按钮"""

    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon:
            self.setIcon(icon)

        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


class FluentLineEdit(QLineEdit):
    """Fluent风格的输入框"""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class FluentComboBox(QComboBox):
    """Fluent风格的下拉框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class FluentGroupBox(QGroupBox):
    """Fluent风格的分组框"""

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # 创建内部布局
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(12)
        inner_layout.setContentsMargins(16, 24, 16, 16)
        self.setLayout(inner_layout)


class FluentTabWidget(QTabWidget):
    """Fluent风格的标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


class FluentApplication(QApplication):
    """Fluent风格的应用程序"""

    def __init__(self, argv):
        super().__init__(argv)
        self.setStyle("Fusion")

        # 设置应用调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(246, 246, 246))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(51, 51, 51))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(249, 249, 249))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(51, 51, 51))
        palette.setColor(QPalette.ColorRole.Text, QColor(51, 51, 51))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(51, 51, 51))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(palette)
