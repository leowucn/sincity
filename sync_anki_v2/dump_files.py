#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os.path

from utils import *

record_path = "./data/file_record.json"


def _get_current_data(path_list):
    def get_file_list(dir_list):
        res = []
        for dir_path in dir_list:
            res.extend(get_absolute_paths(dir_path))
        return res

    data = {}

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

        data[file_path] = int(get_file_last_modified_time(file_path))

    return data


def _get_old_data():
    od = {}

    # if os.path.isfile(record_path):
    #     od = read_json_file(record_path)

    return od


def get_files():
    create_directory_if_necessary(os.path.dirname(record_path))

    old_data = _get_old_data()
    new_data = _get_current_data([OB_NOTE_PATH])

    new_data1 = new_data.copy()

    need_handle_file_paths = []
    for key in merge_and_filter(old_data, new_data):
        need_handle_file_paths.append(key)

    with open(record_path, 'w') as json_file:
        # 使用json.dump将字典写入文件
        json.dump(new_data1, json_file)

    all_path = list(new_data.keys())

    return need_handle_file_paths, all_path

# 调用示例
# ./dump_files.py "/dir/path1" "/dir/path2"
