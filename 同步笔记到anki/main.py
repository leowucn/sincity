#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time

import requests
import json
import base64


class ExtractData:
    def __init__(self):
        pass

    def remove_whitespace(self, str_data):
        return "".join(str_data.split())

    def remove_prefix_from_string(self, s):
        """
        去掉字符串前面的一个或多个数字、空格、"."
        """
        pattern = r"^[\d\s\.]+"
        return re.sub(pattern, "", s)

    def extract_content(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        content_list = []
        title = ""
        content = ""

        extract = False
        for line in lines:
            if "<!--s-->" in line:
                extract = True
                title = line[line.find("#") + 1 : line.find("<!--s-->")].strip()
                title = re.sub(r"^#+\s*", "", title).strip()
                title = self.remove_prefix_from_string(title)
                title = title.replace("**", "")
                title = title.replace("$", "")
                title = title.removesuffix(":")
                title = title.removesuffix("：")
            elif "<!--e-->" in line:
                extract = False

                content = content.strip()
                content = content.replace("$", "")
                content = content.strip().replace("\n", "<br/>")
                # content = content.strip().replace("\n", "<br/>")
                item = {"header": title, "content": content}
                content_list.append(item)

                title = ""
                content = ""
            elif extract:
                content += line

        return content_list

    def extract_contents_from_dir(
        self, dir_path, level=1, parent_name=None, ignore_dirs=None
    ):
        results = {}
        for file in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file)
            if os.path.isfile(file_path) and file.endswith(".md"):
                contents = self.extract_content(file_path)
                if contents:
                    dir_name = os.path.basename(os.path.dirname(file_path))
                    key = dir_name if level == 1 else f"{parent_name}::{dir_name}"
                    key = self.remove_whitespace(key)
                    if key not in results:
                        results[key] = []
                    results[key].extend(contents)
            elif os.path.isdir(file_path) and (
                ignore_dirs is None or os.path.basename(file_path) not in ignore_dirs
            ):
                sub_results = self.extract_contents_from_dir(
                    file_path,
                    level + 1,
                    os.path.basename(dir_path)
                    if parent_name is None
                    else f"{parent_name}::{os.path.basename(dir_path)}",
                    ignore_dirs=ignore_dirs,
                )
                if sub_results:
                    results.update(sub_results)
        return results


class CheckSETag:
    """
    检查 directory 中的md文件是否有未匹配的 "<!--s-->"和"<!--e-->"标签
    """

    def check_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        stack = []
        line_number = 1

        for line in lines:
            pos = 0
            while pos < len(line):
                start_pos = line.find("<!--s-->", pos)
                end_pos = line.find("<!--e-->", pos)

                if start_pos != -1 and (end_pos == -1 or start_pos < end_pos):
                    stack.append((start_pos, line_number))
                    pos = start_pos + len("<!--s-->")
                elif end_pos != -1 and (start_pos == -1 or end_pos < start_pos):
                    if not stack:
                        msg = f"""
                        File {file_path} contains mismatched tags:
                        Found an unmatched <!--e--> at line {line_number}
                        """
                        raise Exception(f"文件检查错误: {msg}")
                    stack.pop()
                    pos = end_pos + len("<!--e-->")
                else:
                    break
            line_number += 1

        if stack:
            msg = f"""
            File {file_path} contains mismatched tags:
            Found an unmatched <!--s--> at line {stack[-1][1]}")
            """
            raise Exception(f"文件检查错误: {msg}")

    def get_file_extension(self, file_name):
        if file_name.startswith("."):
            return file_name
        return os.path.splitext(file_name)[1]

    def check_directory(self, directory, ignored_directories, ignored_extensions):
        """
        检查目录中的md文件是否有没有匹配的 "<!--s-->"和"<!--e-->"标签
        """
        for root, dirs, files in os.walk(directory):
            # Remove ignored directories from the list of dirs to prevent further traversal
            dirs[:] = [d for d in dirs if d not in ignored_directories]

            for file in files:
                file_extension = self.get_file_extension(file)
                if file_extension not in ignored_extensions:
                    file_path = os.path.join(root, file)
                    self.check_file(file_path)


class Sync:
    def __init__(self, url, image_dir_path):
        self.url = url
        self.image_path = image_dir_path

    def update_data(self, data, rootdeck_name):
        deck_name_set = set()

        all_decks = self.get_all_decks()
        for deck_name in all_decks:
            if not deck_name.startswith(rootdeck_name):
                continue

            deck_name_set.add(deck_name)

        print("处理牌组----------------------------------------------------")
        front_m = {}
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
            deck_notes_list = self.find_notes_by_deck(deck_name)
            for note_info in deck_notes_list:
                front_m[note_info["fields"]["Front"]["value"]] = note_info["noteId"]

            print(f"处理牌组 - <<{deck_name}>>")
            for key in front_m:
                print(f"<<{deck_name}>> 牌组已存在的笔记: {key}")

            notes_list = data[deck_name]

            self.create_deck_if_need(deck_name)

            for note in notes_list:
                # 从anki获取的卡片里去掉即将要更新的
                if note["header"] in front_m:
                    print(f'该笔记需要保留: {note["header"]}')
                    del front_m[note["header"]]

                notes_info_list = self.find_notes_by_front(note["header"])
                #
                if len(notes_info_list) > 0:
                    for note_info in notes_info_list:
                        if note_info["fields"]["Back"]["value"] != self.prepare_answer(
                            note["content"]
                        ):
                            # 更新卡片之前先从anki删除卡片
                            self.delete_note(note_info["noteId"])
                            self.add_note(deck_name, note["header"], note["content"])

                            # 如果采用更新的方式。修改后的卡片不会作为需要复习的
                            # self.update_note_fields(card_info["note"], deck_name, note["header"], note["content"])
                else:
                    self.add_note(deck_name, note["header"], note["content"])

        print("\n\n处理需要删除的笔记----------------------------------------\n")
        for header, note_id in front_m.items():
            print(f"删除笔记: {header}")
            # 删除在od中已经不存在的笔记卡片
            self.delete_note(note_id)

        print("\n\n删除多余牌组----------------------------------------------\n")
        for deck_name in deck_name_set:
            print(f"删除牌组: {deck_name}")
            # 删除在od中已经不存在的笔记卡片
            self.delete_deck(deck_name)

    def get_all_decks(self):
        decks = self.invoke("deckNames")
        return decks

    def prepare_answer(self, answer):
        image_info_list = re.findall(r"\!\[\[.*?\]\]", answer)
        for raw_md_image_info in image_info_list:
            image_info = self.extract_image_info(raw_md_image_info)
            image_width = image_info[1]
            image_path = os.path.join(self.image_path, str(image_info[0]))
            image_url = self.store_media_file(image_path)

            img_tag = f"<img src='{image_url}'>"
            if image_width is not None:
                img_tag = f"<img src='{image_url}' width={int(image_width)}>"
            answer = answer.replace(raw_md_image_info, img_tag)
        return answer

    def add_note(self, deck_name, front, answer):
        answer = self.prepare_answer(answer)
        fields = {"Front": front, "Back": answer}
        response = requests.post(
            self.url,
            json.dumps(
                {
                    "action": "addNote",
                    "version": 6,
                    "params": {
                        "note": {
                            "deckName": deck_name,
                            "modelName": modelName,
                            "fields": fields,
                            "options": {"allowDuplicate": False},
                            "tags": [],
                        }
                    },
                }
            ),
        )

        self.print_msg(f"添加笔记, 标题: {front}", response.json()["error"])

    def delete_note(self, note_id):
        response = requests.post(
            self.url,
            json.dumps(
                {
                    "action": "deleteNotes",
                    "version": 6,
                    "params": {"notes": [int(note_id)]},
                }
            ),
        )
        self.print_msg(f"删除笔记, 笔记id: {note_id}", response.json()["error"])

    def update_note_fields(self, note_id, deck_name, front, answer):
        answer = self.prepare_answer(answer)
        res = requests.put(
            self.url,
            data=json.dumps(
                {
                    "action": "updateNoteFields",
                    "version": 6,
                    "params": {
                        "note": {
                            "id": int(note_id),
                            "deckName": deck_name,
                            "modelName": "KaTex and Markdown Basic",
                            "fields": {"Front": front, "Back": answer},
                        }
                    },
                }
            ),
        )

    def create_deck_if_need(self, deck_name):
        # 检查牌组是否存在，如果不存在则创建
        response = requests.post(self.url, json.dumps({"action": "deckNames"}))

        decks = json.loads(response.text)
        if deck_name not in decks:
            response = requests.post(
                self.url,
                json.dumps(
                    {
                        "action": "createDeck",
                        "version": 6,
                        "params": {"deck": deck_name},
                    }
                ),
            )
            self.print_msg(f"创建牌组, 牌组名称: {deck_name}", response.json()["error"])

    def delete_deck_itself(self, deck_name):
        # 删除牌组
        response = requests.post(
            self.url,
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
        self.print_msg(f"删除牌组, 牌组名称: {deck_name}", response.json()["error"])

    def delete_deck(self, deck_name):
        self.delete_all_images_of_deck(deck_name)
        self.delete_deck_itself(deck_name)

    def delete_all_images_of_deck(self, deck_name):
        image_src_list = []
        card_ids = self.find_cards_by_deck(deck_name)
        card_info_list = self.get_cards_info(card_ids)
        for card_info in card_info_list:
            card_back = card_info["fields"]["Back"]["value"]
            img_src_list = self.extract_image_src(card_back)
            if img_src_list:
                image_src_list.extend(img_src_list)

        for image_src in image_src_list:
            self.delete_media_file(image_src)

    def find_cards_by_deck(self, deck_name):
        action = "findCards"
        # define the AnkiConnect parameters
        params = {"query": f"deck:{deck_name}"}

        response = requests.post(
            self.url, json={"action": action, "params": params, "version": 6}
        )
        self.print_msg(f"根据牌组查询关联的卡片列表, 牌组名称: {deck_name}", response.json()["error"])

        # check if the request was successful
        if response.status_code != 200:
            raise Exception(response)

        return response.json()["result"]

    def find_cards_by_front(self, front):
        action = "findCards"
        # define the AnkiConnect parameters
        params = {"query": f"front:{front}"}

        response = requests.post(
            self.url, json={"action": action, "params": params, "version": 6}
        )
        self.print_msg(f"查询卡片列表", response.json()["error"])

        # check if the request was successful
        if response.status_code != 200:
            raise Exception(response)

        return response.json()["result"]

    def invoke(self, method, **params):
        payload = {"action": method, "params": params, "version": 6}
        response = requests.post(self.url, data=json.dumps(payload))
        return response.json()["result"]

    def find_notes_by_front(self, front):
        query = f'front:"{front}"'
        note_ids = self.invoke("findNotes", query=query)
        notes = []
        for note_id in note_ids:
            data = self.invoke("notesInfo", notes=[int(note_id)])
            notes.extend(data)
        return notes

    def find_notes_by_deck(self, deck_name):
        # query = f'deck:"{deck_name}"'
        query = f'deck:"{deck_name}" -deck:"{deck_name}::*"'
        note_ids = self.invoke("findNotes", query=query)
        notes = []
        for note_id in note_ids:
            data = self.invoke("notesInfo", notes=[int(note_id)])
            notes.extend(data)
        return notes

    def get_cards_info(self, card_ids):
        payload = {"action": "cardsInfo", "version": 6, "params": {"cards": card_ids}}
        response = requests.post(self.url, json=payload)
        self.print_msg(f"根据卡片id查询卡片信息", response.json()["error"])

        return response.json()["result"]

    def delete_media_file(self, media_file_name):
        payload = {
            "action": "deleteMediaFile",
            "version": 6,
            "params": {"filename": media_file_name},
        }
        response = requests.post(self.url, json=payload)
        self.print_msg(f"删除图片或视频", response.json()["error"])

    def extract_image_src(self, str_data):
        return re.findall(r"<img.+?src=['\"](.+?)['\"].*?>", str_data)

    def store_media_file(self, image_path):
        # 上传图片
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_data_base64 = base64.b64encode(image_data).decode()

        filename = os.path.basename(image_path)

        # Construct request data
        request_data = {
            "action": "storeMediaFile",
            "version": 6,
            "params": {
                "data": image_data_base64,
                "filename": filename,
            },
        }

        response = requests.post(f"{self.url}/action", json=request_data)

        self.print_msg(f"存储图片或视频, filename: {filename}", response.json()["error"])

        if response.ok:
            media_id = response.json()["result"]
        else:
            media_id = None
        return media_id

    def extract_image_info(self, md_image_info):
        match = re.match(
            r"!\[\[(?P<filename>[^\[\]|]+)(?:\|(?P<width>\d+))?\]\]", md_image_info
        )
        if match:
            filename = match.group("filename")
            width = match.group("width")
            return (filename, width)
        else:
            return (None, None)

    def print_msg(self, msg, error):
        if error is None:
            print(f"成功{msg}")
        else:
            print(f"--------------------------------------------------------{msg}失败. err: {error}")


# 设置根牌组名称
root_deck_name = "ob"
modelName = "KaTex and Markdown Basic"
note_path = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob"
image_path = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob/资产"
# 忽略目录
ignore_dirs = [".obsidian", ".trash"]
# "<!--s-->"和"<!--e-->"标签时将忽略如下格式的文件
ignored_extensions = [
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

CheckSETag().check_directory(note_path, ignore_dirs, ignored_extensions)
notes = ExtractData().extract_contents_from_dir(note_path, ignore_dirs=ignore_dirs)
Sync("http://localhost:8765", image_path).update_data(notes, root_deck_name)
