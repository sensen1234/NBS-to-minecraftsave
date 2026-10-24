"""A project entry page with read-only song analysis and creative shortcuts."""

from pathlib import Path
import threading

from PyQt6.QtCore import Qt, QObject, QRunnable, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy

from qfluentwidgets import (
    ScrollArea, FluentIcon, SubtitleLabel, CaptionLabel, BodyLabel,
    PrimaryPushButton, PushButton, InfoBar, InfoBarPosition, CardWidget,
    ProgressBar, LineEdit, ComboBox,
)

from ..core.constants import MINECRAFT_VERSIONS
from ..core.song_insights import read_song_insights
from .studio_style import PageHeader, apply_page_style, muted_label


class _PathCard(CardWidget):
    """A stacked path field that fits a narrow project page."""

    fileChanged = pyqtSignal(str)

    def __init__(self, title, placeholder, file_filter, *, save_mode=False, parent=None):
        super().__init__(parent)
        self.file_filter, self.save_mode = file_filter, save_mode
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(BodyLabel(title, self))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.lineEdit = LineEdit(self)
        self.lineEdit.setMinimumWidth(0)
        self.lineEdit.setPlaceholderText(placeholder)
        self.lineEdit.setClearButtonEnabled(True)
        self.browseButton = PushButton("选择文件" if not save_mode else "保存位置", self)
        self.browseButton.setIcon(FluentIcon.FOLDER if not save_mode else FluentIcon.SAVE)
        row.addWidget(self.lineEdit, 1)
        row.addWidget(self.browseButton)
        layout.addLayout(row)
        self.browseButton.clicked.connect(self._onBrowse)
        self.lineEdit.textChanged.connect(self.fileChanged.emit)

    def _onBrowse(self):
        dialog = QFileDialog.getSaveFileName if self.save_mode else QFileDialog.getOpenFileName
        path, _ = dialog(self, "选择保存位置" if self.save_mode else "选择 NBS 乐谱", self.text(), self.file_filter)
        if path:
            self.setText(path)

    def text(self):
        return self.lineEdit.text()

    def setText(self, text):
        self.lineEdit.setText(text)


class _ChoiceField(QWidget):
    valueChanged = pyqtSignal(str)

    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(muted_label(CaptionLabel(title, self)))
        self.comboBox = ComboBox(self)
        self.comboBox.setMinimumWidth(0)
        self.comboBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.comboBox)
        self.comboBox.currentTextChanged.connect(self.valueChanged.emit)

    def addItem(self, text, userData=None):
        self.comboBox.addItem(text, userData=userData)

    def currentData(self):
        return self.comboBox.currentData()

    def currentIndex(self):
        return self.comboBox.currentIndex()

    def setCurrentIndex(self, index):
        self.comboBox.setCurrentIndex(index)


class _InsightSignals(QObject):
    finished = pyqtSignal(int, str, object, str)


class _InsightWorker(QRunnable):
    def __init__(self, revision, path):
        super().__init__()
        self.revision, self.path = revision, path
        self.cancel = threading.Event()
        self.signals = _InsightSignals()

    def run(self):
        result, error = None, ""
        try:
            if not self.cancel.is_set():
                result = read_song_insights(self.path)
        except FileNotFoundError:
            error = "找不到这个文件，请检查路径或重新选择。"
        except PermissionError:
            error = "暂时无法读取这个文件，请检查访问权限。"
        except Exception:
            error = "无法解析这个文件，请选择完整的 Note Block Studio（.nbs）乐谱。"
        self.signals.finished.emit(self.revision, self.path, result, error)


class HomeInterface(ScrollArea):
    startConvertSignal = pyqtSignal()
    loadConfigSignal = pyqtSignal()
    saveConfigSignal = pyqtSignal()
    exitSignal = pyqtSignal()
    openGroupsSignal = pyqtSignal()
    openWorkbenchSignal = pyqtSignal()
    openInstrumentsSignal = pyqtSignal()
    analysisReady = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeInterface")
        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName("scrollWidget")
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(28, 24, 28, 28)
        self.vBoxLayout.setSpacing(14)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        apply_page_style(self)
        self._analysis_revision = 0
        self._analysis_workers = {}
        self._analysis_busy = False
        self._closed = False
        self.songInsights = None
        self._auto_output = ""
        self._analysis_timer = QTimer(self)
        self._analysis_timer.setSingleShot(True)
        self._analysis_timer.setInterval(250)
        self._analysis_timer.timeout.connect(self._start_analysis)
        self._initTitle()
        self._initFileGroup()
        self._initInsights()
        self._initParamGroup()
        self._initActionBar()
        self._initShortcuts()
        self.vBoxLayout.addStretch(1)

    def _initTitle(self):
        self.header = PageHeader(
            "把音乐搭进 Minecraft", "从 NBS 乐谱开始，规划方块布局、试听，再导出音乐结构。",
            eyebrow="NBS STUDIO", parent=self.scrollWidget,
        )
        self.vBoxLayout.addWidget(self.header)

    def _initFileGroup(self):
        self.fileGroup = QWidget(self.scrollWidget)
        layout = QVBoxLayout(self.fileGroup)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.inputFileCard = _PathCard(
            "NBS 乐谱", "选择 .nbs 文件，自动查看歌曲概览", "Note Block Studio (*.nbs)", parent=self.fileGroup,
        )
        layout.addWidget(self.inputFileCard)
        self.vBoxLayout.addWidget(self.fileGroup)
        self.inputFileCard.fileChanged.connect(self._onInputFileChanged)

    def _initInsights(self):
        self.insightsCard = CardWidget(self.scrollWidget)
        layout = QVBoxLayout(self.insightsCard)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(7)
        self.songTitleLabel = SubtitleLabel("你的下一首方块音乐", self.insightsCard)
        self.songTitleLabel.setWordWrap(True)
        layout.addWidget(self.songTitleLabel)
        self.songMetaLabel = muted_label(CaptionLabel("选好乐谱后，这里会显示歌曲信息和音域检查。", self.insightsCard))
        self.songMetaLabel.setWordWrap(True)
        layout.addWidget(self.songMetaLabel)
        self.metricsWidget = QWidget(self.insightsCard)
        metrics = QHBoxLayout(self.metricsWidget)
        metrics.setContentsMargins(0, 3, 0, 3)
        metrics.setSpacing(20)
        self.metricLabels = {}
        for key, title in (("notes", "音符"), ("layers", "使用轨道"), ("range", "超出音域"), ("custom", "自定义音符")):
            column = QVBoxLayout()
            column.setSpacing(2)
            value = SubtitleLabel("—", self.metricsWidget)
            column.addWidget(value)
            column.addWidget(muted_label(CaptionLabel(title, self.metricsWidget)))
            metrics.addLayout(column, 1)
            self.metricLabels[key] = value
        layout.addWidget(self.metricsWidget)
        self.analysisStatusLabel = muted_label(CaptionLabel("歌曲分析只读取文件，不会调整轨道或乐器配置。", self.insightsCard))
        self.analysisStatusLabel.setWordWrap(True)
        layout.addWidget(self.analysisStatusLabel)
        self.metricsWidget.hide()
        self.vBoxLayout.addWidget(self.insightsCard)

    def _initParamGroup(self):
        self.paramGroup = QWidget(self.scrollWidget)
        layout = QVBoxLayout(self.paramGroup)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.outputFileCard = _PathCard(
            "结构导出位置", "设置文件名或选择保存位置", "Schematic (*.schem);;McFunction (*.mcfunction)",
            save_mode=True, parent=self.paramGroup,
        )
        self.outputFileCard.browseButton.clicked.disconnect()
        self.outputFileCard.browseButton.clicked.connect(self._browseOutputFile)
        layout.addWidget(self.outputFileCard)
        choices = QHBoxLayout()
        choices.setSpacing(12)
        self.versionCard = _ChoiceField("Minecraft 目标版本", self.paramGroup)
        for version in MINECRAFT_VERSIONS:
            self.versionCard.addItem(str(version).replace("Version.", ""), version)
        self.typeCard = _ChoiceField("输出格式", self.paramGroup)
        self.typeCard.addItem("WorldEdit · .schem", "schematic")
        self.typeCard.addItem("命令函数 · .mcfunction", "mcfunction")
        choices.addWidget(self.versionCard, 1)
        choices.addWidget(self.typeCard, 1)
        layout.addLayout(choices)
        self.vBoxLayout.addWidget(self.paramGroup)

    def _initActionBar(self):
        self.actionCard = CardWidget(self.scrollWidget)
        layout = QVBoxLayout(self.actionCard)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)
        status = QHBoxLayout()
        self.statusLabel = muted_label(BodyLabel("准备好后，开始导出你的音乐结构。", self.actionCard))
        self.statusLabel.setWordWrap(True)
        status.addWidget(self.statusLabel, 1)
        self.progressBar = ProgressBar(self.actionCard)
        self.progressBar.setFixedWidth(120)
        self.progressBar.hide()
        status.addWidget(self.progressBar)
        layout.addLayout(status)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.loadConfigBtn = PushButton("打开项目", self.actionCard)
        self.loadConfigBtn.setIcon(FluentIcon.FOLDER)
        self.saveConfigBtn = PushButton("保存项目", self.actionCard)
        self.saveConfigBtn.setIcon(FluentIcon.SAVE)
        self.startBtn = PrimaryPushButton("开始导出", self.actionCard)
        self.startBtn.setIcon(FluentIcon.PLAY)
        self.startBtn.setMinimumHeight(36)
        row.addWidget(self.loadConfigBtn)
        row.addWidget(self.saveConfigBtn)
        row.addStretch(1)
        row.addWidget(self.startBtn)
        layout.addLayout(row)
        self.exitBtn = PushButton("退出", self.actionCard)
        self.exitBtn.hide()
        self.exitBtn.clicked.connect(self.exitSignal.emit)
        self.loadConfigBtn.clicked.connect(self.loadConfigSignal.emit)
        self.saveConfigBtn.clicked.connect(self.saveConfigSignal.emit)
        self.startBtn.clicked.connect(self.startConvertSignal.emit)
        self.vBoxLayout.addWidget(self.actionCard)

    def _initShortcuts(self):
        self.shortcutWidget = QWidget(self.scrollWidget)
        layout = QVBoxLayout(self.shortcutWidget)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(muted_label(CaptionLabel("继续创作", self.shortcutWidget)))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.groupsBtn = PushButton("轨道布局", self.shortcutWidget)
        self.workbenchBtn = PushButton("3D 工作台", self.shortcutWidget)
        self.instrumentsBtn = PushButton("自定义音色", self.shortcutWidget)
        for button in (self.groupsBtn, self.workbenchBtn, self.instrumentsBtn):
            row.addWidget(button, 1)
        self.groupsBtn.clicked.connect(self.openGroupsSignal.emit)
        self.workbenchBtn.clicked.connect(self.openWorkbenchSignal.emit)
        self.instrumentsBtn.clicked.connect(self.openInstrumentsSignal.emit)
        layout.addLayout(row)
        self.vBoxLayout.addWidget(self.shortcutWidget)

    def _onInputFileChanged(self, path):
        if path:
            basename = Path(path).stem
            output = self.outputFileCard.text()
            if not output or output == self._auto_output:
                self.outputFileCard.setText(basename)
                self._auto_output = basename
        self._analysis_revision += 1
        self._analysis_timer.stop()
        for worker in self._analysis_workers.values():
            worker.cancel.set()
        self.songInsights = None
        self.metricsWidget.hide()
        self._analysis_busy = False
        self.songTitleLabel.setText("正在读取乐谱…" if path.strip() else "你的下一首方块音乐")
        self.songMetaLabel.setText(Path(path).name if path.strip() else "选好乐谱后，这里会显示歌曲信息和音域检查。")
        self.analysisStatusLabel.setText("正在准备歌曲概览…" if path.strip() else "选择 NBS 文件后自动分析。")
        if path.strip() and not self._closed:
            self._analysis_timer.start()

    def _start_analysis(self):
        if self._closed:
            return
        path = self.getInputFile().strip()
        if not path:
            return
        worker = _InsightWorker(self._analysis_revision, path)
        worker.signals.finished.connect(self._analysis_done)
        self._analysis_workers[worker.revision] = worker
        self._analysis_busy = True
        self.analysisStatusLabel.setText("正在统计音符、轨道与乐器…")
        QThreadPool.globalInstance().start(worker)

    def _analysis_done(self, revision, path, result, error):
        self._analysis_workers.pop(revision, None)
        if self._closed or revision != self._analysis_revision or path != self.getInputFile().strip():
            return
        self._analysis_busy = False
        if error or result is None:
            self.songTitleLabel.setText("暂时无法显示歌曲概览")
            self.analysisStatusLabel.setText(error or "请重新选择 NBS 文件。")
            return
        self.songInsights = result
        self.songTitleLabel.setText(result.title)
        self.songMetaLabel.setText(f"{result.author}  ·  约 {result.duration_text}  ·  {result.tempo:g} NBS tick/秒")
        for key, value in (("notes", result.note_count), ("layers", result.used_layer_count),
                           ("range", result.out_of_range_count), ("custom", result.custom_note_count)):
            self.metricLabels[key].setText(f"{value:,}")
        self.metricsWidget.show()
        findings = []
        if result.out_of_range_count:
            findings.append(f"{result.out_of_range_count:,} 个音符超出 33–57 音域，当前导出会回落到最低音。")
        if result.custom_note_count:
            findings.append(f"使用 {len(result.custom_instruments)} 种自定义乐器，可前往「自定义音色」配置样本。")
        self.analysisStatusLabel.setText("\n".join(findings) or "音高均在音符盒的 25 音范围内，可以继续规划布局。")
        self.analysisStatusLabel.setToolTip("\n".join(f"{item.name}：{item.note_count:,} 个音符" for item in result.custom_instruments))
        self.analysisReady.emit(result)

    def _browseOutputFile(self):
        ext = ".schem" if self.getType() == "schematic" else ".mcfunction"
        filters = "Schematic (*.schem)" if ext == ".schem" else "McFunction (*.mcfunction)"
        path, _ = QFileDialog.getSaveFileName(self, "选择结构保存位置", self.getOutputFile(), filters)
        if path:
            if not path.lower().endswith(ext):
                path += ext
            self.outputFileCard.setText(path)

    def shutdown(self):
        self._closed = True
        self._analysis_revision += 1
        self._analysis_timer.stop()
        self._analysis_busy = False
        for worker in self._analysis_workers.values():
            worker.cancel.set()

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)

    def getInputFile(self):
        return self.inputFileCard.text()

    def setInputFile(self, path):
        self.inputFileCard.setText(path)

    def getOutputFile(self):
        return self.outputFileCard.text()

    def setOutputFile(self, path):
        self.outputFileCard.setText(path)

    def getVersion(self):
        return self.versionCard.currentData()

    def setVersion(self, version):
        for index in range(self.versionCard.comboBox.count()):
            if self.versionCard.comboBox.itemData(index) == version:
                self.versionCard.setCurrentIndex(index)
                return

    def getType(self):
        return self.typeCard.currentData()

    def setType(self, type_str):
        for index in range(self.typeCard.comboBox.count()):
            if self.typeCard.comboBox.itemData(index) == type_str:
                self.typeCard.setCurrentIndex(index)
                return

    def setStatus(self, text):
        self.statusLabel.setText(text)

    def setProgressVisible(self, visible):
        self.progressBar.setVisible(visible)

    def showInfoBar(self, title, content, is_error=False):
        method = InfoBar.error if is_error else InfoBar.success
        method(title=title, content=content, orient=Qt.Orientation.Horizontal,
               isClosable=True, position=InfoBarPosition.TOP,
               duration=5000 if is_error else 2000, parent=self)
