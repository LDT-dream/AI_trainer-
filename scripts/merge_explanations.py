# -*- coding: utf-8 -*-
"""
将解析合并回 HTML 文件
读取 explanations.json，修改 HTML 中的数据结构，为每道题添加解析字段。
"""
import json
import re


def md_to_html(text: str) -> str:
    """将简单的 Markdown 格式转为 HTML"""
    if not text:
        return text

    # 转义 HTML 特殊字符（但保留已有的标签）
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # 先处理加粗 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # 处理列表项 * text 或 - text
    lines = text.split('\n')
    result_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('* ') or stripped.startswith('- '):
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            item_text = stripped[2:]
            result_lines.append(f'<li>{item_text}</li>')
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if stripped:
                result_lines.append(f'<p>{stripped}</p>')
            else:
                result_lines.append('')

    if in_list:
        result_lines.append('</ul>')

    return '\n'.join(result_lines)

with open("explanations.json", "r", encoding="utf-8") as f:
    explanations = json.load(f)

with open("人工智能训练师三级刷题系统_v1.html", "r", encoding="utf-8") as f:
    content = f.read()

# Extract the D=({...}) data
start_marker = 'const D=('
start = content.find(start_marker)
if start == -1:
    print("ERROR: Could not find data start")
    exit(1)
start += len(start_marker)

# Find matching closing brace
depth = 0
end = start
for i, c in enumerate(content[start:]):
    if c == '{': depth += 1
    elif c == '}': depth -= 1
    if depth == 0:
        end = start + i + 1
        break

raw_json = content[start:end]
data = json.loads(raw_json)

# Add/update explanations to each question type
def add_explain_to_list(questions, qtype, prefix):
    """为题目列表添加/更新解析字段"""
    modified = 0
    for i, q in enumerate(questions):
        key = f"{qtype}_{i}"
        exp = explanations.get(key, "")
        if exp:
            # 将 Markdown 转为 HTML
            exp_html = md_to_html(exp)
            if qtype == 'j':
                # 判断题: [question, answer] or [question, answer, explanation]
                if len(q) == 2:
                    q.append(exp_html)
                    modified += 1
                elif len(q) >= 3:
                    q[2] = exp_html  # update existing
                    modified += 1
            else:
                # 选择题: [question, options, answer] or [question, options, answer, explanation]
                if len(q) == 3:
                    q.append(exp_html)
                    modified += 1
                elif len(q) >= 4:
                    q[3] = exp_html  # update existing
                    modified += 1
    return modified

m1 = add_explain_to_list(data.get('bj', []), 'j', 'bj')
m2 = add_explain_to_list(data.get('bs', []), 's', 'bs')
m3 = add_explain_to_list(data.get('bm', []), 'm', 'bm')

print(f"Added explanations:")
print(f"  判断题: {m1}")
print(f"  单选题: {m2}")
print(f"  多选题: {m3}")
print(f"  总计: {m1 + m2 + m3}")

# Reconstruct the JSON data string
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# Replace in HTML
new_content = content[:start] + new_json + content[end:]

with open("人工智能训练师三级刷题系统_v1.html", "w", encoding="utf-8") as f:
    f.write(new_content)

print("HTML file updated successfully!")
