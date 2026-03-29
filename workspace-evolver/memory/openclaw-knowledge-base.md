# OpenClaw 知识库

> Evolver 的 OpenClaw 核心知识整理

## 1. OpenClaw 核心概念

### 1.1 什么是 OpenClaw

OpenClaw 是一个 AI Agent Gateway，核心能力：
- **多渠道接入**：WhatsApp、Telegram、Discord、Slack、Signal、iMessage 等统一接入
- **多智能体路由**：支持多个隔离的 Agent，各自独立工作区和身份
- **模型灵活性**：支持 Anthropic、OpenAI、Google、Qwen、GLM 等多种模型
- **Skills 技能系统**：可扩展的技能模块，教 AI 如何使用工具
- **安全沙箱**：Docker 沙箱隔离执行环境

### 1.2 核心架构

```
用户消息 → Channel → Gateway → Agent Router → Agent Session → Model
                                                    ↓
                                              Tools/Skills
                                                    ↓
                                              Workspace (文件/记忆)
```

### 1.3 重要文件路径

| 文件/目录 | 用途 |
|---------|------|
| `~/.openclaw/openclaw.json` | 主配置文件 (JSON5 格式) |
| `~/.openclaw/workspace` | 默认工作区 |
| `~/.openclaw/agents/<id>/agent/` | Agent 状态目录 |
| `~/.openclaw/agents/<id>/sessions/` | 会话存储 |
| `<workspace>/AGENTS.md` | Agent 行为规则 |
| `<workspace>/SOUL.md` | Agent 人格定义 |
| `<workspace>/USER.md` | 用户信息 |
| `<workspace>/MEMORY.md` | 长期记忆 |
| `<workspace>/memory/` | 日常笔记 |
| `<workspace>/skills/` | Agent 专属技能 |

---

## 2. 模型系统

### 2.1 支持的模型提供商

| 提供商 | 模型示例 | 特点 |
|-------|---------|------|
| **Anthropic** | claude-opus-4-6, claude-sonnet-4-5 | 最强推理能力，支持 extended thinking |
| **OpenAI** | gpt-5.2, gpt-5-mini | 通用性强，生态完善 |
| **Google** | gemini-3-pro, gemini-3-flash | 多模态强，免费额度 |
| **Z.AI (GLM)** | glm-5, glm-4.7 | 中文优化，思考模式 |
| **Qwen** | qwen3-max, qwen3-vl-plus | 阿里云，免费 OAuth |
| **OpenRouter** | 各种开源模型 | 统一代理，免费模型多 |
| **Cerebras** | zai-glm-4.7 | 极速推理 |
| **MiniMax** | MiniMax-M2.1 | 高性价比 |
| **Moonshot** | kimi-k2.5 | 长上下文 |
| **本地模型** | LM Studio | 隐私保护，无成本 |

### 2.2 模型选择策略

**主模型选择原则**：
1. 复杂任务 → Opus/Gemini Pro (最强推理)
2. 日常对话 → Sonnet/GPT-5-mini (性价比)
3. 代码任务 → Claude/GPT (代码能力强)
4. 中文场景 → GLM/Qwen (中文优化)
5. 成本敏感 → OpenRouter 免费模型

**Fallback 策略**：
```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-opus-4-6",
        fallbacks: ["anthropic/claude-sonnet-4-5", "openai/gpt-5.2"]
      }
    }
  }
}
```

### 2.3 Token 优化技巧

1. **Prompt Caching (Anthropic)**
```json5
{
  agents: {
    defaults: {
      models: {
        "anthropic/claude-opus-4-6": {
          params: { cacheRetention: "long" } // 1小时缓存
        }
      }
    }
  }
}
```

2. **Context Pruning (自动裁剪旧工具结果)**
```json5
{
  agents: {
    defaults: {
      contextPruning: {
        mode: "adaptive",  // 或 "aggressive"
        keepLastAssistants: 3,
        softTrimRatio: 0.3,
        hardClearRatio: 0.5
      }
    }
  }
}
```

3. **Compaction (记忆压缩)**
- 自动压缩长对话历史
- `memoryFlush` 在压缩前保存记忆到文件
- 减少重复上下文传输

4. **其他优化**
- 减少 Skills 数量（每个 Skill ~97 字符开销）
- 使用 `historyLimit` 限制群聊历史
- 设置 `dmHistoryLimit` 限制私聊历史
- 图片压缩：`imageMaxDimensionPx: 1200`

---

## 3. 工具系统

### 3.1 核心工具

| 工具 | 功能 | 注意事项 |
|-----|------|---------|
| `exec` | 执行 shell 命令 | 沙箱中受限 |
| `read/write/edit` | 文件操作 | 核心工具 |
| `browser` | 浏览器自动化 | 需要 `browser.enabled=true` |
| `web_search/web_fetch` | 网络搜索和抓取 | 需要 Brave API Key |
| `image/pdf` | 图像/PDF 分析 | 需要配置 imageModel |
| `message` | 跨渠道发消息 | 慎用，防止滥用 |
| `sessions_spawn` | 启动子 Agent | 用于复杂任务 |
| `nodes` | 控制远程节点 | iOS/Android/Mac |
| `canvas` | Canvas 渲染 | A2UI 界面 |
| `cron` | 定时任务 | 自动化场景 |

### 3.2 工具策略配置

**工具组 (group:*)**:
- `group:runtime` → exec, bash, process
- `group:fs` → read, write, edit, apply_patch
- `group:sessions` → sessions_list, sessions_history, sessions_send, sessions_spawn, session_status
- `group:web` → web_search, web_fetch
- `group:ui` → browser, canvas
- `group:messaging` → message

**工具 Profile**:
- `minimal`: 只有 session_status
- `coding`: fs + runtime + sessions + memory + image
- `messaging`: messaging + sessions
- `full`: 无限制

**示例：受限 Agent**
```json5
{
  agents: {
    list: [{
      id: "family",
      tools: {
        profile: "messaging",
        deny: ["exec", "browser"]
      }
    }]
  }
}
```

### 3.3 提升权限 (Elevated)

Elevated 模式允许在**主机**而非沙箱中执行命令：
```json5
{
  tools: {
    elevated: {
      enabled: true,
      allowFrom: {
        whatsapp: ["+15555550123"],
        discord: ["your_username"]
      }
    }
  }
}
```

---

## 4. Skills 技能系统

### 4.1 技能来源与优先级

1. **Workspace Skills** (`<workspace>/skills/`) - 最高优先级
2. **Managed Skills** (`~/.openclaw/skills/`)
3. **Bundled Skills** (内置)
4. **Extra Dirs** (`skills.load.extraDirs`)

### 4.2 技能格式

```markdown
---
name: my-skill
description: 技能描述
metadata:
  {
    "openclaw": {
      "requires": { "bins": ["required-cli"], "env": ["API_KEY"] },
      "emoji": "🔧",
      "homepage": "https://example.com"
    }
  }
---

# 技能说明

这里写具体的使用指南...
```

### 4.3 技能配置

```json5
{
  skills: {
    entries: {
      "my-skill": {
        enabled: true,
        apiKey: "YOUR_API_KEY",  // 或 SecretRef
        env: { API_KEY: "xxx" }
      }
    }
  }
}
```

### 4.4 ClawHub 技能仓库

- 网址：https://clawhub.com
- 安装：`clawhub install <skill-slug>`
- 更新：`clawhub update --all`
- 同步：`clawhub sync --all`

---

## 5. 多 Agent 路由

### 5.1 基本概念

- **Agent**: 独立的"大脑"，有独立工作区、身份、会话
- **Account**: 渠道账号（如两个 WhatsApp 号）
- **Binding**: 路由规则，决定消息发给哪个 Agent

### 5.2 路由示例

```json5
{
  agents: {
    list: [
      { id: "home", default: true, workspace: "~/.openclaw/workspace-home" },
      { id: "work", workspace: "~/.openclaw/workspace-work" }
    ]
  },
  bindings: [
    { agentId: "home", match: { channel: "whatsapp", accountId: "personal" } },
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } }
  ]
}
```

### 5.3 路由优先级

1. `peer` 匹配 (具体用户/群组)
2. `guildId` 匹配 (Discord 服务器)
3. `teamId` 匹配 (Slack 团队)
4. `accountId` 精确匹配
5. `accountId: "*"` (渠道级别)
6. 默认 Agent

---

## 6. 安全最佳实践

### 6.1 威胁模型 (MITRE ATLAS)

OpenClaw 考虑的威胁：
- **Prompt Injection**: 恶意输入操控 Agent
- **Data Exfiltration**: 敏感数据泄露
- **Tool Abuse**: 工具滥用
- **Auth Compromise**: 认证凭证泄露

### 6.2 安全配置

**访问控制**:
```json5
{
  channels: {
    whatsapp: {
      dmPolicy: "pairing",  // 或 "allowlist"
      allowFrom: ["+15555550123"],
      groups: { "*": { requireMention: true } }
    }
  }
}
```

**沙箱隔离**:
```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",  // 非主会话沙箱化
        scope: "agent",
        docker: {
          network: "none",  // 无网络
          capDrop: ["ALL"],
          readOnlyRoot: true
        }
      }
    }
  }
}
```

**敏感操作限制**:
```json5
{
  commands: {
    bash: false,      // 禁用 ! 命令
    config: false,    // 禁用 /config
    restart: false    // 禁用 /restart
  }
}
```

### 6.3 工具安全

- 使用 `tools.allow/deny` 限制工具
- 使用 `tools.profile` 设置基础策略
- 使用 `tools.elevated` 控制提升权限
- 使用 `tools.byProvider` 按模型限制

---

## 7. 会话与记忆

### 7.1 会话作用域

```json5
{
  session: {
    dmScope: "per-channel-peer",  // 推荐多用户
    reset: { mode: "daily", atHour: 4 },
    resetTriggers: ["/new", "/reset"]
  }
}
```

### 7.2 记忆系统

- **MEMORY.md**: 长期记忆 (仅主会话加载)
- **memory/YYYY-MM-DD.md**: 日常笔记
- **自动压缩**: Compaction 触发 memoryFlush

### 7.3 Heartbeat 心跳

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "30m",
        target: "last"  // 或具体渠道
      }
    }
  }
}
```

---

## 8. 常用命令

```bash
# Gateway 管理
openclaw gateway status
openclaw gateway start
openclaw gateway restart
openclaw gateway stop

# 配置
openclaw onboard          # 初始化向导
openclaw configure        # 配置向导
openclaw config get <key>
openclaw config set <key> <value>

# 模型
openclaw models status
openclaw models set <provider/model>
openclaw models scan      # 扫描免费模型

# Agent
openclaw agents list --bindings
openclaw agents add <id>

# 诊断
openclaw doctor
openclaw doctor --fix
openclaw logs
```

---

## 9. 故障排除

### 9.1 常见问题

| 问题 | 解决方案 |
|-----|---------|
| Gateway 启动失败 | 运行 `openclaw doctor` |
| 模型认证失败 | 检查 API Key，运行 `openclaw models status` |
| 配置验证错误 | 使用 `openclaw doctor --fix` |
| Token 消耗过高 | 启用 prompt caching, context pruning |
| Agent 响应慢 | 检查模型延迟，考虑 fallback |

### 9.2 日志位置

- 日志文件：`/tmp/openclaw/openclaw-YYYY-MM-DD.log`
- 或配置：`logging.file: "/tmp/openclaw/openclaw.log"`

---

_此文档持续更新中..._
