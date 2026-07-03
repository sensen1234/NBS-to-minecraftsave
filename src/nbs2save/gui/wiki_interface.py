"""
使用文档界面 - 使用 QFluentWidgets 组件原生渲染 wiki 内容

wiki_content.py 由 tools/generate_wiki_ui.py 从 wiki.md 自动生成，
包含结构化数据 (add_heading / add_paragraph / add_table / ...)。
本模块遍历这些数据，动态创建 QFluentWidgets 组件完成渲染。
"""

import os
import re

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from qfluentwidgets import (
    ScrollArea,
    CardWidget,
    TitleLabel,
    SubtitleLabel,
    StrongBodyLabel,
    BodyLabel,
    CaptionLabel,
    PlainTextEdit,
    TableWidget,
    HyperlinkButton,
    FluentIcon,
    isDarkTheme,
    ToolButton,
    TransparentToolButton,
)

from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView, QSizePolicy, QFrame

from .wiki_content import build_wiki_content


# ── markdown 内联格式: **bold**, `code`, [text](url) → HTML ──

_MD_PATTERNS = [
    (re.compile(r'\*\*(.+?)\*\*'), r'<b>\1</b>'),
    (re.compile(r'`([^`]+)`'),     r'<code>\1</code>'),
    (re.compile(r'\[([^\]]+)\]\(([^)]+)\)'), r'<a href="\2">\1</a>'),
    (re.compile(r'~~(.+?)~~'),     r'<s>\1</s>'),
]


def _md_to_html(text: str) -> str:
    """将 markdown 内联格式转为 HTML (供 QLabel 使用)"""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # 还原我们手动插入的 <b>/<code>/<a>/<s> 标记
    for pat, repl in _MD_PATTERNS:
        text = pat.sub(repl, text)
    return text


def _md_to_plain(text: str) -> str:
    """将 markdown 内联格式转为纯文本"""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    return text


def _find_img_path(raw_src: str) -> str:
    """从 wiki 图片引用 (![alt](img/xxx.png)) 解析出实际文件路径"""
    m = re.search(r'!\[[^\]]*\]\(([^)]+)\)', raw_src)
    if not m:
        m = re.search(r'src="([^"]*)"', raw_src)
    src = m.group(1) if m else raw_src

    if src.startswith(("http://", "https://", "file://", "data:")):
        return src
    if src.startswith("file:///"):
        return src[8:].replace("/", os.sep)

    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base, "..", "..", "..", "documents", src),
        os.path.join(os.getcwd(), "documents", src),
    ]
    for p in candidates:
        ap = os.path.abspath(p)
        if os.path.isfile(ap):
            return ap
    return ""


# ── Interpreter: 结构化数据 → QFluentWidgets 组件 ──

class WikiContentInterpreter:
    """遍历 wiki 结构化元素，创建对应的 QFluentWidgets 组件"""

    def __init__(self, layout: QVBoxLayout, parent: QWidget, collect_only: bool = False):
        self.layout = layout
        self.parent = parent
        self._collect_only = collect_only
        self._headings = []          # [(level, plain_text, widget)]

    def get_headings(self):
        """返回已收集的标题列表 [(level, text, widget)]"""
        return list(self._headings)

    def add_heading(self, level: int, text: str):
        """添加标题 (TitleLabel / SubtitleLabel / StrongBodyLabel / BodyLabel)"""
        t = _md_to_plain(text)
        if self._collect_only:
            # 收集阶段: 只记录标题数据, 不创建任何 widget
            self._headings.append((level, t, None))
            return

        if level == 1:
            w = TitleLabel(t, self.parent)
            w.setStyleSheet("font-size: 24px; font-weight: 700;")
        elif level == 2:
            w = SubtitleLabel(t, self.parent)
            w.setStyleSheet("font-size: 20px; font-weight: 700;")
        elif level == 3:
            w = StrongBodyLabel(t, self.parent)
            w.setStyleSheet("font-size: 17px; font-weight: 700;")
        elif level == 4:
            w = BodyLabel(t, self.parent)
            w.setStyleSheet("font-size: 15px; font-weight: 600;")
        else:
            w = BodyLabel(t, self.parent)
            w.setStyleSheet("font-size: 14px; font-weight: 600;")

        margin_top = 6 if level == 1 else 18 if level == 2 else 14
        w.setContentsMargins(0, margin_top, 0, 4)
        self.layout.addWidget(w)

        self._headings.append((level, t, w))

    def add_paragraph(self, text: str):
        """添加段落 (BodyLabel, 支持内联格式)"""
        if self._collect_only:
            return
        w = BodyLabel(self.parent)
        w.setWordWrap(True)
        w.setTextFormat(Qt.TextFormat.RichText)
        w.setText(_md_to_html(text))
        w.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        w.setOpenExternalLinks(True)
        w.setStyleSheet("font-size: 14px; line-height: 20px;")
        self.layout.addWidget(w)

    def add_code_block(self, language: str, content: str):
        """添加代码块 (CardWidget + 语言标签 + 复制按钮 + PlainTextEdit)"""
        if self._collect_only:
            return
        from PyQt6.QtWidgets import QApplication

        card = CardWidget(self.parent)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # 顶部栏: 语言标签 + 复制按钮
        header = QWidget(card)
        headerLayout = QHBoxLayout(header)
        headerLayout.setContentsMargins(8, 4, 8, 4)
        headerLayout.setSpacing(4)

        if language:
            langLabel = CaptionLabel(language, header)
            langLabel.setStyleSheet("font-size: 11px; color: #888;")
            headerLayout.addWidget(langLabel)
        else:
            headerLayout.addStretch(1)

        copyBtn = ToolButton(FluentIcon.COPY, header)
        copyBtn.setFixedSize(28, 24)
        copyBtn.setToolTip("复制代码")
        code_content = content
        copyBtn.clicked.connect(
            lambda: QApplication.clipboard().setText(code_content)
        )
        headerLayout.addWidget(copyBtn)
        cl.addWidget(header)

        te = PlainTextEdit(card)
        te.setPlainText(content)
        te.setReadOnly(True)
        te.setFrameShape(QFrame.Shape.NoFrame)

        line_count = content.count("\n") + 1
        row_h = te.fontMetrics().lineSpacing() or 18
        te.setFixedHeight(min(line_count * row_h + 16, 500))

        isDark = isDarkTheme()
        te.setStyleSheet(f"""
            PlainTextEdit {{
                background-color: {"#1e1e1e" if isDark else "#f8f8f8"};
                color: {"#d4d4d4" if isDark else "#2b2b2b"};
                font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
                font-size: 13px;
                padding: 8px 12px;
                border: none;
                border-left: 3px solid {"#4cc2ff" if isDark else "#0078d4"};
            }}
        """)
        cl.addWidget(te)
        self.layout.addWidget(card)

    def add_table(self, headers: list, rows: list):
        """添加表格 (TableWidget)"""
        if self._collect_only:
            return
        card = CardWidget(self.parent)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)

        table = TableWidget(card)
        col_count = len(headers)
        row_count = len(rows)
        table.setColumnCount(col_count)
        table.setRowCount(row_count)
        table.setHorizontalHeaderLabels(headers)

        hv = table.horizontalHeader()
        for c in range(col_count):
            hv.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)

        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                item = QTableWidgetItem(_md_to_plain(cell))
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r, c, item)

        table.verticalHeader().setVisible(False)
        table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(TableWidget.SelectionMode.NoSelection)

        vis_rows = min(row_count, 20)
        row_h = table.verticalHeader().defaultSectionSize() or 30
        header_h = table.horizontalHeader().height() or 28
        table.setFixedHeight(vis_rows * row_h + header_h + 4)

        cl.addWidget(table)
        self.layout.addWidget(card)

    def add_blockquote(self, content: str):
        """添加引用块 (CardWidget + 左边框)"""
        if self._collect_only:
            return
        isDark = isDarkTheme()
        accent = "#4cc2ff" if isDark else "#0078d4"
        bg = "#1a2632" if isDark else "#eef6fd"
        text_color = "#aaaaaa" if isDark else "#555555"

        card = QWidget(self.parent)
        card.setStyleSheet(f"""
            background-color: {bg};
            border-left: 3px solid {accent};
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 10, 16, 10)

        w = BodyLabel(card)
        w.setWordWrap(True)
        w.setTextFormat(Qt.TextFormat.RichText)
        w.setText(_md_to_html(content))
        w.setStyleSheet(f"color: {text_color}; background: transparent; border: none;")
        cl.addWidget(w)
        self.layout.addWidget(card)

    def add_image(self, raw_src: str, alt: str):
        """添加图片 (QLabel + 居中显示)"""
        if self._collect_only:
            return
        MAX_W = 560
        path = _find_img_path(raw_src)
        if not path:
            self.add_paragraph(f"[图片未找到: {raw_src}]")
            return

        container = QWidget(self.parent)
        containerLayout = QVBoxLayout(container)
        containerLayout.setContentsMargins(0, 8, 0, 0)
        containerLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        imgLabel = QLabel(container)
        imgLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        try:
            pix = QPixmap(path)
            if pix.isNull():
                raise ValueError(f"无法加载图片: {path}")

            orig_w = pix.width()
            orig_h = pix.height()
            if orig_w > MAX_W:
                ratio = MAX_W / orig_w
                pix = pix.scaled(
                    QSize(MAX_W, int(orig_h * ratio)),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

            imgLabel.setPixmap(pix)
            imgLabel.setStyleSheet("background: transparent;")
        except Exception as e:
            imgLabel.setText(f"[图片加载失败: {e}]")
            imgLabel.setStyleSheet("color: #999; background: transparent;")

        containerLayout.addWidget(imgLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        if alt:
            caption = CaptionLabel(alt, container)
            caption.setStyleSheet("color: #999; font-size: 12px;")
            caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
            containerLayout.addWidget(caption)

        self.layout.addWidget(container)

    def add_bullet_list(self, items: list):
        """添加无序列表"""
        if self._collect_only:
            return
        for item in items:
            w = BodyLabel(self.parent)
            w.setWordWrap(True)
            w.setTextFormat(Qt.TextFormat.RichText)
            w.setText(f"&nbsp;&nbsp;\u2022&nbsp;&nbsp;{_md_to_html(item)}")
            w.setContentsMargins(8, 2, 8, 2)
            self.layout.addWidget(w)

    def add_numbered_list(self, items: list):
        """添加有序列表"""
        if self._collect_only:
            return
        for idx, item in enumerate(items, 1):
            w = BodyLabel(self.parent)
            w.setWordWrap(True)
            w.setTextFormat(Qt.TextFormat.RichText)
            w.setText(f"&nbsp;&nbsp;{idx}.&nbsp;&nbsp;{_md_to_html(item)}")
            w.setContentsMargins(8, 2, 8, 2)
            self.layout.addWidget(w)

    def add_separator(self):
        """添加分隔线"""
        if self._collect_only:
            return
        sep = QFrame(self.parent)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: rgba(128, 128, 128, 0.25);")
        sep.setContentsMargins(0, 12, 0, 12)
        self.layout.addWidget(sep)


# ── Wiki 界面 ──

class WikiInterface(ScrollArea):
    """使用文档界面 - QFluentWidgets 原生渲染"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("wikiInterface")
        self.setWidgetResizable(True)
        self.enableTransparentBackground()

        self.scrollWidget = QWidget(self)
        self.scrollWidget.setObjectName("wikiScrollWidget")

        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(6)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._buildContent()
        self.setWidget(self.scrollWidget)

    def _buildContent(self):
        """构建页面内容 (标题 + 目录 + wiki 正文)"""
        # 页面标题
        self.titleLabel = TitleLabel("使用文档", self.scrollWidget)
        self.titleLabel.setStyleSheet("font-size: 26px; font-weight: 700;")
        self.vBoxLayout.addWidget(self.titleLabel)

        # 第一遍: 仅收集标题结构 (不创建任何 widget)
        collector = WikiContentInterpreter(
            self.vBoxLayout, self.scrollWidget, collect_only=True,
        )
        build_wiki_content(collector)
        headings = collector.get_headings()

        # 构建目录 (只展示 level 2-4，跳过文档标题 level 1)
        toc_items = [(lv, txt) for lv, txt, _ in headings if lv >= 2]
        if toc_items:
            self._buildToc(toc_items)

        # 第二遍: 正式渲染 wiki 内容 (此时 headings 中的 widget 才会被创建)
        interpreter = WikiContentInterpreter(self.vBoxLayout, self.scrollWidget)
        build_wiki_content(interpreter)

        self.vBoxLayout.addStretch(1)

        # 缓存 headings 引用 (含 widget)，供 TOC 跳转使用
        self._headings = interpreter.get_headings()

    def _buildToc(self, toc_items):
        """构建目录卡片 (支持折叠/展开)"""
        card = CardWidget(self.scrollWidget)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(0)

        # 目录标题行
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        toc_icon = TransparentToolButton(FluentIcon.BOOK_SHELF, card)
        toc_icon.setFixedSize(28, 28)
        toc_icon.setEnabled(False)
        header_row.addWidget(toc_icon)
        toc_title = SubtitleLabel("目录", card)
        toc_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_row.addWidget(toc_title)
        header_row.addStretch()

        # 全部折叠/展开按钮
        btn_collapse_all = QPushButton("全部折叠", card)
        btn_collapse_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_collapse_all.setFixedHeight(24)
        btn_collapse_all.setStyleSheet(
            "QPushButton { font-size: 12px; color: #0078d4; background: transparent; "
            "border: none; padding: 0 8px; border-radius: 4px; }"
            "QPushButton:hover { background: rgba(0, 120, 212, 0.08); }"
        )
        header_row.addWidget(btn_collapse_all)
        cl.addLayout(header_row)
        cl.addSpacing(8)

        isDark = isDarkTheme()

        # 样式配置
        _STYLE = {
            2: {"fs": "14px", "fw": "600",
                "fc": "#1a1a1a" if not isDark else "#e0e0e0",
                "arrow_color": "#0078d4" if not isDark else "#4cc2ff"},
            3: {"fs": "13px", "fw": "500",
                "fc": "#444444" if not isDark else "#bbbbbb",
                "arrow_color": "#666666" if not isDark else "#999999"},
            4: {"fs": "12px", "fw": "400",
                "fc": "#666666" if not isDark else "#999999",
                "arrow_color": None},
        }

        def _create_entry(parent_widget, level, text, toc_idx, has_children, collapsed):
            """创建单个目录条目 widget"""
            indent = (level - 2) * 18
            s = _STYLE[level]

            row_widget = QWidget(parent_widget)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(indent, 2, 4, 2)
            row_layout.setSpacing(4)

            arrow_btn = None
            if has_children and level < 4:
                arrow_btn = QPushButton(
                    "\u25B8" if collapsed else "\u25BE", row_widget,
                )
                arrow_btn.setFixedSize(18, 22)
                arrow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                arrow_btn.setStyleSheet(
                    f"QPushButton {{ color: {s['arrow_color']}; font-size: 12px; "
                    f"background: transparent; border: none; font-weight: bold; }}"
                    f"QPushButton:hover {{ color: #0078d4; }}"
                )
                row_layout.addWidget(arrow_btn)
            else:
                # 无子项时用圆点占位
                dot = QLabel("\u2022", row_widget)
                dot.setFixedSize(18, 22)
                dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
                dot.setStyleSheet(
                    f"color: {'#999999' if not isDark else '#666666'}; "
                    f"font-size: 10px; background: transparent;"
                )
                row_layout.addWidget(dot)

            # 标题文字按钮
            text_btn = QPushButton(text, row_widget)
            text_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            text_btn.setStyleSheet(
                f"QPushButton {{ text-align: left; padding: 2px 4px; "
                f"border-radius: 4px; font-size: {s['fs']}; font-weight: {s['fw']}; "
                f"color: {s['fc']}; background: transparent; border: none; }}"
                f"QPushButton:hover {{ color: #0078d4; "
                f"background: rgba(0, 120, 212, 0.08); }}"
            )
            text_btn.setFixedHeight(24)
            text_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            text_btn.clicked.connect(
                lambda checked=False, i=toc_idx: self._scrollToHeading(i)
            )
            row_layout.addWidget(text_btn, 1)

            return row_widget, arrow_btn

        # 构建树形结构 (递归)
        self._toc_sections = []  # [(arrow_btn, children_container)]

        def _build(parent_layout, items, depth=0):
            """递归构建目录树"""
            i = 0
            while i < len(items):
                level, text = items[i]
                # 找到全局 toc_idx (在 toc_items 中的索引)
                toc_idx = toc_items.index(items[i])

                # 统计后续子项 (level > 当前)
                children = []
                j = i + 1
                while j < len(items) and items[j][0] > level:
                    children.append(items[j])
                    j += 1

                has_children = len(children) > 0 and level < 4
                # level 2 默认展开, level 3 默认折叠
                collapsed = level >= 3

                row_widget, arrow_btn = _create_entry(
                    None, level, text, toc_idx, has_children, collapsed,
                )
                parent_layout.addWidget(row_widget)

                if has_children:
                    # 子项容器
                    child_container = QWidget(card)
                    child_layout = QVBoxLayout(child_container)
                    child_layout.setContentsMargins(0, 0, 0, 0)
                    child_layout.setSpacing(0)
                    _build(child_layout, children, depth + 1)

                    child_container.setVisible(not collapsed)
                    parent_layout.addWidget(child_container)

                    # 箭头按钮切换折叠
                    self._toc_sections.append((arrow_btn, child_container))
                    if arrow_btn:
                        arrow_btn.clicked.connect(
                            lambda checked=False,
                            ab=arrow_btn, cc=child_container: self._toggleTocSection(ab, cc)
                        )

                i = j

        _build(cl, toc_items)

        # 全部折叠/展开逻辑
        self._toc_all_expanded = True

        def _toggle_all():
            expand = not self._toc_all_expanded
            self._toc_all_expanded = expand
            btn_collapse_all.setText("全部折叠" if expand else "全部展开")
            for arrow, container in self._toc_sections:
                container.setVisible(expand)
                arrow.setText("\u25BE" if expand else "\u25B8")

        btn_collapse_all.clicked.connect(_toggle_all)

        self.vBoxLayout.addWidget(card)

    def _toggleTocSection(self, arrow_btn, container):
        """切换目录节的折叠/展开"""
        visible = container.isVisible()
        container.setVisible(not visible)
        arrow_btn.setText("\u25B8" if visible else "\u25BE")

    def _scrollToHeading(self, toc_idx):
        """平滑滚动到 toc_items[toc_idx] 对应的标题 widget"""
        # toc_idx 是 toc_items 中的索引, 对应 self._headings 中 level>=2 的那些
        if not hasattr(self, '_headings'):
            return
        # 找到 self._headings 中第 toc_idx 个 level>=2 的条目
        count = 0
        for level, text, widget in self._headings:
            if level >= 2:
                if count == toc_idx and widget is not None:
                    QTimer.singleShot(0, lambda w=widget: self.verticalScrollBar().setValue(
                        max(0, w.pos().y() - 20)
                    ))
                    return
                count += 1

    def reloadContent(self):
        """主题切换后重建所有组件"""
        # 清除旧内容
        while self.vBoxLayout.count():
            item = self.vBoxLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._buildContent()
