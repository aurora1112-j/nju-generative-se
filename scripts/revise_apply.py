#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用修订后的正文清单，替换现有 md 的正文与标题（图片/头部/空行保持不变）。

对齐策略：按时间戳 [HH:MM:SS] 和标题序号对齐，鲁棒、不错位。
"""
import re
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "revise_work")
DOCS = os.path.join(os.path.dirname(HERE), "docs", "lectures")


def load_revised(path):
    headings = {}  # num(去掉前导0后) -> text
    paras = {}     # ts -> text
    order = []     # 记录每段的 key，用于核对
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if line.startswith("@@IMG@@"):
                order.append("IMG")
                continue
            if line.startswith("## "):
                body = line[3:].strip()
                m = re.match(r"^(\d+)\s+", body)
                num = str(int(m.group(1))) if m else str(len(headings) + 1)
                headings[num] = body
                order.append(f"H{num}")
                continue
            m = re.match(r"^\[(\d{2}:\d{2}:\d{2})\]\s*(.*)$", line)
            if m:
                paras[m.group(1)] = m.group(2)
                order.append(f"P{m.group(1)}")
    return headings, paras


def apply(md_name, revised_name):
    md_path = os.path.join(DOCS, md_name)
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    headings, paras = load_revised(os.path.join(WORK, revised_name))

    n_para = n_head = 0
    missing_para = missing_head = 0
    out = []
    for line in lines:
        m = re.match(r"^##\s+(\d+)\s+", line)
        if m:
            num = str(int(m.group(1)))
            if num in headings:
                out.append(f"## {headings[num]}")
                n_head += 1
            else:
                out.append(line)
                missing_head += 1
            continue
        m = re.match(r"^\*\*\[(\d{2}:\d{2}:\d{2})\]\*\*\s*(.*)$", line)
        if m:
            ts = m.group(1)
            if ts in paras:
                out.append(f"**[{ts}]** {paras[ts]}")
                n_para += 1
            else:
                out.append(line)
                missing_para += 1
            continue
        out.append(line)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"{md_name}: 替换正文 {n_para}/{len(paras)} 段, 标题 {n_head}/{len(headings)} 个"
          f"{' | 未匹配正文 ' + str(missing_para) if missing_para else ''}"
          f"{' | 未匹配标题 ' + str(missing_head) if missing_head else ''}")
    if missing_para or missing_head:
        print("  !! 存在未匹配，请核对 revised 文件的时间戳/标题与现有 md 是否一致")


if __name__ == "__main__":
    apply("02-prompt-engineering.md", "02_revised.txt")
    apply("03-repository-management.md", "03_revised.txt")