#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从新 PDF 导出纯正文清单（供错字修订），并验证与现有 md 的图片/标题对齐。"""
import fitz
import re
import os
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("p2m", os.path.join(HERE, "pdf_to_md.py"))
p2m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p2m)

BASE = "/Users/bytedance/Coze/Drive/jyy"
DOCS = os.path.join(BASE, "nju-generative-se", "docs", "lectures")
WORK = os.path.join(HERE, "revise_work")
os.makedirs(WORK, exist_ok=True)


def export(mode, pdf_name, md_name, out_name):
    pages = p2m.extract_blocks(os.path.join(BASE, pdf_name))
    if mode == "02":
        tokens, nav = p2m.tokenize_02(pages)
    else:
        tokens, nav = p2m.tokenize_03(pages)
    merged = p2m.merge_paras(tokens)

    lines = []
    img_count = 0
    heading_count = 0
    para_count = 0
    for kind, payload in merged:
        if kind == "heading":
            lines.append(f"## {payload}")
            heading_count += 1
        elif kind == "image":
            lines.append("@@IMG@@")
            img_count += 1
        elif kind == "caption":
            continue
        else:
            lines.append(payload)
            para_count += 1

    with open(os.path.join(DOCS, md_name), encoding="utf-8") as f:
        md = f.read()
    md_imgs = re.findall(r"^!\[.*\]\(.*\)$", md, re.M)
    md_headings = re.findall(r"^##\s+.+$", md, re.M)

    out = os.path.join(WORK, out_name)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[{mode}] img(token)={img_count}  img(md)={len(md_imgs)}  "
          f"heading(token)={heading_count}  heading(md)={len(md_headings)}  "
          f"para={para_count}  nav={len(nav)}")
    if img_count != len(md_imgs):
        print(f"  !! 图片数量不一致：新PDF={img_count} 现有md={len(md_imgs)}")
    if heading_count != len(md_headings):
        print(f"  !! 标题数量不一致：新PDF={heading_count} 现有md={len(md_headings)}")
    return img_count, len(md_imgs)


if __name__ == "__main__":
    export("02", "提示词工程-图文转录_1789356095138_jj9n.pdf",
           "02-prompt-engineering.md", "02_raw_paras.txt")
    export("03", "软件仓库管理-图文转录_1789356088399_5339.pdf",
           "03-repository-management.md", "03_raw_paras.txt")