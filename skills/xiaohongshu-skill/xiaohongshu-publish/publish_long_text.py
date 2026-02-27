#!/usr/bin/env python3
"""
小红书长文发布脚本
使用playwright通过创作者中心发布长文笔记
"""

import json
import os
import argparse
from time import sleep
from playwright.sync_api import sync_playwright

# ========== 配置 ==========
COOKIE_PATH = os.path.expanduser("~/.openclaw/secrets/xiaohongshu.json")
# 使用相对路径找到 stealth.min.js
STEALTH_JS_PATH = os.path.join(os.path.dirname(__file__), '..', 'stealth.min.js')

def load_cookies():
    """加载cookie配置"""
    with open(COOKIE_PATH, 'r') as f:
        raw = json.load(f)
    # Cookie文件是dict格式，需要转换为playwright格式
    return [{'name': k, 'value': str(v), 'domain': '.xiaohongshu.com', 'path': '/'} for k, v in raw.items()]

def publish_long_text(title, content, headless=True):
    """
    发布小红书长文
    
    Args:
        title: 标题（不超过20字！）
        content: 正文内容
        headless: 是否无头模式
    
    Returns:
        bool: 是否成功
    """
    # 检查标题长度
    if len(title) > 20:
        print(f"⚠️ 标题超过20字，将被截断: {title[:20]}...")
        title = title[:20]
    
    cookies = load_cookies()
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        
        # 加载 stealth.min.js（必须加载，不然容易被反爬检测拦）
        if os.path.exists(STEALTH_JS_PATH):
            print(f'🛡️ 加载stealth脚本: {STEALTH_JS_PATH}')
            context.add_init_script(path=STEALTH_JS_PATH)
        else:
            print(f'⚠️ 未找到stealth脚本: {STEALTH_JS_PATH}')
        
        context.add_cookies(cookies)
        page = context.new_page()
        page.set_default_timeout(60000)
        
        try:
            # 1. 访问创作者中心
            print('🔍 访问创作者中心...')
            page.goto('https://creator.xiaohongshu.com/publish/publish')
            sleep(3)
            
            # 2. 点击"写长文"标签（关键！默认是图文/视频页）
            print('📝 点击写长文...')
            page.click('text=写长文')
            sleep(2)
            
            # 3. 点击"新的创作"
            print('📝 点击新的创作...')
            page.click('text=新的创作')
            sleep(4)  # 编辑器加载慢，必须等
            
            # 4. 填写标题（是textarea，不是input）
            print('📝 填写标题...')
            page.fill('textarea[placeholder="输入标题"]', title)
            
            # 5. 填写正文（是contenteditable div）
            print('📝 填写正文...')
            editor = page.locator('[contenteditable="true"]').first
            editor.click()
            editor.fill(content)
            sleep(2)
            
            # 6. 一键排版
            print('🎨 一键排版...')
            page.click('text=一键排版')
            sleep(5)  # 增加等待时间
            
            # 7. 下一步
            print('➡️ 下一步...')
            
            # 等待下一步按钮可用
            print('  等待下一步按钮可用...')
            max_retries = 10
            for i in range(max_retries):
                try:
                    # 尝试查找并点击下一步按钮
                    next_btn = page.locator('button:has-text("下一步")').first
                    if next_btn.is_visible() and next_btn.is_enabled():
                        print('  下一步按钮可用，点击')
                        next_btn.click()
                        break
                    else:
                        print(f'  按钮不可用，等待... ({i+1}/{max_retries})')
                        sleep(2)
                except Exception as e:
                    print(f'  等待中... ({i+1}/{max_retries}): {e}')
                    sleep(2)
            
            # 等待页面跳转和图片生成
            print('⏳ 等待页面跳转和图片生成...')
            sleep(15)
            
            # 8. 发布
            print('🚀 发布...')
            page.locator('button:has-text("发布")').last.click()
            
            # 发布后多等15-20秒再判断
            print('⏳ 等待发布完成（20秒）...')
            sleep(20)
            
            # 检查成功
            url = page.url
            # 成功判断：URL含published=true，或跳回首页(tab_switch)
            success = 'published=true' in url or 'tab_switch' in url
            
            browser.close()
            
            if success:
                print(f'🎉 发布成功！URL: {url}')
            else:
                print(f'⚠️ 发布结果不确定，URL: {url}')
            
            return success
            
        except Exception as e:
            print(f'❌ 发布失败: {e}')
            browser.close()
            return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='发布小红书长文')
    parser.add_argument('--title', required=True, help='标题（不超过20字）')
    parser.add_argument('--content', required=True, help='正文内容')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口（调试用）')
    
    args = parser.parse_args()
    publish_long_text(args.title, args.content, headless=not args.visible)
