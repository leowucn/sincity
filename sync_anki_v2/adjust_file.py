#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *
from const import *


def _insert_uuid_if_need(file_path):
    """
    如果卡片块没有uuid则插入，否则忽略
    """
    lines = get_file_lines(file_path)

    for i in range(len(lines)):
        if END_FLAG in lines[i]:
            parts = lines[i].strip().split(" ")
            if len(parts) == 1:
                parts.append(generate_uuid())
            elif len(parts[1]) < 20:
                parts[1] = generate_uuid()
            lines[i] = " ".join(parts)
        lines[i] = lines[i].rstrip("\n")

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


def _replace_dollar_symbol(file_path):
    """
    替换$符号
    """
    # 读取文件内容
    with open(file_path, 'r') as file:
        lines = file.readlines()

    for i in range(len(lines)):
        lines[i] = lines[i].replace("$", "🌎")

    # 写回文件
    with open(file_path, 'w') as file:
        file.writelines(lines)
    

def _remove_former_redundant_dash_zero(file_path):
    """
    去掉文件中除最后的 ==0== 外的多余的 ==0==

    原因: 学习时，可能会在文件中创建多个记忆锚点，没有必要专门去找前面的进行删除，只有最后一个==0==需要保留
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    modified_lines = []

    found = False
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i]

        if SUSPEND_FLAG in line:
            if found:
                continue

            found = True

        modified_lines.append(line)

    modified_lines.reverse()

    # 写回文件
    with open(file_path, 'w') as file:
        file.writelines(modified_lines)


def adjust_files(file_list):
    for file_path in file_list:
        _insert_uuid_if_need(file_path)
        _remove_multiple_whitespace_line(file_path)
        _append_three_star(file_path)
        _replace_dollar_symbol(file_path)
        _remove_former_redundant_dash_zero(file_path)

