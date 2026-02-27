#!/usr/bin/env python3
"""
小红书Cookie自动获取工具
扫码登录后自动保存cookie
"""

import json
import os
from time import sleep
from playwright.sync_api import sync_playwright

COOKIE_PATH = os.path.expanduser('~/.openclaw/secrets/xiaohongshu.json')
STEALTH_JS_PATH = os.path.join(os.path.dirname(__file__), '..', 'stealth.min.js')

def get_cookie():
    """获取cookie并保存"""
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)  # 显示窗口以便扫码
        context = browser.new_context()
        if os.path.exists(STEALTH_JS_PATH):
            context.add_init_script(path=STEALTH_JS_PATH)
        
        page = context.new_page()
        
        print('🌐 打开小红书登录页面...')
        page.goto('https://www.xiaohongshu.com')
        
        print('⏳ 请扫码登录，登录完成后按回车继续...')
        input('登录完成后按回车...')
        
        # 访问创作者中心获取完整cookie
        print('🌐 访问创作者中心...')
        page.goto('https://creator.xiaohongshu.com')
        sleep(3)
        
        # 获取所有cookie
        cookies = context.cookies()
        cookie_dict = {}
        
        for cookie in cookies:
            if 'xiaohongshu.com' in cookie.get('domain', ''):
                cookie_dict[cookie['name']] = cookie['value']
        
        # 保存
        os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
        with open(COOKIE_PATH, 'w') as f:
            json.dump(cookie_dict, f, indent=2)
        
        print(f'✅ Cookie已保存到: {COOKIE_PATH}')
        print(f'📋 包含字段: {list(cookie_dict.keys())}')
        
        browser.close()

if __name__ == '__main__':
    get_cookie()
