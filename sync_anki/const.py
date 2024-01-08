#!/usr/bin/env python3
# -*- coding: utf-8 -*-

START_FLAG = "<-s->"
END_FLAG = "<-e->"
ANKI_CONNECT = "http://localhost:8765"
# 设置根牌组名称
ROOT_DECK_NAME = "碧海潮生"
MODEL_NAME = "KaTex and Markdown Basic"

WHITE_LIST_DECKS = [
    "小学古诗大全_上涨网",
    "成语大全",
    "系统默认"
]

OB_NOTE_PATH = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob"
ROOT_IMAGE_PATH = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob/资产"

ATTACHMENT_DIR = "资产"

# 忽略如下目录中数据的处理
IGNORE_UPLOAD_DIRS = [".obsidian", ".trash"]

# START_FLAG和END_FLAG标签时将忽略如下格式的文件
IGNORE_UPLOAD_EXTENSIONS = {
    ".DS_Store",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".svg",
    ".heif",
    ".heic",
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mpg",
    ".3gp",
}

# 视频格式
VIDEO_FORMATS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".3gp"}