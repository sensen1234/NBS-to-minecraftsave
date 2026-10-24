"""A read-only, asynchronous review of the current creation settings."""

from copy import deepcopy

import pynbs
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea, CardWidget, BodyLabel, PrimaryPushButton, isDarkTheme

from ..core.creation_checks import check_creation
from .studio_style import PageHeader, apply_page_style, muted_label, label_font


class _Signals(QObject):
    finished = pyqtSignal(object, str)


class _CheckWorker(QRunnable):
    def __init__(self, path, groups, config):
        super().__init__()
        self.path, self.groups, self.config = path, deepcopy(groups), deepcopy(config)
        self.signals = _Signals()

    def run(self):
        try:
            result = check_creation(pynbs.read(self.path), self.groups, self.config)
            self.signals.finished.emit(result, "")
        except Exception as exc:
            self.signals.finished.emit([], str(exc))


class CreationCheckDialog(QDialog):
    def __init__(self, path, groups, config, parent=None):
        super().__init__(parent)
        self.setObjectName("creationCheckDialog")
        background = "#181c23" if isDarkTheme() else "#f4f6f8"
        self.setStyleSheet(f"QDialog#creationCheckDialog {{ background: {background}; }}")
        self._closed = False
        self.setWindowTitle("创作检查")
        self.resize(660, 580)
        self.setMinimumSize(480, 380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)
        layout.addWidget(PageHeader("创作检查", "检查轨道分配、音域、采样文件与输出格式。", "PROJECT REVIEW", self))
        self.status = BodyLabel("正在读取 NBS 并检查当前设置…", self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.area = ScrollArea(self)
        self.area.setObjectName("creationReview")
        self.area.scrollWidget = QWidget()
        self.results = QVBoxLayout(self.area.scrollWidget)
        self.results.setContentsMargins(8, 8, 8, 8)
        self.results.setSpacing(8)
        self.results.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.area.setWidget(self.area.scrollWidget)
        self.area.setWidgetResizable(True)
        apply_page_style(self.area)
        layout.addWidget(self.area, 1)
        note = muted_label(BodyLabel("检查结果供创作参考；实际结构覆盖和红石连通性请结合 3D 预览与游戏验证。", self))
        note.setWordWrap(True)
        label_font(note, 12)
        layout.addWidget(note)
        close = PrimaryPushButton("返回编辑", self)
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
        self.worker = _CheckWorker(path, groups, config)
        self.worker.signals.finished.connect(self._show_results)
        QThreadPool.globalInstance().start(self.worker)

    def _show_results(self, issues, error):
        if self._closed:
            return
        if error:
            self.status.setText("无法检查：" + error)
            return
        counts = {level: sum(i.severity == level for i in issues) for level in ("error", "warning", "info")}
        self.status.setText(
            f"{counts['error']} 项需修正 · {counts['warning']} 项建议 · {counts['info']} 项提示"
            if issues else "已完成检查，未发现上述范围内的问题。"
        )
        for issue in sorted(issues, key=lambda i: {"error": 0, "warning": 1, "info": 2}[i.severity]):
            card = CardWidget(self.area.scrollWidget)
            row = QVBoxLayout(card)
            row.setContentsMargins(16, 12, 16, 14)
            level = {"error": "需修正", "warning": "建议", "info": "提示"}[issue.severity]
            title = label_font(BodyLabel(f"{level} · {issue.title}", card), 14, QFont.Weight.DemiBold)
            light, dark = {"error": ("#b42318", "#ffb4aa"), "warning": ("#936000", "#f0ca75"), "info": ("#007f79", "#66d9cc")}[issue.severity]
            title.setTextColor(QColor(light), QColor(dark))
            title.setWordWrap(True)
            row.addWidget(title)
            detail = muted_label(BodyLabel(issue.detail, card))
            detail.setWordWrap(True)
            row.addWidget(detail)
            self.results.addWidget(card)

    def done(self, result):
        self._closed = True
        super().done(result)
