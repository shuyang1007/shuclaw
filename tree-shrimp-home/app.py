#!/usr/bin/env python3
"""
树大虾主页 - 后端服务
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import os
from datetime import datetime
from threading import Thread
import time

app = Flask(__name__)
CORS(app)

# 树大虾的状态
shrimp_state = {
    "status": "online",  # online, working, resting, offline
    "mood": "happy",     # happy, tired, excited, calm
    "current_task": None,
    "last_active": datetime.now().isoformat(),
    "messages": [],      # 聊天记录
    "logs": [],          # 工作日志
    "skills": {
        "coding": {"level": 85, "xp": 8500},
        "research": {"level": 90, "xp": 9000},
        "automation": {"level": 75, "xp": 7500},
    }
}

# 加载历史记录
def load_history():
    history_file = os.path.expanduser("~/.openclaw/workspace/tree-shrimp-home/history.json")
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            data = json.load(f)
            shrimp_state["messages"] = data.get("messages", [])
            shrimp_state["logs"] = data.get("logs", [])

def save_history():
    history_file = os.path.expanduser("~/.openclaw/workspace/tree-shrimp-home/history.json")
    with open(history_file, 'w') as f:
        json.dump({
            "messages": shrimp_state["messages"][-100:],  # 保留最近100条
            "logs": shrimp_state["logs"][-50:]            # 保留最近50条日志
        }, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    return jsonify(shrimp_state)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    # 记录用户消息
    shrimp_state["messages"].append({
        "role": "user",
        "content": user_message,
        "time": datetime.now().isoformat()
    })
    
    # 树大虾回复（简单版本，后续接入OpenClaw）
    response = generate_response(user_message)
    
    shrimp_state["messages"].append({
        "role": "assistant",
        "content": response,
        "time": datetime.now().isoformat()
    })
    
    shrimp_state["last_active"] = datetime.now().isoformat()
    save_history()
    
    return jsonify({"response": response})

@app.route('/api/task', methods=['POST'])
def create_task():
    data = request.json
    task = {
        "id": len(shrimp_state["logs"]) + 1,
        "title": data.get('title', '新任务'),
        "description": data.get('description', ''),
        "status": "pending",  # pending, running, completed, failed
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }
    
    shrimp_state["logs"].insert(0, task)
    shrimp_state["current_task"] = task
    shrimp_state["status"] = "working"
    save_history()
    
    # 模拟异步执行任务
    def run_task():
        time.sleep(2)  # 模拟执行时间
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        shrimp_state["status"] = "online"
        shrimp_state["current_task"] = None
        save_history()
    
    Thread(target=run_task).start()
    
    return jsonify(task)

@app.route('/api/logs')
def get_logs():
    return jsonify(shrimp_state["logs"])

@app.route('/api/skills')
def get_skills():
    return jsonify(shrimp_state["skills"])

# 简单的回复生成（后续替换为真实的AI回复）
def generate_response(message):
    message = message.lower()
    
    if "你好" in message or "嗨" in message or "hi" in message:
        return "嗨！我是树大虾 🦐 很高兴见到你！有什么我可以帮你的吗？"
    
    elif "代码" in message or "编程" in message or "python" in message:
        return "我可以帮你写代码！告诉我具体需求，我会尽力帮你实现。💻"
    
    elif "查" in message or "搜索" in message or "找" in message:
        return "我可以帮你查资料！告诉我你想了解什么？🔍"
    
    elif "任务" in message or "工作" in message:
        return "我可以帮你管理任务！点击下方『工作日志』查看，或者直接告诉我你要做什么～"
    
    elif "你是谁" in message:
        return "我是树大虾，一只AI助手虾 🦐 我会写代码、查资料、监控信息，24小时在线陪伴主人！"
    
    elif "谢谢" in message or "thanks" in message:
        return "不用谢！能帮到你我很开心 🦐 随时叫我哦！"
    
    else:
        return "好的，我记下了！如果需要我帮你执行什么任务，随时告诉我～ 🦐"

# 自动保存状态
def auto_save():
    while True:
        time.sleep(60)  # 每分钟保存一次
        save_history()

if __name__ == '__main__':
    load_history()
    
    # 启动自动保存线程
    save_thread = Thread(target=auto_save, daemon=True)
    save_thread.start()
    
    print("🦐 树大虾主页启动中...")
    print("访问 http://localhost:5000")
    app.run(debug=True, port=5000)
