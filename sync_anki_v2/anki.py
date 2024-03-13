#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import time

import requests
from get_files import get_file_path_list, get_no_exist_file_path_list, if_file_changed
from utils import *
from log import *
from parse_file import get_unsuspend_and_suspend_uuid_list


def _extract_image_src(str_data):
    return re.findall(r"<img.+?src=['\"](.+?)['\"].*?>", str_data)


def _store_media_file(media_path):
    ext_format = os.path.splitext(media_path)[1].lower()

    if ext_format in VIDEO_FORMATS:
        request_data = {
            "action": "storeMediaFile",
            "version": 6,
            "params": {
                "path": media_path,
                "filename": os.path.basename(media_path),
            },
        }
    else:
        with open(media_path, "rb") as f:
            image_data = f.read()
        image_data_base64 = base64.b64encode(image_data).decode()

        request_data = {
            "action": "storeMediaFile",
            "version": 6,
            "params": {
                "data": image_data_base64,
                "filename": media_path,
            },
        }
    response = requests.post(f"{ANKI_CONNECT}/action", json=request_data)
    return response.json()["result"] if response.ok else None


def _delete_media_file(media_file_name):
    payload = {
        "action": "deleteMediaFile",
        "version": 6,
        "params": {"filename": media_file_name},
    }
    response = requests.post(ANKI_CONNECT, json=payload)
    if err := response.json()["error"]:
        raise RuntimeError(f"删除图片或视频失败, {media_file_name}, err: {err}")
    print_first_level_log(f"删除图片或视频: {media_file_name}")


def _get_cards_info(card_ids):
    payload = {"action": "cardsInfo", "version": 6, "params": {"cards": card_ids}}
    response = requests.post(ANKI_CONNECT, json=payload)
    return response.json()["result"]


def _invoke(method, **params):
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
    note_ids = _invoke("findNotes", query=query)
    notes = []
    if note_ids:
        for note_id in note_ids:
            data = _invoke("notesInfo", notes=[int(note_id)])
            notes.extend(data)
    return notes


def _find_notes_by_deck(deck_name):
    query = f'deck:"{deck_name}" -deck:"{deck_name}::*"'
    return _find_notes(query)


def _find_cards_by_deck(deck_name):
    response = _find_cards("deck:", deck_name)
    # check if the request was successful
    if response.status_code != 200:
        raise RuntimeError(response)

    return response.json()["result"]


def _delete_all_images_of_deck(deck_name):
    image_src_list = []
    card_ids = _find_cards_by_deck(deck_name)
    card_info_list = _get_cards_info(card_ids)
    for card_info in card_info_list:
        card_back = card_info["fields"]["Back"]["value"]
        if img_src_list := _extract_image_src(card_back):
            image_src_list.extend(img_src_list)

    for image_src in image_src_list:
        _delete_media_file(image_src)


def _get_card_id_by_note_id(deck_name_list, note_id):
    """
    从deck_name_list的所有card中寻找note_id对应的card_id
    """
    for deck_name in deck_name_list:
        card_ids = _find_cards_by_deck(deck_name)
        card_info_list = _get_cards_info(card_ids)
        for card_info in card_info_list:
            if card_info["note"] == note_id:
                return card_info["cardId"]
    raise RuntimeError(f"使用note_id: {note_id} 无法找到card. deck_name_list: {deck_name_list}")


def _get_card_ids_by_note_ids(deck_name_list, note_ids):
    """
    根据笔记id列表查找card id列表
    """
    if type(deck_name_list) is not list:
        raise RuntimeError("deck_name_list 必须是list类型")
    if type(note_ids) is not list:
        raise RuntimeError("note_ids 必须是list类型")

    node_ids_set = set(note_ids)

    res = []
    for deck_name in deck_name_list:
        card_ids = _find_cards_by_deck(deck_name)
        card_info_list = _get_cards_info(card_ids)
        for card_info in card_info_list:
            if card_info["note"] in node_ids_set:
                res.append(card_info["cardId"])
                if len(res) == len(note_ids):
                    return res
    if len(res) != len(note_ids):
        raise RuntimeError("不能完全找到所有笔记的card_id")
    return res


def _delete_deck_itself(deck_name):
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
    if response.json()["error"]:
        raise RuntimeError(f"_delete_deck_itself 操作出错, deck_name: {deck_name}, err: {response.json()['error']}")

    print_first_level_log(f"删除牌组, 牌组名称: {deck_name}")


def _suspend_card(card_ids):
    """
    休眠卡片
    """
    if type(card_ids) is not list:
        raise RuntimeError("参数类型错误")

    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "suspend",
                "version": 6,
                "params": {
                    "cards": card_ids,
                },
            }
        ),
    )
    if response.json()["error"]:
        raise RuntimeError(f"_suspend_card 操作出错, card_ids: {card_ids}, err: {response.json()['error']}")


def _unsuspend_card(card_ids):
    """
    解除休眠卡片
    """
    if type(card_ids) is not list:
        raise RuntimeError("参数类型错误")

    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "unsuspend",
                "version": 6,
                "params": {
                    "cards": card_ids,
                },
            }
        ),
    )
    if response.json()["error"]:
        raise RuntimeError(f"_unsuspend_card 操作出错, card_ids: {card_ids}, err: {response.json()['error']}")


def _get_deck_stats(deck_name):
    """
    查询deck统计信息
    """
    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "getDeckStats",
                "version": 6,
                "params": {
                    "decks": [deck_name],
                },
            }
        ),
    )
    # 返回数据结构如下
    #
    # {
    #     "deck_id": 1651445861960,
    #     "name": "Easy Spanish",
    #     "new_count": 26,
    #     "learn_count": 10,
    #     "review_count": 5,
    #     "total_in_deck": 852
    # }
    response = json.loads(response.text)
    return response["result"][list(response["result"].keys())[0]]


def _create_deck_if_need(deck_name):
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
        if response.json()["error"]:
            raise RuntimeError(f"_create_deck_if_need 操作出错, deck_name: {deck_name}, err: {response.json()['error']}")

    print_first_level_log(f"创建牌组, 牌组名称: {deck_name}")


def _delete_deck(deck_name):
    _delete_all_images_of_deck(deck_name)
    _delete_deck_itself(deck_name)


def _delete_note(note_id):
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
    if response.json()["error"]:
        raise RuntimeError(f"_delete_note 操作出错, note_id: {note_id}, err: {response.json()['error']}")

    print_first_level_log(f"删除笔记, 笔记id: {note_id}")


def _forget_cards(card_id):
    """
    Forget cards, making the cards new again.
    """
    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "forgetCards",
                "version": 6,
                "params": {
                    "cards": [int(card_id)]
                },
            }
        ),
    )
    if response.json()["error"]:
        raise RuntimeError(f"_forget_cards 操作出错, note_id: {card_id}, err: {response.json()['error']}")

    print_first_level_log(f"忘记卡片, 笔记id: {card_id}")


def _add_note(deck_name, front, back):
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
                        "fields": {"Front": front, "Back": back},
                        "options": {"allowDuplicate": False},
                        "tags": [],
                    }
                },
            }
        ),
    )

    resp = response.json()

    if resp["error"]:
        raise RuntimeError(f"_add_note 操作出错, 标题: {_get_title_from_note(front)}, err: {response.json()['error']}")

    print_first_level_log(f"_add_note 笔记, 标题: {_get_title_from_note(front)}")


def _add_notes(note_info_list):
    if type(note_info_list) is not list:
        raise RuntimeError("参数类型错误")

    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "addNotes",
                "version": 6,
                "params": {
                    "notes": note_info_list
                },
            }
        ),
    )

    resp = response.json()

    if resp["error"]:
        raise RuntimeError(f"_add_notes 操作出错, err: {response.json()['error']}")


def _can_add_notes(note_info_list):
    if type(note_info_list) is not list:
        raise RuntimeError("参数类型错误")

    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "canAddNotes",
                "version": 6,
                "params": {
                    "notes": note_info_list
                },
            }
        ),
    )

    resp = response.json()

    if resp["error"]:
        raise RuntimeError(f"_can_add_notes 操作出错, err: {response.json()['error']}")
    
    return resp["result"]



def _update_note(note_id, front, back):
    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "updateNote",
                "version": 6,
                "params": {
                    "note": {
                        "id": note_id,
                        "fields": {
                            "Front": front,
                            "Back": back
                        },
                    }
                }
            }
        ),
    )

    if response.json()["error"]:
        raise RuntimeError(f"_update_note 操作出错, 标题: {_get_title_from_note(front)}, err: {response.json()['error']}")

    print_first_level_log(f"_update_note 笔记, 标题: {_get_title_from_note(front)}")


def _change_deck(deck_name, note_ids):
    """
    将note_ids笔记移动到deck_name
    Args:
        deck_name(str): 新的deck名字
        note_ids: 要移动的笔记的id列表
    """
    if not isinstance(note_ids, list):
        raise RuntimeError("note_ids字段请传递列表类型")

    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "changeDeck",
                "version": 6,
                "params": {
                    "cards": note_ids,
                    "deck": deck_name
                }
            }
        ),
    )

    if response.json()["error"]:
        raise RuntimeError(f"_change_deck 操作出错, deck_name: {deck_name}, note_ids: {note_ids}, err: {response.json()['error']}")

    print_first_level_log(f"_change_deck 笔记, len(note_ids): {len(note_ids)}, deck_name: {deck_name}")


def _gui_check_database():
    """
    检查数据库(调用后，anki会优化重建数据库)
    """
    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "guiCheckDatabase",
                "version": 6,
            }
        ),
    )

    if response.json()["error"]:
        raise RuntimeError(f"_gui_check_database 操作出错, err: {response.json()['error']}")


def _reload_collection():
    """
    命令anki重新从数据库加载数据
    """
    response = requests.post(
        ANKI_CONNECT,
        json.dumps(
            {
                "action": "reloadCollection",
                "version": 6,
            }
        ),
    )

    if response.json()["error"]:
        raise RuntimeError(f"_reload_collection 操作出错, err: {response.json()['error']}")


def _extract_file_paths(text):
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


def _extract_image_tags(markdown_text):
    # 匹配形如 ![[...]], ![](...)
    pattern = re.compile(r"\!\[\[.*?\]\]|\!\[\][\(\[].*?[\)\]]|\!\[.*?\]\([^\)]+\)")

    return pattern.findall(markdown_text)


def _modify_file_path(original_path):
    if os.path.exists(original_path):
        return original_path

    # 提取原始路径的文件名部分
    folder, file_name = os.path.split(original_path)

    if file_name.startswith("Pasted"):
        return os.path.join(folder, file_name)

    if "_MD5" in file_name:
        return os.path.join(folder, file_name.split("|")[0])

    return os.path.join(folder, f"Pasted image {file_name}")


def _prepare_value(answer):
    media_info_list = _extract_image_tags(answer)

    for md_media_tag in media_info_list:
        media_file_name_list = _extract_file_paths(md_media_tag)
        if not media_file_name_list:
            continue
        media_file_name = media_file_name_list[0]
        if not media_file_name:
            continue

        if media_file_name.startswith(ATTACHMENT_DIR):
            # Local images plus这个插件会自动给图片路径添加资产目录名
            # 因此这里需要特殊处理
            media_file_name = media_file_name[len(ATTACHMENT_DIR) + 1:]

        media_file_path = os.path.join(ROOT_IMAGE_PATH, media_file_name)
        if not os.path.exists(media_file_path):
            media_file_path = _modify_file_path(media_file_path)
        media_url = _store_media_file(media_file_path)

        ext_format = os.path.splitext(media_file_name)[1].lower()
        if ext_format in VIDEO_FORMATS:
            # 视频
            media_tag = f"<video width='150' height='150' controls><source src='{media_url}' type='video/mp4'></video>"
        else:
            # 图片
            media_tag = f"<img src='{media_url}'>"
        
        answer = answer.replace(md_media_tag, media_tag)
    return answer


def _get_all_decks():
    return _invoke("deckNames")


def _get_all_valid_decks():
    deck_name_set = set()

    all_decks = _get_all_decks()
    for deck_name in all_decks:
        if deck_name in WHITE_LIST_DECKS:
            continue

        deck_name_set.add(deck_name)

    return list(deck_name_set)


def _calculate_md5(input_string):
    return hashlib.md5(input_string.encode()).hexdigest()


def _generate_short_uuid():
    full_uuid = uuid.uuid4().hex
    return full_uuid[:10]


def _get_title_from_note(front_value):
    return front_value.split("<br/><br/>")[0]


def _remove_prefix_deck_name(deck_list):
    res = []

    deck_list = sorted(deck_list)

    for index in range(len(deck_list)):
        found_prefix = False
        for index1 in range(index + 1, len(deck_list)):
            if deck_list[index1].startswith(deck_list[index]) and deck_list[index1].count("::") != deck_list[index].count("::"):
                found_prefix = True
                break

        if not found_prefix:
            res.append(deck_list[index])
    return sorted(res)


def _create_note_info_list(data_note_list):
    """创建可以用于调用_add_notes和_can_add_notes的参数
    """
    result = []
    for data_note in data_note_list:
        front_value, back_value = _create_card_front_and_back(data_note)

        result.append({
            "deckName": data_note["deck"],
            "modelName": MODEL_NAME,
            "fields": {"Front": front_value, "Back": back_value},
            "options": {"allowDuplicate": False},
            "tags": [],
        })
    return result



def _create_card_front_and_back(data_note):
    """
    生成新卡片或者更新卡片时使用
    """
    fc = _prepare_value(data_note["front_content"])
    front_value = data_note["front_meta_info"] + first_delimiter_for_card() + fc
    if not fc:
        front_value = data_note["front_meta_info"]
    back_value = _prepare_value(data_note["back_content"])
    return front_value, back_value


def create_deck_if_need(block_list):
    data = {}
    for block in block_list:
        deck = block["deck"]
        if deck not in data:
            data[deck] = []
        data[deck].append(block)

    for data_deck in data:
        _create_deck_if_need(data_deck)


def change_deck_note(block_list):
    data = {}
    for block in block_list:
        deck = block["deck"]
        if deck not in data:
            data[deck] = []
        data[deck].append(block)

    data_uuid_to_deck = {}
    for data_deck, data_note_list in data.items():
        for data_note in data_note_list:
            if data_note["uuid"] in data_uuid_to_deck:
                raise RuntimeError("不允许笔记中出现重复uuid")
            data_uuid_to_deck[data_note["uuid"]] = data_deck

    new_deck_to_notes_ids = {}
    for anki_deck in _get_all_valid_decks():
        for deck_note in _find_notes_by_deck(anki_deck):
            deck_note_uuid = extract_value_from_str(deck_note["fields"]["Front"]["value"], "uuid")

            if deck_note_uuid in data_uuid_to_deck and data_uuid_to_deck[deck_note_uuid] != anki_deck:
                if data_uuid_to_deck[deck_note_uuid] not in new_deck_to_notes_ids:
                    new_deck_to_notes_ids[data_uuid_to_deck[deck_note_uuid]] = []
                new_deck_to_notes_ids[data_uuid_to_deck[deck_note_uuid]].append(deck_note["noteId"])

    for new_deck, note_ids in new_deck_to_notes_ids.items():
        _change_deck(new_deck, note_ids)
        _gui_check_database()
        _reload_collection()

        sleep_seconds = 2
        if len(note_ids) > 100:
            sleep_seconds = 3
        time.sleep(sleep_seconds)


def add_deck_note(block_list):
    data = {}
    for block in block_list:
        deck = block["deck"]
        if deck not in data:
            data[deck] = []
        data[deck].append(block)

    # 保存当前anki所有卡片的uuid
    uuid_set = set()
    for item in _get_all_valid_decks():
        note_list = _find_notes_by_deck(item)
        for anki_note in note_list:
            anki_note_uuid = extract_value_from_str(anki_note["fields"]["Front"]["value"], "uuid")
            if anki_note_uuid in uuid_set:
                raise RuntimeError(f"不允许笔记中出现重复的uuid, uuid: {anki_note_uuid}")
            uuid_set.add(anki_note_uuid)

    for data_deck, data_note_list in data.items():
        for data_note in data_note_list:
            if data_note["uuid"] not in uuid_set:
                # 需要新增
                front_value, back_value = _create_card_front_and_back(data_note)
                _add_note(data_deck, front_value, back_value)


def update_deck_note(block_list):
    data = {}
    for block in block_list:
        deck = block["deck"]
        if deck not in data:
            data[deck] = []
        data[deck].append(block)

    for data_deck, data_note_list in data.items():
        cache = {}
        for deck_note in _find_notes_by_deck(data_deck):
            deck_note_md5 = extract_value_from_str(deck_note["fields"]["Front"]["value"], "md5")
            deck_note_uuid = extract_value_from_str(deck_note["fields"]["Front"]["value"], "uuid")
            cache[deck_note_uuid] = {
                "note_id": deck_note["noteId"],
                "md5": deck_note_md5
            }

        for data_note in data_note_list:
            if data_note["uuid"] in cache and data_note["md5"] != cache[data_note["uuid"]]["md5"]:
                front_value, back_value = _create_card_front_and_back(data_note)
                # 需要更新
                _update_note(cache[data_note["uuid"]]["note_id"], front_value, back_value)


def _if_parent_deck(deck_name):
    target_count = deck_name.count("::")
    return any(
        item.startswith(deck_name) and item.count("::") > target_count
        for item in _remove_prefix_deck_name(_get_all_valid_decks())
    )


def delete_note(block_list):
    data = {}
    for block in block_list:
        deck = block["deck"]
        if deck not in data:
            data[deck] = []
        data[deck].append(block)

    cache = {}
    for data_deck, data_note_list in data.items():
        for data_note in data_note_list:
            cache[data_note["uuid"]] = data_deck

    file_path_list = get_file_path_list()
    deck_name_set = {
        convert_file_path_to_anki_deck_name(file_path)
        for file_path in file_path_list
    }

    for anki_deck in _get_all_valid_decks():
        # 这样操作确实只会删除需要删除的卡片，如果笔记中整个文件被删掉了，这里确实处理不了
        # 不过，那种情况可以使用下面的 delete_deck 函数处理
        if anki_deck not in deck_name_set:
            continue

        for deck_note in _find_notes_by_deck(anki_deck):
            deck_note_uuid = extract_value_from_str(deck_note["fields"]["Front"]["value"], "uuid")
            if deck_note_uuid not in cache:
                # 删除无法找到的uuid的卡片
                _delete_note(deck_note["noteId"])

            # 如果卡片所在deck与data中的deck不一致则删除卡片
            # 理论上在change_deck操作中应该成功迁移卡片
            # 但是那个接口似乎有问题
            if deck_note_uuid in cache and cache[deck_note_uuid] != anki_deck:
                _delete_note(deck_note["noteId"])

    # 测试发现父deck的卡片应该为0，如果不为0，则应该清理卡片
    for deck_name in _get_all_valid_decks():
        if not _if_parent_deck(deck_name):
            continue
        note_list = _find_notes_by_deck(deck_name)
        for note in note_list:
            _delete_note(note["noteId"])


def delete_deck():
    file_path_list = get_no_exist_file_path_list()

    for file_path in file_path_list:
        deck_name = convert_file_path_to_anki_deck_name(file_path)
        _delete_deck(deck_name)

    # 删除没有卡片的空deck
    #
    # 这里之所以要执行10次，是因为每次会把最后一空卡片deck删掉
    # 通过执行多次，可以删除嵌套层级很深的空deck
    for i in range(10):
        print_first_level_log(f"尝试第 {i + 1} 次清理空deck")
        for deck_name in _remove_prefix_deck_name(_get_all_valid_decks()):
            if _get_deck_stats(deck_name)["total_in_deck"] == 0:
                _delete_deck(deck_name)


def forget_cards(block_list):
    data = {}
    for block in block_list:
        deck = block["deck"]
        if deck not in data:
            data[deck] = []
        data[deck].append(block)

    data_uuid_to_md5 = {}
    for data_note_list in data.values():
        for data_note in data_note_list:
            if data_note["uuid"] in data_uuid_to_md5:
                raise RuntimeError("不允许笔记中出现重复uuid")
            data_uuid_to_md5[data_note["uuid"]] = data_note["md5_for_data"]

    for anki_deck in _get_all_valid_decks():
        if anki_deck not in data:
            continue
        for deck_note in _find_notes_by_deck(anki_deck):
            deck_note_uuid = extract_value_from_str(deck_note["fields"]["Front"]["value"], "uuid")
            deck_note_md5 = extract_value_from_str(deck_note["fields"]["Front"]["value"], "md5_for_data")

            if deck_note_uuid in data_uuid_to_md5 and data_uuid_to_md5[deck_note_uuid] != deck_note_md5:
                card_id = _get_card_id_by_note_id([anki_deck], deck_note["noteId"])
                _forget_cards(card_id)


def suspend_and_unsuspend_cards(block_list):
    data = {}
    for block in block_list:
        deck = block["deck"]
        if deck not in data:
            data[deck] = []
        data[deck].append(block)

    uuid_data_list = get_unsuspend_and_suspend_uuid_list()
    for uuid_data in uuid_data_list:
        unsuspend_note_ids = []
        suspend_note_ids = []

        unsuspend_uuid_set = uuid_data["unsuspend_uuid_set"]
        suspend_uuid_set = uuid_data["suspend_uuid_set"]
        unsuspend_line_index = uuid_data["unsuspend_line_index"]
        file_path = uuid_data["file_path"]
        line_count = uuid_data["line_count"]
        percent = uuid_data["percent"]
        deck_name = uuid_data["deck"]

        if unsuspend_line_index >= 0:
            print_second_level_log(f"{deck_name}, 行号: {unsuspend_line_index + 1}, 总行数: {line_count}, 百分比: {percent}")
        
        if not if_file_changed(file_path):
            # 如果不是新文件，则内容自上次未发生改变，不需要重新调用suspend和unsuspend
            continue

        if len(unsuspend_uuid_set) == 0 and len(suspend_uuid_set) == 0:
            continue

        for deck_note in _find_notes_by_deck(deck_name):
            deck_note_uuid = extract_value_from_str(deck_note["fields"]["Front"]["value"], "uuid")
            if deck_note_uuid in unsuspend_uuid_set:
                unsuspend_note_ids.append(deck_note["noteId"])

            if deck_note_uuid in suspend_uuid_set:
                suspend_note_ids.append(deck_note["noteId"])

        unsuspend_card_ids = _get_card_ids_by_note_ids([deck_name], unsuspend_note_ids)
        _unsuspend_card(unsuspend_card_ids)

        suspend_card_ids = _get_card_ids_by_note_ids([deck_name], suspend_note_ids)
        _suspend_card(suspend_card_ids)



