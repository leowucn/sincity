#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *
from const import *


def _insert_uuid_if_need(file_path):
    """
    如果卡片块没有uuid则插入，否则忽略
    """
    blocks = split_list_by_element(file_path, END_FLAG, True)

    modified_blocks = []

    uuid_set = set()
    for block in blocks:
        for line_info in block:
            if UUID_FLAG in line_info[1]:
                uuid_str = extract_value_from_str(line_info[1], UUID_FLAG)
                uuid_set.add(uuid_str)

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


def _remove_multiple_whitespace_line(file_path):
    """
    将至少连续5个空白行修改为3个空白行
    """
    # 读取文件内容
    with open(file_path, 'r') as file:
        content = file.read()

    # 使用正则表达式进行替换
    pattern = re.compile(r'\n{5,}')
    modified_content = re.sub(pattern, '\n\n\n\n', content)

    # 写回文件
    with open(file_path, 'w') as file:
        file.write(modified_content)


def _append_three_star(file_path):
    """
    某些行以三个*符号开头，但是不是以三个*结尾。自动在行尾添加三个*
    """
    # 读取文件内容
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # 处理以三个星号开头但不以三个星号结尾的行
    modified_lines = []

    for line in lines:
        if line.startswith('***') and not line.endswith('***\n'):
            line = line.rstrip() + '***\n'
        modified_lines.append(line)

    # 写回文件
    with open(file_path, 'w') as file:
        file.writelines(modified_lines)


def _insert_three_dash(file_path):
    """
    在uuid行前插入---
    """
    # 读取文件内容
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # 处理以 "wpx" 开头的行
    modified_lines = []

    for i in range(len(lines)):
        current_line = lines[i]
        if current_line.startswith("wpx") and (i == 0 or not lines[i-1].startswith("---\n")):
            modified_lines.append("---\n")
        modified_lines.append(current_line)

    # 写回文件
    with open(file_path, 'w') as file:
        file.writelines(modified_lines)


def adjust_files(file_list):
    for file_path in file_list:
        _insert_uuid_if_need(file_path)
        _remove_multiple_whitespace_line(file_path)
        _append_three_star(file_path)
        # _insert_three_dash 一定要在 _add_whitespace_line_before_wpx_line之后执行
        #
        # 另外，在_trim_uuid_line函数中，提取数据时，判断了uuid行前面是不是---，如果是的话会删除
        # 如果哪天不再使用_insert_three_dash则需要在在_trim_uuid_line中删除对应代码
        _insert_three_dash(file_path)

