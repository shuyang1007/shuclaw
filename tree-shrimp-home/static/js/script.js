/**
 * 树大虾主页 - 前端交互
 */

// 全局状态
let currentState = {};

// 初始化
window.onload = function() {
    loadState();
    loadLogs();
    loadSkills();
    
    // 自动刷新状态（每30秒）
    setInterval(loadState, 30000);
    setInterval(loadLogs, 30000);
};

// 加载状态
async function loadState() {
    try {
        const response = await fetch('/api/state');
        currentState = await response.json();
        updateUI();
    } catch (error) {
        console.error('加载状态失败:', error);
    }
}

// 更新UI
function updateUI() {
    // 更新状态徽章
    const statusBadge = document.getElementById('status-badge');
    const moodBadge = document.getElementById('mood-badge');
    
    if (statusBadge && currentState.status) {
        const statusMap = {
            'online': { text: '🟢 在线', class: 'bg-green-100 text-green-800' },
            'working': { text: '🔵 工作中', class: 'bg-blue-100 text-blue-800' },
            'resting': { text: '🟡 休息中', class: 'bg-yellow-100 text-yellow-800' },
            'offline': { text: '⚫ 离线', class: 'bg-gray-100 text-gray-800' }
        };
        
        const status = statusMap[currentState.status] || statusMap['online'];
        statusBadge.textContent = status.text;
        statusBadge.className = `px-3 py-1 rounded-full text-sm font-medium ${status.class}`;
    }
    
    // 更新心情徽章
    if (moodBadge && currentState.mood) {
        const moodMap = {
            'happy': { text: '😊 开心', class: 'bg-yellow-100 text-yellow-800' },
            'tired': { text: '😴 疲惫', class: 'bg-gray-100 text-gray-800' },
            'excited': { text: '🤩 兴奋', class: 'bg-pink-100 text-pink-800' },
            'calm': { text: '😌 平静', class: 'bg-blue-100 text-blue-800' }
        };
        
        const mood = moodMap[currentState.mood] || moodMap['happy'];
        moodBadge.textContent = mood.text;
        moodBadge.className = `px-3 py-1 rounded-full text-sm font-medium ${mood.class}`;
    }
    
    // 更新当前任务显示
    const currentTask = document.getElementById('current-task');
    const taskTitle = document.getElementById('task-title');
    
    if (currentTask && currentState.current_task) {
        currentTask.classList.remove('hidden');
        if (taskTitle) {
            taskTitle.textContent = currentState.current_task.title;
        }
    } else if (currentTask) {
        currentTask.classList.add('hidden');
    }
    
    // 更新统计
    if (currentState.logs) {
        const completedTasks = currentState.logs.filter(l => l.status === 'completed').length;
        document.getElementById('task-count').textContent = completedTasks;
    }
    
    if (currentState.messages) {
        const userMessages = currentState.messages.filter(m => m.role === 'user').length;
        document.getElementById('msg-count').textContent = userMessages;
    }
}

// 加载技能
async function loadSkills() {
    try {
        const response = await fetch('/api/skills');
        const skills = await response.json();
        
        const container = document.getElementById('skills-container');
        if (!container) return;
        
        container.innerHTML = '';
        
        const skillNames = {
            'coding': '代码能力',
            'research': '信息检索',
            'automation': '自动化'
        };
        
        for (const [key, skill] of Object.entries(skills)) {
            const name = skillNames[key] || key;
            const level = skill.level || 0;
            
            const skillDiv = document.createElement('div');
            skillDiv.className = 'mb-3';
            skillDiv.innerHTML = `
                <div class="flex justify-between text-sm mb-1">
                    <span class="text-gray-700">${name}</span>
                    <span class="text-gray-500">Lv.${level}</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="skill-bar h-2 rounded-full" style="width: ${level}%"></div>
                </div>
            `;
            container.appendChild(skillDiv);
        }
    } catch (error) {
        console.error('加载技能失败:', error);
    }
}

// 加载日志
async function loadLogs() {
    try {
        const response = await fetch('/api/logs');
        const logs = await response.json();
        
        const container = document.getElementById('logs-container');
        if (!container) return;
        
        if (logs.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                    暂无任务，创建一个吧！
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        logs.slice(0, 10).forEach(log => {
            const statusClass = `task-${log.status}`;
            const statusText = {
                'pending': '⏳ 待执行',
                'running': '🔄 执行中',
                'completed': '✅ 已完成',
                'failed': '❌ 失败'
            }[log.status] || log.status;
            
            const logDiv = document.createElement('div');
            logDiv.className = `bg-gray-50 rounded-lg p-3 ${statusClass}`;
            logDiv.innerHTML = `
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-medium text-gray-800">${log.title}</h4>
                        <p class="text-sm text-gray-600 mt-1">${log.description || ''}</p>
                        <p class="text-xs text-gray-400 mt-1">${new Date(log.created_at).toLocaleString()}</p>
                    </div>
                    <span class="text-xs px-2 py-1 rounded-full bg-white">${statusText}</span>
                </div>
            `;
            container.appendChild(logDiv);
        });
    } catch (error) {
        console.error('加载日志失败:', error);
    }
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 清空输入框
    input.value = '';
    
    // 添加用户消息到界面
    addMessageToChat('user', message);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        // 添加AI回复
        addMessageToChat('assistant', data.response);
        
        // 更新统计
        loadState();
    } catch (error) {
        console.error('发送消息失败:', error);
        addMessageToChat('assistant', '抱歉，网络有点问题，请稍后再试 🦐');
    }
}

// 快捷发送
function quickSend(text) {
    document.getElementById('chat-input').value = text;
    sendMessage();
}

// 添加消息到聊天界面
function addMessageToChat(role, content) {
    const container = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex items-start space-x-3 animate-fade-in';
    
    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center text-xl flex-shrink-0 ml-auto order-2">
                👤
            </div>
            <div class="bg-blue-500 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-[80%] order-1 ml-auto">
                <p>${escapeHtml(content)}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="w-10 h-10 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex items-center justify-center text-xl flex-shrink-0">
                🦐
            </div>
            <div class="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3 max-w-[80%]">
                <p class="text-gray-800">${escapeHtml(content)}</p>
            </div>
        `;
    }
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// 创建任务
async function createTask() {
    const title = prompt('任务名称：');
    if (!title) return;
    
    const description = prompt('任务描述（可选）：') || '';
    
    try {
        const response = await fetch('/api/task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, description })
        });
        
        const task = await response.json();
        
        // 添加到聊天
        addMessageToChat('assistant', `收到任务：${title} 🦐 我正在处理...`);
        
        // 刷新日志和状态
        loadLogs();
        loadState();
    } catch (error) {
        console.error('创建任务失败:', error);
        alert('创建任务失败，请重试');
    }
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 淡入动画
const style = document.createElement('style');
style.textContent = `
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
        animation: fade-in 0.3s ease-out;
    }
`;
document.head.appendChild(style);
