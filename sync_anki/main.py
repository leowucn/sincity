#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import requests
import json
import base64
import hashlib
import uuid
from const import *


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


def remove_special_chars(string):
    # 使用正则表达式替换所有非字母、数字、空格和下划线的字符为空字符串
    return re.sub(r'[^\w\s]', '', string).strip()


def extract_hash_count(title):
    if title.startswith('#'):
        count = 0
        for char in title:
            if char == '#':
                count += 1
            else:
                break
        return count
    else:
        return 0


def get_code_blocks(lines):
    code_blocks = []

    q = 0
    for i, line in enumerate(lines):
        if i <= q:
            continue

        if '````' in line:
            for k in range(i+1, len(lines)):
                if '````' in lines[k]:
                    code_blocks.append([i, k])
                    q = k
                    break

        if i <= q:
            continue

        if '```' in line:
            for k in range(i+1, len(lines)):
                if '```' in lines[k]:
                    code_blocks.append([i, k])
                    q = k
                    break

    return code_blocks


def find_title_path(curr_index, lines):
    title_path = []

    code_blocks = get_code_blocks(lines)

    pre_hash_count = 100
    for i in range(curr_index, -1, -1):
        hit = False
        for code_block in code_blocks:
            if code_block[0] < i < code_block[1]:
                hit = True
                break

        if hit:
            continue

        curr_line = lines[i].strip()
        if not curr_line.startswith("#") and curr_line.endswith(END_FLAG):
            continue

        curr_line = curr_line.replace(START_FLAG, "").replace(END_FLAG, "")

        if not curr_line:
            continue

        hash_count = extract_hash_count(curr_line)

        if not hash_count:
            continue

        title = curr_line.strip('# ')

        # 如果到了一级标题或者已经倒序遍历了所有行
        if hash_count == 1 or i == 0:
            title_path.append(title)
            return title_path

        # 把当前行的标题加入结果
        if curr_index == i:
            title_path.append(title)
            pre_hash_count = hash_count

        if hash_count < pre_hash_count:
            title_path.append(title)
            pre_hash_count = hash_count

    return title_path


def extract_content(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content_list = []
    front_title = ""
    front_content = ""
    back_content = ""

    extract = False
    prev_line = ""
    title_path = []

    for i in range(len(lines)):
        line = lines[i]

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

            title_path = find_title_path(i, lines)

        elif END_FLAG in line:
            extract = False

            back_content = back_content.strip()
            back_content = back_content.replace("$", "")
            back_content = back_content.strip().replace("\n", "<br/>")

            front_title = front_title.strip()
            if front_title and front_title not in ['````', 'title']:
                if remove_special_chars(
                        front_title.lstrip("#").strip()
                ):
                    item = {
                        "front_title": front_title.lstrip("#").strip(),
                        "front_content": front_content,
                        "back_content": back_content,
                        "file_path": file_path,
                        "title_path": title_path
                    }
                    content_list.append(item)

            front_title = ""
            front_content = ""
            back_content = ""
            title_path = []
        elif extract:
            if line.startswith("````") or line.startswith("title"):
                continue
            back_content += line

        # Update the previous line
        prev_line = line

    return content_list


def extract_contents_from_dir_v2(dir_path, level=1, parent_name=None, IGNORE_UPLOAD_DIRS_list=None):
    results = {}
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isfile(file_path) and file.endswith(".md"):
            if contents := extract_content(file_path):
                dir_name = os.path.basename(os.path.dirname(file_path))
                key = dir_name if level == 1 else f"{parent_name}::{dir_name}::{os.path.basename(file_path).strip('.md')}"
                key = remove_whitespace(key)
                if key not in results:
                    results[key] = []
                results[key].extend(contents)
        elif os.path.isdir(file_path) and (
                IGNORE_UPLOAD_DIRS_list is None or os.path.basename(file_path) not in IGNORE_UPLOAD_DIRS_list
        ):
            sub_results = extract_contents_from_dir_v2(
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

    # print_msg(f"存储图片或视频, image_path: {ROOT_IMAGE_PATH}", response.json()["error"])

    return response.json()["result"] if response.ok else None


def delete_media_file(media_file_name):
    payload = {
        "action": "deleteMediaFile",
        "version": 6,
        "params": {"filename": media_file_name},
    }
    response = requests.post(ANKI_CONNECT, json=payload)
    if err := response.json()["error"]:
        raise RuntimeError(f"删除图片或视频失败, {media_file_name}, err: {err}")
    print_msg(f"删除图片或视频: {media_file_name}", None)


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


def find_notes_by_deck(deck_name):
    query = f'deck:"{deck_name}" -deck:"{deck_name}::*"'
    return _find_notes(query)


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

    resp = response.json()

    if err := resp["error"]:
        raise RuntimeError(f"add 笔记出错 {err}, title: {get_title_from_note(front)}")

    print_msg(f"add 笔记, 标题: {get_title_from_note(front)}", None)
    return resp["result"]


def extract_md5_from_note_header(front_value):
    # 使用正则表达式匹配MD5值的模式
    md5_pattern = r'[0-9a-f]{32}'

    if md5_matches := re.findall(md5_pattern, front_value):
        return md5_matches[0]
    else:
        return None


def extract_file_paths(text):
    # 匹配形如 ![[...]], ![](...)
    pattern = re.compile(r"\!\[\[.*?\]\]|\!\[\][\(\[].*?[\)\]]|\!\[.*?\]\([^\)]+\)")

    # 使用正则表达式找到所有匹配项
    image_info_list = pattern.findall(text)

    # 提取文件路径
    file_paths = []
    for image_info in image_info_list:
        if path_match := re.search(r"\(.*?\)|\[\[.*?\]\]", image_info):
            file_path = path_match[0][1:-1]
            if file_path_match := re.search(r"([^\s]+\.[^\s]+)", file_path):
                file_path = file_path_match[1]
                if file_path.startswith("["):
                    file_path = file_path[1:]
                if file_path.endswith("]"):
                    file_path = file_path[:-1]
                file_paths.append(file_path)

    return file_paths


def extract_image_tags(markdown_text):
    # 匹配形如 ![[...]], ![](...)
    pattern = re.compile(r"\!\[\[.*?\]\]|\!\[\][\(\[].*?[\)\]]|\!\[.*?\]\([^\)]+\)")

    return pattern.findall(markdown_text)


def modify_file_path(original_path):
    if os.path.exists(original_path):
        return original_path

    # 提取原始路径的文件名部分
    folder, file_name = os.path.split(original_path)

    if file_name.startswith("Pasted"):
        return os.path.join(folder, file_name)

    if "_MD5" in file_name:
        return os.path.join(folder, file_name.split("|")[0])

    return os.path.join(folder, f"Pasted image {file_name}")


def prepare_value(answer):
    image_info_list = extract_image_tags(answer)

    for md_img_tag in image_info_list:
        image_file_name_list = extract_file_paths(md_img_tag)
        if not image_file_name_list:
            continue
        image_file_name = image_file_name_list[0]
        if not image_file_name:
            continue

        ext_format = os.path.splitext(image_file_name)[1]
        if ext_format in VIDEO_FORMATS:
            info = "<p style='color: red'> 视频格式文件忽略上传 </p>"
            answer = answer.replace(md_img_tag, info)
            print("已忽略视频文件: ", image_file_name)
        else:
            if image_file_name.startswith(ATTACHMENT_DIR):
                # Local images plus这个插件会自动给图片路径添加资产目录名
                # 因此这里需要特殊处理
                image_file_name = image_file_name[len(ATTACHMENT_DIR) + 1:]

            image_path = os.path.join(ROOT_IMAGE_PATH, image_file_name)
            if not os.path.exists(image_path):
                image_path = modify_file_path(image_path)
            image_url = store_media_file(image_path)

            img_tag = f"<img src='{image_url}'>"

            answer = answer.replace(md_img_tag, img_tag)
    return answer


def get_all_decks():
    return invoke("deckNames")


def create_note_front(title, content, file_path, title_path, md5):
    """创建卡片笔记标题

    Args:
        title (_type_): 原始标题
        content (_type_): 原始内容
        file_path (_type_): 数据源文件路径
        title_path (list): 标题路径
        md5 (str): md5
    """
    title = (
        f" {title}<br/><br/> "
        f" <p id='extra_info'>文件源: {file_path[len(OB_NOTE_PATH):]}</p> <br/><br/>"
        f" <p id='extra_info'>标题路径: {' <- '.join(title_path)} </p> <br/><br/>"
        f" <p id='extra_info'>md5: {md5}<p>"
    )

    if content:
        title = f"{title} <br/><br/> {content}"
    return title


def get_all_valid_decks():
    deck_name_set = set()

    all_decks = get_all_decks()
    for deck_name in all_decks:
        if deck_name in WHITE_LIST_DECKS:
            continue

        deck_name_set.add(deck_name)

    return deck_name_set


def calculate_md5(input_string):
    return hashlib.md5(input_string.encode()).hexdigest()


def generate_short_uuid():
    full_uuid = uuid.uuid4().hex
    return full_uuid[:10]


def get_title_from_note(front_value):
    return front_value.split("<br/><br/>")[0]


def update_data(data):
    # 从anki查询到的deck列表，并且去掉了白名单中需要保存的牌组
    curr_decks = get_all_valid_decks()

    for deck_name in curr_decks.difference(set(data.keys())):
        found = any(item.startswith(deck_name) for item in data.keys())
        if not found:
            print(f"删除牌组: {deck_name}")
            delete_deck(deck_name)

    for deck_name in data:
        print(f"\n\n处理牌组: {deck_name}")
        deck_notes_list = find_notes_by_deck(deck_name)

        anki_deck_note_md5_dict = {}

        for note_info in deck_notes_list:
            note_id = note_info["noteId"]
            note_title = note_info["fields"]["Front"]["value"]
            note_md5 = extract_md5_from_note_header(note_info["fields"]["Front"]["value"])
            anki_deck_note_md5_dict[note_md5] = {
                "noteId": note_id,
                "title": note_title,
            }

        # 当前牌组中的卡片列表
        notes_list = data[deck_name]
        create_deck_if_need(deck_name)

        ob_deck_notes_md5_set = set()
        curr_note = {}

        for note in notes_list:
            print(f"处理笔记: {note['front_title']}")
            note_md5 = calculate_md5(note["front_title"] + note["front_content"] + note["back_content"])
            ob_deck_notes_md5_set.add(note_md5)

            front_value = create_note_front(
                note["front_title"],
                prepare_value(note["front_content"]),
                note["file_path"],
                note["title_path"],
                note_md5,
            ).strip().strip("*")
            back_value = prepare_value(note["back_content"])

            curr_note[note_md5] = {
                "front": front_value,
                "back": back_value,
            }

        for md5 in set(anki_deck_note_md5_dict).difference(ob_deck_notes_md5_set):
            # 删除笔记
            delete_note(anki_deck_note_md5_dict[md5]["noteId"])

        for md5 in ob_deck_notes_md5_set.difference(set(anki_deck_note_md5_dict)):
            item = curr_note[md5]
            add_note(deck_name, item["front"], item["back"])


notes = extract_contents_from_dir_v2(OB_NOTE_PATH, IGNORE_UPLOAD_DIRS_list=IGNORE_UPLOAD_DIRS)
update_data(notes)
