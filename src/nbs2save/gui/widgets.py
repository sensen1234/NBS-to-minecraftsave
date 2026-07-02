"""
自定义 Fluent 设置卡片组件
基于 QFluentWidgets 的 SettingCard 扩展
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFileDialog

from qfluentwidgets import (
    SettingCard,
    PushButton,
    LineEdit,
    ComboBox,
    SwitchButton,
    IndicatorPosition,
)


class FileSelectCard(SettingCard):
    """文件选择卡片 - 带行编辑框和浏览按钮"""

    fileChanged = pyqtSignal(str)

    def __init__(
        self,
        icon,
        title,
        content=None,
        placeholder="",
        file_filter="All Files (*)",
        save_mode=False,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)
        self.file_filter = file_filter
        self.save_mode = save_mode

        self.lineEdit = LineEdit(self)
        self.lineEdit.setPlaceholderText(placeholder)
        self.lineEdit.setFixedWidth(340)

        self.browseButton = PushButton("浏览", self)
        self.browseButton.setFixedWidth(80)

        self.hBoxLayout.addWidget(self.lineEdit)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.browseButton)
        self.hBoxLayout.addSpacing(16)

        self.browseButton.clicked.connect(self._onBrowse)
        self.lineEdit.textChanged.connect(self.fileChanged.emit)

    def _onBrowse(self):
        if self.save_mode:
            path, _ = QFileDialog.getSaveFileName(
                self, "选择保存位置", "", self.file_filter
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", self.file_filter
            )
        if path:
            self.lineEdit.setText(path)

    def text(self) -> str:
        return self.lineEdit.text()

    def setText(self, text: str):
        self.lineEdit.setText(text)


class ComboBoxCard(SettingCard):
    """下拉选择卡片 - 无需 QFluentWidgets 配置系统

    注意: QFluentWidgets ComboBox.addItem 签名为 addItem(text, icon=None, userData=None)
    第二个参数是 icon 而非 userData，切勿直接传非图标对象。
    """

    valueChanged = pyqtSignal(str)

    def __init__(self, icon, title, content=None, texts=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.comboBox = ComboBox(self)
        if texts:
            self.comboBox.addItems(texts)
        self.comboBox.setFixedWidth(220)

        self.hBoxLayout.addWidget(self.comboBox)
        self.hBoxLayout.addSpacing(16)

        self.comboBox.currentTextChanged.connect(self.valueChanged.emit)

    def addItem(self, text, userData=None):
        """添加选项。icon 参数固定为 None，userData 通过第三参数传入。"""
        self.comboBox.addItem(text, None, userData)

    def currentData(self):
        return self.comboBox.currentData()

    def currentIndex(self) -> int:
        return self.comboBox.currentIndex()

    def setCurrentIndex(self, index):
        self.comboBox.setCurrentIndex(index)


class SwitchCard(SettingCard):
    """开关卡片 - 无需 QFluentWidgets 配置系统"""

    checkedChanged = pyqtSignal(bool)

    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.switchButton = SwitchButton(self, IndicatorPosition.RIGHT)

        self.hBoxLayout.addWidget(self.switchButton)
        self.hBoxLayout.addSpacing(16)

        self.switchButton.checkedChanged.connect(self.checkedChanged.emit)

    def isChecked(self) -> bool:
        return self.switchButton.isChecked()

    def setChecked(self, checked: bool):
        self.switchButton.setChecked(checked)
