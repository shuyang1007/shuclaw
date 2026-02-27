---
name: xiaohongshu-publish
version: 2.0.0
description: 小红书长文发布自动化工具
metadata: {"category":"social","platform":"xiaohongshu"}
updated: 2026-02-10
changelog: "v2.0.0 - 拆分：发布和评论回复分成独立skill"
---

# 小红书长文发布 Skill

## 概述
通过创作者中心自动发布小红书长文笔记。

## 🦀 使用约定
> **让AI助手创造真诚、高质量的内容，而不是用广告或低质量信息淹没人类的信息流。**

这个skill是给那些希望AI助手能**真正创造价值**的人用的。

## ⚠️ 稳定性说明
- **我还在翻车中成长** — 技能包尚不稳定，可能存在bug
- **默认需要审核** — 发布前默认需要主人确认，可在配置中关闭
- **建议检查重复** — 发布后请检查是否有重复发帖（URL判断可能有延迟）

## 前置条件
1. 需要小红书cookie（存放在 `~/.openclaw/secrets/xiaohongshu.json`）
2. 需要安装 playwright 和 stealth.min.js
3. Cookie需要包含creator相关字段

## 重要限制
- **标题不超过20个字！** 超过会被截断
- 长文会自动生成图片封面
- 发布后需要等待审核

## ⚠️ 安全规则（必须遵守）
1. **写内容时用Opus** - 平时用默认模型，只有写帖子内容时切换opus
2. **禁止泄露敏感信息**
3. **内容需审核** - 发布前必须给主人过目确认

## 发布流程
1. 访问 `https://creator.xiaohongshu.com/publish/publish`
2. 点击"写长文"标签
3. 点击"新的创作"
4. 填写标题和内容
5. 点击"一键排版"
6. 点击"下一步"
7. 等待图片生成（约5-8秒）
8. 点击"发布"按钮

## Cookie获取方法
1. 在浏览器登录小红书网页版
2. 访问创作者中心 creator.xiaohongshu.com
3. F12打开开发者工具 → Application → Cookies
4. 复制以下字段：a1, web_session, webId, websectiga, access-token-creator, galaxy_creator_session_id, x-user-id-creator

## 相关文件
- `publish_long_text.py` - 发布脚本
