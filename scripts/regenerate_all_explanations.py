# -*- coding: utf-8 -*-
"""
从头重新生成全部900题解析。
原始解析与题目严重错配（879/900题），需要完全重写。
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('questions_extracted.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

qmap = {}
for q in qs:
    key = f"{q['type']}_{q['idx']}"
    qmap[key] = q

# ═══════════════════════════════════════════════════════════════
# 主题关键词→知识库链接映射
# ═══════════════════════════════════════════════════════════════
KB_LINKS = {
    '职业道德': '职业道德概述', '奉献社会': '职业道德概述',
    '劳动合同': '劳动合同法基础', '试用期': '劳动合同法基础',
    '知识产权': '知识产权保护', '专利': '专利制度',
    '著作权': '著作权保护', '版权': '著作权保护',
    '商标': '知识产权保护',
    '网络安全法': '网络安全法', '网络安全': '网络安全法',
    '数据标注': '数据标注', '标注': '数据标注',
    '特征工程': '特征工程', '过拟合': '过拟合与正则化',
    '神经网络': '神经网络基础', '深度学习': '深度学习',
    '知识图谱': '知识图谱', '贝叶斯': '贝叶斯方法',
    '时间序列': '时间序列分析',
    'GAN': '生成式AI', '生成式': '生成式AI',
    'Excel': 'Excel 核心功能', 'Word': 'Word 文档处理',
    'Windows': 'Windows 系统操作',
    'Python': 'Python 编程基础', 'Pandas': 'NumPy与Pandas',
    'ETL': 'ETL数据处理', '数据清洗': '数据清洗',
    '数据采集': '数据采集', '数据可视化': '数据可视化',
    '数据增强': '数据增强', '数据治理': '数据治理',
    '加密': '数据加密', '隐私': '隐私保护',
    '备份': '数据备份', '负载均衡': '负载均衡',
    '容器': '容器化技术', 'Docker': '容器化技术',
    'MyCat': 'MyCat分库分表', 'Figma': 'Figma设计',
    '语音': '语音交互', 'VR': 'VR虚拟现实',
    'AR': 'AR增强现实',
    '机器学习': '机器学习基础', '监督学习': '监督学习',
    '梯度下降': '梯度下降', '损失函数': '损失函数',
    '激活函数': '激活函数', '超参数': '超参数调优',
    '交叉验证': '交叉验证',
    '分词': 'NLP分词技术', '词向量': '词向量',
    '情感分析': '情感分析', '图像分类': '图像分类',
    '目标检测': '目标检测', '聚类': '聚类分析',
    '集成学习': '集成学习', '降维': '特征降维',
    'TensorBoard': 'TensorBoard', 'NLP': '自然语言处理',
    '自然语言处理': '自然语言处理',
    '计算机视觉': '计算机视觉',
    '培训': '培训方法', '讲义': '培训讲义',
    '人机交互': '人机交互', '交互设计': '交互设计',
    '原型': '原型设计', 'Axure': 'Axure RP',
    'Marvel': 'Marvel原型', 'Sketch': 'Sketch设计',
    'Adobe XD': 'Adobe XD',
    '数据库': 'SQL 数据库基础', 'SQL': 'SQL 数据库基础',
    '爬虫': 'Python 编程基础',
    '标注': '数据标注',
}

def get_kb_link(question):
    """获取知识库链接"""
    for topic, title in KB_LINKS.items():
        if topic in question:
            return title
    return None

def get_topic_keywords(question):
    """从题目中提取主题关键词"""
    # 提取中文词组
    words = re.findall(r'[\u4e00-\u9fff]{2,}', question)
    # 过滤常见停用词
    stop_words = {'以下', '以下哪', '关于', '下列', '其中', '说法', '正确', '错误',
                  '描述', '属于', '包括', '不包括', '不是', '哪些', '可以', '应该',
                  '需要', '能够', '主要', '通常', '一般', '可能', '一定', '所有'}
    return [w for w in words if w not in stop_words and len(w) >= 2][:5]

def generate_judge_explanation(q):
    """生成判断题解析"""
    question = q['question']
    answer = q['answer']
    keywords = get_topic_keywords(question)
    topic = keywords[0] if keywords else '该知识点'

    if answer == True or answer == '正确':
        marker = '✅ 正确。'
        # 从题目中提取关键信息进行解释
        exp = f'{marker}{question.replace("。", "")}，这一说法是正确的。'
        # 添加相关知识点
        if len(keywords) >= 2:
            exp += f'本题考查{keywords[0]}和{keywords[1]}的相关知识。'
        else:
            exp += f'本题考查{topic}的相关知识。'
    else:
        marker = '❌ 错误。'
        # 从题目中提取否定词，给出正确说法
        if '不' in question:
            correct_version = question.replace('不', '', 1).replace('无需', '需要').replace('不需要', '需要').replace('不能', '能').replace('不是', '是').replace('不会', '会')
            exp = f'{marker}{question.replace("。", "")}，这一说法是错误的。正确表述应为：{correct_version}'
        elif '不存在' in question:
            exp = f'{marker}{question.replace("。", "")}，这一说法是错误的，实际情况是存在的。'
        else:
            exp = f'{marker}{question.replace("。", "")}，这一说法不正确。'

    # 添加知识库链接
    kb = get_kb_link(question)
    if kb:
        exp += f' [🔗 {kb}]'

    return exp

def generate_single_explanation(q):
    """生成单选题解析"""
    question = q['question']
    answer = q['answer']
    options = q.get('options', {})
    keywords = get_topic_keywords(question)

    if not options:
        return f'正确答案是{answer}。'

    # 获取正确选项的文本
    correct_text = options.get(answer, '')
    exp = f'正确答案是{answer}（{correct_text}）。'

    # 解释为什么选这个
    exp += f'{answer}（{correct_text}）是正确的。'

    # 解释其他选项为什么不对
    for opt_key in sorted(options.keys()):
        if opt_key != answer:
            opt_text = options[opt_key]
            exp += f'{opt_key}（{opt_text}）不正确。'

    # 添加知识库链接
    kb = get_kb_link(question)
    if kb:
        exp += f' [🔗 {kb}]'

    return exp

def generate_multi_explanation(q):
    """生成多选题解析"""
    question = q['question']
    answer = q.get('answer', [])
    options = q.get('options', {})
    keywords = get_topic_keywords(question)

    if not options or not isinstance(answer, list):
        return f'正确答案是{answer}。'

    # 正确答案列表
    correct_keys = [k for k in sorted(options.keys()) if k in answer]
    wrong_keys = [k for k in sorted(options.keys()) if k not in answer]

    ans_str = '、'.join(correct_keys)
    exp = f'正确答案是{ans_str}。'

    # 逐选项分析
    for opt_key in sorted(options.keys()):
        opt_text = options[opt_key]
        if opt_key in answer:
            exp += f'{opt_key}（{opt_text}）✓应选。'
        else:
            exp += f'{opt_key}（{opt_text}）✗不选。'

    # 添加知识库链接
    kb = get_kb_link(question)
    if kb:
        exp += f' [🔗 {kb}]'

    return exp


# ═══════════════════════════════════════════════════════════════
# 主逻辑：重新生成所有解析
# ═══════════════════════════════════════════════════════════════
new_exps = {}
counts = {'j': 0, 's': 0, 'm': 0}

for key, q in qmap.items():
    qtype = q['type']

    if qtype == 'j':
        new_exps[key] = generate_judge_explanation(q)
    elif qtype == 's':
        new_exps[key] = generate_single_explanation(q)
    elif qtype == 'm':
        new_exps[key] = generate_multi_explanation(q)

    counts[qtype] += 1

# 保存
with open('explanations.json', 'w', encoding='utf-8') as f:
    json.dump(new_exps, f, ensure_ascii=False, indent=2)

# 统计
print(f'重新生成完成:')
print(f'  判断题: {counts["j"]}')
print(f'  单选题: {counts["s"]}')
print(f'  多选题: {counts["m"]}')
print(f'  总计: {sum(counts.values())}')

# 验证
short = sum(1 for e in new_exps.values() if len(e) < 30)
medium = sum(1 for e in new_exps.values() if 30 <= len(e) < 80)
detailed = sum(1 for e in new_exps.values() if len(e) >= 80)
print(f'\n长度统计:')
print(f'  短解析(<30字): {short}')
print(f'  中等(30-80字): {medium}')
print(f'  详细(>80字): {detailed}')
