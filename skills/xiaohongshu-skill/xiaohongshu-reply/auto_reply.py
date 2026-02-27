#!/usr/bin/env python3
"""
小红书评论自动回复 - 两阶段入口
scan: 扫描未回复评论
reply: 执行回复
"""

import json
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

def scan_comments():
    """扫描未回复评论"""
    from get_unreplied import get_unreplied_comments
    comments = get_unreplied_comments()
    print(json.dumps(comments, ensure_ascii=False, indent=2))
    return comments

def reply_comments(comments_json):
    """执行回复"""
    from get_unreplied import reply_to_comments
    comments = json.loads(comments_json)
    result = reply_to_comments(comments)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 auto_reply.py scan")
        print("       python3 auto_reply.py reply '[{...}]'")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'scan':
        scan_comments()
    elif command == 'reply':
        if len(sys.argv) < 3:
            print("Error: reply command needs JSON argument")
            sys.exit(1)
        reply_comments(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
