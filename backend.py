from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import subprocess
import json
import os
import re
import uuid  # 用于生成唯一标识符
import shutil  # 用于文件操作

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建用于存储请求相关图片的目录
request_images_dir = os.path.join(os.path.dirname(__file__), 'request_images')
os.makedirs(request_images_dir, exist_ok=True)

# 获取 static 目录的绝对路径
static_dir = os.path.join(os.path.dirname(__file__), 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")
# 挂载请求图片目录
app.mount("/request_images", StaticFiles(directory=request_images_dir), name="request_images")

class ChatRequest(BaseModel):
    question: str
    history: Optional[list] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    # 生成唯一请求ID
    request_id = str(uuid.uuid4())
    
    # 拼接历史对话
    prompt = ""
    if req.history:
        for msg in req.history:
            if msg["role"] == "user":
                prompt += f"用户: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt += f"助手: {msg['content']}\n"
    prompt += f"用户: {req.question}\n助手:"
    
    # 传递请求ID给agent.py
    result = subprocess.run(
        ["python3", "agent.py", prompt, request_id],  # 新增request_id参数
        capture_output=True, text=True, cwd=os.path.dirname(__file__)
    )
    
    try:
        # 提取最后一个 {...} 作为 JSON
        matches = re.findall(r'\{.*\}', result.stdout, re.DOTALL)
        if matches:
            data = json.loads(matches[-1])
            steps = data.get('steps', [])
            answer = data.get('answer', '')
            # answer为空或为无评论时友好提示
            if not answer or '没有符合条件的评论' in str(answer):
                answer = "暂无可用评论数据"
            # 只对用户评论内容做合并行处理
            if answer.startswith('以下是用户评论：'):
                # 找到评论段落，合并所有行
                lines = answer.splitlines()
                merged = []
                in_comment = False
                for line in lines:
                    if line.strip().startswith('以下是用户评论：'):
                        in_comment = True
                        merged.append(line.strip())
                    elif in_comment and line.strip():
                        # 合并到上一行
                        merged[-1] += line.strip()
                    else:
                        merged.append(line)
                answer = "\n".join(merged)
            # 只用 agent.py 返回的 charts 字段
            charts = data.get('charts', [])
            return {"steps": steps, "answer": answer, "charts": charts}
        else:
            # fallback
            return {"steps": [], "answer": "暂无可用评论数据", "charts": []}
    except Exception as e:
        print(f"Error processing response: {e}")
        # 只保留非警告/traceback的有效内容
        raw = result.stdout.strip()
        # 过滤掉包含警告/traceback/英文提示的行
        filter_keywords = [
            "Error in code parsing", "DeprecationWarning", "Traceback", "UserWarning", "Warning",
            "regex pattern", "code snippet", "Make sure", "for instance", "Your code snippet is invalid",
            "Here is your code snippet", "Thoughts:", "<code>", "</code>"
        ]
        filtered = []
        for line in raw.splitlines():
            # 只保留含有中文的行，且不包含上述关键字
            if not any(w in line for w in filter_keywords) and re.search(r'[\u4e00-\u9fff]', line):
                filtered.append(line)
        clean = "\n".join(filtered).strip()
        if clean:
            return {"steps": [], "answer": clean, "charts": []}
        else:
            return {"steps": [], "answer": "暂无可用评论数据", "charts": []}