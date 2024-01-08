#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from const import *


def search_string_in_markdown(directory, target_string):
    def is_blank_line(line):
        return not line.strip()

    def process_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            in_code_block = False

            for i, line in enumerate(lines):
                line = line.strip()
                match_start = re.match(r'```', line)
                match_end = re.match(r'```', line) if in_code_block else None

                if match_start:
                    in_code_block = True

                if in_code_block and re.search(re.escape(target_string), line):
                    if match_start and (not match_end):
                        if i > 0 and (not is_blank_line(lines[i - 1])):
                            print(f"{file_path}:{i + 1} - 非空白行")
                        elif i > 1 and (is_blank_line(lines[i - 1])) and (is_blank_line(lines[i - 2])):
                            print(f"{file_path}:{i + 1} - 两行空白")

                if match_end:
                    in_code_block = False

    for root, dirs, files in os.walk(directory):
        for file in files:
            ignore = False

            for ignore_dir_name in IGNORE_UPLOAD_DIRS:
                if ignore_dir_name in root:
                    ignore = True
                    break

            if ignore:
                continue

            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                process_file(file_path)


def check_unspecified_code_blocks(directory):
    def is_blank_line(line):
        return not line.strip()

    def process_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            in_code_block = False

            for i, line in enumerate(lines):
                match = re.match(r'```(\S*)$', line)
                if match:
                    language_identifier = match.group(1)
                    in_code_block = not in_code_block
                    if i > 0 and is_blank_line(lines[i - 1]) and (not language_identifier or is_blank_line(lines[i])):

                        match_end = False
                        for k, line in enumerate(lines):
                            if k > i:
                                if re.match(r'````$', line):
                                    match_end = True
                                if re.match(r'````ad', line):
                                    break

                        if not match_end:
                            print(f"{file_path}:{i + 1} - 未指定编程语言的代码块")

    for root, dirs, files in os.walk(directory):
        for file in files:
            ignore = False

            for ignore_dir_name in IGNORE_UPLOAD_DIRS:
                if ignore_dir_name in root:
                    ignore = True
                    break

            if ignore:
                continue

            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                process_file(file_path)


def check_directory(directory, ignored_directories, ignore_upload_extensions_list):
    """
    检查目录中的md文件是否有没有匹配的 START_FLAG和END_FLAG标签
    """

    def get_file_extension(file_name):
        if file_name.startswith("."):
            return file_name
        return os.path.splitext(file_name)[1]

    def check_file_unmatched_tag(file_path):
        if not file_path.endswith(".md"):
            return

        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        stack = []
        for line_number, line in enumerate(lines, start=1):
            pos = 0
            while pos < len(line):
                start_pos = line.find(START_FLAG, pos)
                end_pos = line.find(END_FLAG, pos)

                if start_pos != -1 and (end_pos == -1 or start_pos < end_pos):
                    stack.append((start_pos, line_number))
                    pos = start_pos + len(START_FLAG)
                elif end_pos != -1 and (start_pos == -1 or end_pos < start_pos):
                    if not stack:
                        msg = f"""
                        File {file_path} contains mismatched tags:
                        Found an unmatched <-e-> at line {line_number}
                        """
                        raise RuntimeError(f"文件检查错误: {msg}")
                    stack.pop()
                    pos = end_pos + len(END_FLAG)
                else:
                    break
        if stack:
            msg = f"""
            File {file_path} contains mismatched tags:
            Found an unmatched <-s-> at line {stack[-1][1]}")
            """
            raise RuntimeError(f"文件检查错误: {msg}")

    def check_empty_line_before_s(file_path):
        if not file_path.endswith(".md"):
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        error_lines = []

        for i in range(1, len(lines)):
            current_line = lines[i].strip()
            if current_line == "<-s->":
                previous_line = lines[i - 1].strip()
                if not previous_line:
                    error_lines.append(i)

        if error_lines:
            print("错误：以下行之前有空白行，请修正：")
            for line_number in error_lines:
                print(f"行号 {line_number}: {lines[line_number - 1].strip()}")

            raise RuntimeError(f"<-s->前空行检查错误, 文件路径 {file_path}")

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignored_directories]

        for file in files:
            file_extension = get_file_extension(file)
            if file_extension not in ignore_upload_extensions_list:
                file_path = os.path.join(root, file)
                check_file_unmatched_tag(file_path)
                check_empty_line_before_s(file_path)


#TODO 检查是否存在空白的标题行，就是<-s->上一行为空

# 检测是否 "存在多余空白行" 或者 "代码块前不存在空白行"
search_string_in_markdown(OB_NOTE_PATH, "```")

# 检测是否存在代码块未指定编程语言
check_unspecified_code_blocks(OB_NOTE_PATH)

# 检查是否有未配对的标识符
check_directory(OB_NOTE_PATH, IGNORE_UPLOAD_DIRS, IGNORE_UPLOAD_EXTENSIONS)
