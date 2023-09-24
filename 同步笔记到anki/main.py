#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

import requests
import json
import base64

START_FLAG = "<-s->"
END_FLAG = "<-e->"
ANKI_CONNECT = "http://localhost:8765"
# 设置根牌组名称
ROOT_DECK_NAME = "ob"
MODEL_NAME = "KaTex and Markdown Basic"
OB_NOTE_PATH = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob"
ROOT_IMAGE_PATH = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob/资产"
# 忽略目录
IGNORE_UPLOAD_DIRS = [".obsidian", ".trash"]
# START_FLAG和END_FLAG标签时将忽略如下格式的文件
IGNORE_UPLOAD_EXTENSIONS = [
    ".DS_Store",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".svg",
    ".heif",
    ".heic",
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mpg",
    ".3gp",
]


def print_msg(msg, error):
    if error is None:
        print(f"成功{msg}")
    else:
        print(
            f"--------------------------------------------------------{msg}失败. err: {error}"
        )


def remove_whitespace(str_data):
    return "".join(str_data.split())


def remove_prefix_from_string(s):
    """
    去掉字符串前面的一个或多个数字、空格、"."
    """
    pattern = r"^[\d\s\.]+"
    return re.sub(pattern, "", s)


def extract_content(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content_list = []
    front_title = ""
    front_content = ""
    back_content = ""

    extract = False
    prev_line = ""

    for line in lines:
        if START_FLAG in line:
            extract = True
            # Use the content from the previous non-empty line as the title
            front_title = prev_line.strip()
            front_title = re.sub(r"^#+\s*", "", front_title).strip()
            front_title = remove_prefix_from_string(front_title)
            front_title = front_title.replace("**", "")
            front_title = front_title.replace("$", "")
            front_title = front_title.removesuffix(":")
            front_title = front_title.removesuffix("：")

            front_content = line.strip().removesuffix(START_FLAG)

        elif END_FLAG in line:
            extract = False

            back_content = back_content.strip()
            back_content = back_content.replace("$", "")
            back_content = back_content.strip().replace("\n", "<br/>")
            if front_title and front_title not in ['````', 'title']:
                item = {
                    "front_title": front_title.lstrip("#").strip(),
                    "front_content": front_content,
                    "back_content": back_content
                }
                content_list.append(item)

            front_title = ""
            front_content = ""
            back_content = ""
        elif extract:
            if line.startswith("````") or line.startswith("title"):
                continue
            back_content += line

        # Update the previous line
        prev_line = line

    return content_list


def extract_contents_from_dir(dir_path, level=1, parent_name=None, IGNORE_UPLOAD_DIRS_list=None):
    results = {}
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isfile(file_path) and file.endswith(".md"):
            if contents := extract_content(file_path):
                dir_name = os.path.basename(os.path.dirname(file_path))
                key = dir_name if level == 1 else f"{parent_name}::{dir_name}"
                key = remove_whitespace(key)
                if key not in results:
                    results[key] = []
                results[key].extend(contents)
        elif os.path.isdir(file_path) and (
                IGNORE_UPLOAD_DIRS_list is None or os.path.basename(file_path) not in IGNORE_UPLOAD_DIRS_list
        ):
            sub_results = extract_contents_from_dir(
                file_path,
                level + 1,
                os.path.basename(dir_path)
                if parent_name is None
                else f"{parent_name}::{os.path.basename(dir_path)}",
                IGNORE_UPLOAD_DIRS_list=IGNORE_UPLOAD_DIRS_list,
            )
            if sub_results:
                results |= sub_results
    return results


def check_file(file_path):
    if not file_path.endswith(".md"):
        return

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    stack = []
    for line_number, line in enumerate(lines, start=1):
        pos = 0
        while pos < len(line):
            start_pos = line.find(START_FLAG, pos)
            end_pos = line.find(END_FLAG, pos)

            if start_pos != -1 and (end_pos == -1 or start_pos < end_pos):
                stack.append((start_pos, line_number))
                pos = start_pos + len(START_FLAG)
            elif end_pos != -1 and (start_pos == -1 or end_pos < start_pos):
                if not stack:
                    msg = f"""
                    File {file_path} contains mismatched tags:
                    Found an unmatched <-e-> at line {line_number}
                    """
                    raise RuntimeError(f"文件检查错误: {msg}")
                stack.pop()
                pos = end_pos + len(END_FLAG)
            else:
                break
    if stack:
        msg = f"""
        File {file_path} contains mismatched tags:
        Found an unmatched <-s-> at line {stack[-1][1]}")
        """
        raise RuntimeError(f"文件检查错误: {msg}")


def get_file_extension(file_name):
    if file_name.startswith("."):
        return file_name
    return os.path.splitext(file_name)[1]


def check_directory(directory, ignored_directories, IGNORE_UPLOAD_EXTENSIONS_list):
    """
    检查目录中的md文件是否有没有匹配的 START_FLAG和END_FLAG标签
    """
    for root, dirs, files in os.walk(directory):
        # Remove ignored directories from the list of dirs to prevent further traversal
        dirs[:] = [d for d in dirs if d not in ignored_directories]

        for file in files:
            file_extension = get_file_extension(file)
            if file_extension not in IGNORE_UPLOAD_EXTENSIONS_list:
                file_path = os.path.join(root, file)
                check_file(file_path)


def extract_image_src(str_data):
    return re.findall(r"<img.+?src=['\"](.+?)['\"].*?>", str_data)


def extract_image_info(md_image_info):
    def v1():
        nonlocal md_image_info
        if "[[" in md_image_info:
            md_image_info = "|".join(list(map(lambda x: x.strip(), md_image_info.split("|"))))
            if not (
                    match := re.match(
                        r"!\[\[(?P<filename>[^\[\]|]+)(?:\|(?P<width>\d+))?\]\]",
                        md_image_info,
                    )
            ):
                return None
            return match["filename"]
        
        return None

    def v2():
        pattern = r"!\[\]\((.*?)\)"
        match = re.search(pattern, md_image_info)

        if match:
            path = match[1]
            return path
        else:
            return None

    file_name = v1() or v2()

    return file_name


def store_media_file(image_path):
    # 上传图片
    with open(image_path, "rb") as f:
        image_data = f.read()
    image_data_base64 = base64.b64encode(image_data).decode()

    # Construct request data
    request_data = {
        "action": "storeMediaFile",
        "version": 6,
        "params": {
            "data": image_data_base64,
            "filename": image_path,
        },
    }

    response = requests.post(f"{ANKI_CONNECT}/action", json=request_data)

    print_msg(f"存储图片或视频, image_path: {ROOT_IMAGE_PATH}", response.json()["error"])

    return response.json()["result"] if response.ok else None


def delete_media_file(media_file_name):
    payload = {
        "action": "deleteMediaFile",
        "version": 6,
        "params": {"filename": media_file_name},
    }
    response = requests.post(ANKI_CONNECT, json=payload)
    print_msg("删除图片或视频", response.json()["error"])


def get_cards_info(card_ids):
    payload = {"action": "cardsInfo", "version": 6, "params": {"cards": card_ids}}
    response = requests.post(ANKI_CONNECT, json=payload)
    print_msg("根据卡片id查询卡片信息", response.json()["error"])

    return response.json()["result"]


def invoke(method, **params):
    payload = {"action": method, "params": params, "version": 6}
    response = requests.post(ANKI_CONNECT, data=json.dumps(payload))
    return response.json()["result"]


def _find_cards(arg0, arg1):
    action = "findCards"
    params = {"query": f"{arg0}{arg1}"}
    return requests.post(
        ANKI_CONNECT, json={"action": action, "params": params, "version": 6}
    )


def _find_notes(query):
    note_ids = invoke("findNotes", query=query)
    notes = []
    if note_ids:
        for note_id in note_ids:
            data = invoke("notesInfo", notes=[int(note_id)])
            notes.extend(data)
    return notes


def find_notes_by_front(front):
    query = f'front:"{front}"'
    return _find_notes(query)


def find_notes_by_deck(deck_name):
    query = f'deck:"{deck_name}" -deck:"{deck_name}::*"'
    return _find_notes(query)


def find_cards_by_front(front):
    response = _find_cards("front:", front)
    print_msg("查询卡片列表", response.json()["error"])

    # check if the request was successful
    if response.status_code != 200:
        raise RuntimeError(response)

    return response.json()["result"]


def find_cards_by_deck(deck_name):
    response = _find_cards("deck:", deck_name)
    print_msg(f"根据牌组查询关联的卡片列表, 牌组名称: {deck_name}", response.json()["error"])

    # check if the request was successful
    if response.status_code != 200:
        raise RuntimeError(response)

    return response.json()["result"]


def delete_all_images_of_deck(deck_name):
    image_src_list = []
    card_ids = find_cards_by_deck(deck_name)
    card_info_list = get_cards_info(card_ids)
    for card_info in card_info_list:
        card_back = card_info["fields"]["Back"]["value"]
        if img_src_list := extract_image_src(card_back):
            image_src_list.extend(img_src_list)

    for image_src in image_src_list:
        delete_media_file(image_src)


def delete_deck_itself(deck_name):
    # 删除牌组
    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "deleteDecks",
                "version": 6,
                "params": {
                    "decks": [deck_name],
                    "cardsToo": True,  # 如果该牌组下存在卡片，也会一并删除
                },
            }
        ),
    )
    print_msg(f"删除牌组, 牌组名称: {deck_name}", response.json()["error"])


def create_deck_if_need(deck_name):
    # 检查牌组是否存在，如果不存在则创建
    response = requests.post(ANKI_CONNECT, json.dumps({"action": "deckNames"}))

    decks = json.loads(response.text)
    if deck_name not in decks:
        response = requests.post(
            ANKI_CONNECT,
            json.dumps(
                {
                    "action": "createDeck",
                    "version": 6,
                    "params": {"deck": deck_name},
                }
            ),
        )
        print_msg(f"创建牌组, 牌组名称: {deck_name}", response.json()["error"])


def delete_deck(deck_name):
    delete_all_images_of_deck(deck_name)
    delete_deck_itself(deck_name)


def delete_note(note_id):
    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "deleteNotes",
                "version": 6,
                "params": {"notes": [int(note_id)]},
            }
        ),
    )
    print_msg(f"删除笔记, 笔记id: {note_id}", response.json()["error"])


def add_note(deck_name, front, back):
    fields = {"Front": front, "Back": back}
    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "addNote",
                "version": 6,
                "params": {
                    "note": {
                        "deckName": deck_name,
                        "modelName": MODEL_NAME,
                        "fields": fields,
                        "options": {"allowDuplicate": False},
                        "tags": [],
                    }
                },
            }
        ),
    )

    print()

    print_msg(f"添加笔记, 标题: {get_front_title(front)}", response.json()["error"])


def get_front_title(front_value):
    """
    根据卡片的front获取标题。主要用于显示日志信息
    """
    return front_value.strip().split('---')[0]


def prepare_value(answer):
    image_info_list = re.findall(r"\!\[\[.*?\]\]", answer)
    image_info_list.extend(re.findall(r"!\[\][\(\[].*?[\)\]]", answer))

    for raw_md_image_info in image_info_list:

        image_file_name = extract_image_info(raw_md_image_info)

        image_path = os.path.join(ROOT_IMAGE_PATH, image_file_name)
        image_url = store_media_file(image_path)

        img_tag = f"<img src='{image_url}'>"

        answer = answer.replace(raw_md_image_info, img_tag)
    return answer


def get_all_decks():
    return invoke("deckNames")


def create_note_front(title, content):
    if content:
        return f" {title} <br /> <br /> --- <br /> {content} "
    else:
        return f" {title}"


def update_data(data):
    # 从anki查询到的deck列表
    deck_name_set = set()

    all_decks = get_all_decks()
    for deck_name in all_decks:
        if not deck_name.startswith(ROOT_DECK_NAME):
            continue

        deck_name_set.add(deck_name)

    print("处理牌组----------------------------------------------------")
    # 用于记录卡片的标题的map，方便判断是否已存在相同标题的卡片
    front_m = {}
    # 用于记录卡片的背面的map，方便判断是否已存在相同背面的卡片。如果卡面背面内容已变更则需要重新上传
    back_m = {}

    for deck_name in data:
        # 判断是否有多余牌组需要删除
        if deck_name in deck_name_set:
            deck_name_set.remove(deck_name)

        tmp_deck_name_set = deck_name_set.copy()
        for dn in deck_name_set:
            if deck_name.startswith(dn):
                tmp_deck_name_set.remove(dn)
        deck_name_set = tmp_deck_name_set.copy()

        print("\n")
        deck_notes_list = find_notes_by_deck(deck_name)

        for note_info in deck_notes_list:
            front_m[note_info["fields"]["Front"]["value"]] = note_info["noteId"]
            back_m[note_info["fields"]["Back"]["value"]] = note_info["noteId"]

        print(f"处理牌组 - <<{deck_name}>>")
        for key in front_m:
            print(f"<<{deck_name}>> 牌组已存在的笔记: {key.split('---')[0].strip()}")

        notes_list = data[deck_name]

        create_deck_if_need(deck_name)

        for note in notes_list:
            front_value = create_note_front(note["front_title"], prepare_value(note["front_content"]))
            back_value = prepare_value(note["back_content"])

            # 从anki获取的卡片里去掉即将要更新的
            if front_value in front_m and back_value in back_m:
                print(f"该笔记需要保留: {get_front_title(front_value)}")
                del front_m[front_value]
                continue

            notes_info_list = find_notes_by_front(front_value)
            #
            if len(notes_info_list) > 0:
                for note_info in notes_info_list:
                    if note_info["fields"]["Back"]["value"] != back_value:
                        # 更新卡片之前先从anki删除卡片
                        delete_note(note_info["noteId"])
                        add_note(deck_name, front_value, back_value)

                        # 如果采用更新的方式。修改后的卡片不会作为需要复习的
                        # self.update_note_fields(card_info["note"], deck_name, note["header"], note["content"])
            else:
                add_note(deck_name, front_value, back_value)

    print("\n\n处理需要删除的笔记----------------------------------------\n")
    for header, note_id in front_m.items():
        print(f"删除笔记: {get_front_title(header)}")
        # 删除在od中已经不存在的笔记卡片
        delete_note(note_id)

    print("\n\n删除多余牌组----------------------------------------------\n")
    for deck_name in deck_name_set:
        print(f"删除牌组: {deck_name}")
        # 删除在od中已经不存在的笔记卡片
        delete_deck(deck_name)


# 检查是否有未配对的标识符
check_directory(OB_NOTE_PATH, IGNORE_UPLOAD_DIRS, IGNORE_UPLOAD_EXTENSIONS)
notes = extract_contents_from_dir(OB_NOTE_PATH, IGNORE_UPLOAD_DIRS_list=IGNORE_UPLOAD_DIRS)
update_data(notes)
