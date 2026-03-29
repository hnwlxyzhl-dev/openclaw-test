# OpenClaw Skills 技能系统指南

> Evolver 整理的 Skills 知识

---

## 1. Skills 概述

Skills 是 OpenClaw 的扩展模块，教 Agent 如何使用特定工具或执行特定任务。

### 1.1 Skills 来源

| 来源 | 路径 | 优先级 |
|-----|------|-------|
| Workspace | `<workspace>/skills/` | 最高 |
| Managed | `~/.openclaw/skills/` | 中 |
| Bundled | 内置 | 低 |
| Extra | `skills.load.extraDirs` | 最低 |

### 1.2 Skill 结构

```
skill-name/
├── SKILL.md          # 必需：技能说明
├── scripts/          # 可选：可执行脚本
├── references/       # 可选：参考文档
└── assets/           # 可选：资源文件
```

---

## 2. 已安装的 Skills

### 2.1 核心 Skills

| Skill | 功能 | 用途 |
|-------|------|------|
| **clawhub** | 技能仓库 CLI | 安装、更新、发布技能 |
| **healthcheck** | 安全加固审计 | 主机安全检查 |
| **skill-creator** | 创建技能 | 开发新技能 |
| **weather** | 天气查询 | 获取天气和预报 |
| **video-frames** | 视频帧提取 | ffmpeg 视频处理 |
| **tushare** | 财经数据 | 股票、基金、期货数据 |

### 2.2 Feishu Skills

| Skill | 功能 |
|-------|------|
| **feishu-doc** | 飞书文档读写 |
| **feishu-drive** | 飞书云盘管理 |
| **feishu-perm** | 飞书权限管理 |
| **feishu-wiki** | 飞书知识库 |

### 2.3 QQ Bot Skills

| Skill | 功能 |
|-------|------|
| **qqbot-channel** | QQ 频道管理 |
| **qqbot-remind** | QQ 定时提醒 |
| **qqbot-media** | QQ 媒体发送 |
| **qqbot-cron** | QQ 智能提醒 |

### 2.4 用户安装的 Skills

| Skill | 功能 |
|-------|------|
| **crawl4ai-skill** | Web 爬虫 |
| **faster-whisper** | 本地语音转文字 |
| **playwright-web-scraper** | Playwright 网页抓取 |

**已删除**（用户要求专注于 AI 和 OpenClaw）：
- akshare-stock, china-stock-analysis, stock-analysis, stock-market-pro, yahoo-finance, finance-news

---

## 3. 重要 Skills 使用指南

### 3.1 ClawHub - 技能仓库

```bash
# 安装技能
clawhub install my-skill

# 更新技能
clawhub update my-skill
clawhub update --all

# 搜索技能
clawhub search "postgres backups"

# 发布技能
clawhub publish ./my-skill --slug my-skill --name "My Skill" --version 1.0.0
```

### 3.2 Healthcheck - 安全审计

**工作流程**：
1. 确定系统上下文（OS、权限、网络暴露等）
2. 运行 `openclaw security audit --deep`
3. 确定风险容忍度（家庭/VPS/开发者）
4. 生成修复计划
5. 执行修复（需要确认）

**关键命令**：
```bash
openclaw security audit          # 基础审计
openclaw security audit --deep   # 深度审计
openclaw security audit --fix    # 应用安全默认配置
openclaw update status           # 检查更新
```

### 3.3 Tushare - 财经数据

**设置**：
```bash
pip install tushare
export TUSHARE_TOKEN=your_token
```

**示例**：
```python
import tushare as ts
pro = ts.pro_api()

# 获取股票列表
df = pro.stock_basic(list_status='L')

# 获取日行情
df = pro.daily(ts_code='000001.SZ', start_date='20240101')
```

### 3.4 Faster Whisper - 语音转文字

- 4-6x 速度提升（相比 OpenAI Whisper）
- GPU 加速可达 ~20x 实时转录
- 支持 SRT/VTT/TTML/CSV 字幕
- 支持说话人分离

### 3.5 Weather - 天气查询

```bash
# 当前天气
curl "wttr.in/Shanghai?format=3"

# 详细预报
curl "wttr.in/Shanghai"

# JSON 格式
curl "wttr.in/Shanghai?format=j1"
```

---

## 4. 创建自定义 Skill

### 4.1 基本格式

```markdown
---
name: my-skill
description: 技能描述，包含触发条件
metadata:
  {
    "openclaw": {
      "emoji": "🔧",
      "requires": { "bins": ["required-cli"], "env": ["API_KEY"] },
      "homepage": "https://example.com"
    }
  }
---

# 技能说明

具体的使用指南...
```

### 4.2 元数据字段

| 字段 | 说明 |
|-----|------|
| `name` | 技能名称（必需） |
| `description` | 技能描述（必需） |
| `metadata.openclaw.emoji` | 显示图标 |
| `metadata.openclaw.requires.bins` | 依赖的二进制 |
| `metadata.openclaw.requires.env` | 依赖的环境变量 |
| `metadata.openclaw.requires.config` | 依赖的配置项 |
| `metadata.openclaw.install` | 安装说明 |

### 4.3 最佳实践

1. **简洁**：SKILL.md 保持 <500 行
2. **渐进披露**：详细内容放 references/
3. **避免重复**：不在多处写相同信息
4. **示例驱动**：用示例代替冗长解释

---

## 5. 技能配置

### 5.1 启用/禁用

```json5
{
  skills: {
    entries: {
      "my-skill": { enabled: true },
      "unused-skill": { enabled: false }
    }
  }
}
```

### 5.2 注入环境变量

```json5
{
  skills: {
    entries: {
      "tushare": {
        env: { TUSHARE_TOKEN: "your_token" }
      }
    }
  }
}
```

### 5.3 API Key 管理

```json5
{
  skills: {
    entries: {
      "my-skill": {
        apiKey: { source: "env", provider: "default", id: "MY_API_KEY" }
      }
    }
  }
}
```

---

## 6. Token 优化

每个 Skill 的 token 开销：
- 基础开销：~195 字符
- 每个 Skill：~97 字符 + 名称 + 描述 + 路径

**优化策略**：
- 只启用必要的 Skills
- 使用 `skills.allowBundled` 白名单
- 保持描述简洁

---

_持续更新中..._
