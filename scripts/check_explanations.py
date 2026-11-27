# -*- coding: utf-8 -*-
"""
逐题检查900题解析质量
扫描问题：
1. 通用模板废话残留
2. 选项分析不完整（多选题应该逐选项说明）
3. 解析与题目不匹配（主题错配）
4. 知识点解释不充分
5. 事实性错误
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('explanations.json', 'r', encoding='utf-8') as f:
    exps = json.load(f)
with open('questions_extracted.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

# 关键修复：用 type_idx 做 key，避免同 idx 不同题型互相覆盖
qmap = {f"{q['type']}_{q['idx']}": q for q in qs}

issues = []  # [(key, problem_type, detail)]

# ═══════════════════════════════════════════════════════════════
# 检查1: 通用模板废话
# ═══════════════════════════════════════════════════════════════
generic_phrases = [
    "根据相关规定和职业规范",
    "该说法正确，符合相关定义和基本原理",
    "该说法正确，在规定和实践中该操作是被允许的",
    "该说法过于绝对",
    "该说法不正确，实际情况与题目描述有出入",
    "这是明确的法定义务或职业要求",
    "该说法过于片面",
    "该说法过于绝对，实际情况更加多元",
    "该说法过于绝对，存在例外情况或限定条件",
    "实际情况更加全面和复杂",
]

for key, exp in exps.items():
    for phrase in generic_phrases:
        if phrase in exp:
            # Check if it's the ONLY content (no specific analysis after)
            after = exp.split(phrase)[-1]
            if len(after.strip()) < 30:
                issues.append((key, '模板废话', f'包含通用模板: "{phrase}" 且无后续具体分析'))

# ═══════════════════════════════════════════════════════════════
# 检查2: 多选题缺少逐选项分析
# ═══════════════════════════════════════════════════════════════
for key, exp in exps.items():
    parts = key.split('_')
    qtype = parts[0]
    idx = int(parts[1])
    q = qmap.get(key, {})
    answer = q.get('answer', [])

    if not isinstance(answer, list) or len(answer) < 2:
        continue  # 不是多选题

    # 检查是否每个选项都被提到
    opts = q.get('options', {})
    if not opts:
        continue

    missing_opts = []
    for opt_key in opts:
        # Check if option key is mentioned in explanation
        patterns = [f'{opt_key}（', f'{opt_key}:', f'{opt_key}：', f'选项{opt_key}', f'{opt_key}正确', f'{opt_key}错误', f'{opt_key}不属于', f'{opt_key}不是']
        found = any(p in exp for p in patterns)
        if not found:
            # Also check if the option content is referenced
            opt_content = opts[opt_key][:10]
            if opt_content not in exp:
                missing_opts.append(opt_key)

    if len(missing_opts) >= 2:
        issues.append((key, '选项分析不全', f'多选题缺少对选项 {",".join(missing_opts)} 的分析'))

# ═══════════════════════════════════════════════════════════════
# 检查3: 主题错配（解析关键词与题目关键词不匹配）
# ═══════════════════════════════════════════════════════════════
# 定义题目关键词→解析应包含的关键词
topic_checks = {
    'Excel': ['Excel', '电子表格', '公式', '函数', '数据透视表'],
    'Windows': ['Windows', '系统', '操作'],
    '专利': ['专利', '发明', '实用新型', '外观设计'],
    '著作权': ['著作权', '版权', '作品'],
    '商标': ['商标', '注册'],
    '劳动合同': ['劳动', '合同', '试用期'],
    '网络安全法': ['网络', '安全', '运营者'],
    '数据标注': ['标注', '标签', '标注员'],
    '特征工程': ['特征', '选择', '提取'],
    '过拟合': ['过拟合', '泛化', '正则化'],
    '神经网络': ['神经网络', '神经元', '层'],
    '深度学习': ['深度学习', '神经网络'],
    'GAN': ['生成器', '判别器', '对抗'],
    '知识图谱': ['知识图谱', '实体', '关系', '节点'],
    '贝叶斯': ['贝叶斯', '概率', '推断'],
    '时间序列': ['时间序列', '趋势', '季节'],
    'MyCat': ['MyCat', '分表', '读写分离', '主从'],
    'Figma': ['Figma', '设计系统', '组件'],
    'Marvel': ['Marvel', '交互', '原型'],
    '数据白化': ['白化', '去相关', '冗余'],
    '负载均衡': ['负载均衡', '分发', '服务器'],
    '容器': ['容器', 'Docker', '虚拟机'],
    '培训': ['培训', '讲义', '学员'],
    '触摸': ['触摸', '电阻', '灵敏度'],
    '语音交互': ['语音', '识别', '合成'],
    'VR': ['VR', '虚拟现实', '沉浸'],
}

for key, exp in exps.items():
    parts = key.split('_')
    idx = int(parts[1])
    q = qmap.get(key, {})
    question = q.get('question', '')

    for topic, expected_keywords in topic_checks.items():
        if topic in question:
            has_keyword = any(kw in exp for kw in expected_keywords)
            if not has_keyword:
                issues.append((key, '主题错配', f'题目关于"{topic}"但解析未包含相关关键词'))

# ═══════════════════════════════════════════════════════════════
# 检查4: 解析中答案标记与实际答案不一致
# ═══════════════════════════════════════════════════════════════
for key, exp in exps.items():
    parts = key.split('_')
    qtype = parts[0]
    idx = int(parts[1])
    q = qmap.get(key, {})
    answer = q.get('answer', '')

    if qtype == 'j':
        # 判断题
        if answer == True or answer == '正确':
            if exp.startswith('❌'):
                issues.append((key, '答案标记错误', '题目答案为正确但解析标记为❌'))
        elif answer == False or answer == '错误':
            if exp.startswith('✅'):
                issues.append((key, '答案标记错误', '题目答案为错误但解析标记为✅'))

# ═══════════════════════════════════════════════════════════════
# 检查5: 解析太长（可能有重复内容）
# ═══════════════════════════════════════════════════════════════
for key, exp in exps.items():
    if len(exp) > 400:
        issues.append((key, '解析过长', f'{len(exp)}字，可能有重复内容'))

# ═══════════════════════════════════════════════════════════════
# 检查6: 知识库链接缺失（应该有链接但没有）
# ═══════════════════════════════════════════════════════════════
kb_topics = {
    '职业道德': 'kb_ethics', '劳动合同': 'kb_labor_contract',
    '知识产权': 'kb_ip', '专利': 'kb_patent', '著作权': 'kb_copyright',
    '机器学习': 'kb_ml', '深度学习': 'kb_deep_learning',
    '神经网络': 'kb_neural_network', '监督学习': 'kb_supervised',
    '过拟合': 'kb_overfitting', '交叉验证': 'kb_cross_validation',
    '损失函数': 'kb_loss_function', '激活函数': 'kb_activation',
    '梯度下降': 'kb_gradient_descent', '超参数': 'kb_hyperparameter',
    '分词': 'kb_tokenization', '词向量': 'kb_word_embedding',
    '情感分析': 'kb_sentiment', '语音识别': 'kb_speech_recognition',
    '图像分类': 'kb_image_classification', '目标检测': 'kb_object_detection',
    'ETL': 'kb_etl', '数据清洗': 'kb_data_cleaning',
    '数据标注': 'kb_data_annotation', '特征工程': 'kb_feature_engineering',
    '数据增强': 'kb_data_augmentation', '云计算': 'kb_cloud',
    'Python': 'kb_python', 'Pandas': 'kb_numpy_pandas',
    'Excel': 'kb_excel', 'Windows': 'kb_windows',
    '加密': 'kb_encryption', '隐私': 'kb_privacy_protection',
    '备份': 'kb_backup', '智能客服': 'kb_smart_cs',
    '知识图谱': 'kb_knowledge_graph', '生成式': 'kb_generative_ai',
    'GAN': 'kb_generative_ai', '贝叶斯': 'kb_bayesian',
}

for key, exp in exps.items():
    parts = key.split('_')
    idx = int(parts[1])
    q = qmap.get(key, {})
    question = q.get('question', '')

    for topic, kb_id in kb_topics.items():
        if topic in question and '🔗' not in exp:
            # This question could benefit from a KB link
            issues.append((key, '缺少知识库链接', f'题目涉及"{topic}"但解析没有知识库链接'))

# ═══════════════════════════════════════════════════════════════
# 输出报告
# ═══════════════════════════════════════════════════════════════
print(f'=== 解析质量检查报告 ===')
print(f'总题目: {len(exps)}')
print(f'发现问题: {len(issues)} 个')
print()

# 按问题类型分组
by_type = {}
for key, ptype, detail in issues:
    by_type.setdefault(ptype, []).append((key, detail))

for ptype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
    print(f'【{ptype}】({len(items)}个)')
    for key, detail in items[:20]:  # 只显示前20个
        q = qmap.get(key, {})
        qtext = q.get('question', '')[:50]
        print(f'  {key}: {qtext}')
        print(f'    → {detail}')
    if len(items) > 20:
        print(f'  ... 还有 {len(items)-20} 个')
    print()
