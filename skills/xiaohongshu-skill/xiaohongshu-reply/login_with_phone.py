#!/usr/bin/env python3
"""
小红书短信验证码登录
使用手机号获取验证码登录创作者中心
"""

import json
import os
from time import sleep
from playwright.sync_api import sync_playwright

COOKIE_PATH = os.path.expanduser('~/.openclaw/secrets/xiaohongshu.json')
STEALTH_JS_PATH = os.path.join(os.path.dirname(__file__), '..', 'stealth.min.js')

def login_with_phone(phone_number):
    """使用手机号+验证码登录"""
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        if os.path.exists(STEALTH_JS_PATH):
            context.add_init_script(path=STEALTH_JS_PATH)
        
        page = context.new_page()
        page.set_default_timeout(30000)
        
        print('🌐 打开创作者中心登录页...')
        page.goto('https://creator.xiaohongshu.com/login', timeout=60000)
        sleep(3)
        
        print(f'📱 输入手机号: {phone_number}')
        # 找到手机号输入框并填写
        phone_input = page.locator('input[placeholder="手机号"]').first
        phone_input.click()
        phone_input.fill(phone_number)
        sleep(1)
        
        print('🔢 点击发送验证码...')
        send_btn = page.locator('text=发送验证码').first
        send_btn.click()
        
        print('\\n' + '='*50)
        print('⏳ 请查看手机短信，收到验证码后发给我')
        print('='*50 + '\\n')
        
        code = input('请输入验证码: ').strip()
        
        if not code:
            print('❌ 未输入验证码，退出')
            browser.close()
            return
        
        print('🔐 输入验证码...')
        code_input = page.locator('input[placeholder="验证码"]').first
        code_input.fill(code)
        sleep(1)
        
        print('🚀 点击登录...')
        login_btn = page.locator('button:has-text("登录")').first
        login_btn.click()
        
        sleep(8)  # 等待登录完成
        
        # 检查是否登录成功
        current_url = page.url
        print(f'当前URL: {current_url}')
        
        if 'login' in current_url:
            print('❌ 登录可能失败，仍在登录页')
            browser.close()
            return
        
        # 登录成功后访问创作者中心发布页获取完整cookie
        print('🌐 访问创作者中心发布页...')
        page.goto('https://creator.xiaohongshu.com/publish/publish', timeout=60000)
        sleep(5)
        
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
        
        print(f'\\n✅ Cookie已保存到: {COOKIE_PATH}')
        print(f'📋 包含字段数: {len(cookie_dict)}')
        print(f'📋 字段列表: {sorted(cookie_dict.keys())}')
        
        browser.close()
        print('\\n🎉 登录完成！')

if __name__ == '__main__':
    import sys
    phone = sys.argv[1] if len(sys.argv) > 1 else '13120502967'
    login_with_phone(phone)
