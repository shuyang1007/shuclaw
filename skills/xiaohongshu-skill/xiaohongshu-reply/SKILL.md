---
name: xiaohongshu-reply
version: 2.0.0
description: 小红书评论自动回复工具
metadata: {"category":"social","platform":"xiaohongshu"}
updated: 2026-02-17
changelog: "v2.0.0 - 完全重构：HTML DOM解析、ID持久化、两阶段架构"
---

# 小红书评论回复 Skill v2.0

## 概述
自动扫描和回复小红书笔记评论，支持防重复回复和Prompt injection检测。

## 🦀 使用约定
> **让AI助手创造真诚、高质量的内容...**

## 核心特性
- HTML DOM结构解析评论
- 已回复ID持久化
- Prompt injection自动检测
- 频率控制（每批最多3条，间隔10-15秒）
- 崩溃恢复机制

## 两阶段架构

### scan 阶段
```bash
python3 auto_reply.py scan
```n输出JSON格式的未回复评论列表

### reply 阶段
```bash
python3 auto_reply.py reply '[{"keyword":"...","reply":"..."}]'
```
执行回复操作

## 相关文件
- `auto_reply.py` - 主入口
- `get_unreplied.py` - 评论解析库
- `get_cookie.py` - Cookie获取工具
