#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *
from const import *


def _adjust_file(file_path):
    blocks = split_list_by_element(file_path, END_FLAG, True)

    modified_blocks = []

    uuid_set = set()
    for block in blocks:
        for line_info in block:
            if UUID_FLAG in line_info[1]:
                uuid = extract_value_from_str(line_info[1], UUID_FLAG)
                uuid_set.add(uuid)

    for block in blocks:
        found_uuid_line = False
        for line_info in block:
            if UUID_FLAG in line_info[1]:
                found_uuid_line = True
                break
        if found_uuid_line:
            modified_blocks.append(block)
        else:
            end_line_index = -1
            for index in range(len(block)):
                if END_FLAG in block[index]:
                    end_line_index = index
                    break
            if end_line_index < 0:
                # 可能这一个数据块尚未被卡片化。数据仍然需要保留
                modified_blocks.append(block)
            else:
                valid_uuid = generate_uuid()
                while True:
                    if valid_uuid not in uuid_set:
                        break
                    else:
                        valid_uuid = generate_uuid()

                # 这里的666没有实际意义，至少为了符合line_info的格式
                block.insert(end_line_index, (666, get_uuid_line(valid_uuid)))
                modified_blocks.append(block)

    modified_blocks = trim_blocks(modified_blocks)

    lines = []
    for block in modified_blocks:
        for line_info in block:
            lines.append(line_info[1].rstrip())
        lines.append("\n\n")
    backup_and_write_to_file(lines, file_path)


def adjust_files(file_list):
    for file_path in file_list:
        _adjust_file(file_path)
