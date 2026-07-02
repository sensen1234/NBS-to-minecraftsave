"""
使用文档界面 - 加载预生成的 wiki_content.py (由 tools/generate_wiki_ui.py 生成)

QTextBrowser 使用 Qt 富文本引擎，CSS 支持有限，因此：
- CSS 在生成阶段已适配 Qt (无 var/shadow/border-radius/nth-child)
- 图片在生成阶段已添加 width 属性 (Qt 不支持 CSS max-width)
- 运行时根据主题选择 CSS，并在窗口缩放时动态调整图片大小
"""

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QTextCursor, QTextDocument
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from qfluentwidgets import TitleLabel, isDarkTheme

from .wiki_content import WIKI_CSS_DARK, WIKI_CSS_LIGHT, WIKI_HTML


class WikiInterface(QWidget):
    """使用文档界面 - 预渲染 HTML"""

    # 图片最小宽度限制 (防止过度缩小)
    MIN_IMG_WIDTH = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("wikiInterface")
        self._rescaleTimer = QTimer(self)
        self._rescaleTimer.setSingleShot(True)
        self._rescaleTimer.timeout.connect(self._rescaleImages)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 20, 36, 20)
        layout.setSpacing(12)

        # 标题栏 (与其他页面保持一致)
        self.titleLabel = TitleLabel("使用文档", self)
        layout.addWidget(self.titleLabel)

        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setOpenExternalLinks(True)
        self._applyStyle()

        layout.addWidget(self.textBrowser, 1)

        self._loadContent()

    def _applyStyle(self):
        self.textBrowser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(128, 128, 128, 0.35);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(128, 128, 128, 0.6);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: rgba(128, 128, 128, 0.35);
                border-radius: 4px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(128, 128, 128, 0.6);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def _loadContent(self):
        """加载 HTML 内容，根据当前主题选择 CSS"""
        css = WIKI_CSS_DARK if isDarkTheme() else WIKI_CSS_LIGHT
        html = (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head>"
            f"<body>{WIKI_HTML}</body></html>"
        )
        self.textBrowser.setHtml(html)
        # 延迟执行一次图片缩放
        QTimer.singleShot(50, self._rescaleImages)

    def _rescaleImages(self):
        """根据视口宽度动态调整图片大小 (Qt 不支持 CSS max-width)"""
        vw = self.textBrowser.viewport().width() - 24
        if vw < self.MIN_IMG_WIDTH:
            return

        doc = self.textBrowser.document()
        cursor = QTextCursor(doc)
        modified = False

        block = doc.firstBlock()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                fmt = frag.charFormat()
                if fmt.isImageFormat():
                    img_fmt = fmt.toImageFormat()
                    name = img_fmt.name()

                    # 获取原始图片尺寸
                    resource = doc.resource(
                        int(QTextDocument.ResourceType.ImageResource),
                        QUrl(name)
                    )

                    orig_w = 0
                    orig_h = 0
                    if resource is not None:
                        # resource 是 QVariant，尝试转换为 QPixmap/QImage
                        try:
                            if hasattr(resource, 'width') and hasattr(resource, 'height'):
                                orig_w = resource.width()
                                orig_h = resource.height()
                            elif hasattr(resource, 'size'):
                                sz = resource.size()
                                orig_w = sz.width()
                                orig_h = sz.height()
                        except Exception:
                            pass

                    if orig_w > 0 and orig_h > 0:
                        target_w = min(orig_w, vw)
                        # 仅在尺寸变化时更新
                        current_w = int(img_fmt.width())
                        if current_w != target_w:
                            ratio = target_w / orig_w
                            img_fmt.setWidth(int(target_w))
                            img_fmt.setHeight(int(orig_h * ratio))

                            # 应用新格式到该 fragment
                            apply_cursor = QTextCursor(block)
                            apply_cursor.setPosition(frag.position())
                            apply_cursor.setPosition(
                                frag.position() + frag.length(),
                                QTextCursor.MoveMode.KeepAnchor
                            )
                            apply_cursor.setCharFormat(img_fmt)
                            modified = True
                it += 1
            block = block.next()

    def resizeEvent(self, event):
        """窗口缩放时延迟重新调整图片大小"""
        super().resizeEvent(event)
        self._rescaleTimer.start(150)

    def reloadContent(self):
        """主题切换后刷新配色"""
        self._loadContent()
