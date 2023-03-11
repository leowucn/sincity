#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import requests
import json
import base64


class ExtractData:
    def __init__(self):
        pass

    def remove_whitespace(self, str_data):
        return ''.join(str_data.split())

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
                title = line[line.find("#") + 1: line.find("<!--s-->")].strip()
                title = re.sub(r"^#+\s*", "", title).strip()
            elif "<!--e-->" in line:
                extract = False
                content_list.append({"header": title, "content": content.strip().replace("\n", "<br>")})
                title = ""
                content = ""
            elif extract:
                content += line

        return content_list

    def extract_contents_from_dir(self, dir_path, level=1, parent_name=None, ignore_dirs=None):
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
            elif os.path.isdir(file_path) and (ignore_dirs is None or os.path.basename(file_path) not in ignore_dirs):
                sub_results = self.extract_contents_from_dir(
                    file_path,
                    level + 1,
                    os.path.basename(dir_path)
                    if parent_name is None
                    else f"{parent_name}::{os.path.basename(dir_path)}",
                    ignore_dirs=ignore_dirs
                )
                if sub_results:
                    results.update(sub_results)
        return results


class Sync:
    def __init__(self, url, image_dir_path):
        self.url = url
        self.image_path = image_dir_path

    def update_data(self, data):
        for deck_name in data:
            notes_list = data[deck_name]

            print(f"处理牌组 - {deck_name}")
            # 先删除旧的牌组及其卡片数据
            self.delete_all_note_of_deck_v2(deck_name)

            self.create_deck_if_need(deck_name)

            for note in notes_list:
                self.add_note(deck_name, note["header"], note["content"])

    def add_note(self, deck_name, front, answer):
        image_info_list = re.findall(r'\!\[\[.*?\]\]', answer)
        for raw_md_image_info in image_info_list:
            image_info = self.extract_image_info(raw_md_image_info)
            image_width = image_info[1]
            image_path = os.path.join(self.image_path, str(image_info[0]))
            image_url = self.store_media_file(image_path)

            img_tag = f"<img src='{image_url}'>"
            if image_width is not None:
                img_tag = f"<img src='{image_url}' width={int(image_width)}>"
            answer = answer.replace(raw_md_image_info, img_tag)

        fields = {
            "Front": front,
            "Back": answer
        }
        requests.post(self.url, json.dumps({
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": deck_name,
                    "modelName": "Basic",
                    "fields": fields,
                    "options": {
                        "allowDuplicate": False
                    },
                    "tags": []
                }
            }
        }))

    def create_deck_if_need(self, deck_name):
        # 检查牌组是否存在，如果不存在则创建
        response = requests.post(self.url, json.dumps({
            "action": "deckNames"
        }))
        decks = json.loads(response.text)
        if deck_name not in decks:
            requests.post(self.url, json.dumps({
                "action": "createDeck",
                "version": 6,
                "params": {
                    "deck": deck_name
                }
            }))

    def delete_deck(self, deck_name):
        # 删除牌组
        requests.post(self.url, json.dumps({
            "action": "deleteDecks",
            "version": 6,
            "params": {
                "decks": [deck_name],
                "cardsToo": True  # 如果该牌组下存在卡片，也会一并删除
            }
        }))

    def delete_all_note_of_deck_v2(self, deck_name):
        self.delete_all_images_of_deck(deck_name)
        self.delete_deck(deck_name)

    def delete_all_images_of_deck(self, deck_name):
        action = "findCards"

        # define the AnkiConnect parameters
        params = {
            "query": f"deck:{deck_name}"
        }

        response = requests.post(self.url, json={
            "action": action,
            "params": params,
            "version": 6
        })

        # check if the request was successful
        if response.status_code != 200:
            raise Exception(response)

        image_src_list = []
        card_ids = response.json()["result"]
        payload = {
            "action": "cardsInfo",
            "version": 6,
            "params": {
                "cards": card_ids
            }
        }
        response = requests.post(self.url, json=payload)
        for card_info in response.json()["result"]:
            card_back = card_info["fields"]["Back"]["value"]
            img_src_list = self.extract_image_src(card_back)
            if img_src_list:
                image_src_list.extend(img_src_list)

        for image_src in image_src_list:
            self.delete_media_file(image_src)

    def delete_media_file(self, media_file_name):
        payload = {
            "action": "deleteMediaFile",
            "version": 6,
            "params": {
                "filename": media_file_name
            }
        }
        requests.post(self.url, json=payload)

    def extract_image_src(self, str_data):
        return re.findall(r"<img.+?src=['\"](.+?)['\"].*?>", str_data)

    def store_media_file(self, image_path):
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
                "filename": os.path.basename(image_path),
            }
        }

        response = requests.post(f"{self.url}/action", json=request_data)

        if response.ok:
            media_id = response.json()["result"]
        else:
            media_id = None
        return media_id

    def extract_image_info(self, md_image_info):
        match = re.match(r"!\[\[(?P<filename>[^\[\]|]+)(?:\|(?P<width>\d+))?\]\]", md_image_info)
        if match:
            filename = match.group("filename")
            width = match.group("width")
            return (filename, width)
        else:
            return (None, None)


note_path = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob"
image_path = "/Users/wupeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/ob/资产"
ignore_dirs = [".obsidian", ".trash"]
notes = ExtractData().extract_contents_from_dir(note_path, ignore_dirs=ignore_dirs)
Sync("http://localhost:8765", image_path).update_data(notes)
