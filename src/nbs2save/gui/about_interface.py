"""
关于界面 - 展示程序信息
"""

import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout

from qfluentwidgets import (
    ScrollArea,
    CardWidget,
    TitleLabel,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    HyperlinkButton,
    FluentIcon,
    IconWidget,
)


# ── 程序元信息 ──

APP_NAME = "NBS-to-Minecraftsave"
APP_VERSION = "3.0.0.DEV0"
APP_DESCRIPTION = "将 Note Block Studio 制作的音乐文件 (.nbs) 转换为 Minecraft 中可播放格式的强大工具"
DEVELOPERS = ["sensen1234"]
CONTRIBUTORS = ["LY-Xiang", "Lumine1909", "NoteBlockMR", "LeoDreamer2004"]
GITHUB_URL = "https://github.com/sensen1234/NBS-to-minecraftsave"
GITHUB_RELEASES = "https://github.com/sensen1234/NBS-to-minecraftsave/releases"
LICENSE = "Apache License 2.0"
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


class InfoCard(CardWidget):
    """信息卡片 - 图标 + 标题 + 值"""

    def __init__(self, icon, title, value, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # 图标
        iw = IconWidget(icon, self)
        iw.setFixedSize(28, 28)
        layout.addWidget(iw)

        # 文字
        textLayout = QVBoxLayout()
        textLayout.setSpacing(2)
        titleLabel = BodyLabel(title)
        titleLabel.setStyleSheet("color: #888; font-size: 12px;")
        valueLabel = BodyLabel(value)
        valueLabel.setStyleSheet("font-size: 14px; font-weight: 500;")
        textLayout.addWidget(titleLabel)
        textLayout.addWidget(valueLabel)

        layout.addLayout(textLayout)
        layout.addStretch(1)


def _find_avatar_path(username: str) -> str:
    """查找本地头像文件 documents/img/avatar_{username}.png"""
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base, "..", "..", "..", "documents", "img", f"avatar_{username}.png"),
        os.path.join(base, "..", "..", "..", "..", "documents", "img", f"avatar_{username}.png"),
        os.path.join(os.getcwd(), "documents", "img", f"avatar_{username}.png"),
    ]
    for p in candidates:
        ap = os.path.abspath(p)
        if os.path.isfile(ap):
            return ap
    return ""


class DeveloperAvatar(QWidget):
    """单个开发者: 本地头像 + 用户名链接"""

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self._avatarSize = 40

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 头像
        self.avatarLabel = BodyLabel(self)
        self.avatarLabel.setFixedSize(self._avatarSize, self._avatarSize)
        self.avatarLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatarLabel.setStyleSheet(
            f"background-color: #e0e0e0; border-radius: {self._avatarSize // 2}px; color: #aaa;"
        )

        # 加载本地头像
        avatar_path = _find_avatar_path(username)
        if avatar_path:
            pix = QPixmap(avatar_path)
            if not pix.isNull():
                size = self._avatarSize
                display = QPixmap(size, size)
                display.fill(Qt.GlobalColor.transparent)
                painter = QPainter(display)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, size, size)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, size, size, pix)
                painter.end()
                self.avatarLabel.setPixmap(display)
                self.avatarLabel.setStyleSheet("")
            else:
                self.avatarLabel.setText(username[0].upper())
        else:
            self.avatarLabel.setText(username[0].upper())

        layout.addWidget(self.avatarLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        # 用户名链接
        linkBtn = HyperlinkButton(
            FluentIcon.LINK,
            f"https://github.com/{username}",
            username,
            self,
        )
        layout.addWidget(linkBtn, alignment=Qt.AlignmentFlag.AlignCenter)


class DeveloperCard(CardWidget):
    """开发者 & 贡献者卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # ── 开发者 ──
        devTitle = SubtitleLabel("开发者", self)
        devTitle.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(devTitle)

        devsLayout = QHBoxLayout()
        devsLayout.setSpacing(24)
        for username in DEVELOPERS:
            devsLayout.addWidget(DeveloperAvatar(username, self))
        devsLayout.addStretch(1)
        layout.addLayout(devsLayout)

        # ── 贡献者 ──
        contribTitle = SubtitleLabel("贡献者", self)
        contribTitle.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(contribTitle)

        contribLayout = QHBoxLayout()
        contribLayout.setSpacing(24)
        for username in CONTRIBUTORS:
            contribLayout.addWidget(DeveloperAvatar(username, self))
        contribLayout.addStretch(1)
        layout.addLayout(contribLayout)


class AboutInterface(ScrollArea):
    """关于界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutInterface")

        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName("scrollWidget")
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(16)

        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self._initHeader()
        self._initInfoCards()
        self._initDevelopers()
        self._initTechStack()
        self._initLinks()
        self._initDisclaimer()

        self.vBoxLayout.addStretch(1)

    # ── 顶部头部 ──

    def _initHeader(self):
        headerCard = CardWidget(self.scrollWidget)
        headerLayout = QVBoxLayout(headerCard)
        headerLayout.setContentsMargins(32, 28, 32, 28)
        headerLayout.setSpacing(8)
        headerLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 应用名
        nameLabel = TitleLabel(APP_NAME, headerCard)
        nameLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nameLabel.setStyleSheet("font-size: 28px; font-weight: 700;")
        headerLayout.addWidget(nameLabel)

        # 版本号
        versionLabel = SubtitleLabel(f"v{APP_VERSION}", headerCard)
        versionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        versionLabel.setStyleSheet("font-size: 16px; color: #0078d4; font-weight: 600;")
        headerLayout.addWidget(versionLabel)

        # 描述
        descLabel = BodyLabel(APP_DESCRIPTION, headerCard)
        descLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descLabel.setWordWrap(True)
        descLabel.setStyleSheet("font-size: 13px; color: #666; margin-top: 10px;min-height: 40px;")
        headerLayout.addWidget(descLabel)

        self.vBoxLayout.addWidget(headerCard)

    # ── 信息卡片 ──

    def _initInfoCards(self):
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        cards = [
            (FluentIcon.TAG, "版本", f"v{APP_VERSION}"),
            (FluentIcon.CODE, "Python", PYTHON_VERSION),
            (FluentIcon.CERTIFICATE, "许可证", LICENSE),
        ]

        for i, (icon, title, value) in enumerate(cards):
            card = InfoCard(icon, title, value, self.scrollWidget)
            grid.addWidget(card, 0, i)

        self.vBoxLayout.addLayout(grid)

    # ── 开发者卡片 ──

    def _initDevelopers(self):
        card = DeveloperCard(self.scrollWidget)
        self.vBoxLayout.addWidget(card)

    # ── 技术栈 ──

    def _initTechStack(self):
        techCard = CardWidget(self.scrollWidget)
        techLayout = QVBoxLayout(techCard)
        techLayout.setContentsMargins(24, 20, 24, 20)
        techLayout.setSpacing(12)

        titleLabel = SubtitleLabel("技术栈", techCard)
        titleLabel.setStyleSheet("font-size: 16px; font-weight: 600;")
        techLayout.addWidget(titleLabel)

        techs = [
            ("PyQt6", "GUI 框架"),
            ("QFluentWidgets", "Fluent Design 组件库"),
            ("pynbs", "NBS 文件解析"),
            ("mcschematic", "Minecraft 结构文件生成"),
        ]

        for name, desc in techs:
            row = QHBoxLayout()
            nameLabel = BodyLabel(name)
            nameLabel.setStyleSheet("font-size: 13px; font-weight: 600; min-width: 140px;")
            descLabel = CaptionLabel(desc)
            descLabel.setStyleSheet("font-size: 12px; color: #888;")
            row.addWidget(nameLabel)
            row.addWidget(descLabel)
            row.addStretch(1)
            techLayout.addLayout(row)

        self.vBoxLayout.addWidget(techCard)

    # ── 链接 ──

    def _initLinks(self):
        linkCard = CardWidget(self.scrollWidget)
        linkLayout = QHBoxLayout(linkCard)
        linkLayout.setContentsMargins(24, 20, 24, 20)
        linkLayout.setSpacing(16)

        titleLabel = SubtitleLabel("链接", linkCard)
        titleLabel.setStyleSheet("font-size: 16px; font-weight: 600;")
        linkLayout.addWidget(titleLabel)
        linkLayout.addStretch(1)

        githubBtn = HyperlinkButton(
            FluentIcon.GITHUB,
            GITHUB_URL,
            "GitHub 仓库",
            linkCard,
        )
        releaseBtn = HyperlinkButton(
            FluentIcon.DOWNLOAD,
            GITHUB_RELEASES,
            "Releases",
            linkCard,
        )

        linkLayout.addWidget(githubBtn)
        linkLayout.addWidget(releaseBtn)

        self.vBoxLayout.addWidget(linkCard)

    # ── 声明 ──

    def _initDisclaimer(self):
        disclaimerCard = CardWidget(self.scrollWidget)
        disclaimerLayout = QVBoxLayout(disclaimerCard)
        disclaimerLayout.setContentsMargins(24, 20, 24, 20)
        disclaimerLayout.setSpacing(8)

        titleLabel = SubtitleLabel("声明", disclaimerCard)
        titleLabel.setStyleSheet("font-size: 16px; font-weight: 600;")
        disclaimerLayout.addWidget(titleLabel)

        lines = [
            "严禁使用本程序用于生成与《花之舞》(Flower Dance) 有关的 nbs。如需生成，请联系开发者获取授权。",
            "严禁将本程序用于商业用途（如有需要需授权）。",
            "使用本程序生成的作品如发布到视频平台，需要在视频简介标注使用本程序生成。",
        ]
        for line in lines:
            lbl = CaptionLabel(line)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size: 12px; color: #888; line-height: 1.5;")
            disclaimerLayout.addWidget(lbl)

        copyrightLabel = CaptionLabel(f"\n© 2025-2026 sensen1234. All rights reserved.")
        copyrightLabel.setStyleSheet("font-size: 11px; color: #aaa;")
        copyrightLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimerLayout.addWidget(copyrightLabel)

        contribLabel = CaptionLabel(f"贡献者: {' & '.join(CONTRIBUTORS)}")
        contribLabel.setStyleSheet("font-size: 11px; color: #aaa;")
        contribLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimerLayout.addWidget(contribLabel)

        self.vBoxLayout.addWidget(disclaimerCard)
