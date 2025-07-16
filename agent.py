import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import subprocess
from datetime import datetime
from smolagents import LiteLLMModel, DuckDuckGoSearchTool
from smolagents import CodeAgent
import os
import sys
import json
import matplotlib.pyplot as plt
import matplotlib
import traceback


# 使用ollama api
model = LiteLLMModel(
    model_id="ollama/mistral-nemo",
    api_base="http://127.0.0.1:11434",
    api_key="ollama",
)

steps = []

# 支持step回调收集思考过程
class StepRecorder:
    def __init__(self):
        self.steps = []
    def __call__(self, step):
        if isinstance(step, dict):
            self.steps.append({
                "thought": step.get("thought", ""),
                "action": step.get("action", ""),
                "observation": step.get("observation", "")
            })
        else:
            # 兜底：直接存字符串或其它类型
            self.steps.append({"thought": str(step), "action": "", "observation": ""})

recorder = StepRecorder()

agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model, max_steps=2, step_callbacks=[recorder])

# 1. 交互输入或命令行参数解析
# 新：解析请求ID参数（来自后端传递）
request_id = None
if len(sys.argv) > 1:
    user_question = sys.argv[1]
    # 调整参数顺序：question, request_id, start_date, end_date
    request_id = sys.argv[2] if len(sys.argv) > 2 else None
    start_date = sys.argv[3] if len(sys.argv) > 3 else None
    end_date = sys.argv[4] if len(sys.argv) > 4 else None
    need_time = bool(start_date or end_date)
else:
    print("请输入分析问题（如：请分析xtool的用户反馈）")
    user_question = input().strip()
    print("是否需要筛选时间范围？(y/n)")
    need_time = input().strip().lower() == 'y'
    start_date = end_date = None
    if need_time:
        print("请输入起始日期（格式：2025年6月1日），直接回车则不限制：")
        start_date = input().strip() or None
        print("请输入结束日期（格式：2025年7月1日），直接回车则不限制：")
        end_date = input().strip() or None

# 兜底逻辑：如果问题与xtool用户反馈无关，直接用mistral-nemo回答
class DummyMsg(dict):
    @property
    def role(self):
        return self['role']
    @property
    def content(self):
        return self['content']

if not (('xtool' in user_question.lower() or '用户反馈' in user_question or '评论' in user_question)):
    prompt = user_question + "\n请用中文简明回答，不要输出任何代码。"
    msg = DummyMsg(role="user", content=[{"type": "text", "text": prompt}])
    result = model([msg])
    if hasattr(result, 'content'):
        answer = result.content
    else:
        answer = str(result)
    output = {
        "steps": [],
        "answer": answer,
        "charts": []
    }
    print(json.dumps(output, ensure_ascii=False))
    exit(0)
# 下面是主流程，只有分析评论时才会执行

print("数据爬取开始")
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_py_path = os.path.join(base_dir, "Main.py")
    subprocess.run(["python3", main_py_path], timeout=300, check=True)
    print("数据爬取完成")
except subprocess.TimeoutExpired:
    print("Main.py 执行超时（超过300秒），请检查网络或数据源！")
    sys.exit(1)
except Exception as e:
    print("Main.py 执行出错：", e)
    traceback.print_exc()
    sys.exit(1)

base_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(base_dir, "Input", "xtool0.txt")
comment_path = os.path.join(base_dir, "Output", "comment", "xtool0.txt")
date_path = os.path.join(base_dir, "Output", "date", "xtool0.txt")

print("准备读取 input_path")
with open(input_path, encoding="utf-8") as f:
    input_content = f.read()
print("读取 input_path 完成")

if "令牌过期" in input_content or "FAIL_SYS_TOKEN_EXOIRED" in input_content:
    # 令牌过期，直接用 Input/xtool0.txt 做分析
    comments = [line.strip() for line in input_content.splitlines() if line.strip() and "令牌过期" not in line and "FAIL_SYS_TOKEN_EXOIRED" not in line]
    dates = []
    use_input = True
else:
    # 没有令牌过期，继续生成 Output/comment/xtool0.txt
    # 这里假设 filePreRegular 相关处理已在 Main.py 内部完成
    use_input = False
    with open(comment_path, encoding="utf-8") as f:
        comments = [line.strip() for line in f if line.strip()]
    with open(date_path, encoding="utf-8") as f:
        dates = [line.strip() for line in f if line.strip()]

# 4. 按需筛选（仅对 Output 数据源有效）
if not use_input and need_time and (start_date or end_date):
    def parse_date(s):
        try:
            return datetime.strptime(s, "%Y年%m月%d日")
        except Exception:
            return None
    start = parse_date(start_date) if start_date else None
    end = parse_date(end_date) if end_date else None
    filtered = []
    for c, d in zip(comments, dates):
        dt = parse_date(d)
        if dt is None:
            continue
        if (not start or dt >= start) and (not end or dt <= end):
            filtered.append(c)
    comments = filtered

if not comments:
    print(json.dumps({"steps": [], "answer": "没有符合条件的评论。"}, ensure_ascii=False))
    exit(0)

# 5. 用大模型分析
# 只取前5条评论测试
comments = comments[:5]

# 情感分析（简单规则/模拟）
sentiments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
for c in comments:
    # 简单模拟：带“好”“棒”“满意”算正面，带“差”“失望”算负面，否则中性
    if any(word in c for word in ['好', '棒', '满意', '喜欢', '推荐', '赞']):
        sentiments['Positive'] += 1
    elif any(word in c for word in ['差', '失望', '一般', '吐槽', '不行']):
        sentiments['Negative'] += 1
    else:
        sentiments['Neutral'] += 1

# 生成饼图 - 使用请求ID区分不同图片
# 创建 request_images 目录（如果不存在）
request_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'request_images')
os.makedirs(request_images_dir, exist_ok=True)

# 确定图片文件名和路径
if request_id:
    # 有请求ID时，使用带ID的文件名
    img_filename = f'sentiment_pie_{request_id}.png'
    img_path = os.path.join(request_images_dir, img_filename)
else:
    # 无请求ID时，使用默认路径
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    os.makedirs(static_dir, exist_ok=True)
    img_filename = 'sentiment_pie.png'
    img_path = os.path.join(static_dir, img_filename)

# 用英文标签
labels = ['Positive', 'Neutral', 'Negative']
sizes = [sentiments['Positive'], sentiments['Neutral'], sentiments['Negative']]
colors = ['#4CAF50', '#FF9800', '#2196F3']  # 绿色、橙色、蓝色
explode = [0.05 if s > 0 else 0 for s in sizes]  # 突出显示非0部分

pie_result = plt.pie(
    sizes,
    labels=labels,
    autopct='%1.1f%%',
    startangle=140,
    colors=colors,
    explode=explode,
    textprops={'fontsize': 14}
)
if len(pie_result) == 3:
    wedges, texts, autotexts = pie_result
else:
    wedges, texts = pie_result
    autotexts = []
plt.title('Sentiment Distribution', fontsize=16)
plt.setp(autotexts, size=14, weight='bold', color='white')
plt.setp(texts, size=14)
plt.tight_layout()
plt.savefig(img_path)
plt.close()

# 确定图片URL（根据存储位置）
if request_id:
    img_url = f'http://localhost:8000/request_images/{img_filename}'
else:
    img_url = f'http://localhost:8000/static/{img_filename}'

prompt = (
    f"{user_question}\n"
    "你是Xtool用户评论分析助手，请对以下用户评论进行情感分析，并分别总结主要优点、不足和建议。\n"
    "输出格式必须严格如下：\n"
    "【情感分布】正面X条，中性Y条，负面Z条\n"
    "【优点】：\n"
    "【不足】：\n"
    "【建议】：\n"
    "以下是用户评论：\n"
    + "\n".join(comments)
    + "\n请严格按照上述格式输出，只输出结论，不要输出任何代码，不要输出任何解释，不要输出任何格式化内容。"
)
# print("正在分析，请稍候...")   # 注释掉
msg = DummyMsg(role="user", content=[{"type": "text", "text": prompt}])
print("准备调用大模型")
result = model([msg])
print("大模型调用完成")
output = {
    "steps": recorder.steps if recorder.steps else [],
    "answer": result.content,
    "charts": [img_url]
}
print(json.dumps(output, ensure_ascii=False))
exit(0)

# 优先用recorder收集的steps，否则用默认
if recorder.steps:
    steps = recorder.steps
else:
    steps = [{"thought": "正在分析用户问题...", "action": "准备分析", "observation": ""}]

# 主流程最后输出也只输出answer字符串
# print(answer) # 注释掉