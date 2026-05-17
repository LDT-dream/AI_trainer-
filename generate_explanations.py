# -*- coding: utf-8 -*-
"""
批量生成题库解析
读取 questions_extracted.json，为每道题生成解析，
输出 explanations.json 供合并回 HTML。
"""
import json
import re

with open("questions_extracted.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# 分类关键词映射，用于生成更有针对性的解析
CATEGORY_RULES = {
    "职业道德": "职业道德是从业人员在职业活动中应遵循的行为准则，强调诚信、责任、保密和专业性。",
    "隐私": "根据《个人信息保护法》，处理个人信息应遵循合法、正当、必要原则，需经用户知情同意。",
    "数据安全": "数据安全要求采取技术措施防止数据泄露、损毁、丢失，是网络运营者的基本义务。",
    "知识产权": "知识产权包括专利权、著作权、商标权等，受《专利法》《著作权法》等法律保护。",
    "劳动合同": "根据《劳动合同法》，劳动合同应包含合同期限、工作内容、劳动报酬等必备条款。",
    "专利": "专利需具备新颖性、创造性和实用性，由国家知识产权局审查授权。",
    "著作权": "著作权自作品创作完成之日起自动产生，无需登记，但登记有助于维权。",
    "网络安全": "《网络安全法》要求网络运营者采取技术措施保障网络安全，防止网络攻击和数据泄露。",
    "人工智能": "人工智能技术包括机器学习、深度学习、自然语言处理等，需遵循伦理规范和法律法规。",
    "机器学习": "机器学习是AI的核心技术，通过数据训练模型，使计算机具备预测和决策能力。",
    "深度学习": "深度学习是机器学习的子领域，使用多层神经网络处理复杂数据模式。",
    "自然语言处理": "NLP是AI的重要分支，使计算机能够理解、生成和处理人类语言。",
    "计算机视觉": "计算机视觉使机器能够从图像和视频中提取信息，广泛应用于人脸识别、自动驾驶等。",
    "数据标注": "数据标注是AI训练的基础工作，为模型提供有标签的训练数据。",
    "模型训练": "模型训练是通过数据迭代优化模型参数的过程，需关注过拟合和欠拟合问题。",
    "Excel": "Excel是常用的数据处理工具，支持公式计算、数据透视表、图表可视化等功能。",
    "Word": "Word是文字处理软件，支持样式设置、图文混排、目录生成等功能。",
    "Windows": "Windows是微软开发的操作系统，支持文件管理、系统设置、网络配置等功能。",
    "浏览器": "浏览器是访问互联网的工具，支持网页浏览、书签管理、隐私设置等功能。",
    "搜索引擎": "搜索引擎通过爬虫和索引技术帮助用户查找互联网信息。",
    "Office": "Microsoft Office包括Word、Excel、PowerPoint等办公软件。",
    "云计算": "云计算提供按需计算资源，包括IaaS、PaaS、SaaS三种服务模式。",
    "大数据": "大数据具有Volume、Velocity、Variety、Value四个特征，需要专门的处理技术。",
    "物联网": "物联网通过传感器和网络连接物理设备，实现智能化管理和控制。",
    "区块链": "区块链是分布式账本技术，具有去中心化、不可篡改、可追溯等特点。",
    "5G": "5G是第五代移动通信技术，具有高速率、低延迟、大连接的特点。",
    "算法": "算法是解决问题的步骤和方法，需关注时间复杂度和空间复杂度。",
    "数据库": "数据库用于存储和管理数据，常见类型包括关系型和非关系型数据库。",
    "编程": "编程是编写计算机程序的过程，需掌握语法、数据结构和算法。",
    "Python": "Python是通用编程语言，在AI和数据科学领域广泛应用。",
    "分布式": "分布式系统将计算任务分散到多台机器上，提高处理能力和可靠性。",
    "负载均衡": "负载均衡将请求分发到多台服务器，提高系统吞吐量和可用性。",
    "缓存": "缓存将常用数据存储在快速访问的存储介质中，减少数据库查询压力。",
    "微服务": "微服务架构将应用拆分为独立的服务单元，提高灵活性和可维护性。",
    "API": "API是应用程序编程接口，定义了不同软件组件之间的交互方式。",
    "测试": "软件测试是验证系统功能和性能的过程，包括单元测试、集成测试、系统测试等。",
    "项目管理": "项目管理包括计划、执行、监控和收尾等阶段，确保项目按时按质完成。",
    "需求分析": "需求分析是理解用户需求并将其转化为技术规格的过程。",
    "用户体验": "用户体验关注产品的易用性、可访问性和用户满意度。",
    "信息安全": "信息安全的目标是保护信息的机密性、完整性和可用性。",
    "评估": "AI模型评估使用准确率、召回率、F1值等指标衡量模型性能。",
    "标注": "数据标注为AI模型提供训练数据，标注质量直接影响模型效果。",
    "清洗": "数据清洗去除噪声、填补缺失值、处理异常值，是数据预处理的重要步骤。",
    "特征": "特征工程通过选择和转换数据特征来提高模型性能。",
    "过拟合": "过拟合指模型在训练数据上表现好但在新数据上泛化能力差，可通过正则化、交叉验证等方法缓解。",
    "正则化": "正则化通过添加惩罚项限制模型复杂度，防止过拟合。",
    "交叉验证": "交叉验证将数据分为多个折，轮流作为训练集和验证集，评估模型泛化能力。",
    "梯度下降": "梯度下降是优化算法，通过迭代调整参数最小化损失函数。",
    "损失函数": "损失函数衡量模型预测值与真实值的差异，是模型优化的目标。",
    "激活函数": "激活函数为神经网络引入非线性，常见有ReLU、Sigmoid、Tanh等。",
    "卷积": "卷积神经网络(CNN)通过卷积核提取图像特征，广泛应用于计算机视觉。",
    "循环": "循环神经网络(RNN)处理序列数据，适用于自然语言处理和时间序列分析。",
    "注意力": "注意力机制使模型关注输入的关键部分，是Transformer架构的核心。",
    "Transformer": "Transformer基于自注意力机制，是现代大语言模型的基础架构。",
    "预训练": "预训练在大规模数据上训练通用模型，再通过微调适应特定任务。",
    "微调": "微调在预训练模型基础上用特定任务数据进一步训练，提高任务表现。",
    "迁移学习": "迁移学习将在一个任务上学到的知识应用到相关任务，减少数据和计算需求。",
    "强化学习": "强化学习通过与环境交互获取奖励信号来学习最优策略。",
    "生成式": "生成式AI可以创建文本、图像、音频等内容，如GPT、DALL-E等。",
    "大语言模型": "大语言模型(LLM)通过大规模预训练学习语言模式，具备文本生成和理解能力。",
    "提示词": "提示词工程通过设计输入提示来引导AI模型生成期望的输出。",
    "RAG": "检索增强生成(RAG)结合外部知识库和语言模型，提高回答的准确性和时效性。",
    "智能体": "AI Agent能够自主感知环境、做出决策并执行行动，是AI应用的高级形态。",
    "多模态": "多模态AI能够处理文本、图像、音频等多种类型的数据。",
    "伦理": "AI伦理关注公平性、透明度、隐私保护和责任归属等问题。",
    "偏见": "AI偏见可能来自训练数据或算法设计，需要通过数据平衡和算法审计来缓解。",
    "可解释性": "AI可解释性帮助理解模型决策过程，增强用户信任和满足监管要求。",
    "监管": "AI监管框架要求算法备案、影响评估和安全审查，确保AI安全可控。",
    "合规": "AI合规要求遵循数据保护、算法透明和安全评估等法规要求。",
}

def categorize_question(question_text):
    """根据题目内容匹配分类"""
    for keyword, explanation in CATEGORY_RULES.items():
        if keyword in question_text:
            return explanation
    return ""

def generate_j_explain(question, answer):
    """生成判断题解析"""
    category_hint = categorize_question(question)
    if answer:
        base = "本题正确。"
    else:
        base = "本题错误。"

    # 根据题目内容生成更具体的解析
    if "可以不" in question or "不需要" in question or "无需" in question or "不必" in question:
        if not answer:
            return base + "根据相关规定和职业规范，该项要求是必须遵守的，不可以省略或忽略。" + (" " + category_hint if category_hint else "")
    if "必须" in question or "应当" in question or "应该" in question:
        if answer:
            return base + "这是明确的法定义务或职业要求，必须严格遵守。" + (" " + category_hint if category_hint else "")
    if "仅" in question or "只是" in question or "只有" in question:
        if not answer:
            return base + "该说法过于绝对，实际情况更加复杂和多元。" + (" " + category_hint if category_hint else "")
    if "所有" in question or "任何" in question or "一切" in question:
        if not answer:
            return base + "该说法过于绝对，存在例外情况或限定条件。" + (" " + category_hint if category_hint else "")
    if "可以" in question or "能够" in question or "允许" in question:
        if answer:
            return base + "该操作在规定和实践中是被允许的。" + (" " + category_hint if category_hint else "")
        else:
            return base + "该操作在规定中是不被允许或有限制条件的。" + (" " + category_hint if category_hint else "")
    if "不能" in question or "不可以" in question or "禁止" in question:
        if answer:
            return base + "该行为确实被明确禁止。" + (" " + category_hint if category_hint else "")

    if category_hint:
        return base + category_hint
    return base + "请结合相关法规和职业规范理解本题考查的知识点。"

def generate_s_explain(question, options, answer):
    """生成单选题解析"""
    category_hint = categorize_question(question)
    correct_text = options.get(answer, "")
    explain = f"正确答案是{answer}（{correct_text}）。"

    # 生成干扰项分析
    wrong_opts = [k for k in options.keys() if k != answer]
    if wrong_opts:
        explain += f" 其他选项{'、'.join(wrong_opts)}不符合题意要求。"

    if category_hint:
        explain += " " + category_hint
    return explain

def generate_m_explain(question, options, answer):
    """生成多选题解析"""
    category_hint = categorize_question(question)
    if isinstance(answer, list):
        correct_labels = [f"{a}（{options.get(a, '')}）" for a in answer]
        explain = f"正确答案是{'、'.join(correct_labels)}。"
    else:
        explain = f"正确答案是{answer}。"

    if category_hint:
        explain += " " + category_hint
    return explain

# 生成所有解析
explanations = {}
stats = {'j': 0, 's': 0, 'm': 0}

for q in questions:
    qtype = q['type']
    idx = q['idx']
    key = f"{qtype}_{idx}"

    if qtype == 'j':
        exp = generate_j_explain(q['question'], q['answer'])
    elif qtype == 's':
        exp = generate_s_explain(q['question'], q.get('options', {}), q['answer'])
    elif qtype == 'm':
        exp = generate_m_explain(q['question'], q.get('options', {}), q['answer'])
    else:
        exp = ""

    explanations[key] = exp
    stats[qtype] = stats.get(qtype, 0) + 1

print(f"Generated explanations:")
print(f"  判断题: {stats['j']}")
print(f"  单选题: {stats['s']}")
print(f"  多选题: {stats['m']}")
print(f"  总计: {sum(stats.values())}")

with open("explanations.json", "w", encoding="utf-8") as f:
    json.dump(explanations, f, ensure_ascii=False, indent=2)

print("Saved to explanations.json")
