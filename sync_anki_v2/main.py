#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from anki import *
from get_files import get_files
from parse_file import get_blocks
from adjust_file import adjust_files
from log import *
from utils import *


def sync():
    start_time = time.time()

    print_dash_with_title(" total files ")
    path_list = get_files()
    # 调整文件内容。比如自动增加uuid行
    adjust_files(path_list)
    for file_path in path_list:
        print_first_level_log(file_path)

    print_dash_with_title(" decks ")
    blocks = get_blocks()
    create_deck_if_need(blocks)

    print_dash_with_title(" forget_cards ")
    blocks = get_blocks()
    print_first_level_log(f"本地同步需要处理的卡片总数: {len(blocks)}")
    forget_cards(blocks)

    print_dash_with_title(" change_deck_note ")
    blocks = get_blocks()
    print_first_level_log(f"本地同步需要处理的卡片总数: {len(blocks)}")
    change_deck_note(blocks)

    print_dash_with_title(" add_deck_note ")
    blocks = get_blocks()
    print_first_level_log(f"本地同步需要处理的卡片总数: {len(blocks)}")
    add_deck_note(blocks)

    print_dash_with_title(" update_deck_note ")
    blocks = get_blocks()
    print_first_level_log(f"本地同步需要处理的卡片总数: {len(blocks)}")
    update_deck_note(blocks)

    print_dash_with_title(" delete_deck_note ")
    blocks = get_blocks()
    print_first_level_log(f"本地同步需要处理的卡片总数: {len(blocks)}")
    data_original_deck_list = []
    for file_path in path_list:
        data_original_deck_list.append(convert_file_path_to_anki_deck_name(file_path))
    delete_deck_note(blocks, data_original_deck_list)

    print_dash_with_title(" suspend_and_unsuspend ")
    blocks = get_blocks()
    suspend_and_unsuspend_cards(blocks)

    print_dash_with_title_for_end(f" END. 同步耗时: {round(time.time() - start_time, 1)} ")


if __name__ == '__main__':
    sync()
