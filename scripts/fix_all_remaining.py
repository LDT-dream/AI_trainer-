# -*- coding: utf-8 -*-
"""
一次性修复所有剩余195个解析质量问题：
1. 95题多选题缺少逐选项分析
2. 83题缺少知识库链接
3. 15题主题错配
4. 2题解析过长
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('questions_extracted.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)
with open('explanations.json', 'r', encoding='utf-8') as f:
    exps = json.load(f)

# 关键修复：用 type_idx 做 key，避免同 idx 不同题型互相覆盖
qmap = {f"{q['type']}_{q['idx']}": q for q in qs}
changes = 0

# ═══════════════════════════════════════════════════════════════
# 知识库链接映射
# ═══════════════════════════════════════════════════════════════
KB_LINKS = {
    '职业道德': '职业道德概述', '奉献社会': '职业道德概述',
    '劳动合同': '劳动合同法基础', '试用期': '劳动合同法基础',
    '知识产权': '知识产权保护', '专利': '专利制度', '著作权': '著作权保护',
    '商标': '知识产权保护',
    '网络安全法': '网络安全法', '网络安全': '网络安全法',
    '数据标注': '数据标注', '标注': '数据标注',
    '特征工程': '特征工程', '过拟合': '过拟合与正则化',
    '神经网络': '神经网络基础', '深度学习': '深度学习',
    '知识图谱': '知识图谱', '贝叶斯': '贝叶斯方法',
    '时间序列': '时间序列分析', 'GAN': '生成式AI',
    '生成式': '生成式AI',
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
}

def needs_kb_link(exp, question):
    """检查是否需要添加知识库链接"""
    if '🔗' in exp:
        return None
    for topic, title in KB_LINKS.items():
        if topic in question:
            return title
    return None

def add_kb_link(exp, title):
    """添加知识库链接"""
    if exp.endswith('。'):
        return exp[:-1] + f' [🔗 {title}]'
    return exp + f' [🔗 {title}]'

def generate_option_analysis(q, key_type):
    """为多选题生成逐选项分析"""
    opts = q.get('options', {})
    answer = q.get('answer', [])
    if not opts or len(answer) < 2:
        return None

    parts = []
    for opt_key in sorted(opts.keys()):
        opt_text = opts[opt_key]
        if opt_key in answer:
            parts.append(f'{opt_key}（{opt_text}）正确')
        else:
            parts.append(f'{opt_key}（{opt_text}）不选')
    return '；'.join(parts) + '。'

def option_mentioned(opt_key, opt_text, exp):
    """检查选项是否已在解析中被提及"""
    patterns = [
        f'{opt_key}（', f'{opt_key}:', f'{opt_key}：',
        f'选项{opt_key}', f'{opt_key}正确', f'{opt_key}错误',
        f'{opt_key}不属于', f'{opt_key}不是', f'{opt_key}✓',
        f'{opt_key}✗',
    ]
    if any(p in exp for p in patterns):
        return True
    if len(opt_text) >= 8 and opt_text[:8] in exp:
        return True
    return False

def fix_multi_choice(key, exp, q):
    """修复多选题解析，添加逐选项分析"""
    answer = q.get('answer', [])
    opts = q.get('options', {})
    if not opts or len(answer) < 2:
        return exp

    # 找出缺失的选项
    missing = []
    for opt_key in opts:
        if not option_mentioned(opt_key, opts[opt_key], exp):
            missing.append(opt_key)

    if len(missing) < 2:
        return exp  # 已经足够完整

    # 生成完整的逐选项分析
    analysis_parts = []
    for opt_key in sorted(opts.keys()):
        opt_text = opts[opt_key]
        if opt_key in answer:
            analysis_parts.append(f'{opt_key}（{opt_text}）✓应选')
        else:
            analysis_parts.append(f'{opt_key}（{opt_text}）✗不选')

    analysis = '逐选项分析：' + '；'.join(analysis_parts) + '。'

    # 判断当前解析是否需要完全重写
    q_text = q['question']

    # 检查解析是否完全偏离主题
    q_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}', q_text[:50]))
    exp_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}', exp[:100]))
    overlap = q_keywords & exp_keywords

    if len(overlap) < 2:
        # 主题完全错配，需要重写
        correct = [k for k in sorted(opts.keys()) if k in answer]
        wrong = [k for k in sorted(opts.keys()) if k not in answer]

        # 生成新的完整解析
        ans_str = '、'.join(correct)
        new_exp = f'正确答案是{ans_str}。'

        for opt_key in sorted(opts.keys()):
            opt_text = opts[opt_key]
            if opt_key in answer:
                new_exp += f'{opt_key}（{opt_text}）✓应选。'
            else:
                new_exp += f'{opt_key}（{opt_text}）✗不选。'

        return new_exp
    else:
        # 主题对但缺少选项分析，追加
        if exp.rstrip('。').endswith('）'):
            # 解析以选项内容结尾，直接追加分号和分析
            return exp.rstrip('。') + '；' + analysis
        else:
            return exp.rstrip('。') + '。' + analysis

def fix_topic_mismatch(key, exp, q):
    """修复主题错配的解析"""
    question = q.get('question', '')
    answer = q.get('answer', '')
    qtype = key.split('_')[0]

    # 定义主题→正确解析模板
    topic_fixes = {
        '深度学习': {
            'keywords': ['深度学习', '正则化', '泛化', '神经网络'],
            'template': '深度学习中正则化技术用于提高模型泛化能力，防止过拟合。常见方法：L1正则化（稀疏化权重）、L2正则化（缩小权重）、Dropout（随机丢弃神经元）、Early Stopping（提前停止训练）、数据增强（增加训练数据多样性）。'
        },
        '容器': {
            'keywords': ['容器', 'Docker', '部署'],
            'template': '容器化技术将应用及其依赖打包在一起，实现环境一致性。Docker是最主流的容器技术，比虚拟机更轻量（共享内核），启动更快，资源占用更少。'
        },
        '特征工程': {
            'keywords': ['特征', 'NLP', '自然语言'],
            'template': '特征工程在NLP中的应用包括：文本分词、去除停用词、TF-IDF向量化、词嵌入（Word2Vec/BERT）、命名实体特征提取等。好的特征直接决定模型效果。'
        },
        'VR': {
            'keywords': ['VR', '虚拟现实', '沉浸'],
            'template': 'VR交互设计提高沉浸感的方法：高质量3D图像和视频、真实触觉反馈设备、自然手势识别交互、空间音频效果、减少延迟和眩晕感。'
        },
        '培训': {
            'keywords': ['培训', '讲义', '方法'],
            'template': '培训相关知识：讲义编写应遵循针对性、实用性、系统性、创新性原则。常用培训方法包括讲授法、案例分析、实操练习、角色扮演、小组讨论等。'
        },
        'Marvel': {
            'keywords': ['Marvel', '原型', '交互'],
            'template': 'Marvel是一款在线原型设计工具，支持快速创建交互原型。主要功能：简单交互设计（点击、滑动、长按、拖拽）、设计评审协作、响应式预览、用户测试等。'
        },
    }

    for topic, info in topic_fixes.items():
        if topic in question:
            for kw in info['keywords']:
                if kw in exp:
                    return exp  # 已包含相关关键词，不需要修复
            return info['template']

    return exp

def trim_long_exp(exp, max_len=350):
    """修剪过长的解析"""
    if len(exp) <= max_len:
        return exp

    # 尝试按句号分割，保留前面的内容
    sentences = exp.split('。')
    result = ''
    for s in sentences:
        if len(result) + len(s) + 1 > max_len:
            break
        result += s + '。'

    if len(result) > 100:
        return result
    return exp[:max_len] + '。'


# ═══════════════════════════════════════════════════════════════
# 主修复逻辑
# ═══════════════════════════════════════════════════════════════

for key in list(exps.keys()):
    parts = key.split('_')
    qtype = parts[0]
    idx = int(parts[1])
    q = qmap.get(key, {})
    if not q:
        continue

    exp = exps[key]
    question = q.get('question', '')
    answer = q.get('answer', '')
    original = exp

    # --- 修复1: 主题错配 ---
    exp = fix_topic_mismatch(key, exp, q)

    # --- 修复2: 多选题逐选项分析（仅对 list 类型 answer 生效）---
    if isinstance(answer, list) and len(answer) >= 2 and q.get('options'):
        exp = fix_multi_choice(key, exp, q)

    # --- 修复3: 添加知识库链接 ---
    kb_title = needs_kb_link(exp, question)
    if kb_title:
        exp = add_kb_link(exp, kb_title)

    # --- 修复4: 修剪过长解析 ---
    exp = trim_long_exp(exp)

    if exp != original:
        exps[key] = exp
        changes += 1

# ═══════════════════════════════════════════════════════════════
# 保存结果
# ═══════════════════════════════════════════════════════════════
with open('explanations.json', 'w', encoding='utf-8') as f:
    json.dump(exps, f, ensure_ascii=False, indent=2)

print(f'修复完成: {changes} 题解析已更新')

# 验证
short = sum(1 for e in exps.values() if len(e) < 30)
medium = sum(1 for e in exps.values() if 30 <= len(e) < 80)
detailed = sum(1 for e in exps.values() if len(e) >= 80)
print(f'短解析(<30字): {short}')
print(f'中等(30-80字): {medium}')
print(f'详细(>80字): {detailed}')
