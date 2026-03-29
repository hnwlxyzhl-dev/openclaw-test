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

## 🔍 Web Search Priority

当需要搜索网页时，按以下优先级使用工具：

1. **Tavily Search** (首选) - `tavily_search`
   - API Key 已配置在 `~/.openclaw/.env`
   - 支持 search、extract、crawl、map、research
   - 返回结构化结果 + 可选 AI 摘要

2. **Multi Search Engine** (备选) - 使用 `web_fetch` 直接访问搜索引擎
   - 无需 API Key
   - 支持 17 个搜索引擎（百度、Bing、Google、DuckDuckGo 等）
   - 当 Tavily 没找到结果时使用

### Multi Search Engine 快速参考

```javascript
// 国内搜索
web_fetch({url: "https://www.baidu.com/s?wd=关键词"})
web_fetch({url: "https://cn.bing.com/search?q=关键词"})

// 国际搜索
web_fetch({url: "https://www.google.com/search?q=keyword"})
web_fetch({url: "https://duckduckgo.com/html/?q=keyword"})

// 高级搜索
web_fetch({url: "https://www.google.com/search?q=site:github.com+react"})
web_fetch({url: "https://www.google.com/search?q=AI&tbs=qdr:w"}) // 过去一周
```

---

Add whatever helps you do your job. This is your cheat sheet.
