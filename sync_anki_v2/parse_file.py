#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import concurrent.futures
from utils import *
from const import *
from get_files import get_all_file_path_list, get_file_path_list


def _get_raw_blocks(file_path):
    line_list = get_file_lines(file_path)

    split_parts = []
    sublist = []

    for index in range(len(line_list)):
        if END_FLAG in line_list[index]:
            if not sublist:
                continue

            sublist.append((index, line_list[index]))
            split_parts.append(sublist)
            sublist = []
        else:
            sublist.append((index, line_list[index]))

    blocks = []

    for part in split_parts:
        start_flag_index = -1
        for index, line_info in enumerate(part):
            if START_FLAG in line_info[1]:
                start_flag_index = index

            if start_flag_index > 0:
                title_index = -1
                for index1 in range(start_flag_index - 1, -1, -1):
                    if part[index1][1].strip():
                        title_index = index1
                        break
                if title_index < 0:
                    raise RuntimeError("无法找到块起始位置")

                lines1 = []
                for line1 in part[title_index:]:
                    # if START_FLAG in line1[1]:
                    #     continue
                    lines1.append(line1)
                blocks.append(lines1)
                break

        if start_flag_index < 0:
            raise RuntimeError(f"格式错误，无法找到块标题. 块起始行: {part[0][0]}, 文件: {file_path}")

    return trim_blocks(blocks)


def _check_blocks(file_path, blocks):
    for block in blocks:
        tmp = []
        for index, line_info in enumerate(block):
            if START_FLAG in line_info[1]:
                tmp.append(START_FLAG)
            if CONTENT_FLAG in line_info[1]:
                tmp.append(CONTENT_FLAG)
            if END_FLAG in line_info[1]:
                tmp.append(END_FLAG)
        
        if len(tmp) not in [2, 3]:
            raise RuntimeError(f"块标记格式不对. 块起始行索引: {block[0][0]}, 文件: {file_path}")
        if len(tmp) == 3 and (tmp[0] != START_FLAG or tmp[1] != CONTENT_FLAG or tmp[2] != END_FLAG):
            raise RuntimeError(f"请使用s c e的顺序组织块内容. 块起始行索引: {block[0][0]}, 文件: {file_path}")
        if len(tmp) == 2 and (tmp[0] != START_FLAG or tmp[1] != END_FLAG):
            raise RuntimeError(f"请使用s e的顺序组织块内容. 块起始行索引: {block[0][0]}, 文件: {file_path}")

        for index, line_info in enumerate(block):
            if index <= 1 or index == len(block) - 1:
                continue

            if START_FLAG in line_info[1]:
                raise RuntimeError(f"不允许嵌套块起始标记. 块起始行索引: {line_info[0]}, 文件路径: {file_path}")
            if END_FLAG in line_info[1]:
                raise RuntimeError(f"不允许嵌套块结束标记. 块起始行索引: {line_info[0]}, 文件路径: {file_path}")


def _get_blocks(file_path):
    """
    解析文件并获取卡片块。

    注意，文件块的前后空白行已经被去掉
    """
    blocks = _get_raw_blocks(file_path)
    _check_blocks(file_path, blocks)
    return _add_meta_info(file_path, blocks)


def _get_backend_value(block_lines):
    # return second_delimiter_for_card() + "\n---\n" + "\n".join(block_lines) + "<br><br>" + third_delimiter_for_card()
    return third_delimiter_for_card() + "\n---\n" + "\n".join(block_lines) + "<br><br>" + third_delimiter_for_card()


def _get_file_path_value(file_path):
    file_path = file_path[len(OB_NOTE_PATH):]
    if file_path.startswith("/"):
        file_path = file_path[1:]
    return file_path.replace("/", " / ")


def _is_markdown_heading(text):
    # 使用正则表达式匹配Markdown标题格式
    pattern = r'^#{1,6}\s+.+$'
    return bool(re.match(pattern, text))


def _count_hashes(text):
    # 使用正则表达式匹配标题
    pattern = r'^(#+)'  # 匹配以一个或多个#号开头的行
    if matches := re.match(pattern, text, re.MULTILINE):
        # 提取匹配到的第一个标题中#的数量
        return len(matches.group(1))
    else:
        return 0


def _add_meta_info(file_path, blocks):
    lines = get_file_lines(file_path)
    code_block_list = _get_code_blocks(lines)

    all_title_path = []
    for i in range(len(lines)):
        if _is_markdown_heading(lines[i]):
            found = False
            for code_block in code_block_list:
                if code_block[0] <= i <= code_block[1]:
                    found = True
                    break
            if not found:
                all_title_path.append((i, lines[i]))
    all_title_path.reverse()

    def get_title_path(start_index):
        """start_index是当前标题的索引. 从该所以开始寻找标题路径
        """
        title_path = []
        dash_count = []
        for item in all_title_path:
            if item[0] > start_index:
                continue

            if not title_path:
                title_path.append(_get_pure_title(item[1]))
                dash_count.append(_count_hashes(item[1]))
            else:
                curr_hash_count = _count_hashes(item[1])
                if curr_hash_count == 1:
                    title_path.append(_get_pure_title(item[1]))
                    return title_path
                if curr_hash_count >= dash_count[-1]:
                    continue
                title_path.append(_get_pure_title(item[1]))
                dash_count.append(_count_hashes(item[1]))
        return title_path
        
    res = []
    for block in blocks:
        title_path = get_title_path(block[0][0])
        front_title, front_content, back_content = _parse_block(block)

        item = {
            # front_title不允许重复，如果重复则报错
            "front_title": front_title,
            "front_content": front_content,
            "back_content": back_content,
            "title_path": title_path,
            "file_path": _get_file_path_value(file_path),
            "deck": convert_file_path_to_anki_deck_name(file_path).replace(" ", "_"),
            "uuid": _find_block_uuid(file_path, block),
        }
        # md5_for_data 是根据卡片中真正的数据计算出来的
        # 如果 md5_for_data 变化，说明卡片需要重新被记忆，因此相关的代码逻辑会重置卡片的记忆次数
        # 注意，这里会重置卡片次数
        item["front_meta_info"] = _create_note_front(
            item["front_title"],
            item["file_path"],
            item["title_path"],
            item["uuid"]
        )
        item["md5_for_data"] = _cal_md5_str_list(item["front_title"], item["front_content"], item["back_content"])
        item["front_meta_info"] = item["front_meta_info"].replace("md5_for_data_str", item["md5_for_data"])

        md5_str = _cal_md5_for_block(item)
        item["front_meta_info"] = item["front_meta_info"].replace("md5_str", md5_str)
        # 这里的 md5 字段是根据item所有字段计算出来的。也就是说item中任何字段改变都会导致卡片被更新
        # 注意，这里的md5变化只会导致卡片被更新，也就是说即使内容更新，也不会在更新后立即需要重新记忆
        item["md5"] = md5_str

        res.append(item)

    return res


def _create_note_front(title, file_path, title_path, uuid_str):
    """创建卡片笔记标题

    Args:
        title (_type_): 原始标题
        file_path (_type_): 文件路径
        title_path (list): 标题路径
        uuid_str (str): uuid
    """
    def get_title_path_str(title_path_list):
        res = []
        for item in title_path_list:
            res.append(f"<span> {item} </span>")
        return res

    return (
        f"{title}<br/><br/>" +
        f"<p class='extra_info'>📕 {file_path}</p>" +
        f"<p class='extra_info'>🗺️ {' <- '.join(get_title_path_str(title_path))}</p>" +
        f"<p class='hide'>uuid: {uuid_str}<p>" +
        f"<p class='hide'>md5: md5_str <p>"
        f"<p class='hide'>md5_for_data: md5_for_data_str <p>"
    )


def _get_code_blocks(lines):
    code_blocks = []

    q = 0
    for i, line in enumerate(lines):
        if i <= q:
            continue

        if '````' in line:
            for k in range(i + 1, len(lines)):
                if '````' in lines[k]:
                    code_blocks.append([i, k])
                    q = k
                    break

        if i <= q:
            continue

        if '```' in line:
            for k in range(i + 1, len(lines)):
                if '```' in lines[k]:
                    code_blocks.append([i, k])
                    q = k
                    break

    return code_blocks


def _get_pure_title(raw_title):
    return raw_title.strip("#").strip()


def _find_block_uuid(file_path, block):
    """
    查找block中的uuid
    """
    for line_info in block:
        if END_FLAG in line_info[1]:
            return line_info[1].split()[1].strip()
    raise RuntimeError(f"无法找到uuid. 文件: {file_path}, 行: {block[0][0]}")


def _trim_lines(lines):
    """
    将前后空白行去掉
    """
    start_index = -1
    end_index = -1

    for index, line in enumerate(lines):
        if line.strip():
            start_index = index
            break

    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip():
            end_index = index
            break

    if end_index >= start_index:
        return lines[start_index:end_index + 1]

    return []


def _parse_block(block):
    """
    解析block
    """
    front_title = block[0][1].strip("#").strip()
    front_content = []
    back_content = []

    start_flag_index = -1
    content_flag_index = -1

    for index, line_info in enumerate(block):
        if START_FLAG in line_info[1]:
            start_flag_index = index

        if CONTENT_FLAG in line_info[1]:
            content_flag_index = index
        
        if start_flag_index >= 0 and content_flag_index >= 0:
            break

    if content_flag_index > 0:
        for line_info in block[start_flag_index + 1:content_flag_index]:
            front_content.append(line_info[1].rstrip())

    back_index = -1
    if content_flag_index > 0:
        back_index = content_flag_index + 1
    else:
        back_index = start_flag_index + 1

    for line_info in block[back_index:len(block)-1]:
        back_content.append(line_info[1].rstrip())
    back_content = _trim_lines(back_content)

    ad_prefix = "````ad-"
    for i in range(len(front_content)):
        if front_content[i].startswith("title") and i > 0 and front_content[i-1].startswith(ad_prefix):
            front_content[i] = "==" + front_content[i] + "=="
    for i in range(len(back_content)):
        if back_content[i].startswith("title") and i > 0 and back_content[i-1].startswith(ad_prefix):
            back_content[i] = "==" + back_content[i] + "=="

    # 将ad-note插件的形式转换为方便在卡片中显示的形式
    # 仍旧会包裹内容
    for i in range(len(back_content)):
        if back_content[i].startswith("````"):
            back_content[i] = ad_line() + "\n"
    
    front_content = "\n".join(front_content) 
    back_content = _get_backend_value(back_content)

    return front_title, front_content, back_content


def _cal_md5_for_block(block):
    """
    对block计算md5
    """
    json_data = json.dumps(block, sort_keys=True)
    return hashlib.md5(json_data.encode()).hexdigest()


def _cal_md5_str_list(*args):
    """
    计算列表的md5
    """
    sorted_args = sorted(args)
    concatenated_string = ''.join(sorted_args)
    return hashlib.md5(concatenated_string.encode()).hexdigest()


def get_blocks(all_block=True):
    """
    获取卡片块
    """
    path_list = get_all_file_path_list()
    if not all_block:
        path_list = get_file_path_list()

    result = []

    # 使用 ProcessPoolExecutor 进行多进程处理
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # 将每个文件路径提交给 _get_blocks 函数进行处理，并获取结果
        results = list(executor.map(_get_blocks, path_list))

    # 将所有结果合并到一个列表中
    for blocks in results:
        result.extend(blocks)

    return result


def get_unsuspend_and_suspend_uuid_list():
    """
    获取unsuspend和suspend的uuid列表
    注意,会返回两个值,一个是unsuspend的uuid列表,一个是suspend的uuid列表
    """
    path_list = get_all_file_path_list()

    result = []

    for file_path in path_list:
        all_uuid_set = set()
        unsuspend_uuid_set = set()
        unsuspend_line_index = -1

        lines = get_file_lines(file_path)
        for index in range(len(lines)):
            line = lines[index]
            if SUSPEND_FLAG in line:
                unsuspend_line_index = index

            if END_FLAG in line:
                all_uuid_set.add(line.split()[1].strip())

            if END_FLAG in line and unsuspend_line_index == -1:
                unsuspend_uuid_set.add(line.split()[1].strip())
        
        percent = 0
        if unsuspend_line_index > -1:
            percent = round((unsuspend_line_index + 1) / len(lines), 2)

        result.append({
            "deck": convert_file_path_to_anki_deck_name(file_path),
            "unsuspend_uuid_set": unsuspend_uuid_set,
            "suspend_uuid_set": all_uuid_set.difference(unsuspend_uuid_set),
            "unsuspend_line_index": unsuspend_line_index,
            "file_path": file_path,
            "line_count": len(lines),
            "percent": percent
        })
    
    return sorted(result, key=lambda x: (-x["percent"], x["file_path"]))
