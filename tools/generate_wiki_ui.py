#!/usr/bin/env python3
"""
wiki.md → wiki_content.py 生成器

开发人员修改 documents/wiki.md 后运行此脚本：
    python tools/generate_wiki_ui.py

即可将 wiki.md 转换为 src/nbs2save/gui/wiki_content.py，
程序运行时直接加载预生成的 HTML，无需运行时依赖 markdown 库。

注意：QTextBrowser 使用 Qt 富文本引擎，CSS 支持有限：
  - 不支持 CSS 变量 var(--xxx)
  - 不支持 box-shadow / border-radius / gradient
  - 不支持 nth-child / :hover 等伪选择器
  - 不支持 max-width / max-height
  - 不支持后代选择器 (如 body.dark th)
因此本生成器输出两套 CSS (LIGHT / DARK)，并直接在 <img> 上设置 width 属性。
"""

import os
import re
import struct
import sys

import markdown


def find_wiki_md() -> str:
    """查找 wiki.md 路径"""
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base, "..", "documents", "wiki.md"),
        os.path.join(os.getcwd(), "documents", "wiki.md"),
    ]
    for p in candidates:
        ap = os.path.abspath(p)
        if os.path.isfile(ap):
            return ap
    print("ERROR: 找不到 wiki.md", file=sys.stderr)
    sys.exit(1)


def find_docs_dir(wiki_path: str) -> str:
    return os.path.dirname(wiki_path)


def get_image_size(path: str):
    """从文件头读取图片尺寸 (PNG / JPEG / GIF / BMP)"""
    try:
        with open(path, "rb") as f:
            header = f.read(32)
        if len(header) < 24:
            return None
        if header[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", header[16:24])
            return w, h
        if header[:3] == b"\xff\xd8\xff":
            with open(path, "rb") as f:
                f.read(2)
                while True:
                    buf = f.read(4)
                    if len(buf) < 4:
                        break
                    marker, length = struct.unpack(">HH", buf)
                    if marker in (0xFFC0, 0xFFC1, 0xFFC2, 0xFFC3):
                        f.read(1)
                        h, w = struct.unpack(">HH", f.read(4))
                        return w, h
                    f.read(length - 2)
        if header[:6] in (b"GIF87a", b"GIF89a"):
            w, h = struct.unpack("<HH", header[6:10])
            return w, h
        if header[:2] == b"BM":
            w, h = struct.unpack("<II", header[18:26])
            return w, h
    except Exception:
        pass
    return None


def resolve_image_paths(html: str, docs_dir: str) -> str:
    """将相对图片路径替换为 file:/// 绝对路径"""
    if not docs_dir:
        return html

    def make_abs(src: str) -> str:
        if src.startswith(("http://", "https://", "file://", "data:")):
            return src
        abs_path = os.path.abspath(os.path.join(docs_dir, src))
        return "file:///" + abs_path.replace("\\", "/")

    html = re.sub(
        r'(<img\s+[^>]*src=")([^"]*)"',
        lambda m: m.group(1) + make_abs(m.group(2)) + '"',
        html,
    )
    html = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda m: "![]({})".format(make_abs(m.group(2))),
        html,
    )
    return html


def constrain_images(html: str, docs_dir: str, max_width: int = 500) -> str:
    """为大图片添加 width 属性 (QTextBrowser 不支持 CSS max-width)"""
    def replacer(match):
        tag = match.group(0)
        src_match = re.search(r'src="([^"]*)"', tag)
        if not src_match:
            return tag
        src = src_match.group(1)

        # 解析为本地文件路径
        if src.startswith("file:///"):
            path = src[8:].replace("/", os.sep)
        elif src.startswith(("http://", "https://", "data:")):
            return tag
        else:
            path = os.path.join(docs_dir, src)

        size = get_image_size(path)
        if size and size[0] > max_width:
            # 移除已有的 width/height 属性
            tag = re.sub(r'\s+width="[^"]*"', "", tag)
            tag = re.sub(r"\s+height=[^>]*", "", tag)
            # 在 <img 后插入 width
            tag = tag.replace("<img", f'<img width="{max_width}"', 1)
        return tag

    return re.sub(r"<img\s+[^>]*/?>", replacer, html)


# ============================================================
# CSS — 仅使用 QTextBrowser (Qt Rich Text) 支持的属性
# 不使用: var(), box-shadow, border-radius, nth-child, gradient
# ============================================================

def build_css_light() -> str:
    return """
body { font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; font-size: 14px; color: #2b2b2b; }
h1 { font-size: 24px; font-weight: 600; color: #0078d4; border-bottom: 2px solid #0078d4; padding-bottom: 8px; margin-top: 6px; margin-bottom: 18px; }
h2 { font-size: 19px; font-weight: 600; color: #1a1a1a; border-left: 4px solid #0078d4; padding-left: 10px; margin-top: 30px; margin-bottom: 14px; }
h3 { font-size: 16px; font-weight: 600; color: #333333; margin-top: 24px; margin-bottom: 10px; }
h4 { font-size: 15px; font-weight: 600; color: #555555; margin-top: 16px; margin-bottom: 8px; }
h5 { font-size: 14px; font-weight: 600; color: #666666; }
h6 { font-size: 13px; font-weight: 600; color: #888888; }
p { margin: 8px 0; color: #333333; line-height: 1.8; }
a { color: #0078d4; text-decoration: none; }
img { margin: 12px 0; border: 1px solid #e0e0e0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; border: 1px solid #dddddd; }
th { background-color: #f0f4f8; color: #1a1a1a; font-weight: 600; padding: 8px 12px; border: 1px solid #dddddd; text-align: left; }
td { padding: 6px 12px; border: 1px solid #dddddd; color: #333333; }
code { background-color: #f0f0f0; color: #0078d4; padding: 1px 5px; font-family: "Consolas", "Courier New", monospace; font-size: 12px; }
pre { background-color: #f8f8f8; border: 1px solid #e0e0e0; border-left: 3px solid #0078d4; padding: 12px 14px; margin: 10px 0; }
pre code { background-color: transparent; color: #333333; padding: 0; font-size: 13px; }
blockquote { border-left: 3px solid #0078d4; background-color: #eef6fd; margin: 10px 0; padding: 8px 14px; color: #555555; }
blockquote p { color: #555555; }
hr { border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }
strong { font-weight: 600; color: #1a1a1a; }
em { color: #666666; }
ul { margin: 8px 0; padding-left: 24px; }
ol { margin: 8px 0; padding-left: 24px; }
li { margin: 4px 0; color: #333333; }
del { color: #999999; }
kbd { background-color: #f5f5f5; border: 1px solid #cccccc; padding: 1px 5px; font-size: 12px; font-family: monospace; }
"""


def build_css_dark() -> str:
    return """
body { font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; font-size: 14px; color: #d6d6d6; }
h1 { font-size: 24px; font-weight: 600; color: #4cc2ff; border-bottom: 2px solid #4cc2ff; padding-bottom: 8px; margin-top: 6px; margin-bottom: 18px; }
h2 { font-size: 19px; font-weight: 600; color: #f0f0f0; border-left: 4px solid #4cc2ff; padding-left: 10px; margin-top: 30px; margin-bottom: 14px; }
h3 { font-size: 16px; font-weight: 600; color: #dddddd; margin-top: 24px; margin-bottom: 10px; }
h4 { font-size: 15px; font-weight: 600; color: #aaaaaa; margin-top: 16px; margin-bottom: 8px; }
h5 { font-size: 14px; font-weight: 600; color: #999999; }
h6 { font-size: 13px; font-weight: 600; color: #888888; }
p { margin: 8px 0; color: #cccccc; line-height: 1.8; }
a { color: #4cc2ff; text-decoration: none; }
img { margin: 12px 0; border: 1px solid #404040; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; border: 1px solid #404040; }
th { background-color: #2a2a2a; color: #f0f0f0; font-weight: 600; padding: 8px 12px; border: 1px solid #404040; text-align: left; }
td { padding: 6px 12px; border: 1px solid #383838; color: #cccccc; }
code { background-color: #2d2d2d; color: #4cc2ff; padding: 1px 5px; font-family: "Consolas", "Courier New", monospace; font-size: 12px; }
pre { background-color: #1e1e1e; border: 1px solid #383838; border-left: 3px solid #4cc2ff; padding: 12px 14px; margin: 10px 0; }
pre code { background-color: transparent; color: #d4d4d4; padding: 0; font-size: 13px; }
blockquote { border-left: 3px solid #4cc2ff; background-color: #1a2632; margin: 10px 0; padding: 8px 14px; color: #aaaaaa; }
blockquote p { color: #aaaaaa; }
hr { border: none; border-top: 1px solid #404040; margin: 24px 0; }
strong { font-weight: 600; color: #ffffff; }
em { color: #999999; }
ul { margin: 8px 0; padding-left: 24px; }
ol { margin: 8px 0; padding-left: 24px; }
li { margin: 4px 0; color: #cccccc; }
del { color: #666666; }
kbd { background-color: #333333; border: 1px solid #555555; padding: 1px 5px; font-size: 12px; font-family: monospace; }
"""


def build_html_body(md_text: str, wiki_path: str) -> str:
    """将 Markdown 转为 HTML body 内容"""
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    docs_dir = find_docs_dir(wiki_path)
    body = resolve_image_paths(body, docs_dir)
    body = constrain_images(body, docs_dir, max_width=500)
    return body


def generate_python_file(css_light: str, css_dark: str, body_html: str) -> str:
    """生成 wiki_content.py 文件内容"""
    lines = [
        "#!/usr/bin/env python3",
        '"""',
        "自动生成的 Wiki 内容文件",
        "",
        "此文件由 tools/generate_wiki_ui.py 从 documents/wiki.md 生成。",
        "请勿手动修改此文件，修改 wiki.md 后重新运行生成器：",
        "",
        "    python tools/generate_wiki_ui.py",
        '"""',
        "",
        "# CSS 样式表 - 亮色主题 (仅使用 Qt Rich Text 支持的属性)",
        'WIKI_CSS_LIGHT = r"""',
        css_light.strip(),
        '"""',
        "",
        "# CSS 样式表 - 暗色主题",
        'WIKI_CSS_DARK = r"""',
        css_dark.strip(),
        '"""',
        "",
        "# HTML body 内容 (图片已添加 width 属性)",
        'WIKI_HTML = r"""',
        body_html,
        '"""',
        "",
    ]
    return "\n".join(lines)


def main():
    wiki_path = find_wiki_md()
    print(f"读取: {wiki_path}")

    with open(wiki_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    css_light = build_css_light()
    css_dark = build_css_dark()
    body_html = build_html_body(md_text, wiki_path)

    py_content = generate_python_file(css_light, css_dark, body_html)

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "src", "nbs2save", "gui", "wiki_content.py",
    )
    output_path = os.path.abspath(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(py_content)

    # 统计图片处理情况
    img_count = body_html.count("<img")
    width_count = body_html.count('width="500"')

    print(f"生成: {output_path}")
    print(f"CSS Light: {len(css_light)} 字符 | CSS Dark: {len(css_dark)} 字符")
    print(f"HTML: {len(body_html)} 字符 | 图片: {img_count} 张 (其中 {width_count} 张已限制宽度)")
    print("完成！")


if __name__ == "__main__":
    main()
