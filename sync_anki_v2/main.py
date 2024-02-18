#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from anki import update_anki
from dump_files import get_files
from parse_file import get_blocks
from adjust_block import adjust_blocks
from adjust_file import adjust_files

from utils import *


def sync():
    path_list = get_files()

    # 调整文件内容。比如自动增加uuid行
    adjust_files(path_list)

    blocks = []

    for file_path in path_list:
        blocks_of_file = get_blocks(file_path)
        print(f"卡片块数: {len(blocks_of_file)}, 文件: {file_path[len(OB_NOTE_PATH):]}")
        blocks.extend(blocks_of_file)

    blocks = adjust_blocks(blocks)

    print(f"本地同步需要处理的卡片总数: {len(blocks)}")

    data_original_deck_list = []
    for file_path in path_list:
        data_original_deck_list.append(path_to_double_colon(file_path))

    update_anki(blocks, data_original_deck_list)


if __name__ == '__main__':
    sync()
