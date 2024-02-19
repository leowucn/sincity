#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils import *
from const import *


def _create_note_front(title, file_path, title_path, md5, uuid_str):
    """创建卡片笔记标题

    Args:
        title (_type_): 原始标题
        file_path (_type_): 数据源文件路径
        title_path (list): 标题路径
        md5 (str): md5
    """
    return (
        f"{title}<br/><br/>"
        f"<p class='extra_info'>文件源: {file_path[len(OB_NOTE_PATH):]}</p> <br/><br/>"
        f"<p class='extra_info'>标题路径: {' <- '.join(title_path)} </p> <br/><br/>"
        f"<p class='hide'>uuid: {uuid_str}<p>"
        f"<p class='hide'>md5: {md5}<p>"
    )


def _cal_md5_for_block(block):
    """
    对block计算md5
    """
    json_data = json.dumps(block, sort_keys=True)
    return hashlib.md5(json_data.encode()).hexdigest()


def adjust_block(block):
    """
    优化卡片块的格式。修改字段内容格式，或者增加字段
    """
    block["back_content"] = second_delimiter_for_card() + "\n---\n" + block["back_content"] + "<br><br>" + third_delimiter_for_card()

    md5_val = _cal_md5_for_block(block)
    block["md5"] = md5_val

    block["front_meta_info"] = _create_note_front(
        block["front_title"],
        block["file_path"],
        block["title_path"],
        block["md5"],
        block["uuid"]
    )
    return block


def adjust_blocks(blocks):
    for index in range(len(blocks)):
        blocks[index] = adjust_block(blocks[index])

    return blocks
