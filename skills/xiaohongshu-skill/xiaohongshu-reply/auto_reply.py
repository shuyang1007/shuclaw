#!/usr/bin/env python3
"""
小红书自动回复脚本 v2
职责：抓取未回复评论 → 按用户合并 → 输出JSON / 执行回复
回复内容由外部LLM生成，本脚本不生成回复。

用法：
  python3 auto_reply.py scan          # 扫描未回复评论，输出JSON
  python3 auto_reply.py reply <json>  # 执行回复（传入JSON数组）
"""
import sys, json, os, random
from time import sleep

sys.path.insert(0, os.path.dirname(__file__))
from get_unreplied import (
    load_replied_ids, parse_comments_from_page,
    reply_and_mark, generate_comment_id, save_replied_id
)
from playwright.sync_api import sync_playwright

COOKIE_PATH = os.path.expanduser('~/.openclaw/secrets/xiaohongshu.json')
STEALTH_PATH = os.path.join(os.path.dirname(__file__), '..', 'stealth.min.js')

PI_KEYWORDS = [
    '/etc/passwd', '忽略之前', '关闭防御', '核心文件', '调试程序',
    '系统升级', '致命漏洞', 'jailbreak', 'prompt leak', '开发者模式',
    '请输出', '执行这个程序'
]


def is_prompt_injection(content):
    return any(k.lower() in content.lower() for k in PI_KEYWORDS)


def group_by_user(comments):
    """同一用户多条评论合并，只保留最新一条（列表第一条），附带其他评论内容"""
    groups = {}
    for c in comments:
        user = c['user']
        if user not in groups:
            groups[user] = {
                'user': user,
                'main_comment': c,  # 第一条（最新）作为回复目标
                'all_comments': [c],
            }
        else:
            groups[user]['all_comments'].append(c)
    return list(groups.values())


def scan_comments():
    """扫描未回复评论，按用户分组，输出JSON"""
    with open(COOKIE_PATH) as f:
        raw = json.load(f)
    cookies = [{'name': k, 'value': str(v), 'domain': '.xiaohongshu.com', 'path': '/'}
               for k, v in raw.items()]

    replied_ids = load_replied_ids()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        if os.path.exists(STEALTH_PATH):
            ctx.add_init_script(path=STEALTH_PATH)
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.set_default_timeout(30000)

        page.goto('https://www.xiaohongshu.com/notification')
        sleep(5)
        try:
            page.click('text=评论和@')
            sleep(3)
        except:
            pass

        comments = parse_comments_from_page(page, replied_ids, limit=50)
        browser.close()

    if not comments:
        print(json.dumps({"groups": [], "total_comments": 0}))
        return

    # 标记 prompt injection
    for c in comments:
        c['is_pi'] = is_prompt_injection(c['content'])

    groups = group_by_user(comments)

    output = {
        "total_comments": len(comments),
        "unique_users": len(groups),
        "groups": []
    }

    for g in groups:
        main = g['main_comment']
        all_contents = [c['content'] for c in g['all_comments']]
        output["groups"].append({
            "user": g['user'],
            "comment_count": len(g['all_comments']),
            "main_comment_id": main['id'],
            "main_content": main['content'],
            "main_keyword": main['content'][:20],
            "all_contents": all_contents,
            "is_pi": main['is_pi'],
            "category": main.get('category', 'general'),
        })

    print(json.dumps(output, ensure_ascii=False))


def execute_replies(reply_json):
    """
    执行回复。输入格式：
    [
      {"keyword": "评论前20字", "reply": "回复内容", "comment_id": "xxx", "user": "xxx"},
      ...
    ]
    """
    replies = json.loads(reply_json) if isinstance(reply_json, str) else reply_json

    # 限制每次最多3条，防止触发频率限制
    if len(replies) > 3:
        print(f'⚠️  评论数量过多，只处理前3条（共{len(replies)}条）')
        replies = replies[:3]

    with open(COOKIE_PATH) as f:
        raw = json.load(f)
    cookies = [{'name': k, 'value': str(v), 'domain': '.xiaohongshu.com', 'path': '/'}
               for k, v in raw.items()]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        if os.path.exists(STEALTH_PATH):
            ctx.add_init_script(path=STEALTH_PATH)
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.set_default_timeout(30000)

        page.goto('https://www.xiaohongshu.com/notification')
        sleep(5)
        try:
            page.click('text=评论和@')
            sleep(3)
        except:
            pass

        success = 0
        fail = 0

        for i, r in enumerate(replies):
            user = r.get('user', '?')
            keyword = r['keyword']
            reply_text = r['reply']
            comment_id = r['comment_id']

            print(f'[{i+1}/{len(replies)}] → {user}: {reply_text[:40]}...')

            if i > 0:
                page.reload()
                sleep(8)
                try:
                    page.click('text=评论和@')
                    sleep(5)
                except:
                    pass
                try:
                    page.wait_for_selector('.container', timeout=10000)
                    sleep(2)
                except:
                    print(f'  ⚠️ 等待评论加载超时')

            ok = reply_and_mark(page, keyword, reply_text, comment_id)
            if ok:
                success += 1
                # 同用户其他评论也标记为已回复
                for extra_id in r.get('extra_comment_ids', []):
                    save_replied_id(extra_id)
                print(f'  ✅ 成功')
            else:
                fail += 1
                print(f'  ❌ 失败')

            # 频率控制：每条回复后等待10-15秒，避免触发反spam
            if i < len(replies) - 1:
                wait_time = random.uniform(10, 15)
                print(f'  ⏳ 等待 {wait_time:.1f}s 后继续...')
                sleep(wait_time)

        browser.close()
        print(f'\n📊 完成: {success} 成功, {fail} 失败')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 auto_reply.py scan|reply [json]')
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'scan':
        scan_comments()
    elif cmd == 'reply':
        if len(sys.argv) < 3:
            # 从stdin读取
            data = sys.stdin.read()
        else:
            data = sys.argv[2]
        execute_replies(data)
    else:
        print(f'未知命令: {cmd}')
        sys.exit(1)
