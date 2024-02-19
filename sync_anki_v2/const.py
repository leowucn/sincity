#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 卡片块起始标志
START_FLAG = "<-s->"
# 卡片块内容开始标志
CONTENT_FLAG = "<-c->"
# 卡片块结束标志
END_FLAG = "<-e->"

# 卡片块的uuid
# 卡片块的uuid行的格式是  <p>wpx: fwe2iex </p>
UUID_FLAG = "wpx"

WHITE_LIST_DECKS = ["系统默认"]
ANKI_CONNECT = "http://localhost:8765"
MODEL_NAME = "KaTeX and Markdown Basic"
ATTACHMENT_DIR = "资产"
# 视频格式
VIDEO_FORMATS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".3gp"}

OB_NOTE_PATH = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob"
ROOT_IMAGE_PATH = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob/资产"

# 忽略如下目录中数据的处理
IGNORE_UPLOAD_DIRS = [".obsidian", ".trash", ".DS_Store"]
# START_FLAG和END_FLAG标签时将忽略如下格式的文件
IGNORE_UPLOAD_EXTENSIONS = {
    ".DS_Store", ".jpeg", ".jpg", ".webp", ".avif", ".png", ".gif", ".bmp",
    ".tiff", ".svg", ".heif", ".heic", ".mp4", ".avi", ".mkv", ".mov",
    ".wmv", ".flv", ".webm", ".mpg", ".3gp",
}
