#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *


def _get_path_list(path_list):
    def get_file_list(dir_list):
        res = []
        for dir_path in dir_list:
            res.extend(get_absolute_paths(dir_path))
        return res

    data = []

    file_list = get_file_list(path_list)
    for file_path in file_list:
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

        data.append(file_path)

    return data


def get_files():
    path_list = _get_path_list([OB_NOTE_PATH])

    return path_list

# 调用示例
# ./get_files.py "/dir/path1" "/dir/path2"
