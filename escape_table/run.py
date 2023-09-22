import re

# 定义一个处理每行文本的函数
def process_line(line):
    return re.sub(r'([$#&<>{}\[\]()\_*+-.!])', r'\\\1', line)

# 指定 Markdown 文件的路径
markdown_file_path = './data.md'

# 输出文件路径
output_file_path = './escaped_data.md'

# 读取并处理文件
with open(markdown_file_path, 'r', encoding='utf-8') as file, open(output_file_path, 'w', encoding='utf-8') as output_file:
    for line_number, line in enumerate(file, start=1):
        if line_number <= 2:
            output_file.write(line)
        else:
            processed_line = process_line(line.strip())
            output_file.write(processed_line + '\n')
