#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from anki import *
from get_files import get_files
from parse_file import get_blocks
from adjust_file import adjust_files

from utils import *


def sync():
    path_list = get_files()
    # 调整文件内容。比如自动增加uuid行
    adjust_files(path_list)

    print("=========================================要处理的文件列表==========================================")
    for file_path in path_list:
        print(file_path)

    blocks = get_blocks()
    create_deck_if_need(blocks)

    blocks = get_blocks()
    print("==========================================forget_cards===========================================")
    print(f"本地同步需要处理的卡片总数: {len(blocks)}")
    forget_cards(blocks)

    blocks = get_blocks()
    print("========================================change_deck_note=========================================")
    print(f"本地同步需要处理的卡片总数: {len(blocks)}")
    change_deck_note(blocks)

    blocks = get_blocks()
    print("==========================================add_deck_note==========================================")
    print(f"本地同步需要处理的卡片总数: {len(blocks)}")
    add_deck_note(blocks)

    blocks = get_blocks()
    print("========================================update_deck_note=========================================")
    print(f"本地同步需要处理的卡片总数: {len(blocks)}")
    update_deck_note(blocks)

    blocks = get_blocks()
    print("========================================delete_deck_note=========================================")
    print(f"本地同步需要处理的卡片总数: {len(blocks)}")
    data_original_deck_list = []
    for file_path in path_list:
        data_original_deck_list.append(path_to_double_colon(file_path))
    delete_deck_note(blocks, data_original_deck_list)
    print("**********************************************end************************************************")


if __name__ == '__main__':
    sync()
