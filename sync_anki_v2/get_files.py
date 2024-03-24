#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from utils import *


def _get_path_list():
    path_list = [OB_NOTE_PATH]

    def get_file_list(dir_list):
        res = []
        for dir_path in dir_list:
            res.extend(get_absolute_paths(dir_path))
        return res

    file_path_list = []

    file_list = get_file_list(path_list)
    for file_path in file_list:
        if not file_path.lower().endswith('.md'):
            continue

        ext = get_file_extension(file_path)
        if ext in IGNORE_UPLOAD_EXTENSIONS:
            continue

        found = False
        for item in IGNORE_UPLOAD_DIRS:
            if item in file_path:
                found = True
                break
        if found:
            continue

        file_path_list.append(file_path)

    return file_path_list


def _get_file_mtime(file_path):
    # 获取绝对路径
    abs_path = os.path.abspath(file_path)

    # 检查文件是否存在
    if not os.path.exists(abs_path):
        return -1  # 文件不存在，返回-1

    # 获取文件的修改时间（时间戳）
    mtime_timestamp = os.path.getmtime(abs_path)

    return int(datetime.fromtimestamp(mtime_timestamp).timestamp())


def _read_file_path_cache():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    cache = {}

    cache_fiel_path = f"{CACHE_DIR}/file_path_cache.json"
    if os.path.isfile(cache_fiel_path):
        with open(cache_fiel_path, "r") as json_file:
            cache = json.load(json_file)

    return cache


def _get_file_path_new_cache():
    all_file_path = _get_path_list()
    return {file_path: _get_file_mtime(file_path) for file_path in all_file_path}


def update_file_path_cache():
    """更新文件路径缓存
    """
    cache = _get_file_path_new_cache()
    cache_fiel_path = f"{CACHE_DIR}/file_path_cache.json"
    with open(cache_fiel_path, "w") as json_file:
        json.dump(dict(sorted(cache.items())), json_file, indent=2)


def get_file_path_list():
    """根据缓存情况获取当前有效的文件路径列表

    注意，这里只会获取自上次修改后的文件路径列表
    """
    all_file_path = _get_path_list()
    curr_cache = _read_file_path_cache()

    result = []
    for file_path in all_file_path:
        # 新文件
        if file_path not in curr_cache:
            result.append(file_path)

        # 文件已被修改
        if file_path in curr_cache and curr_cache[file_path] != _get_file_mtime(file_path):
            result.append(file_path)
    return result


def get_no_exist_file_path_list():
    """获取缓存中不再有效的文件路径列表, 用于删除deck
    """
    all_file_path_set = set(_get_path_list())
    curr_cache = _read_file_path_cache()

    return [
        file_path
        for file_path in curr_cache
        if file_path not in all_file_path_set
    ]


def get_all_file_path_list():
    """获取所有文件路径 (不考虑缓存)
    """
    return _get_path_list()


def if_file_changed(target_file_path):
    """从当前文件路径列表中查找文件 (考虑了缓存)

    如果找到了，说明文件已经被修改，是新文件
    """
    curr_cache = _read_file_path_cache()
    if target_file_path not in curr_cache:
        return True

    return _get_file_mtime(target_file_path) != curr_cache[target_file_path]
