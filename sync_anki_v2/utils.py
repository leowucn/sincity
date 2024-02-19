#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import os
import json
import uuid
import shutil
import re

from const import *


def p(blocks):
    print("*************************************************")
    for block in blocks:
        print("--------", block)
    print("*************************************************")


def create_directory_if_necessary(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created successfully.")


def get_absolute_paths(directory):
    """
    递归遍历目录，并返回目录中所有文件的绝对路径
    """
    path_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            path_list.append(os.path.join(root, file))

    return path_list


def get_file_last_modified_time(file_path):
    try:
        return os.path.getmtime(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(file_path)
    except Exception as e:
        raise Exception(e, file_path)


def read_json_file(file_path):
    try:
        with open(file_path, 'r') as json_file:
            # 使用json.load加载JSON文件内容到字典
            data_dict = json.load(json_file)
            return data_dict
    except FileNotFoundError:
        raise FileNotFoundError(file_path)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"error: {e}, file_path: {file_path}")
    except Exception as e:
        raise Exception(e, file_path)


def merge_and_filter(dict1, dict2):
    """
    返回不包含同时存在于dict1和dict2相同key:value的字典
    """
    d = dict1.copy()
    for key, value in d.items():
        if key in dict2 and dict2[key] == value:
            del dict1[key]
            del dict2[key]

    dict1.update(dict2)
    return dict1


def get_file_lines(file_path, encoding='utf-8'):
    """
    获取文件行列表
    """
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.readlines()
    except UnicodeDecodeError as e:
        raise Exception(f"error: {e}, file_path: {file_path}")


def get_file_extension(file_path):
    """
    获取文件后缀名
    """
    _, file_extension = os.path.splitext(file_path)
    return file_extension


def first_delimiter_for_card(num=1):
    """
    卡片正面和反面之间的分割线
    Returns:

    """
    return "<p style='width: 100%; height: 8px; background-color: #1d9ed1; margin: 30px 0;'></p>" * num


def second_delimiter_for_card(num=1):
    """
    卡片正面和反面之间的分割线
    Returns:

    """
    return "<p style='width: 100%; height: 8px; background-color: #f2c631; margin: 30px 0;'></p>" * num


def third_delimiter_for_card(num=1):
    """
    卡片正面和反面之间的分割线
    Returns:

    """
    return "<p style='width: 100%; height: 10px; background-color: #f76132; margin: 40px 0;'></p>" * num


def delimiter_for_line(num=1):
    """
    分割线。可以用在任意位置
    """
    return "<hr>" * num


def calculate_dict_md5(data_dict):
    # 将字典转换为字符串，确保键值对的顺序一致
    data_str = json.dumps(data_dict, sort_keys=True)

    # 计算MD5值
    md5_hash = hashlib.md5(data_str.encode()).hexdigest()

    return md5_hash


def split_list_by_element(file_path, split_element, keep_last):
    """
    打开文件，获取所有行，并使用指定元素分割
    Args:
        file_path: 文件路径
        split_element: 使用该元素进行数组切分
        keep_last: 因为算法缺陷，最后一部分切分块未必包含 split_element，这里需要判断是否进行检查及返回

    Returns:
        块列表。要返回所有块，keep_last传递True
    """
    line_list = get_file_lines(file_path)

    tmp = []
    sublist = []

    for index in range(len(line_list)):
        if split_element in line_list[index]:
            sublist.append((index, split_element))
            tmp.append(sublist)
            sublist = []
        else:
            sublist.append((index, line_list[index]))

    if sublist:
        tmp.append(sublist)

    if keep_last:
        return tmp
    else:
        result = []
        for item_list in tmp:
            found = False
            for item in item_list:
                if split_element in item:
                    found = True
                    break
            if found:
                result.append(item_list)

        return result


def trim_blocks(blocks):
    """
    将每个块的前后空白行去掉
    """
    res = []
    for block in blocks:
        start_index = -1
        end_index = -1

        for index, line_info in enumerate(block):
            if line_info[1].strip():
                start_index = index
                break

        for index in range(len(block) - 1, -1, -1):
            if block[index][1].strip():
                end_index = index
                break

        if end_index > start_index:
            res.append(block[start_index:end_index + 1])

    return res


def generate_uuid():
    # 生成一个随机 UUID
    return str(uuid.uuid4()).replace("-", "")


def get_uuid_line(uuid):
    """
    生成uuid行。该行将被插入到卡片块中
    """
    return f"\n{UUID_FLAG}: {uuid}"


def backup_and_write_to_file(data, file_path):
    """
    将data写入file_path

    如果写入过程出错，则报错。同时恢复原文件
    """
    if not os.path.isfile(file_path):
        raise Exception(f"文件不存在. {file_path}")
    # 备份文件到临时目录
    backup_dir = f"/tmp/{generate_uuid()}"
    os.makedirs(backup_dir, exist_ok=True)
    backup_file_path = os.path.join(backup_dir, "backup_file.txt")
    shutil.copyfile(file_path, backup_file_path)

    try:
        # 写入文件前清空原有内容
        with open(file_path, 'w') as file:
            # 将列表中的元素写入文件
            for item in data:
                file.write(str(item) + '\n')
        # 删除临时备份文件
        shutil.rmtree(backup_dir)
    except Exception as e:
        # 写入失败时，恢复文件
        shutil.copyfile(backup_file_path, file_path)
        # 删除临时备份文件
        shutil.rmtree(backup_dir)
        raise e


def extract_value_from_str(input_str, field_name):
    """
    从字符串中提取值。

    字符串的格式如  "hello: wefxv"，
    调用该函数传递hello，则提取hello后面的值。

    注意: 原始字符串必须有冒号
    """
    # 使用正则表达式匹配字段名称后面的值
    pattern = re.compile(fr"{field_name}:\s*(\w+)")
    match = pattern.search(input_str)

    # 如果匹配到，返回匹配到的值
    if not match:
        raise Exception("指定字段错误")
    return match.group(1)


def path_to_double_colon(file_path):
    """
    将文件路径转换为deck格式。即将 /a/b/c.md转换为 a::b::c
    返回结果将去掉路径前指定部分
    """
    # 使用os.path.normpath来处理相对路径
    normalized_path = os.path.normpath(file_path)

    # 分割路径
    path_parts = normalized_path.split(os.path.sep)

    # 过滤掉空部分
    filtered_path_parts = [part for part in path_parts if part]

    # 将路径部分用双冒号连接起来
    result_string = "::".join(filtered_path_parts)

    res, _ = os.path.splitext(result_string)

    parts = res.split("::")

    return "::".join(parts[7:])