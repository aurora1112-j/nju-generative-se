#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把课程图文转录 PDF 转成 MkDocs 章节 Markdown。

流程：extract_blocks（按 y 排序的文图块）→ tokenize（结构化识别标题/图注/时间块/导航）
→ 合并普通段落 → render Markdown。
"""
import fitz  # PyMuPDF
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RE_NOISE_02 = [
    r"^提示词工程\s*/\s*生成式软件工程$",
    r"^生成式软件工程\s*/\s*02$",
    r"^NJU\s*·\s*02-Raw\s*\d*$",
    r"^\d+$",
]
RE_NOISE_01 = [
    r"^欢迎来到未来\s*\|\s*本地\s*Qwen\s*图文转录$",
    r"^\d+$",
]
RE_NOISE_03 = [
    r"^软件仓库管理\s*/\s*生成式软件工程$",
    r"^生成式软件工程\s*/\s*03$",
    r"^NJU\s*·\s*03-Raw\s*\d*$",
    r"^\d+$",
]
RE_NAV_ITEM_03 = r"^(\d{2}:\d{2}:\d{2})\s*(.+)$"
RE_CAPTION_02 = r"^画面\s+(\d{2}:\d{2}:\d{2})$"
RE_CAPTION_01 = r"^原视频画面\s*·\s*(\d{2}:\d{2}:\d{2})$"
RE_TIMEBLOCK_01 = r"^(\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})$"
RE_HEADING_02 = r"^(\d{2})\s+(.+)$"
RE_TS_PARA = r"^\[(\d{2}:\d{2}:\d{2})\]\s*(.*)$"
RE_NAV_ITEM = r"^(\d{2}:\d{2}:\d{2})\s+(.+)$"


def extract_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    for pno in range(len(doc)):
        page = doc[pno]
        d = page.get_text("dict")
        blocks = sorted(d["blocks"], key=lambda b: (round(b["bbox"][1], 1), b["bbox"][0]))
        items = []
        for b in blocks:
            if b["type"] == 0:
                text = "".join(s["text"] for l in b["lines"] for s in l["spans"]).strip()
                if text:
                    items.append(("text", text))
            else:
                img = b.get("image")
                if img:
                    items.append(("image", (img, b.get("ext", "png"))))
        pages.append(items)
    doc.close()
    return pages


def tokenize_02(pages):
    """第2讲：跳过封面(p1)；导航页(p2)单独提取；正文识别章节/图注/时间戳段落。"""
    tokens = []
    nav = []
    # 导航页：整页文本里抓时间戳导航
    for kind, payload in pages[1]:
        if kind == "text":
            m = re.match(RE_NAV_ITEM, payload)
            if m and not payload.startswith("阅读"):
                nav.append((m.group(1), m.group(2)))
    for items in pages[2:]:
        for kind, payload in items:
            if kind == "image":
                tokens.append(("image", payload))
                continue
            t = payload
            if any(re.fullmatch(p, t) for p in RE_NOISE_02):
                continue
            m = re.fullmatch(RE_CAPTION_02, t)
            if m:
                tokens.append(("caption", m.group(1)))
                continue
            m = re.match(RE_HEADING_02, t)
            if m and ":" not in t.split()[0] and not t.startswith("["):
                tokens.append(("heading", f"{m.group(1)} {m.group(2)}"))
                continue
            tokens.append(("para", t))
    return tokens, nav


def tokenize_01(pages):
    """第1讲：跳过封面(p1)；识别时间块/图注；正文为流式段落。"""
    tokens = []
    for items in pages[1:]:
        for kind, payload in items:
            if kind == "image":
                tokens.append(("image", payload))
                continue
            t = payload
            if any(re.fullmatch(p, t) for p in RE_NOISE_01):
                continue
            m = re.fullmatch(RE_TIMEBLOCK_01, t)
            if m:
                tokens.append(("timeblock", m.group(1)))
                continue
            m = re.fullmatch(RE_CAPTION_01, t)
            if m:
                tokens.append(("caption", m.group(1)))
                continue
            tokens.append(("para", t))
    return tokens


def merge_paras(tokens):
    """连续 para 合并为一段；[ts] 开头的 para 另起新段。"""
    out = []
    for kind, payload in tokens:
        if kind != "para":
            out.append((kind, payload))
            continue
        if out and out[-1][0] == "para" and not re.match(RE_TS_PARA, payload):
            out[-1] = ("para", out[-1][1] + payload)
        else:
            out.append(("para", payload))
    return out


def render_02(tokens, nav, assets_rel, assets_dir):
    os.makedirs(assets_dir, exist_ok=True)
    md = []
    if nav:
        md.append('!!! quote "阅读导航（对应原视频时间点）"\n')
        for ts, title in nav:
            md.append(f"    **{ts}** {title}  ")
        md.append("")
    caption = None
    img_n = 0
    for kind, payload in tokens:
        if kind == "heading":
            md.append(f"\n## {payload}\n")
        elif kind == "caption":
            caption = payload
        elif kind == "image":
            img_bytes, ext = payload
            img_n += 1
            name = f"02_{img_n:02d}.{ext}"
            with open(os.path.join(assets_dir, name), "wb") as f:
                f.write(img_bytes)
            cap = f"画面 {caption}" if caption else "课堂画面"
            md.append(f"![{cap}]({assets_rel}/{name})\n")
            caption = None
        else:
            m = re.match(RE_TS_PARA, payload)
            if m:
                md.append(f"**[{m.group(1)}]** {m.group(2).strip()}\n")
            else:
                md.append(payload + "\n")
    return md


def render_01(tokens, assets_rel, assets_dir):
    """第1讲布局：时间块 → 图 → 图注 → 正文。图注在图后，需回填上一张图。"""
    os.makedirs(assets_dir, exist_ok=True)
    md = []
    pending_img_idx = None  # 等待图注回填的图片行索引
    img_n = 0
    for kind, payload in tokens:
        if kind == "timeblock":
            md.append(f"\n**{payload}**\n")
            pending_img_idx = None
        elif kind == "caption":
            if pending_img_idx is not None:
                md[pending_img_idx] = md[pending_img_idx].replace("原视频画面", f"原视频画面 {payload}", 1)
                pending_img_idx = None
        elif kind == "image":
            img_bytes, ext = payload
            img_n += 1
            name = f"01_{img_n:02d}.{ext}"
            with open(os.path.join(assets_dir, name), "wb") as f:
                f.write(img_bytes)
            md.append(f"![原视频画面]({assets_rel}/{name})\n")
            pending_img_idx = len(md) - 1
        else:
            md.append(payload + "\n")
    return md


def tokenize_03(pages):
    """第3讲：版式与第2讲一致（03-Raw）；导航页(p2)抓时间戳导航。"""
    tokens = []
    nav = []
    for kind, payload in pages[1]:
        if kind == "text":
            m = re.match(RE_NAV_ITEM_03, payload)
            if m and not payload.startswith("阅读"):
                nav.append((m.group(1), m.group(2)))
    for items in pages[2:]:
        for kind, payload in items:
            if kind == "image":
                tokens.append(("image", payload))
                continue
            t = payload
            if any(re.fullmatch(p, t) for p in RE_NOISE_03):
                continue
            m = re.fullmatch(RE_CAPTION_02, t)
            if m:
                tokens.append(("caption", m.group(1)))
                continue
            m = re.match(RE_HEADING_02, t)
            if m and ":" not in t.split()[0] and not t.startswith("["):
                tokens.append(("heading", f"{m.group(1)} {m.group(2)}"))
                continue
            tokens.append(("para", t))
    return tokens, nav


def render_03(tokens, nav, assets_rel, assets_dir):
    os.makedirs(assets_dir, exist_ok=True)
    md = []
    if nav:
        md.append('!!! quote "阅读导航（对应原视频时间点）"\n')
        for ts, title in nav:
            md.append(f"    **{ts}** {title}  ")
        md.append("")
    caption = None
    img_n = 0
    for kind, payload in tokens:
        if kind == "heading":
            md.append(f"\n## {payload}\n")
        elif kind == "caption":
            caption = payload
        elif kind == "image":
            img_bytes, ext = payload
            img_n += 1
            name = f"03_{img_n:02d}.{ext}"
            with open(os.path.join(assets_dir, name), "wb") as f:
                f.write(img_bytes)
            cap = f"画面 {caption}" if caption else "课堂画面"
            md.append(f"![{cap}]({assets_rel}/{name})\n")
            caption = None
        else:
            m = re.match(RE_TS_PARA, payload)
            if m:
                md.append(f"**[{m.group(1)}]** {m.group(2).strip()}\n")
            else:
                md.append(payload + "\n")
    return md


def build03():
    base = "/Users/bytedance/Coze/Drive/jyy"
    docs = os.path.join(ROOT, "docs", "lectures")
    pages = extract_blocks(os.path.join(base, "软件仓库管理-图文转录_1789112794947_gv8z.pdf"))
    tokens, nav = tokenize_03(pages)
    md = render_03(merge_paras(tokens), nav, "assets/03", os.path.join(docs, "assets", "03"))
    with open(os.path.join(docs, "03-body.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"03: {sum(1 for k,_ in tokens if k=='para')} paras, "
          f"{sum(1 for k,_ in tokens if k=='heading')} headings, "
          f"{sum(1 for k,_ in tokens if k=='image')} images, nav={len(nav)}")
    for k, payload in tokens:
        if k == "heading":
            print("H:", payload)
    for ts, title in nav:
        print("NAV:", ts, title)


def build():
    base = "/Users/bytedance/Coze/Drive/jyy"
    docs = os.path.join(ROOT, "docs", "lectures")

    pages = extract_blocks(os.path.join(base, "提示词工程-图文转录_1789024088047_3s68.pdf"))
    tokens, nav = tokenize_02(pages)
    md = render_02(merge_paras(tokens), nav, "assets/02", os.path.join(docs, "assets", "02"))
    with open(os.path.join(docs, "02-body.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"02: {sum(1 for k,_ in tokens if k=='para')} paras, "
          f"{sum(1 for k,_ in tokens if k=='heading')} headings, "
          f"{sum(1 for k,_ in tokens if k=='image')} images, nav={len(nav)}")

    pages = extract_blocks(os.path.join(base, "欢迎来到未来-图文转录_1789024088047_w1w4.pdf"))
    tokens = tokenize_01(pages)
    md = render_01(merge_paras(tokens), "assets/01", os.path.join(docs, "assets", "01"))
    with open(os.path.join(docs, "01-body.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"01: {sum(1 for k,_ in tokens if k=='para')} paras, "
          f"{sum(1 for k,_ in tokens if k=='timeblock')} timeblocks, "
          f"{sum(1 for k,_ in tokens if k=='image')} images")


if __name__ == "__main__":
    build03()
