# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## 时区设置

- **默认时区**: 北京时间 (Asia/Shanghai, UTC+8)
- 所有时间显示、定时任务、日志记录均使用北京时间
- 用户本地时间为美西时间，但要求我统一使用北京时间

## GitHub 代码仓库

- **仓库**: https://github.com/shuyang1007/shuclaw
- **Token 路径**: `~/.openclaw/secrets/github-token.txt`
- **默认分支**: main
- 所有代码自动推送到此仓库
