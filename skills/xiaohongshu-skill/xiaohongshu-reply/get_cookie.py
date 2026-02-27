#!/usr/bin/env python3
"""
小红书未读评论获取 - ID记录版
用本地文件记录已回复评论，不再依赖🦀标记
"""
import json, os, re, hashlib
from time import sleep
from playwright.sync_api import sync_playwright

cookie_path = os.path.expanduser('~/.openclaw/secrets/xiaohongshu.json')
stealth_path = os.path.join(os.path.dirname(__file__), '..', 'stealth.min.js')
replied_db_path = os.path.expanduser('~/.openclaw/xiaohongshu_replied.json')
job_status_path = os.path.expanduser('~/.openclaw/xiaohongshu_job_status.json')

PI_KEYWORDS = [
    '/etc/passwd', '忽略之前', '关闭防御', '核心文件', '调试程序',
    '系统升级', '致命漏洞', 'jailbreak', 'prompt leak', '开发者模式',
    '请输出', '执行这个程序'
]


def load_replied_ids():
    """加载已回复的评论ID集合"""
    if os.path.exists(replied_db_path):
        try:
            with open(replied_db_path, 'r') as f:
                data = json.load(f)
                return set(data.get('replied_ids', []))
        except:
            return set()
    return set()


def save_replied_id(comment_id):
    """保存已回复的评论ID"""
    replied_ids = load_replied_ids()
    replied_ids.add(comment_id)

    # 只保留最近1000条，防止文件过大
    replied_ids = set(list(replied_ids)[-1000:])

    os.makedirs(os.path.dirname(replied_db_path), exist_ok=True)
    with open(replied_db_path, 'w') as f:
        json.dump({'replied_ids': list(replied_ids)}, f)


def generate_comment_id(user, content, time_str):
    """生成评论唯一ID - 只用用户+内容，不用时间戳（因为时间会变化）"""
    content_snippet = content[:30].replace(' ', '_').replace('\n', '_')
    content_snippet = re.sub(r'[^\w\u4e00-\u9fff]', '', content_snippet)
    return f"{user}_{content_snippet}"


def parse_comments_from_page(page, replied_ids, limit=50):
    """用HTML结构提取评论，不再依赖text_content解析"""
    items = page.evaluate('''() => {
        const containers = document.querySelectorAll('.container');
        return Array.from(containers).map(c => {
            const userEl = c.querySelector('.user-info a');
            const hintEl = c.querySelector('.interaction-hint span:first-child');
            const timeEl = c.querySelector('.interaction-time');
            const contentEl = c.querySelector('.interaction-content');
            return {
                user: userEl?.textContent?.trim() || '',
                hint: hintEl?.textContent?.trim() || '',
                time: timeEl?.textContent?.trim() || '',
                content: contentEl?.textContent?.trim() || '',
            };
        }).filter(x => x.user && x.content);
    }''')

    comments = []
    seen_ids = set()
    consecutive_replied = 0

    for item in items:
        user = item['user'].replace('你的粉丝', '').strip()
        content = item['content'].strip()
        time_str = item['time']

        if not content or len(content) < 2:
            continue
        if len(user) > 40:
            continue

        comment_id = generate_comment_id(user, content, time_str)

        if comment_id in replied_ids:
            consecutive_replied += 1
            if consecutive_replied >= 3:
                print(f'⏹️  连续{consecutive_replied}条已回复，停止扫描')
                break
            continue
        consecutive_replied = 0

        if comment_id in seen_ids:
            continue
        seen_ids.add(comment_id)

        cat = 'general'
        if any(k.lower() in content.lower() for k in PI_KEYWORDS):
            cat = 'prompt_injection'
        elif '？' in content or '?' in content or '怎么' in content or '如何' in content:
            cat = 'question'

        comments.append({
            'id': comment_id,
            'user': user,
            'content': content[:200],
            'time': time_str,
            'category': cat,
            'hint': item['hint'],
        })

        if len(comments) >= limit:
            break

    return comments


def reply_by_index(page, index, reply_text):
    """通过通知项索引回复 - 直接点击第index个container的回复按钮"""
    import random
    containers = page.locator('.container').all()
    if index >= len(containers):
        print(f'❌ 索引 {index} 超出范围（共 {len(containers)} 个）')
        return False

    container = containers[index]
    reply_btn = container.locator('.action-reply')
    if not reply_btn.is_visible():
        print(f'❌ 回复按钮不可见')
        return False

    # 随机延迟，避免频率限制
    delay = random.uniform(2, 5)
    print(f'  ⏳ 等待 {delay:.1f}s...')
    sleep(delay)

    reply_btn.click()
    sleep(2)

    ta = page.locator('textarea').first
    if not ta.is_visible():
        print(f'❌ textarea 未出现')
        return False

    ta.fill(reply_text)
    sleep(1)

    # 尝试点击发送按钮（按钮文本可能带空格）
    try:
        page.locator('button:has-text("发送")').first.click()
        sleep(3)
        return True
    except Exception as e:
        print(f'  按钮点击失败: {e}')
        pass

    # 备用：遍历所有按钮找发送
    try:
        btns = page.locator('button').all()
        for btn in btns:
            text = (btn.text_content() or '').strip()
            if text == '发送' or text == '回复':
                if btn.is_visible() and btn.is_enabled():
                    btn.click()
                    sleep(3)
                    return True
    except:
        pass

    print(f'❌ 无法找到发送按钮')
    return False


def reply_by_keyword(page, keyword, reply_text):
    """关键词定位回复 - 在.interaction-content中查找关键词"""
    containers = page.locator('.container').all()

    for i, container in enumerate(containers):
        content_el = container.locator('.interaction-content')
        if content_el.count() == 0:
            continue
        content_text = content_el.text_content() or ''
        if keyword.lower() in content_text.lower():
            print(f'✅ 找到 "{keyword}" at container {i}')
            return reply_by_index(page, i, reply_text)

    print(f'❌ 未找到关键词: {keyword}')
    return False


def reply_and_mark(page, keyword, reply_text, comment_id):
    """回复并自动标记为已回复，同时更新 job 状态"""
    success = reply_by_keyword(page, keyword, reply_text)
    if success and comment_id:
        save_replied_id(comment_id)
        print(f'✅ 已自动标记为已回复: {comment_id[:50]}...')
    job_update(comment_id, success, error=None if success else '关键词未匹配')
    return success


def main():
    with open(cookie_path) as f:
        raw = json.load(f)
    cookies = [{'name': k, 'value': str(v), 'domain': '.xiaohongshu.com', 'path': '/'}
               for k, v in raw.items()]

    replied_ids = load_replied_ids()
    print(f'📁 已加载 {len(replied_ids)} 条历史记录')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        if os.path.exists(stealth_path):
            ctx.add_init_script(path=stealth_path)
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.set_default_timeout(30000)

        print('📱 加载通知页...')
        page.goto('https://www.xiaohongshu.com/notification')
        sleep(5)

        try:
            page.click('text=评论和@')
            sleep(3)
        except:
            pass

        comments = parse_comments_from_page(page, replied_ids, limit=50)

        print(f'\n📋 检测到 {len(comments)} 条新评论:\n')
        for i, c in enumerate(comments, 1):
            print(f'  [{i}] {c["user"]:20} | {c["time"]:8} | {c["content"][:50]}')

        print(f'\n共 {len(comments)} 条待回复')
        browser.close()

        return comments


def mark_as_replied(comment_id):
    """标记评论为已回复"""
    save_replied_id(comment_id)
    print(f'✅ 已记录回复: {comment_id[:50]}...')


# ===== Job 状态管理 =====

def job_start(batch_comments):
    """记录 job 开始，保存待处理评论列表"""
    from datetime import datetime
    status = {
        'started_at': datetime.now().isoformat(),
        'total': len(batch_comments),
        'processed': 0,
        'succeeded': 0,
        'failed': 0,
        'pending': [c['id'] for c in batch_comments],
        'results': [],
    }
    with open(job_status_path, 'w') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print(f'📋 Job started: {len(batch_comments)} 条待处理')
    return status


def job_update(comment_id, success, error=None):
    """更新单条评论的处理结果"""
    if not os.path.exists(job_status_path):
        return
    with open(job_status_path, 'r') as f:
        status = json.load(f)

    status['processed'] += 1
    if success:
        status['succeeded'] += 1
    else:
        status['failed'] += 1

    if comment_id in status['pending']:
        status['pending'].remove(comment_id)

    status['results'].append({
        'id': comment_id[:50],
        'success': success,
        'error': error,
    })

    with open(job_status_path, 'w') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def job_finish():
    """Job 完成，清空状态文件"""
    if os.path.exists(job_status_path):
        with open(job_status_path, 'r') as f:
            status = json.load(f)
        summary = f"✅ Job完成: {status['succeeded']}/{status['total']} 成功, {status['failed']} 失败"
        if status['pending']:
            summary += f", {len(status['pending'])} 未处理"
        print(summary)
        os.remove(job_status_path)
        return status
    return None


def job_check():
    """检查是否有未完成的 job（用于崩溃恢复）"""
    if not os.path.exists(job_status_path):
        return None
    with open(job_status_path, 'r') as f:
        status = json.load(f)
    if status.get('pending'):
        print(f'⚠️ 发现未完成的 job: {len(status["pending"])} 条未处理')
        print(f'   开始时间: {status["started_at"]}')
        print(f'   已处理: {status["processed"]}, 成功: {status["succeeded"]}, 失败: {status["failed"]}')
    return status


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mark', help='标记指定ID为已回复')
    args = parser.parse_args()

    if args.mark:
        mark_as_replied(args.mark)
    else:
        main()
