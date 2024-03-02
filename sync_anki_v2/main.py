#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from anki import *
from get_files import get_file_path_list, update_file_path_cache
from parse_file import get_blocks
from adjust_file import adjust_files
from log import *
from utils import *


def sync():
    start_time = time.time()

    print_dash_with_title(" total files ")
    path_list = get_file_path_list()
    # 调整文件内容。比如自动增加uuid行
    adjust_files(path_list)
    for file_path in path_list:
        print_first_level_log(file_path)

    blocks = get_blocks(False)
    all_blocks = get_blocks()

    print_dash_with_title(" create_deck_if_need ")
    create_deck_if_need(all_blocks)

    print_dash_with_title("forget_cards")
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    forget_cards(blocks)

    print_dash_with_title(" change_deck_note ")
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    # ankiconnect的change_deck方法可能有bug。导致每次总是有一点点数据没有迁移成功
    # 因此这里change完后，下面会删除没有迁移成功的卡片，然后在此add
    change_deck_note(blocks)

    print_dash_with_title(" delete_note ")
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    delete_note(blocks)

    print_dash_with_title(" add_deck_note ")
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(all_blocks)}")
    add_deck_note(all_blocks)

    print_dash_with_title(" delete_deck ")
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    delete_deck()

    print_dash_with_title(" update_deck_note ")
    print_first_level_log(f"本次同步需要处理的卡片总数: {len(blocks)}")
    update_deck_note(blocks)

    print_dash_with_title(" suspend_and_unsuspend ")
    suspend_and_unsuspend_cards(blocks)

    # 更新文件缓存
    update_file_path_cache()

    print_dash_with_title_for_end(f" END. 耗时: {time.time() - start_time:.2f} s")


if __name__ == '__main__':
    sync()
