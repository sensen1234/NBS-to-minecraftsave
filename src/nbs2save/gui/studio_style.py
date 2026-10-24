"""Small, theme-aware building blocks shared by the studio pages."""

from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import TitleLabel, BodyLabel, CaptionLabel, isDarkTheme, qconfig


def label_font(label, size, weight=QFont.Weight.Normal):
    font = label.font()
    font.setPixelSize(size)
    font.setWeight(weight)
    label.setFont(font)
    return label


def muted_label(label):
    """Keep secondary text legible when the app theme changes."""
    label.setTextColor(QColor("#64748b"), QColor("#a6b3c5"))
    return label


class PageHeader(QWidget):
    def __init__(self, title, description, eyebrow="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(7)
        if eyebrow:
            self.eyebrowLabel = label_font(CaptionLabel(eyebrow, self), 11, QFont.Weight.DemiBold)
            self.eyebrowLabel.setTextColor(QColor("#007f79"), QColor("#66d9cc"))
            layout.addWidget(self.eyebrowLabel)
        self.titleLabel = label_font(TitleLabel(title, self), 28, QFont.Weight.DemiBold)
        layout.addWidget(self.titleLabel)
        self.descriptionLabel = muted_label(label_font(BodyLabel(description, self), 13))
        self.descriptionLabel.setWordWrap(True)
        layout.addWidget(self.descriptionLabel)


class _PagePalette(QObject):
    def __init__(self, page):
        super().__init__(page)
        self.page = page
        qconfig.themeChanged.connect(self.apply)
        self.apply()

    @pyqtSlot()
    def apply(self):
        page = self.page
        content = page.scrollWidget
        color = "#181c23" if isDarkTheme() else "#f4f6f8"
        content.setAutoFillBackground(False)
        page.setStyleSheet(
            f"QScrollArea#{page.objectName()} {{ background: {color}; border: none; }}"
            f"QWidget#{content.objectName()} {{ background: {color}; }}"
        )


def apply_page_style(page):
    """Apply only page backgrounds; Fluent controls retain their own styling."""
    if hasattr(page, "_studio_palette"):
        page._studio_palette.apply()
        return
    page.scrollWidget.setObjectName(page.objectName() + "Content")
    page._studio_palette = _PagePalette(page)
