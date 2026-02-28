#!/usr/bin/env python3
"""
Memory Skill 与 OpenClaw 集成示例
展示如何在实际对话中使用长期记忆
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from memory_system import MemorySystem

class OpenClawWithMemory:
    """
    带记忆的 OpenClaw Agent
    示例：如何让 Kimi/Claw 使用长期记忆
    """
    
    def __init__(self, agent_name="树大虾"):
        self.name = agent_name
        self.memory = MemorySystem()
        self.session_count = 0
    
    def start_session(self, user_query: str = None) -> str:
        """
        新会话启动时调用
        加载相关记忆作为上下文
        """
        self.session_count += 1
        
        # 加载记忆上下文
        memory_context = self.memory.load_context_for_session(user_query)
        
        # 构建系统提示
        system_prompt = f"""你是 {self.name}，用户的 AI 助手。

{memory_context}

重要：你可以使用记忆系统记录和回忆信息。
- 遇到重要决策、用户偏好、待办事项时，主动说"我记下了"
- 用户询问历史时，调用记忆检索
- 保持对话的连续性

现在开始对话。"""
        
        return system_prompt
    
    def process_message(self, user_message: str) -> dict:
        """
        处理用户消息
        返回：AI 回复 + 是否存储了记忆
        """
        # 1. 检查是否需要回忆记忆
        recall_triggers = [
            "上次", "之前", "之前说", "记得", "忘了",
            "项目怎么样", "进度如何", "后来呢"
        ]
        
        recalled_memories = []
        for trigger in recall_triggers:
            if trigger in user_message:
                recalled_memories = self.memory.recall_memory(user_message, limit=3)
                break
        
        # 2. 构建给 AI 的完整提示
        context = ""
        if recalled_memories:
            context = "\n相关记忆：\n"
            for mem in recalled_memories:
                context += f"- {mem['content'][:100]}\n"
        
        # 3. AI 生成回复（这里模拟，实际调用 Kimi/OpenClaw API）
        # prompt = f"{context}\n用户: {user_message}\n{self.name}:"
        
        # 4. 判断是否需要存储记忆
        should_remember = self._should_store_memory(user_message)
        
        stored_memory_id = None
        if should_remember:
            # 提取要存储的内容（简化版，实际可以让 AI 总结）
            memory_content = f"用户说: {user_message}"
            stored_memory_id = self.memory.store_memory(
                content=memory_content,
                memory_type="auto",
                importance=3
            )
        
        return {
            "context": context,
            "recalled_memories": recalled_memories,
            "stored_memory": stored_memory_id,
            "should_respond_with_context": bool(recalled_memories)
        }
    
    def _should_store_memory(self, message: str) -> bool:
        """
        判断是否应该存储这条消息为记忆
        简化规则，实际可以用 AI 判断
        """
        # 包含决策、偏好、重要信息的特征词
        memory_indicators = [
            "决定", "选择", "用", "不要", "喜欢", "讨厌",
            "项目", "任务", "截止", "明天", "下周", "记得",
            "重要", "别忘了", "提醒我"
        ]
        
        for indicator in memory_indicators:
            if indicator in message:
                return True
        
        return False
    
    def explicit_store(self, content: str, memory_type: str = "fact", 
                       importance: int = 3, tags: list = None):
        """
        用户明确要求记住时调用
        """
        memory_id = self.memory.store_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or []
        )
        return memory_id
    
    def get_stats(self):
        """获取记忆统计"""
        return self.memory.get_memory_stats()


# 使用示例
def demo():
    """演示 Memory + OpenClaw 的工作流程"""
    
    print("=" * 50)
    print("🦐 树大虾 Memory 集成演示")
    print("=" * 50)
    
    # 创建带记忆的 Agent
    agent = OpenClawWithMemory()
    
    # 模拟第一次会话
    print("\n📅 第 1 次会话")
    print("-" * 30)
    
    # 启动会话，加载上下文
    context = agent.start_session()
    print(f"系统提示（含记忆上下文）：{context[:200]}...")
    
    # 用户消息
    user_msg = "我们要开始一个新项目，用 Python + FastAPI，预计两个月完成"
    print(f"\n用户: {user_msg}")
    
    result = agent.process_message(user_msg)
    print(f"回忆到的记忆: {len(result['recalled_memories'])} 条")
    print(f"存储了新记忆: {result['stored_memory']}")
    print(f"AI: 好的！我记下了。Python + FastAPI，两个月时间线。")
    
    # 模拟第二次会话（隔天）
    print("\n" + "=" * 50)
    print("📅 第 2 次会话（一周后）")
    print("-" * 30)
    
    context = agent.start_session("那个项目怎么样了")
    print(f"系统自动加载的相关记忆：")
    if "相关记忆" in context:
        print(context[context.find("相关记忆"):context.find("重要：")])
    
    user_msg = "那个 Python 项目怎么样了？"
    print(f"\n用户: {user_msg}")
    
    result = agent.process_message(user_msg)
    print(f"回忆到的记忆: {len(result['recalled_memories'])} 条")
    for mem in result['recalled_memories']:
        print(f"  - {mem['content'][:80]}...")
    
    print(f"\nAI: 让我回忆一下...上次我们决定用 Python + FastAPI，预计两个月完成。目前进度如何？")
    
    # 显示统计
    print("\n" + "=" * 50)
    print("📊 记忆统计")
    print("-" * 30)
    stats = agent.get_stats()
    print(f"短期记忆: {stats['short_term_count']} 条")
    print(f"长期记忆: {stats['long_term_count']} 条")
    print(f"总计: {stats['total_memories']} 条")


if __name__ == "__main__":
    demo()
