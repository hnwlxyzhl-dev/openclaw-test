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

### ClawHub
- Token: `clh_HFznCaeYn_jRaRsGe3yA4R3VCeeONDgO-9E09vJVwx0`
- 用途：从 clawhub.com 下载 skills

### 网页搜索工具优先级

1. **Tavily Search（首选）**
   - Skill: `openclaw-tavily-search`
   - API Key 已配置在 `~/.openclaw/.env`
   - 用法: `tavily_search` tool 或 `python3 skills/openclaw-tavily-search/scripts/tavily_search.py --query "..." --format md`

2. **Multi Search Engine（备选）**
   - Skill: `multi-search-engine`
   - 17 个搜索引擎，无需 API Key
   - 当 Tavily 搜索无结果时使用
   - 国内: Baidu, Bing CN, 360, Sogou, WeChat, Toutiao, 集思录
   - 国际: Google, DuckDuckGo, Yahoo, Startpage, Brave, Ecosia, Qwant, WolframAlpha
   - 用法: `web_fetch` + 搜索引擎 URL

3. **Brave Search（兜底）**
   - 用法: `web_search` tool
   - 需要 `BRAVE_API_KEY`

---

Add whatever helps you do your job. This is your cheat sheet.
