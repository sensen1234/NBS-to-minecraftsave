#!/usr/bin/env python3
"""
wiki.md → wiki_content.py 生成器 (v2)

将 wiki.md 解析为结构化数据，输出 wiki_content.py。
程序运行时由 wiki_interface.py 使用 QFluentWidgets 组件渲染，不依赖 QTextBrowser。

运行:
    python tools/generate_wiki_ui.py
"""

import os
import sys


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


# ============================================================
# Markdown 解析器 - 解析为结构化元素列表
# ============================================================

def parse_markdown(md_text: str) -> list:
    """
    将 markdown 文本解析为结构化元素列表。
    每个元素是一个 dict，包含 'type' 和其他字段。
    """
    elements = []
    lines = md_text.split("\n")
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 空行 → 跳过
        if not stripped:
            i += 1
            continue

        # 标题 # ~ ######
        if stripped.startswith("#"):
            level = 0
            while level < len(stripped) and stripped[level] == "#":
                level += 1
            if level <= 6 and level < len(stripped) and stripped[level] == " ":
                text = stripped[level:].strip()
                elements.append({"type": "heading", "level": level, "text": text})
                i += 1
                continue

        # 分隔线
        if stripped in ("---", "***", "___") or (
            len(stripped) >= 3 and all(c in "-*_" for c in stripped)
        ):
            elements.append({"type": "separator"})
            i += 1
            continue

        # 代码块
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # 跳过结束的 ```
            elements.append({
                "type": "code",
                "language": lang,
                "content": "\n".join(code_lines),
            })
            continue

        # 表格 (以 | 开头的连续行)
        if stripped.startswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2:
                headers = _parse_table_row(table_lines[0])
                rows = []
                for tl in table_lines[2:]:  # 跳过表头和分隔行
                    cells = _parse_table_row(tl)
                    # 补齐列数
                    while len(cells) < len(headers):
                        cells.append("")
                    rows.append(cells[:len(headers)])
                elements.append({
                    "type": "table",
                    "headers": headers,
                    "rows": rows,
                })
            continue

        # 引用块
        if stripped.startswith(">"):
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                txt = lines[i].strip()
                if txt.startswith("> "):
                    txt = txt[2:]
                elif txt == ">":
                    txt = ""
                quote_lines.append(txt)
                i += 1
            elements.append({
                "type": "blockquote",
                "content": " ".join(quote_lines),
            })
            continue

        # 图片
        if stripped.startswith("!["):
            img_match = stripped
            elements.append({"type": "image", "alt": "", "src": img_match})
            i += 1
            continue

        # 无序列表
        if stripped.startswith("- ") or stripped.startswith("* "):
            items = []
            while i < n and (
                lines[i].strip().startswith("- ")
                or lines[i].strip().startswith("* ")
            ):
                item_text = lines[i].strip()
                item_text = item_text[2:].strip()
                items.append(item_text)
                i += 1
            elements.append({"type": "bullet_list", "items": items})
            continue

        # 有序列表
        if len(stripped) >= 3 and stripped[0].isdigit() and ". " in stripped[:5]:
            items = []
            while i < n:
                s = lines[i].strip()
                if len(s) >= 3 and s[0].isdigit() and ". " in s[:5]:
                    items.append(s[s.index(". ") + 2:].strip())
                    i += 1
                else:
                    break
            elements.append({"type": "numbered_list", "items": items})
            continue

        # 普通段落（合并连续非空行）
        para_lines = []
        while i < n:
            s = lines[i].strip()
            if not s:
                break
            if s.startswith("#") or s.startswith("```") or s.startswith("|"):
                break
            if s.startswith(">") or s.startswith("!["):
                break
            if s in ("---", "***", "___"):
                break
            if len(s) >= 3 and all(c in "-*_" for c in s):
                break
            if s.startswith("- ") or s.startswith("* "):
                break
            if len(s) >= 3 and s[0].isdigit() and ". " in s[:5]:
                break
            para_lines.append(s)
            i += 1
        if para_lines:
            text = " ".join(para_lines)
            if text.strip():
                elements.append({"type": "paragraph", "text": text})

    return elements


def _parse_table_row(line: str) -> list:
    """解析表格一行 |a|b|c| → ['a', 'b', 'c']"""
    cells = line.split("|")
    # 去掉首尾空元素
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [c.strip() for c in cells]


# ============================================================
# Python 代码生成器
# ============================================================

def generate_python(elements: list) -> str:
    """将结构化元素列表转换为 Python 代码"""
    lines = []

    def emit(text=""):
        lines.append(text)

    def emit_element(elem):
        t = elem["type"]

        if t == "heading":
            level = elem["level"]
            text = _escape_py(elem["text"])
            emit(f'    el.add_heading({level}, "{text}")')

        elif t == "paragraph":
            text = _escape_py(elem["text"])
            emit(f'    el.add_paragraph("{text}")')

        elif t == "code":
            lang = _escape_py(elem.get("language", ""))
            content = _escape_py(elem["content"])
            emit(f'    el.add_code_block("{lang}", "{content}")')

        elif t == "table":
            headers = elem["headers"]
            rows = elem["rows"]
            emit(f'    el.add_table(')
            emit(f'        headers={_py_list(headers)},')
            emit(f'        rows=[')
            for row in rows:
                emit(f'            {_py_list(row)},')
            emit(f'        ],')
            emit(f'    )')

        elif t == "blockquote":
            content = _escape_py(elem["content"])
            emit(f'    el.add_blockquote("{content}")')

        elif t == "image":
            src = _escape_py(elem["src"])
            alt = _escape_py(elem.get("alt", ""))
            emit(f'    el.add_image("{src}", "{alt}")')

        elif t == "bullet_list":
            emit(f'    el.add_bullet_list([')
            for item in elem["items"]:
                emit(f'        "{_escape_py(item)}",')
            emit(f'    ])')

        elif t == "numbered_list":
            emit(f'    el.add_numbered_list([')
            for item in elem["items"]:
                emit(f'        "{_escape_py(item)}",')
            emit(f'    ])')

        elif t == "separator":
            emit(f'    el.add_separator()')

    # 文件头部
    emit('#!/usr/bin/env python3')
    emit('"""')
    emit('自动生成的 Wiki 结构化数据')
    emit('')
    emit('此文件由 tools/generate_wiki_ui.py 从 documents/wiki.md 自动生成。')
    emit('请勿手动修改。修改 wiki.md 后重新运行:')
    emit('')
    emit('    python tools/generate_wiki_ui.py')
    emit('"""')
    emit('')
    emit('')
    emit('def build_wiki_content(el):')
    emit('    """向 Interpreter 添加 wiki 内容元素"""')
    emit('')

    # 生成每个元素
    for elem in elements:
        emit_element(elem)

    emit('')
    return "\n".join(lines)


def _escape_py(s: str) -> str:
    """转义字符串用于 Python 源码中的双引号字符串"""
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "")
    s = s.replace("\t", "    ")
    return s


def _py_list(items: list) -> str:
    """将字符串列表转为 Python 列表字面量"""
    escaped = [f'"{_escape_py(item)}"' for item in items]
    return "[" + ", ".join(escaped) + "]"


# ============================================================
# 主函数
# ============================================================

def main():
    wiki_path = find_wiki_md()
    print(f"读取: {wiki_path}")

    with open(wiki_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 解析 Markdown
    elements = parse_markdown(md_text)
    print(f"解析: {len(elements)} 个元素")

    # 统计
    counts = {}
    for elem in elements:
        t = elem["type"]
        counts[t] = counts.get(t, 0) + 1
    for t, c in sorted(counts.items()):
        print(f"  {t}: {c}")

    # 生成 Python 代码
    py_code = generate_python(elements)

    # 写入文件
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "src", "nbs2save", "gui", "wiki_content.py",
    )
    output_path = os.path.abspath(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(py_code)

    print(f"生成: {output_path}")
    print(f"大小: {len(py_code)} 字符")
    print("完成！")


if __name__ == "__main__":
    main()
