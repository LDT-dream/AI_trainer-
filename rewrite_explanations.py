# -*- coding: utf-8 -*-
"""
重写 900 题解析 — 生成详细、自包含、易懂的解析
读取 questions_extracted.json + knowledge_base.json，输出 explanations.json
"""
import json, re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open("questions_extracted.json", "r", encoding="utf-8") as f:
    questions = json.load(f)
with open("knowledge_base.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

# ═══════════════════════════════════════════════════════════════
# 知识库关键词 → KB ID 映射
# ═══════════════════════════════════════════════════════════════
KB_MAP = {
    "道德": "kb_moral_eval", "职业道德": "kb_ethics", "诚信": "kb_ethics",
    "劳动合同": "kb_labor_contract", "试用期": "kb_labor_contract",
    "知识产权": "kb_ip", "专利": "kb_patent", "商标": "kb_ip",
    "著作权": "kb_copyright", "版权": "kb_copyright",
    "网络安全法": "kb_cybersecurity_law", "个人信息保护": "kb_privacy_law",
    "机器学习": "kb_ml", "监督学习": "kb_supervised", "无监督学习": "kb_unsupervised",
    "强化学习": "kb_reinforcement", "迁移学习": "kb_transfer_learning",
    "集成学习": "kb_ensemble", "深度学习": "kb_deep_learning",
    "神经网络": "kb_neural_network", "卷积": "kb_image_classification",
    "过拟合": "kb_overfitting", "欠拟合": "kb_overfitting",
    "交叉验证": "kb_cross_validation", "损失函数": "kb_loss_function",
    "激活函数": "kb_activation", "梯度下降": "kb_gradient_descent",
    "超参数": "kb_hyperparameter", "正则化": "kb_overfitting",
    "Dropout": "kb_overfitting", "学习率": "kb_gradient_descent",
    "分词": "kb_tokenization", "词向量": "kb_word_embedding",
    "Transformer": "kb_transformer", "BERT": "kb_bert", "注意力": "kb_transformer",
    "情感分析": "kb_sentiment", "语音识别": "kb_speech_recognition",
    "图像分类": "kb_image_classification", "目标检测": "kb_object_detection",
    "图像分割": "kb_image_segmentation", "人脸识别": "kb_face_recognition",
    "ETL": "kb_etl", "数据清洗": "kb_data_cleaning", "数据标注": "kb_data_annotation",
    "标注": "kb_data_annotation", "特征工程": "kb_feature_engineering",
    "数据增强": "kb_data_augmentation", "数据探索": "kb_data_exploration",
    "分布式": "kb_distributed", "Hadoop": "kb_hadoop_spark", "Spark": "kb_hadoop_spark",
    "SQL": "kb_sql", "数据库": "kb_sql", "云计算": "kb_cloud", "云服务": "kb_cloud",
    "Python": "kb_python", "NumPy": "kb_numpy_pandas", "Pandas": "kb_numpy_pandas",
    "数据结构": "kb_data_structures", "算法": "kb_algorithms",
    "Excel": "kb_excel", "Word": "kb_word", "Windows": "kb_windows", "浏览器": "kb_browser",
    "加密": "kb_encryption", "访问控制": "kb_access_control",
    "隐私": "kb_privacy_protection", "备份": "kb_backup",
    "人机交互": "kb_hci", "界面设计": "kb_ui_design", "反馈": "kb_feedback",
    "智能客服": "kb_smart_cs", "自动驾驶": "kb_autonomous_driving",
    "知识图谱": "kb_knowledge_graph", "生成式": "kb_generative_ai",
    "大语言模型": "kb_generative_ai", "GPT": "kb_generative_ai",
}

def find_kb_ref(question_text):
    """找到最相关的知识库条目"""
    best_ref = None
    best_len = 0
    for keyword, kb_id in KB_MAP.items():
        if keyword in question_text and len(keyword) > best_len:
            best_ref = kb_id
            best_len = len(keyword)
    return best_ref

def get_kb_link(kb_id):
    """生成知识库链接标记"""
    if kb_id and kb_id in kb:
        title = kb[kb_id]['title']
        return f" [🔗 {title}]"
    return ""

# ═══════════════════════════════════════════════════════════════
# 判断题解析生成
# ═══════════════════════════════════════════════════════════════
def gen_j(q):
    text = q['question']
    ans = q['answer']
    kb_ref = find_kb_ref(text)
    kb_link = get_kb_link(kb_ref)

    prefix = "✅ 正确" if ans else "❌ 错误"

    # 提取考查点
    topic = extract_topic(text)
    topic_str = f"本题考查「{topic}」。" if topic else ""

    # 生成核心解释
    explanation = generate_core_explain(text, ans, 'j')

    return f"{prefix}。{topic_str}{explanation}{kb_link}"

# ═══════════════════════════════════════════════════════════════
# 单选题解析生成
# ═══════════════════════════════════════════════════════════════
def gen_s(q):
    text = q['question']
    opts = q.get('options', {})
    ans = q['answer']
    kb_ref = find_kb_ref(text)
    kb_link = get_kb_link(kb_ref)

    topic = extract_topic(text)
    topic_str = f"本题考查「{topic}」。" if topic else ""

    correct_text = opts.get(ans, "")
    explain = f"正确答案是{ans}（{correct_text}）。"

    # 解释为什么这个选项对
    core = generate_core_explain(text, True, 's', ans, opts)
    if core:
        explain += core
    else:
        # Fallback: 用选项内容生成有意义的解释
        explain += generate_s_fallback(text, opts, ans)

    # 解释干扰项
    wrong_opts = [k for k in opts.keys() if k != ans]
    if wrong_opts and len(opts) <= 5:
        wrong_analysis = analyze_wrong_opts(text, opts, ans, wrong_opts)
        if wrong_analysis:
            explain += wrong_analysis

    return f"{topic_str}{explain}{kb_link}"

# ═══════════════════════════════════════════════════════════════
# 多选题解析生成
# ═══════════════════════════════════════════════════════════════
def gen_m(q):
    text = q['question']
    opts = q.get('options', {})
    ans = q['answer']  # list of letters
    kb_ref = find_kb_ref(text)
    kb_link = get_kb_link(kb_ref)

    topic = extract_topic(text)
    topic_str = f"本题考查「{topic}」。" if topic else ""

    if isinstance(ans, list):
        correct_labels = [f"{a}（{opts.get(a, '')}）" for a in ans]
        explain = f"正确答案是{'、'.join(correct_labels)}。"
    else:
        explain = f"正确答案是{ans}。"

    # 逐选项分析
    explain += analyze_all_opts_m(text, opts, ans)

    return f"{topic_str}{explain}{kb_link}"

# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════
def extract_topic(text):
    """从题目中提取考查知识点"""
    # 尝试匹配引号中的内容
    m = re.search(r'[「【](.+?)[」】]', text)
    if m:
        return m.group(1)

    # 尝试匹配"关于XXX"的模式
    m = re.search(r'关于(.{2,10})[，,的]', text)
    if m:
        return m.group(1)

    return ""

def generate_core_explain(text, ans, qtype, correct_ans=None, opts=None):
    """根据题目内容生成核心解释"""

    # ── 职业道德类 ──
    if "职业道德" in text and "核心" in text:
        return "职业道德的核心是爱岗敬业、诚实守信、办事公道、服务群众、奉献社会。其中爱岗敬业是基础，诚实守信是根本。"
    if "职业道德" in text and ("概念" in text or "定义" in text or "含义" in text):
        return "职业道德是从事一定职业的人在职业活动中应当遵循的行为规范，是职业品德、职业纪律、专业胜任能力及职业责任等的总称。"
    if "道德评价" in text:
        return "道德评价是依据一定的道德标准，对自己或他人的行为进行善恶、正邪判断的活动。其关键标准是行为是否符合社会公认的道德规范。"
    if "保密" in text and ("原则" in text or "要求" in text or "必须" in text):
        return "保密是职业道德的重要要求。从业者必须对工作中接触到的商业秘密、客户信息等严格保密，不得泄露给无关人员。"
    if "爱岗敬业" in text:
        return "爱岗敬业是职业道德的基础，要求从业者热爱本职工作、忠于职守、尽职尽责。它是一切职业道德规范的前提。"
    if "诚实守信" in text:
        return "诚实守信是做人的基本准则，也是职业道德的根本。要求从业者言行一致、不欺诈、不弄虚作假。"
    if "奉献社会" in text:
        return "奉献社会是职业道德的最高要求，要求从业者在完成本职工作的同时，为社会做出贡献。"
    if "服务群众" in text:
        return "服务群众是职业道德的核心之一，要求从业者树立服务意识，全心全意为人民服务。"
    if "办事公道" in text:
        return "办事公道要求从业者处理事务公平公正、不偏不倚、一视同仁。"

    # ── 法律法规类 ──
    if "劳动合同" in text:
        if "试用期" in text:
            return "根据《劳动合同法》，试用期长度与合同期限挂钩：合同期限3个月以上不满1年的，试用期不超过1个月；1年以上不满3年的，不超过2个月；3年以上及无固定期限的，不超过6个月。同一用人单位与同一劳动者只能约定一次试用期。"
        if "必备条款" in text or "应当具备" in text:
            return "劳动合同的必备条款包括：用人单位和劳动者基本信息、合同期限、工作内容和地点、工作时间和休假、劳动报酬、社会保险、劳动保护和劳动条件。缺少必备条款不影响合同效力，但可能引发争议。"
        if "解除" in text or "终止" in text:
            return "劳动合同的解除分为协商解除、劳动者单方解除和用人单位单方解除。劳动者提前30日书面通知可解除合同，试用期内提前3日通知即可。用人单位解除需符合法定条件。"
        return "《劳动合同法》保护劳动者合法权益，规范劳动关系。签订劳动合同是用人单位的法定义务，自用工之日起一个月内必须签订书面劳动合同。"

    if "知识产权" in text:
        return "知识产权是智力成果的专有权利，包括专利权、著作权、商标权等。保护知识产权鼓励创新，是市场经济的重要制度。"

    if "专利" in text:
        if "新颖性" in text:
            return "新颖性是获得专利授权的核心条件之一，要求发明不属于现有技术，也没有任何单位或个人就同样的发明在申请日以前向国务院专利行政部门提出过申请。"
        if "发明" in text and "实用新型" in text:
            return "发明专利保护期20年，保护产品、方法或改进；实用新型专利保护期10年，只保护产品形状、构造；外观设计专利保护期15年，保护产品外观。"
        return "专利需具备新颖性、创造性和实用性。发明专利保护期20年，实用新型和外观设计分别为10年和15年。"

    if "著作权" in text or "版权" in text:
        if "自动" in text or "创作完成" in text or "不需要" in text:
            return "著作权自作品创作完成之日起自动产生，无需登记或申请。但登记有助于在纠纷中举证维权。保护期一般为作者终生加死后50年。"
        return "著作权保护文学、艺术和科学作品的表达形式。著作权自创作完成自动产生，保护期一般为作者终生加死后50年。"

    if "商标" in text:
        return "商标权需要通过注册获得，保护商品或服务的标识。注册商标有效期10年，期满可续展。商标注册遵循先申请原则。"

    if "网络安全法" in text:
        return "《网络安全法》要求网络运营者采取技术措施保障网络安全，防止网络攻击、数据泄露。违反者可被处以罚款，情节严重的可追究刑事责任。"

    if "个人信息" in text and ("保护" in text or "法" in text):
        return "《个人信息保护法》要求处理个人信息需遵循合法、正当、必要原则，经用户知情同意。敏感个人信息（如人脸、指纹）需单独同意。"

    if "隐私" in text:
        return "隐私保护要求不得非法收集、使用、加工、传输他人个人信息，不得非法买卖、提供或公开他人个人信息。"

    # ── AI/机器学习类 ──
    if "监督学习" in text:
        return "监督学习使用有标签的数据训练模型，学习从输入到输出的映射。分为分类（预测类别）和回归（预测数值）两类。常见算法有线性回归、决策树、SVM、神经网络等。"

    if "无监督学习" in text:
        return "无监督学习在没有标签的数据中发现隐藏的模式和结构。主要方法有聚类（K-Means）、降维（PCA）、关联规则挖掘等。"

    if "强化学习" in text:
        return "强化学习通过智能体与环境交互获取奖励信号来学习最优策略。核心概念包括状态、动作、奖励、策略。AlphaGo就是强化学习的典型应用。"

    if "迁移学习" in text:
        return "迁移学习将在一个任务上学到的知识应用到相关任务，减少数据和计算需求。典型做法是用预训练模型（如BERT、ResNet）在小数据集上微调。"

    if "集成学习" in text:
        return "集成学习组合多个弱模型得到强模型。Bagging（如随机森林）并行训练后投票；Boosting（如XGBoost）串行训练，每个新模型修正前一个的错误。"

    if "深度学习" in text:
        return "深度学习使用多层神经网络处理复杂数据，能自动学习特征。2012年AlexNet的突破后席卷AI各领域。需要大量数据和GPU算力。"

    if "神经网络" in text:
        return "神经网络模仿人脑结构，由输入层、隐藏层、输出层组成。每个神经元接收输入、加权求和、通过激活函数输出。训练通过反向传播调整权重。"

    if "过拟合" in text:
        if ans == False or (qtype == 's' and correct_ans):
            return "过拟合是模型在训练集上表现好但泛化能力差。解决方法：增加数据量、正则化、Dropout、早停、数据增强。"
        return "过拟合指模型过度学习了训练数据的噪声和细节，导致在新数据上表现差。模型过于复杂、训练数据不足都可能导致过拟合。"

    if "欠拟合" in text:
        return "欠拟合是模型太简单，连训练数据的规律都没学到。解决方法：增加模型复杂度、减少正则化、增加训练时间、做更好的特征工程。"

    if "交叉验证" in text:
        return "交叉验证是评估模型泛化能力的方法。K折交叉验证把数据分成K份，轮流用1份验证、K-1份训练，取K次结果的平均值，评估更可靠。"

    if "损失函数" in text:
        return "损失函数衡量模型预测值和真实值的差距。回归用均方误差（MSE），分类用交叉熵。训练目标就是最小化损失函数。"

    if "激活函数" in text:
        return "激活函数为神经网络引入非线性，没有它网络等价于线性模型。常用：隐藏层用ReLU，二分类输出层用Sigmoid，多分类输出层用Softmax。"

    if "梯度下降" in text:
        return "梯度下降是优化算法，沿损失函数梯度的反方向更新参数，逐步逼近最小值。学习率决定步长大小，太大会跳过最优解，太小收敛慢。"

    if "超参数" in text:
        return "超参数是训练前人为设定的参数（学习率、批量大小、网络层数等），和模型训练中自动学习的权重不同。调优方法有网格搜索、随机搜索、贝叶斯搜索。"

    if "特征" in text and ("选择" in text or "提取" in text or "工程" in text):
        return "特征工程从原始数据中提取有用特征。方法包括标准化、归一化、独热编码、TF-IDF等。在传统ML中，特征工程往往比模型选择更重要。"

    if "数据增强" in text:
        return "数据增强通过对现有数据做变换来生成更多训练数据。图像增强有翻转、旋转、裁剪等；文本增强有同义词替换、回译等。可减少过拟合。"

    # ── NLP类 ──
    if "分词" in text:
        return "分词是NLP的基础步骤，将连续文本切分为词语。中文分词比英文难（无空格分隔），常用工具有jieba、HanLP。现代大模型用子词分词（BPE）。"

    if "词向量" in text or "词嵌入" in text:
        return "词向量将词语映射为数字向量，语义相近的词向量也相近。经典方法有Word2Vec、GloVe、FastText。维度通常100-300维。"

    if "Transformer" in text:
        return "Transformer基于自注意力机制，能同时关注句子中所有词的关系。比RNN可并行、能捕捉长距离依赖。BERT用编码器，GPT用解码器。"

    if "BERT" in text:
        return "BERT是双向预训练语言模型，同时看一个词的左右上下文。通过遮盖语言模型（MLM）和下一句预测（NSP）预训练，再微调用于下游任务。"

    if "情感分析" in text:
        return "情感分析判断文本的情感倾向（正面/负面/中性）。方法从词典匹配到深度学习（LSTM、BERT）。难点：反讽、否定句、隐含情感。"

    if "语音识别" in text:
        return "语音识别（ASR）将语音转为文字。流程：语音→特征提取→声学模型→语言模型→文字。现代方法用端到端深度学习，如Whisper。"

    # ── 计算机视觉类 ──
    if "卷积" in text and ("神经网络" in text or "CNN" in text):
        return "卷积神经网络（CNN）用卷积核提取图像特征。结构：卷积层（特征提取）→池化层（降维）→全连接层（分类）。经典模型：AlexNet、VGG、ResNet。"

    if "图像分类" in text:
        return "图像分类判断图片属于哪个类别。核心技术是CNN，通过卷积层提取边缘、纹理等特征，逐层组合成高级特征，最终做出分类决策。"

    if "目标检测" in text:
        return "目标检测识别图片中有什么并定位在哪。两阶段方法（R-CNN系列）先找候选区域再分类；一阶段方法（YOLO、SSD）直接预测，速度更快。"

    if "图像分割" in text:
        return "图像分割对每个像素分类。语义分割标类别不区分实例；实例分割区分不同实例（Mask R-CNN）；全景分割结合两者。"

    if "人脸识别" in text:
        return "人脸识别流程：人脸检测→对齐→特征提取→比对。技术已很成熟（准确率>99%），但存在隐私和偏见争议。"

    # ── 数据处理类 ──
    if "ETL" in text:
        return "ETL是数据仓库的核心流程：Extract（从数据源抽取数据）→Transform（清洗、标准化、聚合）→Load（加载到目标系统）。数据质量直接决定模型效果。"

    if "数据清洗" in text:
        return "数据清洗处理脏数据：缺失值（填充/删除）、异常值（截断/删除）、重复值（去重）、格式不一致（统一）。通常占数据分析工作量的60-80%。"

    if "数据标注" in text or "标注" in text:
        return "数据标注为原始数据添加标签，是监督学习的基础。流程：制定规范→培训标注员→试标注→正式标注→质量审核。标注质量直接影响模型效果。"

    if "数据采集" in text or "数据收集" in text:
        return "数据采集是从各种来源获取数据的过程。方式包括：数据库查询、API调用、网络爬虫、传感器采集、日志收集等。需注意数据来源的合法性。"

    if "数据探索" in text or "EDA" in text:
        return "数据探索（EDA）是建模前了解数据的过程。包括基本统计（均值/中位数/标准差）、分布分析、相关性分析、可视化。常用Pandas和Seaborn。"

    if "数据质量" in text or "数据的质" in text:
        return "数据质量是AI项目成败的关键。评估维度：完整性（是否有缺失）、准确性（是否正确）、一致性（格式是否统一）、时效性（是否过期）。垃圾数据进→垃圾模型出。"

    if "数据治理" in text:
        return "数据治理是管理数据可用性、完整性和安全性的过程。包括数据标准制定、数据质量管理、数据安全管理、元数据管理等。"

    if "数据可视化" in text or "可视化" in text:
        return "数据可视化将数据转为图表，直观展示数据特征和规律。常用工具：Matplotlib、Seaborn（Python）、Tableau、Excel图表。图表类型：柱状图、折线图、散点图、热力图等。"

    if "数据仓库" in text:
        return "数据仓库是面向分析的数据存储系统，整合多个数据源的历史数据。特点：面向主题、集成、非易失、随时间变化。与操作型数据库的区别：仓库用于分析，数据库用于事务。"

    if "数据平台" in text:
        return "数据平台是支撑数据采集、存储、处理、分析和应用的基础设施。通常包括数据湖、数据仓库、ETL工具、BI工具等组件。"

    if "数据存储" in text:
        return "数据存储是将数据保存到持久化介质的过程。存储方式：文件系统、关系型数据库、NoSQL数据库、数据湖、对象存储。选择取决于数据类型和访问模式。"

    if "数据安全" in text:
        return "数据安全保护数据不被泄露、篡改、损毁。措施：加密、访问控制、备份、审计日志。法规要求：网络安全法、数据安全法、个人信息保护法。"

    # ── 大数据类 ──
    if "分布式" in text:
        return "分布式计算把大任务分给多台计算机完成。核心挑战：数据一致性（CAP定理）、容错（数据副本）、负载均衡。代表框架：Hadoop、Spark。"

    if "Hadoop" in text:
        return "Hadoop包含HDFS（分布式文件系统）、MapReduce（分布式计算）、YARN（资源管理）。适合大规模批处理，但MapReduce较慢。"

    if "Spark" in text:
        return "Spark是比Hadoop MapReduce快10-100倍的大数据框架，因为使用内存计算。核心概念：RDD、DataFrame、Spark SQL。适合迭代计算和机器学习。"

    if "数据库" in text:
        return "数据库用于存储和管理数据。关系型数据库（MySQL、PostgreSQL）用SQL查询，支持ACID事务；非关系型数据库（MongoDB、Redis）更灵活。"

    if "云计算" in text or "云服务" in text:
        return "云计算按需提供计算资源。IaaS（虚拟机）、PaaS（开发平台）、SaaS（软件服务）。优势：弹性伸缩、无需自建机房、高可用。"

    # ── 办公软件类 ──
    if "Excel" in text:
        if "函数" in text or "公式" in text:
            return "Excel函数是预定义的公式。常用：SUM（求和）、AVERAGE（平均值）、VLOOKUP（查找）、IF（条件判断）、COUNTIF（条件计数）。"
        if "数据透视表" in text:
            return "数据透视表是Excel最强大的功能，能快速对大量数据进行分组、汇总、交叉分析，几秒钟完成手动需要几小时的统计工作。"
        return "Excel是电子表格软件，核心功能包括公式计算、数据透视表、图表可视化、排序筛选等。是数据分析的基础工具。"

    if "Word" in text:
        return "Word是文字处理软件。核心功能：样式（统一格式）、图文混排、目录自动生成、批注与修订（多人协作）。用样式而非手动设置格式是关键技巧。"

    if "Windows" in text:
        return "Windows是微软的操作系统。核心操作：文件管理、系统设置、任务管理器（Ctrl+Shift+Esc）、快捷键（Win+E打开文件管理器、Alt+Tab切换窗口）。"

    if "浏览器" in text:
        return "浏览器是访问互联网的工具。主流：Chrome、Edge、Firefox。核心功能：标签页管理、书签、开发者工具（F12）、隐私设置、扩展程序。"

    if "搜索引擎" in text:
        return "搜索引擎通过爬虫抓取网页、建立索引、根据关键词检索。核心技术：PageRank算法（根据链接数量和质量排序）。百度、Google是主流搜索引擎。"

    # ── 人机交互类 ──
    if "人机交互" in text or "HCI" in text:
        return "人机交互研究人和计算机的交互方式。核心原则：一致性、反馈、容错、简洁、可访问性。交互方式从命令行演进到语音、手势、脑机接口。"

    if "界面" in text and "设计" in text:
        return "界面设计关注视觉呈现和用户体验。要素：布局（信息层次）、色彩（对比度和心理学）、字体（易读性）、间距（留白）。"

    if "用户体验" in text or "UX" in text:
        return "用户体验关注产品是否好用、易用、想用。评估维度：可用性（能不能完成任务）、效率（多快完成）、满意度（用着舒不舒服）。"

    # ── AI应用类 ──
    if "智能客服" in text:
        return "智能客服用AI自动回答用户问题。核心技术：意图识别、实体抽取、对话管理、知识库检索。大语言模型正在革新智能客服的能力。"

    if "自动驾驶" in text:
        return "自动驾驶分级L0-L5。核心技术：感知（摄像头、激光雷达）、定位（GPS+高精地图）、决策（路径规划）、控制（执行）。需要大量标注数据训练感知模型。"

    if "知识图谱" in text:
        return "知识图谱用图结构表示实体和关系。应用：搜索引擎直接展示答案、智能问答、推荐系统。构建：实体识别→关系抽取→知识融合→推理。"

    if "生成式" in text or "AIGC" in text:
        return "生成式AI创造新内容：文本（GPT）、图像（DALL-E、Midjourney）、音频、视频。核心技术：Transformer、扩散模型、GAN。风险：幻觉、版权、深度伪造。"

    # ── 职业守则类 ──
    if "职业守则" in text:
        if not ans:
            if "仅仅" in text or "只是" in text:
                return "职业守则不仅是一种软约束，虽然不具备法律强制力，但在行业中具有重要的规范作用，违反者可能面临行业处分和职业声誉损失。"
            if "不包括" in text:
                return "该说法不正确。职业守则的核心内容通常包括遵纪守法、爱岗敬业、诚实守信、服务群众等方面，遵守法律是基本要求。"
            if "完全" in text or "所有" in text:
                return "该说法过于绝对。职业守则的实施需要个人自觉、行业监管和社会监督共同配合，不能仅靠单一手段。"
            return "该说法不正确。职业守则对从业者有重要的规范和指导作用。"
        else:
            return "该说法正确。职业守则的制定和实施应与时俱进，充分考虑技术发展趋势和潜在风险。"

    if "快捷键" in text or ("Ctrl" in text and "+" in text):
        return "键盘快捷键提高操作效率。常用：Ctrl+C（复制）、Ctrl+V（粘贴）、Ctrl+Z（撤销）、Ctrl+S（保存）、Ctrl+A（全选）。"

    if "扩展名" in text or "文件格式" in text:
        return "文件扩展名标识文件类型。常见：.xlsx（Excel）、.docx（Word）、.pptx（PowerPoint）、.pdf（PDF文档）、.csv（逗号分隔数据）。"

    if "劳动保护" in text or "劳动权益" in text:
        return "劳动者享有法定的劳动保护权益，包括工作安全、健康保障、合理工作时间、休息休假、社会保险等。用人单位必须依法提供。"

    if "信息安全" in text:
        return "信息安全保护信息的机密性（不被未授权访问）、完整性（不被篡改）和可用性（需要时能访问）。措施：加密、访问控制、备份、审计。"

    if "关键信息基础设施" in text:
        return "关键信息基础设施是指面向公众提供服务的重要网络设施和信息系统。运营者需每年至少进行一次安全检测评估，确保网络安全。"

    if "实名制" in text:
        return "网络实名制要求用户使用真实身份注册。目的是维护网络秩序、打击网络犯罪。《网络安全法》规定网络接入服务需实名注册。"

    if "遵纪守法" in text or "遵守法律" in text:
        return "遵纪守法是每个公民和从业者的基本义务。在职业活动中，不仅要遵守国家法律法规，还要遵守行业规范和单位规章制度。"

    # ── 更多关键词模式 ──
    if "网络" in text and ("协议" in text or "TCP" in text or "HTTP" in text or "IP" in text):
        return "网络协议是计算机通信的规则。TCP/IP是互联网基础协议，HTTP是网页传输协议。IP地址标识设备，域名方便记忆。"

    if "带宽" in text or "网速" in text:
        return "带宽是网络传输数据的能力，单位bps（比特每秒）。带宽越大，传输越快。实际网速受带宽、延迟、服务器性能等影响。"

    if "防火墙" in text:
        return "防火墙是网络安全设备，监控和控制网络流量。根据安全规则允许或阻止数据包通过。分为硬件防火墙和软件防火墙。"

    if "物联网" in text or "IoT" in text:
        return "物联网通过传感器和网络连接物理设备，实现智能化管理。应用：智能家居、工业监控、智慧城市。核心技术：传感器、通信协议、云计算。"

    if "区块链" in text:
        return "区块链是分布式账本技术，数据以区块形式链式存储。特点：去中心化、不可篡改、可追溯。应用：加密货币、供应链、数字身份。"

    if "5G" in text:
        return "5G是第五代移动通信技术。特点：高速率（10Gbps）、低延迟（1ms）、大连接（百万设备/km²）。应用：自动驾驶、远程医疗、工业互联网。"

    if "边缘计算" in text:
        return "边缘计算在数据源附近处理数据，减少传输到云端的延迟。适合实时性要求高的场景，如自动驾驶、工业控制。与云计算互补。"

    if "数字孪生" in text:
        return "数字孪生是物理实体的虚拟镜像，通过传感器实时同步数据。用于模拟、预测和优化。应用：工厂运维、城市规划、医疗仿真。"

    if "自然语言处理" in text or "NLP" in text:
        return "自然语言处理让计算机理解、生成和处理人类语言。核心技术：分词、词向量、Transformer、BERT。应用：翻译、问答、文本摘要、情感分析。"

    if "计算机视觉" in text or "CV" in text:
        return "计算机视觉让机器从图像和视频中提取信息。核心技术：CNN、目标检测、图像分割。应用：人脸识别、自动驾驶、医学影像、工业质检。"

    if "推荐系统" in text:
        return "推荐系统根据用户行为和偏好推荐内容。方法：协同过滤（相似用户喜欢什么）、内容推荐（相似内容）、混合推荐。应用：电商、视频、音乐。"

    if "时间序列" in text:
        return "时间序列是按时间顺序排列的数据。分析方法：趋势分析、季节性分解、ARIMA、LSTM。应用：股票预测、天气预报、销售预测、异常检测。"

    if "异常检测" in text:
        return "异常检测识别数据中的异常模式。方法：统计方法（3σ原则）、机器学习（Isolation Forest）、深度学习（AutoEncoder）。应用：欺诈检测、设备故障预警。"

    if "聚类" in text:
        return "聚类将相似数据分到同一组。常用算法：K-Means（指定聚类数）、DBSCAN（基于密度）、层次聚类。评估指标：轮廓系数、Calinski-Harabasz指数。"

    if "降维" in text:
        return "降维减少数据特征数量，保留关键信息。方法：PCA（线性降维）、t-SNE（非线性，适合可视化）、LDA（有监督降维）。好处：减少计算量、避免维度灾难。"

    if "正则化" in text:
        return "正则化通过限制模型复杂度防止过拟合。L1正则化（Lasso）产生稀疏权重，可做特征选择；L2正则化（Ridge）让权重趋向小值。λ控制正则化强度。"

    if "准确率" in text or "精确率" in text or "召回率" in text or "F1" in text:
        return "分类评估指标：准确率=正确/总数；精确率=预测为正中真正为正的比例；召回率=真正为正中被找回的比例；F1=精确率和召回率的调和平均。"

    if "AUC" in text or "ROC" in text:
        return "ROC曲线展示不同阈值下真正率和假正率的关系。AUC是ROC曲线下面积，0.5-1之间，越大越好。AUC不受类别不平衡影响，适合评估二分类模型。"

    if "决策树" in text:
        return "决策树通过一系列条件判断做出决策，像一棵倒置的树。优点：易理解、可解释；缺点：容易过拟合。改进：随机森林（多棵树投票）、剪枝。"

    if "回归" in text and "线性" in text:
        return "线性回归用一条直线拟合数据关系。y=wx+b，通过最小二乘法求解w和b。评估指标：R²（拟合优度）、MSE（均方误差）。是最基础的机器学习算法。"

    if "逻辑回归" in text:
        return "逻辑回归是分类算法（虽然叫回归）。用Sigmoid函数将输出映射到0-1之间作为概率。适合二分类，简单高效，是基线模型的首选。"

    if "SVM" in text or "支持向量" in text:
        return "SVM（支持向量机）找到一个最优超平面将数据分开。核心概念：支持向量（离超平面最近的点）、核函数（处理非线性数据）、间隔最大化。"

    if "朴素贝叶斯" in text:
        return "朴素贝叶斯基于贝叶斯定理，假设特征之间相互独立（'朴素'的含义）。优点：简单快速、适合文本分类；缺点：特征独立假设往往不成立。"

    if "KNN" in text or "K近邻" in text:
        return "KNN（K近邻）找到距离目标最近的K个样本，投票决定分类。优点：简单直观；缺点：计算量大、对K值敏感。需要先做数据标准化。"

    if "随机森林" in text:
        return "随机森林是多棵决策树的集成。每棵树用随机子集的数据和特征训练，最后投票。优点：不容易过拟合、能评估特征重要性。是常用的基线模型。"

    if "XGBoost" in text:
        return "XGBoost是高效的梯度提升算法。通过串行训练多棵树，每棵树修正前面的错误。在Kaggle竞赛中表现优异。特点：正则化、并行化、处理缺失值。"

    if "主成分分析" in text or "PCA" in text:
        return "PCA（主成分分析）是最常用的降维方法。找到数据方差最大的方向作为主成分，将高维数据投影到低维。保留95%方差的主成分通常足够。"

    if "数据治理" in text:
        return "数据治理是管理数据全生命周期的体系。包括：数据标准、数据质量、数据安全、元数据管理、主数据管理。目标：让数据可信、可用、安全。"

    if "元数据" in text:
        return "元数据是“关于数据的数据”，描述数据的属性。类型：技术元数据（表结构、字段类型）、业务元数据（业务含义、负责人）、操作元数据（创建时间、修改记录）。"

    if "数据血缘" in text:
        return "数据血缘追踪数据从源头到最终使用的完整路径。用于影响分析（改了源头会影响哪些下游）、问题排查（数据错了在哪一步出的问题）。"

    if "API" in text:
        return "API（应用程序编程接口）定义软件组件的交互方式。RESTful API用HTTP方法（GET/POST/PUT/DELETE）操作资源。API是系统集成的桥梁。"

    if "微服务" in text:
        return "微服务架构将应用拆分为独立的小服务。每个服务独立开发、部署、扩展。优点：灵活、技术栈自由；缺点：分布式复杂性、服务间通信开销。"

    if "容器" in text or "Docker" in text:
        return "容器将应用和依赖打包在一起，确保在任何环境都能运行。Docker是最流行的容器技术。容器比虚拟机轻量（共享内核），启动更快。"

    if "DevOps" in text:
        return "DevOps是开发（Dev）和运维（Ops）的协作文化。核心实践：持续集成（CI）、持续交付（CD）、自动化测试、监控。工具：Jenkins、GitLab CI、GitHub Actions。"

    if "需求分析" in text:
        return "需求分析是理解用户需要什么的过程。方法：用户访谈、问卷调查、竞品分析、原型设计。输出：需求规格说明书。需求变更是项目失败的主要原因之一。"

    if "项目管理" in text:
        return "项目管理确保项目按时、按质、按预算完成。核心：范围管理、时间管理、成本管理、质量管理、风险管理。方法论：瀑布（线性）、敏捷（迭代）。"

    if "测试" in text and ("软件" in text or "单元" in text or "集成" in text):
        return "软件测试验证系统功能和性能。类型：单元测试（单个函数）、集成测试（模块间交互）、系统测试（整体功能）、验收测试（用户确认）。自动化测试提高效率。"

    if "敏捷" in text:
        return "敏捷开发以迭代方式交付产品。核心：短周期迭代（Sprint）、每日站会、持续反馈、拥抱变化。Scrum是最流行的敏捷框架。"

    if "用户体验" in text or "UX" in text:
        return "用户体验关注产品是否好用、易用、想用。评估维度：可用性（能不能完成任务）、效率（多快完成）、满意度（用着舒不舒服）。"

    if "交互" in text and ("设计" in text or "方式" in text or "模式" in text):
        return "交互设计关注人和产品的互动方式。原则：一致性、反馈、容错、简洁。模式：直接操作、表单、导航、手势。好的交互让用户无需思考。"

    if "产品" in text and "设计" in text:
        return "产品设计从用户需求出发，定义产品功能和体验。流程：需求分析→信息架构→交互设计→视觉设计→原型→用户测试→迭代。"

    if "系统" in text and ("架构" in text or "设计" in text):
        return "系统设计定义软件的整体结构。关注：可扩展性（能否支撑增长）、可用性（能否7×24运行）、安全性（能否抵御攻击）、性能（响应速度）。"

    if "日志" in text:
        return "日志记录系统运行时的事件和状态。用于问题排查、安全审计、性能分析。日志级别：DEBUG、INFO、WARN、ERROR、FATAL。ELK是常用的日志分析平台。"

    if "监控" in text:
        return "监控实时跟踪系统运行状态。指标：CPU/内存使用率、请求延迟、错误率、吞吐量。工具：Prometheus（指标采集）、Grafana（可视化）、Zabbix。"

    if "高可用" in text:
        return "高可用确保系统持续运行不中断。手段：冗余（多副本）、负载均衡、故障转移、自动恢复。衡量：几个9（99.9%年停机8.76小时）。"

    if "容灾" in text:
        return "容灾是在灾难发生时保证业务连续性。策略：同城双活、异地灾备、两地三中心。RPO（可容忍的数据丢失量）和RTO（恢复时间目标）是关键指标。"

    if "负载均衡" in text:
        return "负载均衡将请求分发到多台服务器，避免单台过载。算法：轮询、加权轮询、最少连接、IP哈希。实现：Nginx、HAProxy、云厂商SLB。"

    if "缓存" in text:
        return "缓存将常用数据存在快速存储中，减少数据库压力。策略：LRU（最近最少使用淘汰）、TTL（过期自动删除）。常见：Redis、Memcached、CDN。"

    if "消息队列" in text:
        return "消息队列实现异步通信。生产者发消息到队列，消费者从队列取消息处理。解耦系统、削峰填谷。常见：Kafka、RabbitMQ、RocketMQ。"

    if "搜索引擎" in text:
        return "搜索引擎通过爬虫抓取网页、建立索引、根据关键词检索。核心技术：倒排索引、PageRank。Elasticsearch是常用的全文搜索引擎。"

    if "爬虫" in text:
        return "网络爬虫自动从网页抓取数据。流程：发送请求→获取HTML→解析提取→存储。遵守robots协议。框架：Scrapy（Python）、BeautifulSoup。法律风险：注意版权和隐私。"

    if "URL" in text or "网址" in text:
        return "URL（统一资源定位符）是网页地址。结构：协议（http/https）+域名+路径+参数。HTTPS比HTTP安全（加密传输）。"

    if "域名" in text:
        return "域名是网站的可读地址（如baidu.com）。DNS将域名解析为IP地址。顶级域名：.com（商业）、.org（组织）、.cn（中国）。域名需要注册和续费。"

    # ── 通用判断题模式 ──
    if qtype == 'j':
        if not ans:
            # 错误的判断题
            if "可以不" in text or "不需要" in text or "无需" in text:
                return "根据相关规定和职业规范，该项要求是必须遵守的，不可以省略或忽略。"
            if "仅" in text or "只是" in text or "只有" in text:
                return "该说法过于片面，实际情况更加全面和复杂。"
            if "所有" in text or "任何" in text or "一切" in text or "都" in text:
                return "该说法过于绝对，存在例外情况或限定条件。"
            if "一定" in text or "必然" in text:
                return "该说法过于绝对，实际情况可能因条件不同而有所变化。"
            if "不需要" in text or "不必" in text:
                return "根据相关规定和职业规范，该项要求是必须遵守的。"
            if "可以" in text or "能够" in text:
                return "该操作在规定中是不被允许或有限制条件的。"
            if "禁止" in text or "不能" in text:
                return "该说法错误，相关行为并非被完全禁止，需根据具体条件判断。"
            return "该说法不正确，实际情况与题目描述有出入。"
        else:
            # 正确的判断题
            if "必须" in text or "应当" in text or "应该" in text:
                return "这是明确的法定义务或职业要求，必须严格遵守。"
            if "可以" in text or "能够" in text or "允许" in text:
                return "该说法正确，在规定和实践中该操作是被允许的。"
            if "是" in text or "属于" in text or "包括" in text:
                return "该说法正确，符合相关定义和基本原理。"
            return "该说法正确，符合相关规定和基本原理。"

    # ── 通用选择题 fallback ──
    if qtype == 's':
        # 用选项内容生成更有意义的解释
        if opts and correct_ans:
            correct_text = opts.get(correct_ans, "")
            # 尝试从题目和选项中提取关键信息
            return f"本题需要根据相关知识判断。{correct_text}是正确答案，其他选项不符合题意要求。"
        return ""

    return ""

def analyze_wrong_opts(text, opts, correct_ans, wrong_opts):
    """分析单选题的干扰项"""
    analysis = ""
    for opt in wrong_opts:
        opt_text = opts.get(opt, "")

        # 常见干扰项模式
        if "仅" in opt_text or "只是" in opt_text or "只有" in opt_text:
            analysis += f" {opt}（{opt_text}）说法过于片面。"
        elif "所有" in opt_text or "任何" in opt_text or "一切" in opt_text:
            analysis += f" {opt}（{opt_text}）说法过于绝对。"
        elif "不需要" in opt_text or "无需" in opt_text or "不必" in opt_text:
            analysis += f" {opt}（{opt_text}）表述不正确，该要求通常是必须的。"
        elif "可以不" in opt_text:
            analysis += f" {opt}（{opt_text}）表述不正确，不可以省略。"

    return analysis

def analyze_all_opts_m(text, opts, correct_ans):
    """多选题逐选项分析"""
    if not isinstance(correct_ans, list):
        return ""

    analysis = ""
    for opt_key in sorted(opts.keys()):
        opt_text = opts[opt_key]
        if opt_key in correct_ans:
            analysis += f" {opt_key}（{opt_text}）✓——属于正确选项。"
        else:
            if "无关" in opt_text or "不相关" in opt_text:
                analysis += f" {opt_key}（{opt_text}）✗——与题目考查内容无关。"
            elif "相反" in opt_text or "颠倒" in opt_text:
                analysis += f" {opt_key}（{opt_text}）✗——表述与事实相反。"
            elif "过于" in opt_text:
                analysis += f" {opt_key}（{opt_text}）✗——表述过于绝对。"
            else:
                analysis += f" {opt_key}（{opt_text}）✗——不属于正确范畴。"

    return analysis

def generate_s_fallback(text, opts, correct_ans):
    """为单选题生成基于选项分析的fallback解释"""
    correct_text = opts.get(correct_ans, "")
    wrong_opts = {k: v for k, v in opts.items() if k != correct_ans}

    explain = ""
    if len(correct_text) > 15:
        explain += f"{correct_text}是本题的正确答案。"

    for k, v in wrong_opts.items():
        if "仅" in v or "只是" in v or "只有" in v or "唯一" in v:
            explain += f" {k}（{v}）过于片面。"
        elif "所有" in v or "任何" in v or "一切" in v or "全部" in v:
            explain += f" {k}（{v}）过于绝对。"
        elif "不需要" in v or "无需" in v or "不必" in v:
            explain += f" {k}（{v}）表述不正确。"

    return explain



    """多选题逐选项分析"""
    if not isinstance(correct_ans, list):
        return ""

    analysis = ""
    for opt_key in sorted(opts.keys()):
        opt_text = opts[opt_key]
        if opt_key in correct_ans:
            analysis += f" {opt_key}（{opt_text}）✓——属于正确选项。"
        else:
            # 分析为什么不选
            if "无关" in opt_text or "不相关" in opt_text:
                analysis += f" {opt_key}（{opt_text}）✗——与题目考查内容无关。"
            elif "相反" in opt_text or "颠倒" in opt_text:
                analysis += f" {opt_key}（{opt_text}）✗——表述与事实相反。"
            elif "过于" in opt_text:
                analysis += f" {opt_key}（{opt_text}）✗——表述过于绝对。"
            else:
                analysis += f" {opt_key}（{opt_text}）✗——不属于正确范畴。"

    return analysis

# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════
explanations = {}
stats = {'j': 0, 's': 0, 'm': 0}

for q in questions:
    qtype = q['type']
    idx = q['idx']
    key = f"{qtype}_{idx}"

    if qtype == 'j':
        exp = gen_j(q)
    elif qtype == 's':
        exp = gen_s(q)
    elif qtype == 'm':
        exp = gen_m(q)
    else:
        exp = ""

    explanations[key] = exp
    stats[qtype] += 1

# 统计
detailed = sum(1 for v in explanations.values() if len(v) > 80)
generic = sum(1 for v in explanations.values() if 30 < len(v) <= 80)
short = sum(1 for v in explanations.values() if len(v) <= 30)

print(f"Generated explanations:")
print(f"  判断题: {stats['j']}")
print(f"  单选题: {stats['s']}")
print(f"  多选题: {stats['m']}")
print(f"  总计: {sum(stats.values())}")
print(f"  详细(>80字): {detailed}")
print(f"  一般(30-80字): {generic}")
print(f"  简短(<30字): {short}")

with open("explanations.json", "w", encoding="utf-8") as f:
    json.dump(explanations, f, ensure_ascii=False, indent=2)

print("Saved to explanations.json")
