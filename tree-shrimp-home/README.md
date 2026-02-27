# 树大虾主页 🦐

树大虾的个人主页 - 一个AI Agent的展示和互动平台。

## 功能特性

- 🦐 **形象展示**：树大虾的状态、心情、技能等级
- 💬 **实时聊天**：和树大虾对话，发送任务指令
- 📋 **工作日志**：查看任务执行记录
- 📊 **技能系统**：树大虾的能力成长展示
- 🔄 **自动保存**：聊天记录和日志自动保存

## 安装运行

### 1. 安装依赖

```bash
cd tree-shrimp-home
pip install flask flask-cors
```

### 2. 运行服务

```bash
python3 app.py
```

### 3. 访问页面

打开浏览器访问：http://localhost:5000

## 页面结构

```
tree-shrimp-home/
├── app.py                 # Flask后端
├── templates/
│   └── index.html         # 主页
├── static/
│   ├── css/
│   │   └── style.css      # 样式
│   └── js/
│       └── script.js      # 交互逻辑
└── history.json           # 数据存储（自动生成）
```

## 使用说明

1. **聊天**：在输入框输入消息，和树大虾对话
2. **快捷指令**：点击快捷按钮快速发送常用指令
3. **创建任务**：点击"新建任务"让树大虾执行工作
4. **查看日志**：在工作日志区域查看任务执行情况

## 后续扩展

- [ ] 接入真实的OpenClaw AI回复
- [ ] 添加语音对话功能
- [ ] 接入你们的KUKIIII产品
- [ ] 实现Agent间通信

## 技术栈

- 后端：Python Flask
- 前端：HTML + Tailwind CSS + Vanilla JS
- 实时通信：REST API（后续可升级WebSocket）
