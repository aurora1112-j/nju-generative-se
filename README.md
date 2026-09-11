# 生成式软件工程 · 图文转录

> NJU《生成式软件工程 26fall 》（蒋炎岩）课程录屏图文转录，包含带时间戳的全文 + 课堂截图 + 原视频链接。
>
> Fan-made companion transcripts for the NJU course *Generative Software Engineering* (Yanyan Jiang): timestamped full text with lecture screenshots, searchable and video-aligned.

**在线阅读 / Read online**: <https://aurora1112-j.github.io/nju-generative-se/>

## 讲次 / Lectures

| # | 主题 | 日期 | 原视频 | PDF |
| --- | --- | --- | --- | --- |
| 01 | 欢迎来到未来 | 2026-09-08 | [B 站](https://www.bilibili.com/video/BV1qAa3z2EvA/) | [pdf/01-welcome-to-the-future.pdf](pdf/01-welcome-to-the-future.pdf) |
| 02 | 提示词工程 | 2026-09-09 | [B 站](https://www.bilibili.com/video/BV1CQt365EzW/) | [pdf/02-prompt-engineering.pdf](pdf/02-prompt-engineering.pdf) |

*每周二随讲次更新 / Updated weekly after each lecture.*

## 为什么 / Why

课程讲生成式软件工程，本站的生产管线也是生成式的：ASR 转写 → Agent 整理 → PDF → 自动拆解成网页。

The course teaches generative software engineering — and this site is built the same way: ASR → agent-assisted cleanup → PDF → scripted conversion into this website.

## 目录结构 / Structure

```
├── docs/                  # MkDocs 站点源文件
│   ├── index.md           # 首页
│   └── lectures/          # 各讲 Markdown + 截图 assets
├── pdf/                   # 每讲 PDF 原件
├── scripts/pdf_to_md.py   # PDF → Markdown 转换脚本
├── mkdocs.yml             # MkDocs + Material 配置
└── .github/workflows/     # push 后自动部署 GitHub Pages
```

## 本地构建 / Build locally

```bash
pip install "mkdocs<2" mkdocs-material jieba mkdocs-glightbox mkdocs-git-revision-date-localized-plugin
mkdocs serve   # http://127.0.0.1:8000
```

## 声明 / Disclaimer

非官方学习资料，与南京大学及讲者无隶属关系。课程内容版权归原讲者所有；如需调整或下架请提 Issue，将立即处理。转录文本以 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) 分享。

Unofficial fan-made transcripts. All lecture content belongs to the original lecturer. Transcription texts are shared under CC BY-NC-SA 4.0.
