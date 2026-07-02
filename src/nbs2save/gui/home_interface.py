"""
主页界面 - 文件设置、转换参数、操作按钮
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog

from qfluentwidgets import (
    ScrollArea,
    SettingCardGroup,
    FluentIcon,
    SubtitleLabel,
    TitleLabel,
    CaptionLabel,
    PrimaryPushButton,
    PushButton,
    InfoBar,
    InfoBarPosition,
    CardWidget,
    ProgressBar,
)

from ..core.constants import MINECRAFT_VERSIONS
from .widgets import FileSelectCard, ComboBoxCard


class HomeInterface(ScrollArea):
    """主页界面 - 基础设置"""

    # 向主窗口暴露操作信号
    startConvertSignal = pyqtSignal()
    loadConfigSignal = pyqtSignal()
    saveConfigSignal = pyqtSignal()
    exitSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeInterface")
        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName("scrollWidget")
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(12)

        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self._initTitle()
        self._initFileGroup()
        self._initParamGroup()
        self._initActionBar()

        self.vBoxLayout.addStretch(1)

    # ── 标题 ──

    def _initTitle(self):
        headerCard = CardWidget(self)
        headerLayout = QVBoxLayout(headerCard)
        headerLayout.setContentsMargins(24, 20, 24, 20)
        headerLayout.setSpacing(4)

        titleLabel = TitleLabel("NBS-to-Minecraftsave", headerCard)
        titleLabel.setStyleSheet("font-size: 22px; font-weight: 700;")
        headerLayout.addWidget(titleLabel)

        descLabel = CaptionLabel("将 .nbs 音乐文件转换为 Minecraft 存档！", headerCard)
        descLabel.setStyleSheet("font-size: 13px; color: #888;")
        headerLayout.addWidget(descLabel)

        self.vBoxLayout.addWidget(headerCard)
        self.vBoxLayout.addSpacing(8)

    # ── 文件设置 ──

    def _initFileGroup(self):
        self.fileGroup = SettingCardGroup("文件设置", self.scrollWidget)

        self.inputFileCard = FileSelectCard(
            FluentIcon.DOCUMENT,
            "NBS 文件",
            "选择要转换的 Note Block Studio 文件",
            placeholder="选择 .nbs 文件...",
            file_filter="Note Block Studio (*.nbs)",
            parent=self.fileGroup,
        )

        self.outputFileCard = FileSelectCard(
            FluentIcon.SAVE,
            "输出路径",
            "设置转换后的文件保存路径",
            placeholder="设置保存路径...",
            file_filter="Schematic (*.schem);;McFunction (*.mcfunction)",
            save_mode=True,
            parent=self.fileGroup,
        )

        self.fileGroup.addSettingCard(self.inputFileCard)
        self.fileGroup.addSettingCard(self.outputFileCard)
        self.vBoxLayout.addWidget(self.fileGroup)

        # 输入文件改变时自动填充输出文件名
        self.inputFileCard.fileChanged.connect(self._onInputFileChanged)

        # 输出文件浏览：根据输出格式自动补全扩展名
        self.outputFileCard.browseButton.clicked.disconnect()
        self.outputFileCard.browseButton.clicked.connect(self._browseOutputFile)

    def _onInputFileChanged(self, path: str):
        """选择输入文件后自动填充输出文件名（仅当输出为空或与上次自动填充一致时）"""
        if path:
            base_name = os.path.splitext(os.path.basename(path))[0]
            current_output = self.outputFileCard.text()
            # 如果输出为空，或输出不含路径分隔符（即只是个文件名），则自动填充
            if not current_output or os.sep not in current_output:
                self.outputFileCard.setText(base_name)

    def _browseOutputFile(self):
        """浏览输出文件，根据输出格式自动补全扩展名"""
        output_type = self.typeCard.currentData()
        ext = ".schem" if output_type == "schematic" else ".mcfunction"
        path, _ = QFileDialog.getSaveFileName(
            self, "选择保存位置", "",
            "Schematic (*.schem);;McFunction (*.mcfunction)"
        )
        if path:
            if not path.endswith(ext):
                path += ext
            self.outputFileCard.setText(path)

    # ── 转换参数 ──

    def _initParamGroup(self):
        self.paramGroup = SettingCardGroup("转换参数", self.scrollWidget)

        self.versionCard = ComboBoxCard(
            FluentIcon.GAME,
            "目标游戏版本",
            "选择输出 schematic 文件的目标 Minecraft 版本",
            parent=self.paramGroup,
        )
        for v in MINECRAFT_VERSIONS:
            self.versionCard.addItem(str(v), v)

        self.typeCard = ComboBoxCard(
            FluentIcon.CODE,
            "输出格式",
            "选择转换输出的文件格式",
            parent=self.paramGroup,
        )
        self.typeCard.addItem("WorldEdit Schematic (.schem)", "schematic")
        self.typeCard.addItem("Minecraft Function (.mcfunction)", "mcfunction")

        self.paramGroup.addSettingCard(self.versionCard)
        self.paramGroup.addSettingCard(self.typeCard)
        self.vBoxLayout.addWidget(self.paramGroup)

    # ── 操作栏 ──

    def _initActionBar(self):
        self.actionCard = CardWidget(self.scrollWidget)
        actionLayout = QHBoxLayout(self.actionCard)
        actionLayout.setContentsMargins(20, 16, 20, 16)
        actionLayout.setSpacing(12)

        # 状态标签
        self.statusLabel = SubtitleLabel("就绪", self.actionCard)
        self.statusLabel.setStyleSheet("font-size: 13px; font-weight: 400; color: #888;")

        # 进度条
        self.progressBar = ProgressBar(self.actionCard)
        self.progressBar.setVisible(False)
        self.progressBar.setFixedWidth(200)

        self.loadConfigBtn = PushButton("加载配置", self.actionCard)
        self.loadConfigBtn.setIcon(FluentIcon.FOLDER)
        self.saveConfigBtn = PushButton("保存配置", self.actionCard)
        self.saveConfigBtn.setIcon(FluentIcon.SAVE)
        self.exitBtn = PushButton("退出", self.actionCard)
        self.exitBtn.setIcon(FluentIcon.CLOSE)
        self.startBtn = PrimaryPushButton("开始转换", self.actionCard)
        self.startBtn.setIcon(FluentIcon.PLAY)
        self.startBtn.setFixedHeight(40)
        self.startBtn.setMinimumWidth(160)

        actionLayout.addWidget(self.statusLabel)
        actionLayout.addWidget(self.progressBar)
        actionLayout.addStretch(1)
        actionLayout.addWidget(self.loadConfigBtn)
        actionLayout.addWidget(self.saveConfigBtn)
        actionLayout.addWidget(self.exitBtn)
        actionLayout.addSpacing(20)
        actionLayout.addWidget(self.startBtn)

        self.vBoxLayout.addSpacing(8)
        self.vBoxLayout.addWidget(self.actionCard)

        # 连接信号
        self.loadConfigBtn.clicked.connect(self.loadConfigSignal.emit)
        self.saveConfigBtn.clicked.connect(self.saveConfigSignal.emit)
        self.exitBtn.clicked.connect(self.exitSignal.emit)
        self.startBtn.clicked.connect(self.startConvertSignal.emit)

    # ── 公开接口 ──

    def getInputFile(self) -> str:
        return self.inputFileCard.text()

    def setInputFile(self, path: str):
        self.inputFileCard.setText(path)

    def getOutputFile(self) -> str:
        return self.outputFileCard.text()

    def setOutputFile(self, path: str):
        self.outputFileCard.setText(path)

    def getVersion(self):
        return self.versionCard.currentData()

    def setVersion(self, version):
        """根据 Version 枚举值设置下拉框选中项"""
        for i in range(self.versionCard.comboBox.count()):
            if self.versionCard.comboBox.itemData(i) == version:
                self.versionCard.setCurrentIndex(i)
                return

    def getType(self) -> str:
        return self.typeCard.currentData()

    def setType(self, type_str: str):
        """根据类型字符串设置下拉框选中项"""
        for i in range(self.typeCard.comboBox.count()):
            if self.typeCard.comboBox.itemData(i) == type_str:
                self.typeCard.setCurrentIndex(i)
                return

    def setStatus(self, text: str):
        self.statusLabel.setText(text)

    def setProgressVisible(self, visible: bool):
        self.progressBar.setVisible(visible)

    def showInfoBar(self, title, content, is_error=False):
        if is_error:
            InfoBar.error(
                title=title,
                content=content,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self,
            )
        else:
            InfoBar.success(
                title=title,
                content=content,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
