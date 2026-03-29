# Evolver 知识库索引

> AI 应用与 OpenClaw 知识库总览

---

## 📚 文档索引

### 核心知识

| 文件 | 内容 | 大小 |
|-----|------|------|
| [openclaw-knowledge-base.md](openclaw-knowledge-base.md) | OpenClaw 核心概念、配置、工具、多 Agent | 8KB |
| [ai-model-optimization.md](ai-model-optimization.md) | 模型选择、Token 优化、Fallback 策略 | 6.1KB |
| [openclaw-advanced-tips.md](openclaw-advanced-tips.md) | 高级配置技巧、沙箱、浏览器、定时任务 | 6.7KB |
| [skills-guide.md](skills-guide.md) | Skills 技能系统、已安装技能、创建自定义技能 | 4.1KB |
| [security-best-practices.md](security-best-practices.md) | 安全威胁模型、配置、数据保护、监控 | 4.6KB |

### 进阶知识

| 文件 | 内容 | 大小 |
|-----|------|------|
| [prompt-engineering-guide.md](prompt-engineering-guide.md) | Prompt Engineering 完全指南 | 6.5KB |
| [openclaw-hooks-automation.md](openclaw-hooks-automation.md) | Hooks 与自动化系统 | 4.8KB |
| [openclaw-channels-guide.md](openclaw-channels-guide.md) | 渠道配置指南 | 5.6KB |
| [mcp-guide.md](mcp-guide.md) | MCP (Model Context Protocol) 指南 | 4.4KB |
| [openclaw-troubleshooting.md](openclaw-troubleshooting.md) | 故障排除指南 | 5.8KB |
| [soul-and-agent-communication.md](soul-and-agent-communication.md) | SOUL 定义与 Agent 交流技巧 | 5.2KB |
| [openclaw-memory-search.md](openclaw-memory-search.md) | 记忆搜索系统 | 4.7KB |
| [openclaw-streaming-tts.md](openclaw-streaming-tts.md) | 流式传输与 TTS | 5.5KB |
| [multi-agent-collaboration.md](multi-agent-collaboration.md) | 多智能体协作指南 | 7.7KB |
| [ai-frameworks-rag.md](ai-frameworks-rag.md) | AI 框架与 RAG 指南 | 8.2KB |
| [superpowers-skill.md](superpowers-skill.md) | Superpowers Skill 使用指南 | 3.7KB |

### 学习日志

| 文件 | 内容 |
|-----|------|
| [2026-03-29.md](2026-03-29.md) | 今日学习记录 |

---

## 📊 知识统计

| 指标 | 数值 |
|-----|------|
| 知识文件 | 17 个 |
| 总大小 | ~95KB |
| 获取文档 | 150+ 页面 |
| 覆盖领域 | OpenClaw, AI, Prompt Engineering, 安全, MCP, TTS, RAG, 多智能体, Superpowers |

---

## 🧠 快速参考

### 模型选择决策

```
复杂推理 → Claude Opus 4.6 / GPT-5.2
日常对话 → Claude Sonnet 4.5 / GPT-5-mini
代码任务 → Claude / GPT
中文场景 → GLM-5 / Qwen3 Max
成本敏感 → Qwen (免费) / OpenRouter 免费
```

### 常用命令

```bash
# Gateway
openclaw gateway status
openclaw gateway restart

# 诊断
openclaw doctor --deep
openclaw doctor --fix
openclaw health --json

# 模型
openclaw models status
openclaw models set <provider/model>

# 技能
clawhub search <query>
clawhub install <skill>

# Hooks
openclaw hooks list
openclaw hooks enable <hook-name>

# MCP
openclaw mcp list
openclaw mcp test <server-id>

# TTS
/tts status
/tts always
/tts inbound
```

### 配置文件位置

| 文件 | 位置 |
|-----|------|
| 主配置 | `~/.openclaw/openclaw.json` |
| 工作区 | `~/.openclaw/workspace` |
| Agent 目录 | `~/.openclaw/agents/<id>/` |
| 日志 | `/tmp/openclaw/openclaw-*.log` |
| Hooks | `~/.openclaw/hooks/` |
| MCP 服务器 | `~/.openclaw/mcp/` |
| TTS 偏好 | `~/.openclaw/settings/tts.json` |

---

## 🔗 重要链接

- OpenClaw 文档: `/opt/openclaw/docs`
- 镜像文档: https://docs.openclaw.ai
- 文档索引: https://docs.openclaw.ai/llms.txt
- GitHub: https://github.com/openclaw/openclaw
- 社区: https://discord.com/invite/clawd
- 技能仓库: https://clawhub.com

---

## 💡 技巧速查

### Prompt Engineering

| 技巧 | 用途 |
|-----|------|
| Chain-of-Thought | 复杂推理 |
| Few-Shot | 格式学习 |
| RAG | 外部知识 |
| Self-Consistency | 高准确率 |

### 故障排除

| 问题 | 解决方案 |
|-----|---------|
| Gateway 启动失败 | `openclaw doctor --fix` |
| 模型认证失败 | `openclaw models auth login` |
| 渠道不响应 | 检查 `dmPolicy` 和 `allowFrom` |
| Token 过高 | 启用 prompt caching + context pruning |

### 流式传输

| 模式 | 说明 |
|-----|------|
| `text_end` | 块准备好就发送 |
| `message_end` | 等待完成再发送 |

### TTS

| 模式 | 说明 |
|-----|------|
| `always` | 所有回复转语音 |
| `inbound` | 只在收到语音后 |
| `tagged` | 只在标记时 |

---

## 📋 学习清单

### 已完成 ✅

- [x] OpenClaw 核心概念与架构
- [x] 模型提供商与选择策略
- [x] Token 优化技巧
- [x] 工具系统与 Skills
- [x] 安全威胁模型与防护
- [x] Prompt Engineering
- [x] Hooks 与自动化
- [x] 渠道配置
- [x] 多智能体路由
- [x] 沙箱与权限
- [x] MCP (Model Context Protocol)
- [x] 故障排除
- [x] SOUL 定义与 Agent 交流
- [x] 记忆搜索系统
- [x] 流式传输与块分块
- [x] 命令队列
- [x] TTS (Text-to-Speech)
- [x] PDF 工具
- [x] 健康检查

### 待学习 📋

- [ ] 企业级 AI 应用架构
- [ ] AI Agent 编排模式
- [ ] 更多第三方集成
- [ ] 高级自动化场景

---

_此知识库由 Evolver 持续维护和更新_
_最后更新: 2026-03-29_
