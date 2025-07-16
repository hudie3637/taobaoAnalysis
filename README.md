# Xtool用户评论分析助手

## 项目结构
- `agent.py`：大模型分析主逻辑
- `Main.py`、`filePreRegular.py` 等：数据抓取与预处理
- `backend.py`：FastAPI 后端接口
- `frontend/`：React 前端页面
- `Image/`：示例图片
## 运行前准备
     - Python 依赖安装 ：
      pip install matplotlib smolagents duckduckgo-search fastapi uvicorn
   - Node 依赖（前端）：
     cd frontend
     npm install
   - 启动 Ollama 服务（如本地）：
     ollama serve
    -下载并测试模型
     ollama run mistral-nemo
## 使用说明
  ### 方法一
    在 `taobaoAnalysis` 目录下运行：
    python agent.py
    通过命令行与agent进行交互   
    注1：为了更快得到输出结果，我只使用了前5条用户评论，agent推理最大迭代次数设为2
        要是想使用全部评论，可以注释掉comments = comments[:5]，
        agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model, max_steps=2, step_callbacks=[recorder])
        修改max_steps自行设置最大迭代次数
    注2：我在Infor.conf设置了爬取淘宝xtool用户评价的url,Cookie,referer
        由于不同设备登陆淘宝，网页的cookie会不一样，
        所以爬虫程序会无法自动爬取信息，会直接使用我已经爬取好的用户评价 
        例如：Input/xtool0.txt
        如果你想自己爬，可以修改Infor.conf设置，运行Main.py即可
  ### 方法二（前提是agent.py可以正常运行）
    ### 启动后端（FastAPI）
      在 `taobaoAnalysis` 目录下运行：
      uvicorn backend:app --reload --host 0.0.0.0 --port 8000
    ### 启动前端（React）
      在 `taobaoAnalysis/frontend` 目录下运行：
      npm run dev
      浏览器访问：http://localhost:5173
    
