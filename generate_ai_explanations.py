"""
用 MiMo API 为 900 题生成教学级解析
用法: python generate_ai_explanations.py
支持断点续传：每 50 题自动保存进度，中断后重新运行会跳过已处理的题
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

# 强制刷新输出
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

# ─── 配置 ───
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")
MIMO_BASE_URL = os.environ.get("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
MODEL = "mimo-v2.5-pro"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(SCRIPT_DIR, "questions_extracted.json")
EXPLANATIONS_FILE = os.path.join(SCRIPT_DIR, "explanations.json")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "ai_explain_progress.json")

MIN_KEEP_LENGTH = 200  # 已有解析 >= 200 字的跳过
REQUIRE_STRUCTURE = True  # 要求必须有"核心知识点"结构化格式
CALL_INTERVAL = 1.5     # 每次 API 调用间隔（秒）
MAX_RETRIES = 3
SAVE_EVERY = 50         # 每处理 50 题保存一次


def call_mimo(prompt: str) -> str:
    """调用 MiMo API"""
    url = f"{MIMO_BASE_URL}/chat/completions"
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={
        "api-key": MIMO_API_KEY,
        "Content-Type": "application/json",
    })

    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  [重试 {attempt+1}/{MAX_RETRIES}] {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(3)
    return ""


def build_prompt(q: dict) -> str:
    """为每道题构建 prompt"""
    qtype = {"j": "判断题", "s": "单选题", "m": "多选题"}[q["type"]]

    # 构建答案文本
    if q["type"] == "j":
        answer_text = "正确" if q["answer"] else "错误"
    elif q["type"] == "s":
        answer_text = q["answer"]
    else:
        answer_text = "、".join(q["answer"])

    # 构建选项文本
    options_text = ""
    if "options" in q:
        options_text = "\n".join(f"{k}. {v}" for k, v in q["options"].items())

    prompt = f"""你是一个AI培训考试辅导老师。请为以下题目生成解析。你必须严格按照以下格式输出，不能遗漏任何部分。

题目类型：{qtype}
题目：{q["question"]}
{f'选项：{chr(10)}{options_text}' if options_text else ''}
正确答案：{answer_text}

【必须包含的格式】
1. 第一行：✅ 正确答案是X。（判断题写"正确/错误"，选择题写选项字母）
2. 第二行起：**核心知识点**：用2-3句话讲解这道题涉及的核心概念，让人真正理解
3. 然后：**选项解析**：逐个解释每个选项为什么对/为什么错（判断题也要解释为什么对/为什么错）
4. 最后：**实际例子**：给一个实际例子帮助理解（如果适用）
5. 语言简洁直接，不要说"本题考查..."、"根据相关规定..."这类废话
6. 总长度控制在 300-500 字

【重要】
- 必须包含"核心知识点"这四个字作为标题
- 必须包含"选项解析"这四个字作为标题
- 不要把所有内容挤在一段里，要分段分标题

直接输出解析内容，不要加任何前缀或标记。"""

    return prompt


def main():
    if not MIMO_API_KEY:
        print("错误：请先设置环境变量 MIMO_API_KEY")
        sys.exit(1)

    # 读取题目
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # 读取已有解析
    existing = {}
    if os.path.exists(EXPLANATIONS_FILE):
        with open(EXPLANATIONS_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)

    # 读取进度
    done_keys = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            done_keys = set(json.load(f))
        print(f"[恢复进度] 已完成 {len(done_keys)} 题")

    # 统计
    total = len(questions)
    to_process = []
    skipped_long = 0
    skipped_done = 0

    for q in questions:
        key = f"{q['type']}_{q['idx']}"
        if key in done_keys:
            skipped_done += 1
            continue
        if key in existing and len(existing[key]) >= MIN_KEEP_LENGTH:
            if REQUIRE_STRUCTURE and '核心知识点' not in existing[key]:
                to_process.append(q)  # 长度够但没结构，需要重写
                continue
            skipped_long += 1
            continue
        to_process.append(q)

    print(f"[统计] 总计 {total} 题")
    print(f"[统计] 跳过已完成: {skipped_done}, 跳过长解析(>={MIN_KEEP_LENGTH}字): {skipped_long}")
    print(f"[统计] 待处理: {len(to_process)} 题")
    print(f"[统计] 预计耗时: {len(to_process) * CALL_INTERVAL / 60:.0f} 分钟")
    print()

    if not to_process:
        print("[完成] 所有题目都已处理")
        return

    # 处理
    processed = 0
    for q in to_process:
        key = f"{q['type']}_{q['idx']}"
        prompt = build_prompt(q)

        print(f"[{processed+1}/{len(to_process)}] {key}: {q['question'][:40]}...")
        result = call_mimo(prompt)

        if result:
            existing[key] = result
            done_keys.add(key)
            processed += 1
            print(f"  -> {len(result)} 字")
        else:
            print(f"  -> 失败，跳过")

        # 定期保存
        if processed % SAVE_EVERY == 0 and processed > 0:
            save_progress(existing, done_keys)
            print(f"  [自动保存] 已处理 {processed} 题")

        time.sleep(CALL_INTERVAL)

    # 最终保存
    save_progress(existing, done_keys)

    # 统计结果
    short = sum(1 for v in existing.values() if len(v) < 100)
    medium = sum(1 for v in existing.values() if 100 <= len(v) < 200)
    long_ = sum(1 for v in existing.values() if len(v) >= 200)
    print(f"\n[完成] 新生成 {processed} 题解析")
    print(f"[结果] 短(<100字): {short}, 中(100-200字): {medium}, 长(>=200字): {long_}")


def save_progress(existing: dict, done_keys: set):
    """保存解析和进度"""
    with open(EXPLANATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(done_keys), f)


if __name__ == "__main__":
    main()
