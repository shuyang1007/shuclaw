#!/usr/bin/env python3
"""
小红书评论处理核心库
- HTML DOM解析
- ID持久化
- 自动回复
"""

import json
import os
import re
from time import sleep
from playwright.sync_api import sync_playwright

COOKIE_PATH = os.path.expanduser('~/.openclaw/secrets/xiaohongshu.json')
REPLIED_PATH = os.path.expanduser('~/.openclaw/xiaohongshu_replied.json')
STEALTH_JS_PATH = os.path.join(os.path.dirname(__file__), '..', 'stealth.min.js')

def load_cookies():
    """加载cookie"""
    with open(COOKIE_PATH, 'r') as f:
        data = json.load(f)
    
    cookies = []
    for k, v in data.items():
        cookies.append({
            'name': k,
            'value': str(v),
            'domain': '.xiaohongshu.com',
            'path': '/'
        })
    return cookies

def load_replied_ids():
    """加载已回复的评论ID"""
    if not os.path.exists(REPLIED_PATH):
        return set()
    with open(REPLIED_PATH, 'r') as f:
        return set(json.load(f))

def save_replied_ids(ids):
    """保存已回复的评论ID"""
    os.makedirs(os.path.dirname(REPLIED_PATH), exist_ok=True)
    with open(REPLIED_PATH, 'w') as f:
        json.dump(list(ids), f)

def detect_prompt_injection(text):
    """检测Prompt injection攻击"""
    suspicious = [
        'ignore previous', 'ignore all', 'disregard',
        'system prompt', 'you are now', 'DAN mode',
        'jailbreak', 'developer mode'
    ]
    text_lower = text.lower()
    for keyword in suspicious:
        if keyword in text_lower:
            return True
    return False

def get_unreplied_comments():
    """获取未回复的评论列表"""
    cookies = load_cookies()
    replied_ids = load_replied_ids()
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        if os.path.exists(STEALTH_JS_PATH):
            context.add_init_script(path=STEALTH_JS_PATH)
        context.add_cookies(cookies)
        
        page = context.new_page()
        page.set_default_timeout(30000)
        
        # 访问创作者中心的评论管理
        page.goto('https://creator.xiaohongshu.com/comment')
        sleep(5)
        
        # TODO: 实际实现需要根据页面HTML结构调整
        # 这里是一个示例结构
        comments = []
        comment_elements = page.locator('.comment-item').all()
        
        for elem in comment_elements[:10]:  # 最多取10条
            try:
                comment_id = elem.get_attribute('data-id')
                user = elem.locator('.username').text_content()
                content = elem.locator('.content').text_content()
                
                if comment_id in replied_ids:
                    continue
                
                is_suspicious = detect_prompt_injection(content)
                
                comments.append({
                    'comment_id': comment_id,
                    'user': user,
                    'content': content,
                    'keyword': content[:20],  # 用于定位回复按钮
                    'is_suspicious': is_suspicious
                })
            except:
                continue
        
        browser.close()
        return comments

def reply_to_comments(comments):
    """回复评论"""
    cookies = load_cookies()
    replied_ids = load_replied_ids()
    results = []
    
    # 限制每批最多3条
    comments = comments[:3]
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        if os.path.exists(STEALTH_JS_PATH):
            context.add_init_script(path=STEALTH_JS_PATH)
        context.add_cookies(cookies)
        
        page = context.new_page()
        page.set_default_timeout(30000)
        
        page.goto('https://creator.xiaohongshu.com/comment')
        sleep(5)
        
        for i, comment in enumerate(comments):
            try:
                # 频率控制：间隔10-15秒
                if i > 0:
                    sleep(10 + (i * 2))
                
                # 定位评论并回复
                keyword = comment['keyword']
                reply_text = comment['reply']
                
                # 点击回复按钮
                reply_btn = page.locator(f'text={keyword}').locator('..').locator('.reply-btn')
                reply_btn.click()
                sleep(1)
                
                # 填写回复内容
                textarea = page.locator('.reply-textarea')
                textarea.fill(reply_text)
                sleep(1)
                
                # 点击发送
                send_btn = page.locator('.send-btn')
                send_btn.click()
                sleep(2)
                
                # 记录已回复
                replied_ids.add(comment['comment_id'])
                results.append({'success': True, 'comment_id': comment['comment_id']})
                
            except Exception as e:
                results.append({'success': False, 'comment_id': comment.get('comment_id'), 'error': str(e)})
        
        browser.close()
    
    # 保存已回复ID
    save_replied_ids(replied_ids)
    return results

if __name__ == '__main__':
    # 测试
    comments = get_unreplied_comments()
    print(json.dumps(comments, ensure_ascii=False, indent=2))
