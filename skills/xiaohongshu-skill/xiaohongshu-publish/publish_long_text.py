#!/usr/bin/env python3
"""
小红书长文发布脚本 - 使用playwright通过创作者中心发布
"""
import json, argparse, os
from time import sleep
from playwright.sync_api import sync_playwright

# ========== 配置 ==========
COOKIE_PATH = os.path.expanduser("~/.openclaw/secrets/xiaohongshu.json")
STEALTH_JS_PATH = os.path.expanduser("~/.openclaw/workspace/skills/xiaohongshu-skill/stealth.min.js")

def load_cookies():
    with open(COOKIE_PATH, 'r') as f:
        raw = json.load(f)
    return [{'name': k, 'value': str(v), 'domain': '.xiaohongshu.com', 'path': '/'} for k, v in raw.items()]

def publish_long_text(title, content, headless=True):
    if len(title) > 20:
        print(f"⚠️ 标题超20字，截断: {title[:20]}...")
        title = title[:20]
    
    cookies = load_cookies()
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context()
        if os.path.exists(STEALTH_JS_PATH):
            ctx.add_init_script(path=STEALTH_JS_PATH)
        ctx.add_cookies(cookies)
        
        page = ctx.new_page()
        page.set_default_timeout(60000)
        
        try:
            # 1. 打开创作者中心
            print('🔍 访问创作者中心...')
            page.goto('https://creator.xiaohongshu.com/publish/publish')
            sleep(3)
            
            # 2. 切到"写长文"（关键！默认是图文/视频页）
            print('📝 切到写长文...')
            page.click('text=写长文')
            sleep(2)
            
            # 3. 点击"新的创作"
            print('📝 点击新的创作...')
            page.click('text=新的创作')
            sleep(4)  # 编辑器加载慢，必须等
            
            # 4. 填标题（是textarea，不是input）
            print('📝 填写标题...')
            page.fill('textarea[placeholder="输入标题"]', title)
            
            # 5. 填正文（是contenteditable div，不是textarea）
            print('📝 填写正文...')
            editor = page.locator('[contenteditable="true"]').first
            editor.click()
            editor.fill(content)
            sleep(2)
            
            # 6. 一键排版
            print('🎨 一键排版...')
            page.click('text=一键排版')
            sleep(3)
            
            # 7. 下一步
            print('➡️ 下一步...')
            page.click('button:has-text("下一步")')
            sleep(8)  # 等图片生成
            
            # 8. 发布
            print('🚀 发布...')
            page.locator('button:has-text("发布")').last.click()
            sleep(15)  # 多等一会，不要急
            
            url = page.url
            # 成功判断：URL含published=true，或跳回首页(tab_switch)
            success = 'published=true' in url or 'tab_switch' in url
            
            browser.close()
            print(f'{"🎉 发布成功！" if success else "❌ 可能失败"} URL: {url}')
            return success
            
        except Exception as e:
            browser.close()
            print(f'❌ 出错: {e}')
            return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', required=True, help='标题（≤20字）')
    parser.add_argument('--content', required=True, help='正文')
    parser.add_argument('--visible', action='store_true', help='显示浏览器（调试用）')
    args = parser.parse_args()
    publish_long_text(args.title, args.content, headless=not args.visible)
