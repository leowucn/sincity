#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import shutil
from print_color import print


def print_dash_with_title(msg):
    """
    打印=符号
    """
    # 获取终端窗口的宽度
    terminal_width, _ = shutil.get_terminal_size()
    star_number = int((terminal_width - len(msg)) / 2)
    print(int(star_number) * '=' + msg + int(star_number) * '=', color='yellow')


def print_dash_with_title_for_end(msg):
    """
    打印=符号
    """
    # 获取终端窗口的宽度
    terminal_width, _ = shutil.get_terminal_size()
    star_number = int((terminal_width - len(msg)) / 2)
    print(int(star_number) * '=' + msg + int(star_number) * '=', color='green')


def print_first_level_log(msg):
    print(msg, color='red')


def print_second_level_log(msg):
    max_length = 110
    star_number = int((max_length - len(msg)) / 2)
    print(int(star_number) * '*' + f" {msg} " + int(star_number) * '*', color='yellow')
