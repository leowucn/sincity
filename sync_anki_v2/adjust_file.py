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


def _format_end_flag_lines(file_path):
    """
    格式化 end_flag 附近的行的格式
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    modified_lines = []
    for i in range(len(lines)):
        if i < len(lines) - 1 and lines[i].strip() == '---' and lines[i+1].strip().startswith('==3=='):
            # Check if there are less than 2 consecutive empty lines before '---'
            empty_lines_count = 0
            j = i - 1
            while j >= 0 and lines[j].strip() == '':
                empty_lines_count += 1
                j -= 1

            if empty_lines_count < 2:
                modified_lines.extend(['\n' for _ in range(2 - empty_lines_count)])

            # Check if there are more than 2 consecutive empty lines before '---'
            j = i - 1
            while j >= 0 and lines[j].strip() == '':
                j -= 1
            while j >= 0 and lines[j].strip() == '':
                modified_lines.pop()
                j -= 1

        modified_lines.append(lines[i])

    with open(file_path, 'w') as file:
        file.writelines(modified_lines)


def _insert_three_dash(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    modified_lines = []
    for i in range(len(lines)):
        if i > 0 and '==3==' in lines[i] and lines[i-1].strip() != '---':
            modified_lines.append('---\n')
        modified_lines.append(lines[i])

    with open(file_path, 'w') as file:
        file.writelines(modified_lines)


def adjust_files(file_list):
    for file_path in file_list:
        if not file_path.lower().endswith('.md'):
            continue

        _insert_uuid_if_need(file_path)
        _remove_multiple_whitespace_line(file_path)
        _replace_dollar_symbol(file_path)
        _remove_former_redundant_dash_zero(file_path)
        # _insert_three_dash 必须在 _format_end_flag_lines 之前执行
        _insert_three_dash(file_path)
        _format_end_flag_lines(file_path)

