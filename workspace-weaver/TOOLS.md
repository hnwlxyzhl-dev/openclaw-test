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

## 📊 16 个技能快速参考（2026-03-30）

### PPT 制作技能（6 个）

| 技能 | 用途 | 触发 | 输出 |
|------|------|------|------|
| **powerpoint-pptx** | 读写 PPTX、布局、模板 | 涉及 `.pptx` | PPTX |
| **ppt-generator** | 乔布斯风竖屏 | 产品发布/主题演讲 | HTML |
| **openclaw-slides** | 12 种风格 | 通用场景 | HTML |
| **slides-cog** | CellCog 深度研究 | 研究报告 | PDF/PPTX |
| **youmind-slides** | 在线编辑协作 | 云端管理 | 在线 |
| **ppt-visual** | 设计规范指导 | 设计指导 | 文档 |

### 搜索技能（2 个）

| 技能 | 用途 | 触发 |
|------|------|------|
| **tavily-search** | Tavily API 搜索 | 搜索/查找/搜索链接 |
| **multi-search-engine** | 17 搜索引擎 | 多引擎搜索 |

### Office 自动化（2 个）

| 技能 | 用途 | 触发 |
|------|------|------|
| **office-automation** | Word/Excel 自动化 | 批量处理/模板填充 |
| **excel-automation** | Excel 实时交互 | Excel 实时操作 |

### 邮件与文档（2 个）

| 技能 | 用途 | 触发 |
|------|------|------|
| **imap-smtp-email** | 邮件收发/搜索 | 检查邮件/发送邮件 |
| **document-skills** | 创建技能文档 | 创建 skill/写 SKILL.md |

### 工作流（2 个）

| 技能 | 用途 | 触发 |
|------|------|------|
| **superpowers** | TDD + 子代理开发 | 构建功能/调试 |
| **superpowers-cn** | 中文工作流 | 开发/写代码 |

### 自我改进（1 个）

| 技能 | 用途 | 触发 |
|------|------|------|
| **self-improvement** | 持续优化能力 | 自我改进 |

---

## 🔧 技能目录位置

```
/home/admin/.openclaw/workspace-weaver/skills/
├── powerpoint-pptx/
├── ppt-generator/
├── openclaw-slides/
├── slides-cog/
├── youmind-slides-generator/
├── ppt-visual/
├── tavily-search/
├── multi-search-engine/
├── office-automation/
├── excel-automation/
├── imap-smtp-email/
├── document-skills/
├── superpowers/
├── superpowers-cn/
└── self-improvement/
```

---

## 📋 PPT 技能选择指南

**需要 .pptx 文件：**
→ `powerpoint-pptx` + `ppt-visual`

**需要 HTML 演示：**
→ `ppt-generator`（竖屏）/ `openclaw-slides`（横屏）

**需要深度研究：**
→ `slides-cog`

**需要协作编辑：**
→ `youmind-slides-generator`

---

## 🔍 搜索技能选择指南

**需要快速搜索：**
→ `tavily-search`

**需要多引擎对比：**
→ `multi-search-engine`（百度/Bing/Google/DuckDuckGo 等）

---

## 📧 邮件技能使用

```bash
# 检查邮件
node skills/imap-smtp-email/scripts/imap.js check --limit 10

# 发送邮件
node skills/imap-smtp-email/scripts/smtp.js send \
  --to recipient@example.com \
  --subject "主题" \
  --body "内容"
```

---

Add whatever helps you do your job. This is your cheat sheet.
