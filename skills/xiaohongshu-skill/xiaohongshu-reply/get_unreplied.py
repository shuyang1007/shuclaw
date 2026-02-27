#!/usr/bin/env python3
"""
小红书登录获取 Cookie 工具
运行此脚本会打开浏览器，登录后自动保存 cookie
"""

import asyncio
import json
import os
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("请先安装 playwright: pip install playwright")
    exit(1)


async def get_cookie():
    """打开浏览器让用户登录，获取 cookie"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # 注入 stealth.min.js 绕过检测（项目内置）
        stealth_js = Path(__file__).parent.parent / "stealth.min.js"
        if stealth_js.exists():
            await context.add_init_script(path=str(stealth_js))
            print("✅ 已加载 stealth.min.js")

        page = await context.new_page()

        print("\n🦀 小红书登录助手")
        print("=" * 40)
        print("1. 浏览器将打开小红书登录页面")
        print("2. 请使用手机扫码或账号密码登录")
        print("3. 登录成功后，按 Enter 键继续")
        print("=" * 40)

        await page.goto("https://www.xiaohongshu.com")

        input("\n✨ 登录完成后，按 Enter 键保存 cookie...")

        cookies = await context.cookies()

        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        cookie_dict = {c['name']: c['value'] for c in cookies}

        required = ['a1', 'web_session', 'webId']
        missing = [r for r in required if r not in cookie_dict]

        if missing:
            print(f"\n⚠️ 缺少必需字段: {missing}")
            print("请确保已完全登录")
        else:
            print("\n✅ 所有必需字段已获取!")

        secrets_dir = Path.home() / ".openclaw" / "secrets"
        secrets_dir.mkdir(parents=True, exist_ok=True)

        cookie_file = secrets_dir / "xiaohongshu.json"

        save_data = {
            "cookie": cookie_str,
            "a1": cookie_dict.get('a1', ''),
            "web_session": cookie_dict.get('web_session', ''),
            "webId": cookie_dict.get('webId', ''),
            "updated_at": str(asyncio.get_event_loop().time())
        }

        with open(cookie_file, 'w') as f:
            json.dump(save_data, f, indent=2)

        print(f"\n💾 Cookie 已保存到: {cookie_file}")

        await browser.close()

        return save_data


if __name__ == "__main__":
    asyncio.run(get_cookie())
