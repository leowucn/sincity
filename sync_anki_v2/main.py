#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from anki import *
from get_files import get_files
from parse_file import get_blocks
from adjust_file import adjust_files
from log import *
from utils import *


def sync():
    print_dash_with_title(" total files ")
    path_list = get_files()
    # 调整文件内容。比如自动增加uuid行
    adjust_files(path_list)
    for file_path in path_list:
        print_first_level_log(file_path)

    print_dash_with_title(" decks ")
    blocks = get_blocks()
    create_deck_if_need(blocks)

    print_dash_with_title("forget_cards")
    blocks = get_blocks()
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    forget_cards(blocks)

    print_dash_with_title(" change_deck_note ")
    blocks = get_blocks()
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    # ankiconnect的change_deck方法可能有bug。导致每次总是有一点点数据没有迁移成功
    # 因此这里change完后，下面会删除没有迁移成功的卡片，然后在此add
    change_deck_note(blocks)

    print_dash_with_title(" delete_note ")
    blocks = get_blocks()
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    delete_note(blocks)

    print_dash_with_title(" add_deck_note ")
    blocks = get_blocks()
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    add_deck_note(blocks)

    print_dash_with_title(" update_deck_note ")
    blocks = get_blocks()
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    update_deck_note(blocks)

    print_dash_with_title(" delete_deck ")
    blocks = get_blocks()
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    data_original_deck_list = [
        convert_file_path_to_anki_deck_name(file_path)
        for file_path in path_list
    ]
    delete_deck(blocks, data_original_deck_list)

    print_dash_with_title(" suspend_and_unsuspend ")
    blocks = get_blocks()
    suspend_and_unsuspend_cards(blocks)

    print_dash_with_title_for_end(" END ")


if __name__ == '__main__':
    sync()
