"""
运行日志界面
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    CardWidget,
    SubtitleLabel,
    PlainTextEdit,
    PushButton,
    FluentIcon,
)


class LogInterface(QWidget):
    """运行日志界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logInterface")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 20, 36, 36)
        layout.setSpacing(12)

        # 标题栏 + 清空按钮
        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)

        self.titleLabel = SubtitleLabel("运行日志", self)
        self.titleLabel.setStyleSheet("font-size: 20px; font-weight: 600;")
        headerLayout.addWidget(self.titleLabel)
        headerLayout.addStretch(1)

        self.clearBtn = PushButton("清空", self)
        self.clearBtn.setIcon(FluentIcon.DELETE)
        self.clearBtn.setFixedHeight(32)
        self.clearBtn.clicked.connect(self.clear)
        headerLayout.addWidget(self.clearBtn)

        layout.addLayout(headerLayout)
        layout.addSpacing(8)

        # 日志卡片
        self.logCard = CardWidget(self)
        cardLayout = QVBoxLayout(self.logCard)
        cardLayout.setContentsMargins(0, 0, 0, 0)

        self.logText = PlainTextEdit(self.logCard)
        self.logText.setReadOnly(True)
        self.logText.setPlaceholderText("日志输出将在此显示...")
        self.logText.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 16px;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: rgba(128, 128, 128, 0.4);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        cardLayout.addWidget(self.logText)
        layout.addWidget(self.logCard)

    def appendLog(self, message: str):
        """追加日志消息"""
        self.logText.appendPlainText(message)

    def clear(self):
        """清空日志"""
        self.logText.clear()
