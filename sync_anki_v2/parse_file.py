#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *
from const import *


def _get_blocks(file_path):
    """
    解析文件并获取卡片块。

    注意，文件块的前后空白行已经被去掉
    """
    split_blocks = split_list_by_element(file_path, END_FLAG, False)
    if not split_blocks:
        return []

    blocks = []

    for block in split_blocks:
        if not block:
            continue

        title_index = -1
        for index, line_info in enumerate(block):
            if START_FLAG in line_info[1]:
                title_index = index

            if title_index >= 0:
                start_index = -1
                for index1 in range(title_index - 1, -1, -1):
                    if block[index1][1].strip():
                        start_index = index1
                        break
                if start_index < 0:
                    raise Exception("无法找到块起始位置")

                lines1 = []
                for line1 in block[start_index:]:
                    lines1.append(line1)
                blocks.append(lines1)
                break

        if title_index < 0:
            raise Exception(f"格式错误，无法找到块标题. 块起始行: {block[0][0]}, 文件: {file_path}")

    blocks = trim_blocks(blocks)
    for block in blocks:
        tmp = []
        for index, line_info in enumerate(block):
            if START_FLAG in line_info[1] or CONTENT_FLAG in line_info[1] or END_FLAG in line_info[1]:
                tmp.append(line_info[1].strip())
        if len(tmp) != 3 and len(tmp) != 2:
            raise Exception(f"不允许重复或者嵌套块边界标记. 块起始行索引: {block[0][0]}, 文件: {file_path}")
        if len(tmp) == 3:
            if tmp[0] != START_FLAG or tmp[1] != CONTENT_FLAG or tmp[2] != END_FLAG:
                raise Exception(f"请使用s c e的顺序组织块内容. 块起始行索引: {block[0][0]}, 文件: {file_path}")
        if len(tmp) == 2:
            if tmp[0] != START_FLAG or tmp[1] != END_FLAG:
                raise Exception(f"请使用s e的顺序组织块内容. 块起始行索引: {block[0][0]}, 文件: {file_path}")

    for block in blocks:
        for index, line in enumerate(block):
            if index <= 1 or index == len(block) - 1:
                continue

            if START_FLAG in line:
                raise Exception(f"不允许嵌套块起始标记. 内容: {line}")
            if END_FLAG in line:
                raise Exception(f"不允许嵌套块结束标记. 内容: {line}")

    return blocks


def _get_code_blocks(lines):
    code_blocks = []

    q = 0
    for i, line in enumerate(lines):
        if i <= q:
            continue

        if '````' in line:
            for k in range(i + 1, len(lines)):
                if '````' in lines[k]:
                    code_blocks.append([i, k])
                    q = k
                    break

        if i <= q:
            continue

        if '```' in line:
            for k in range(i + 1, len(lines)):
                if '```' in lines[k]:
                    code_blocks.append([i, k])
                    q = k
                    break

    return code_blocks


def _extract_hash_count(title):
    if title.startswith('#'):
        count = 0
        for char in title:
            if char == '#':
                count += 1
            else:
                break
        return count
    else:
        return 0


def _find_title_path(curr_index, lines, code_blocks):
    title_path = []

    pre_hash_count = 100
    for i in range(curr_index, -1, -1):
        hit = False
        for code_block in code_blocks:
            if code_block[0] < i < code_block[1]:
                hit = True
                break

        if hit:
            continue

        curr_line = lines[i].strip()
        if not curr_line.startswith("#") and curr_line.endswith(END_FLAG):
            continue

        curr_line = curr_line.replace(START_FLAG, "").replace(END_FLAG, "")

        if not curr_line:
            continue

        hash_count = _extract_hash_count(curr_line)

        if not hash_count:
            continue

        title = curr_line.strip('# ')

        # 如果到了一级标题或者已经倒序遍历了所有行
        if hash_count == 1 or i == 0:
            title_path.append(title)
            return title_path

        # 把当前行的标题加入结果
        if curr_index == i:
            title_path.append(title)
            pre_hash_count = hash_count

        if hash_count < pre_hash_count:
            title_path.append(title)
            pre_hash_count = hash_count

    return title_path


def _find_block_uuid(file_path, block):
    """
    查找block中的uuid
    """
    for line_info in block:
        if UUID_FLAG in line_info[1]:
            return extract_value_from_str(line_info[1], UUID_FLAG)
    raise Exception(f"无法找到uuid. 文件: {file_path}, 行: {block[0][0]}")


def _trim_lines(lines):
    """
    将前后空白行去掉
    """
    start_index = -1
    end_index = -1

    for index, line in enumerate(lines):
        if line.strip():
            start_index = index
            break

    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip():
            end_index = index
            break

    if end_index >= start_index:
        return lines[start_index:end_index + 1]

    return []


def _trim_uuid_line(lines):
    """
    uuid行不需要在anki中显示
    """
    for index in range(len(lines) - 1, -1, -1):
        if UUID_FLAG in lines[index]:
            lines.pop(index)
            break
    return lines


def _parse_block(block):
    """
    解析block
    """
    front_title = block[0][1].strip("#").strip()
    front_content = []
    back_content = []

    start_index = -1
    content_index = -1
    for index, line_info in enumerate(block):
        if START_FLAG in line_info[1]:
            start_index = index

        if CONTENT_FLAG in line_info[1]:
            content_index = index

    if content_index > 0:
        for line_info in block[start_index + 1:content_index]:
            front_content.append(line_info[1].rstrip())

    back_index = -1
    if content_index > 0:
        back_index = content_index + 1
    else:
        back_index = start_index + 1

    for line_info in block[back_index:len(block) - 1]:
        back_content.append(line_info[1].rstrip())
    back_content = _trim_lines(back_content)

    return front_title, front_content, back_content


def _add_meta_info(file_path, blocks):
    lines = get_file_lines(file_path)
    code_blocks = _get_code_blocks(lines)

    res = []
    for block in blocks:
        uuid = _find_block_uuid(file_path, block)
        title_path = _find_title_path(block[0][0], lines, code_blocks)
        front_title, front_content, back_content = _parse_block(block)
        back_content = _trim_uuid_line(back_content)
        res.append({
            # front_title不允许重复，如果重复则报错
            "front_title": front_title,
            "front_content": "\n".join(front_content),
            "back_content": "\n".join(back_content),
            "title_path": title_path,
            "file_path": file_path,
            "uuid": uuid
        })

    m = {}
    for index in range(len(res)):
        if res[index]["file_path"] in m:
            res[index]["deck"] = m[res[index]["file_path"]]
        else:
            deck = path_to_double_colon(res[index]["file_path"])
            m[res[index]["file_path"]] = deck

            res[index]["deck"] = deck
    return res


def get_blocks(file_path):
    """
    获取卡片块

    返回的格式如下：
    [
        {
            "front_title": "标题",
            "front_content": "正面内容",
            "back_content": "背面内容",
            "title_path": "h3 -> h2 -> h1",
            "md5": "ijwfowi2",
            "file_path": "a/b/c",
            "deck": "a::c:d",
            "uuid": "xvwfwef2"
        }
    ]
    """
    blocks = _get_blocks(file_path)
    return _add_meta_info(file_path, blocks)

# 调用示例
# py3 ./parse_file.py "./abc/w.md"
