"""Small, theme-aware building blocks shared by the studio pages."""

from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from qfluentwidgets import TitleLabel, BodyLabel, CaptionLabel, ComboBox, isDarkTheme, qconfig


class ChoiceComboBox(ComboBox):
    """下拉框：弹出列表紧贴窗口，避免出现一圈"透明边框"。

    qfluentwidgets 的 RoundMenu 会在列表四周预留透明边距，用于绘制
    QGraphicsDropShadowEffect 投影；而 Windows 会在弹窗窗口外沿再描一圈边框，
    于是这段透明边距就显示成悬在列表外的独立边框。这里去掉投影与边距，
    让弹窗边框与列表自身的边框重合。
    """

    def _createComboMenu(self):
        menu = super()._createComboMenu()
        menu.view.setGraphicsEffect(None)
        layout = menu.layout()
        if layout is not None:
            layout.setContentsMargins(0, 0, 0, 0)
        menu.adjustSize()
        return menu


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
        content = page_content(page)
        color = "#181c23" if isDarkTheme() else "#f4f6f8"
        stylesheet = f"QScrollArea#{page.objectName()} {{ background: {color}; border: none; }}"
        if content is not None:
            content.setAutoFillBackground(False)
            stylesheet += f"QWidget#{content.objectName()} {{ background: {color}; }}"
        page.setStyleSheet(stylesheet)


def page_content(page):
    """返回滚动页的内容容器。

    页面通常按 qfluentwidgets 的约定把内容控件保存为 ``scrollWidget``；
    只调用 ``setWidget`` 的页面则回退到 ``widget()``。
    """
    content = getattr(page, "scrollWidget", None)
    return content if content is not None else page.widget()


def apply_page_style(page):
    """Apply only page backgrounds; Fluent controls retain their own styling."""
    if hasattr(page, "_studio_palette"):
        page._studio_palette.apply()
        return
    content = page_content(page)
    if content is not None:
        content.setObjectName(page.objectName() + "Content")
    page._studio_palette = _PagePalette(page)


def table_headers(table):
    """返回表格的（垂直, 水平）表头。

    PyQt6 的类型存根把 ``verticalHeader()`` / ``horizontalHeader()`` 标成
    ``QHeaderView | None``，但 Qt 保证表格存在时表头始终存在，因此这里用
    assert 把可空类型收敛掉，避免调用处反复写忽略注释。
    """
    vertical, horizontal = table.verticalHeader(), table.horizontalHeader()
    assert vertical is not None and horizontal is not None
    return vertical, horizontal


def cell_text(table, row, column):
    """读取单元格文本。

    PyQt6 的类型存根把 ``item()`` 标成可空，但表格自带行时该单元格必然存在；
    这里把可空类型收敛为字符串，避免调用处反复判空。
    """
    item = table.item(row, column)
    return item.text() if item is not None else ""


def copy_to_clipboard(text):
    """写入系统剪贴板；没有可用剪贴板的环境下静默跳过。"""
    clipboard = QApplication.clipboard()
    if clipboard is not None:
        clipboard.setText(text)


def fit_table_height(table, *, min_rows=3, max_height=380):
    """让表格高度跟随行数，避免少量数据时卡片被拉出大片空白。"""
    vertical, header = table_headers(table)
    header_height = max(header.height(), header.sizeHint().height())
    row_height = table.rowHeight(0) if table.rowCount() else vertical.defaultSectionSize()
    rows = max(table.rowCount(), min_rows)
    table.setFixedHeight(min(header_height + rows * row_height + 2 * table.frameWidth(), max_height))
