#!/usr/bin/env python3
"""
Memory Skill - AI 长期记忆系统
让 OpenClaw/Kimi 拥有跨会话的长期记忆

功能：
1. 存储记忆（store_memory）
2. 检索记忆（recall_memory）
3. 更新记忆（update_memory）
4. 总结对话（summarize_for_memory）
5. 启动时加载相关记忆（load_context）

存储格式：JSON + Markdown 混合
- 结构化数据存 JSON（便于检索）
- 长文本存 Markdown（便于阅读）
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re

class MemorySystem:
    """长期记忆系统"""
    
    def __init__(self, memory_dir: str = "~/.openclaw/memory"):
        """
        初始化记忆系统
        
        Args:
            memory_dir: 记忆存储目录
        """
        self.memory_dir = os.path.expanduser(memory_dir)
        self.short_term_file = os.path.join(self.memory_dir, "short_term.json")
        self.long_term_file = os.path.join(self.memory_dir, "long_term.json")
        self.notes_dir = os.path.join(self.memory_dir, "notes")
        
        # 确保目录存在
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.notes_dir, exist_ok=True)
        
        # 加载现有记忆
        self.short_term = self._load_json(self.short_term_file, [])
        self.long_term = self._load_json(self.long_term_file, [])
    
    def _load_json(self, filepath: str, default):
        """加载 JSON 文件"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default
    
    def _save_json(self, filepath: str, data):
        """保存 JSON 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _generate_id(self, content: str) -> str:
        """生成记忆唯一 ID"""
        timestamp = datetime.now().isoformat()
        hash_str = hashlib.md5(f"{content}{timestamp}".encode()).hexdigest()[:8]
        return f"mem_{hash_str}"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现）"""
        # 移除停用词
        stop_words = {'的', '了', '是', '我', '你', '在', '和', '就', '都', '要', '会', '能', '可以', '这个', '那个'}
        
        # 提取中文词汇（2-6个字）
        words = re.findall(r'[\u4e00-\u9fa5]{2,6}', text)
        words = [w for w in words if w not in stop_words and len(w) >= 2]
        
        # 提取英文词汇
        english_words = re.findall(r'[a-zA-Z]{3,}', text)
        
        return list(set(words + english_words))[:10]  # 最多10个关键词
    
    def store_memory(self, content: str, memory_type: str = "auto", 
                    importance: int = 3, tags: List[str] = None,
                    source: str = "conversation") -> str:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型 (fact/decision/preference/task/project/auto)
            importance: 重要程度 (1-5, 5为最重要)
            tags: 标签列表
            source: 来源
            
        Returns:
            记忆 ID
        """
        memory_id = self._generate_id(content)
        keywords = self._extract_keywords(content)
        
        memory = {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "importance": importance,
            "tags": tags or [],
            "keywords": keywords,
            "source": source,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": datetime.now().isoformat()
        }
        
        # 根据重要性和时间决定存短期还是长期
        if importance >= 4 or memory_type in ["preference", "project"]:
            self.long_term.append(memory)
            self._save_json(self.long_term_file, self.long_term)
        else:
            self.short_term.append(memory)
            self._save_json(self.short_term_file, self.short_term)
        
        # 如果内容很长，保存到 markdown 文件
        if len(content) > 200:
            note_path = os.path.join(self.notes_dir, f"{memory_id}.md")
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(f"# 记忆 {memory_id}\n\n")
                f.write(f"**时间**: {memory['created_at']}\n\n")
                f.write(f"**类型**: {memory_type}\n\n")
                f.write(f"**标签**: {', '.join(tags or [])}\n\n")
                f.write("---\n\n")
                f.write(content)
        
        return memory_id
    
    def recall_memory(self, query: str, limit: int = 5, 
                     memory_type: str = None) -> List[Dict]:
        """
        检索记忆
        
        Args:
            query: 查询内容
            limit: 返回数量
            memory_type: 筛选特定类型
            
        Returns:
            相关记忆列表
        """
        query_keywords = set(self._extract_keywords(query))
        all_memories = self.short_term + self.long_term
        
        # 过滤类型
        if memory_type:
            all_memories = [m for m in all_memories if m.get("type") == memory_type]
        
        # 计算相关度分数
        scored_memories = []
        for mem in all_memories:
            mem_keywords = set(mem.get("keywords", []))
            
            # 关键词匹配分数
            keyword_score = len(query_keywords & mem_keywords) * 10
            
            # 内容包含分数
            content_score = 0
            for kw in query_keywords:
                if kw in mem.get("content", ""):
                    content_score += 5
            
            # 重要性加分
            importance_score = mem.get("importance", 3) * 2
            
            # 时间衰减（越新的记忆分数越高）
            try:
                mem_time = datetime.fromisoformat(mem.get("created_at", ""))
                days_old = (datetime.now() - mem_time).days
                time_score = max(0, 20 - days_old)  # 20天内满分，之后递减
            except:
                time_score = 0
            
            total_score = keyword_score + content_score + importance_score + time_score
            
            if total_score > 0:
                scored_memories.append((total_score, mem))
        
        # 按分数排序，返回前 N 个
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        results = [mem for score, mem in scored_memories[:limit]]
        
        # 更新访问计数
        for mem in results:
            mem["access_count"] = mem.get("access_count", 0) + 1
            mem["last_accessed"] = datetime.now().isoformat()
        
        self._save_json(self.short_term_file, self.short_term)
        self._save_json(self.long_term_file, self.long_term)
        
        return results
    
    def load_context_for_session(self, query: str = None) -> str:
        """
        为新的会话加载相关记忆上下文
        
        Args:
            query: 可选的查询，如果有特定主题
            
        Returns:
            格式化的记忆上下文文本
        """
        # 获取最近的重要记忆
        recent_important = [
            m for m in self.long_term 
            if m.get("importance", 3) >= 4
        ][-5:]  # 最近5条重要记忆
        
        # 如果有查询，获取相关记忆
        relevant_memories = []
        if query:
            relevant_memories = self.recall_memory(query, limit=3)
        
        # 合并并去重
        all_memories = recent_important + relevant_memories
        seen_ids = set()
        unique_memories = []
        for m in all_memories:
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                unique_memories.append(m)
        
        if not unique_memories:
            return ""
        
        # 格式化上下文
        context_lines = ["### 相关记忆", ""]
        for mem in unique_memories:
            context_lines.append(f"- [{mem.get('type', '记忆')}] {mem['content'][:100]}...")
        
        return "\n".join(context_lines)
    
    def update_memory(self, memory_id: str, updates: Dict) -> bool:
        """更新记忆"""
        for mem_list in [self.short_term, self.long_term]:
            for mem in mem_list:
                if mem.get("id") == memory_id:
                    mem.update(updates)
                    mem["updated_at"] = datetime.now().isoformat()
                    self._save_json(self.short_term_file, self.short_term)
                    self._save_json(self.long_term_file, self.long_term)
                    return True
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        for mem_list, filepath in [
            (self.short_term, self.short_term_file),
            (self.long_term, self.long_term_file)
        ]:
            for i, mem in enumerate(mem_list):
                if mem.get("id") == memory_id:
                    mem_list.pop(i)
                    self._save_json(filepath, mem_list)
                    # 删除对应的 markdown 文件
                    note_path = os.path.join(self.notes_dir, f"{memory_id}.md")
                    if os.path.exists(note_path):
                        os.remove(note_path)
                    return True
        return False
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计"""
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "total_memories": len(self.short_term) + len(self.long_term),
            "storage_dir": self.memory_dir
        }
    
    def cleanup_old_memories(self, days: int = 30):
        """清理旧记忆（短期记忆超过 N 天的低重要性记忆）"""
        cutoff = datetime.now() - timedelta(days=days)
        
        # 清理短期记忆
        kept_short = []
        for mem in self.short_term:
            mem_time = datetime.fromisoformat(mem.get("created_at", ""))
            # 保留：重要的、最近访问的、或者小于 N 天的
            if (mem.get("importance", 3) >= 4 or 
                mem.get("access_count", 0) >= 3 or
                mem_time > cutoff):
                kept_short.append(mem)
        
        removed_count = len(self.short_term) - len(kept_short)
        self.short_term = kept_short
        self._save_json(self.short_term_file, self.short_term)
        
        return removed_count


# CLI 接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Skill CLI")
    parser.add_argument("command", choices=[
        "store", "recall", "context", "stats", "cleanup"
    ])
    parser.add_argument("--content", "-c", help="记忆内容")
    parser.add_argument("--query", "-q", help="查询内容")
    parser.add_argument("--type", "-t", default="auto", help="记忆类型")
    parser.add_argument("--importance", "-i", type=int, default=3, help="重要性 1-5")
    parser.add_argument("--tags", help="标签，逗号分隔")
    
    args = parser.parse_args()
    
    mem = MemorySystem()
    
    if args.command == "store":
        if not args.content:
            print("Error: --content required")
            exit(1)
        tags = args.tags.split(",") if args.tags else []
        mid = mem.store_memory(args.content, args.type, args.importance, tags)
        print(f"Stored memory: {mid}")
        
    elif args.command == "recall":
        if not args.query:
            print("Error: --query required")
            exit(1)
        results = mem.recall_memory(args.query)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        
    elif args.command == "context":
        context = mem.load_context_for_session(args.query)
        print(context)
        
    elif args.command == "stats":
        print(json.dumps(mem.get_memory_stats(), indent=2))
        
    elif args.command == "cleanup":
        removed = mem.cleanup_old_memories()
        print(f"Removed {removed} old memories")
