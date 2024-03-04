#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import shutil
import colorful as cf


def print_dash_with_title(msg):
    """
    打印=符号
    """
    # 获取终端窗口的宽度
    terminal_width, _ = shutil.get_terminal_size()
    star_number = int((terminal_width - len(msg)) / 2)

    print(cf.bold_green(star_number * '=' + msg + star_number * '='))


def print_dash_with_title_for_end(msg):
    """
    打印=符号
    """
    # 获取终端窗口的宽度
    terminal_width, _ = shutil.get_terminal_size()
    star_number = int((terminal_width - len(msg) - 5) / 2)
    print(cf.bold_green(star_number * '=' + msg + star_number * '='))


def print_first_level_log(msg):
    print(cf.purple(msg))


def print_second_level_log(msg):
    star_number = 10
    content = star_number * '*' + f" {msg} " + star_number * '*'

    MY_COMPANY_PALETTE = {
        'companyOrange': '#32a0d1',
        'companyBaige': '#e8dcc5'
    }
    with cf.with_palette(MY_COMPANY_PALETTE) as c:
        print(c.companyOrange_on_companyBaige(content))
        print()
