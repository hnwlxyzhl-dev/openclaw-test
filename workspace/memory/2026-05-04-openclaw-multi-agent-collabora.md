# Session: 2026-05-04 14:57:45 UTC

- **Session Key**: agent:eden:feishu:eden:direct:ou_5984d8f20adcac5cc0ee74bf3dae2c54
- **Session ID**: d2928d87-5ab6-49e4-94b1-83be05a0aab1
- **Source**: feishu

## Conversation Summary

user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b50bd9607e4a4c3811e65eca73b7",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Mon 2026-05-04 21:22 GMT+8"
}
```

Sender (untrusted metadata):
```json
{
  "label": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "name": "ou_5984d8f20adcac5cc0ee74bf3dae2c54"
}
```

[message_id: om_x100b50bd9607e4a4c3811e65eca73b7]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: openclaw有几种多agents协作的方式，请分别讲述原理。
assistant: OpenClaw 支持以下几种多 Agent 协作方式：

---

## 1. 多智能体路由（Multi-Agent Routing）

**原理：** 在一个 Gateway 进程中运行多个**完全隔离**的 Agent，每个 Agent 有独立的工作区（workspace）、人格文件（SOUL.md）、认证配置和会话存储。入站消息通过 `bindings` 规则路由到对应的 Agent。

**路由优先级：** 精确 peer 匹配 → guildId/teamId → accountId → 渠道级匹配 → 默认 Agent

**典型场景：**
- 多人共用一台服务器，每人一个独立 AI 大脑
- 按渠道分工：WhatsApp 日常快聊 → 轻量模型，Telegram 深度工作 → 重模型
- 一个 WhatsApp 号码，不同联系人路由到不同 Agent
- 每个 Agent 可独立配置沙箱和工具权限

**关键隔离点：** workspace、`agentDir`（认证）、sessions、tools 策略、sandbox 模式均按 agentId 隔离。

---

## 2. 子智能体（Sub-Agents）

**原理：** 一个 Agent 运行时通过 `sessions_spawn` 生成后台子智能体，子智能体在独立会话中执行任务（session key: `agent:<id>:subagent:<uuid>`），完成后**通告**结果回请求者。

**两种模式：**
- `mode: "run"` — 一次性执行，完成后通告结果，会话自动归档
- `mode: "session"` — 持久会话，绑定到频道线程，后续消息持续路由到该子智能体

**嵌套编排（Orchestrator Pattern）：** 默认 `maxSpawnDepth: 1`（不允许嵌套）。设为 2 时支持：主 Agent → 编排者子智能体 → 工作者子子智能体，结果逐级上报。最大支持 5 层。

**特点：**
- 非阻塞，立即返回 runId
- 子智能体默认**不获取** session 工具（防滥用）
- 支持独立模型/思考级别配置（子智能体用便宜模型，主智能体用贵模型）
- 并发队列控制（默认最多 8 个）

---

## 3. ACP 智能体（Agent Client Protocol）

**原理：** 通过 ACP 后端插件（如 acpx）运行**外部编码工具链**——Claude Code、Codex、Gemini CLI、OpenCode 等。这些是独立的进程/运行时，通过标准化的 Agent Client Protocol 与 OpenClaw 通信。

**与子智能体的区别：**
| 维度 | ACP | 子智能体 |
|------|-----|---------|
| 运行时 | 外部 harness 进程 | OpenClaw 原生 |
| Session key | `agent:<id>:acp:<uuid>` | `agent:<id>:subagent:<uuid>` |
| 管理命令 | `/acp ...` | `/subagents ...` |
| 沙箱 | 在宿主机运行，不支持 sandbox | 可选沙箱 |

**线程绑定：** 在支持线程的渠道（如 Discord），ACP 会话可绑定到线程，后续消息自动路由到同一会话。

**特点：** 适合需要专业编码工具链的场景，权限配置灵活（approve-all / approve-reads / deny-all）。

---

## 4. Agent-to-Agent 消息传递（Cross-Session Messaging）

**原理：** 通过 `sessions_send` 工具，一个 Agent 可以向另一个 Agent 的会话发送消息。这是跨 Agent 的点对点通信。

**配置：** 默认关闭（`tools.agentToAgent.enabled: false`），需显式启用并配置 `allow` 白名单。

**场景：** Agent A 完成分析后，把结果转发给 Agent B 做后续处理。

---

## 5. 直接 CLI 调用（`openclaw agent`）

**原理：** 通过命令行直接启动一个 Agent 回合，无需入站聊天消息。可以指定目标 Agent、会话、模型等参数，支持将回复投递到渠道。

**场景：** 脚本自动化、Cron 定时任务、CI/CD 集成中程序化触发 Agent。

---

## 总结对比

| 方式 | 隔离级别 | 通信方向 | 适用场景 |
|------|---------|---------|---------|
| 多智能体路由 | 完全隔离（workspace+认证+会话） | 入站消息路由 | 多用户、多人格、按渠道分工 |
| 子智能体 | 会话隔离，共享 Agent 上下文 | 父→子派发，子→父通告 | 并行研究、长任务、编排模式 |
| ACP | 独立进程，宿主机运行 | OpenClaw↔外部 harness | 专业编码、Claude Code/Codex 集成 |
| 跨会话消息 | 无隔离，点对点 | Agent↔Agent | 简单的 Agent 间协作 |
| CLI 直接调用 | 复用已有会话 | 外部→Agent | 自动化脚本、Cron 任务 |
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b50be4290f4b0c2b54c3eea374b6",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Mon 2026-05-04 21:36 GMT+8"
}
```

Sender (untrusted metadata):
```json
{
  "label": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "name": "ou_5984d8f20adcac5cc0ee74bf3dae2c54"
}
```

[message_id: om_x100b50be4290f4b0c2b54c3eea374b6]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: 关于第二种，子agent能继承母agent的memory，soul等吗？为什么要使用子agent？
跟第四种的差别是什么？
assistant: ## 子 Agent 能继承母 Agent 的 memory/Soul 吗？

**部分继承，大部分不继承。** 具体来说：

| 文件 | 子 Agent 是否注入 |
|------|:---:|
| AGENTS.md | ✅ |
| TOOLS.md | ✅ |
| SOUL.md | ❌ |
| IDENTITY.md | ❌ |
| USER.md | ❌ |
| HEARTBEAT.md | ❌ |
| BOOTSTRAP.md | ❌ |

也就是说，子 Agent 知道**有哪些其他 Agent 存在**（AGENTS.md）和**怎么用工具**（TOOLS.md），但**不知道"我是谁"、"你是谁"、"我的行为准则是什么"**。

**认证（auth）** 是按 agentId 解析的，主 Agent 的认证配置会作为 fallback 合并，所以凭证层面有一定共享。但 workspace 里的 MEMORY.md 等自定义记忆文件也不会自动注入。

> 这是有意为之的设计——子 Agent 是**执行任务的工具**，不是"你的分身"。它不需要人格，只需要任务上下文。

---

## 为什么要用子 Agent？

核心原因就一个：**不阻塞主对话。**

### 具体场景

1. **并行研究：** 用户问"帮我分析 A 股和美股的 AI 板块"。你可以同时 spawn 两个子 Agent，一个分析 A 股，一个分析美股，主对话不卡住，用户还能继续聊天。

2. **长耗时任务：** 爬取 50 个页面、跑深度分析、生成报告——这些可能要几分钟。在子 Agent 里跑，主对话秒回"在处理了"，完成后自动通告结果。

3. **成本优化：** 子 Agent 可以配便宜模型做重复性工作（比如批量抓数据），主 Agent 用贵模型做最终分析。

4. **编排模式（Orchestrator）：** 设 `maxSpawnDepth: 2` 后，一个编排者子 Agent 可以派生多个工作者子子 Agent，实现扇出-收集（fan-out/fan-in）。

### 简单说：子 Agent = 异步后台 worker，带结果回调。

---

## 子 Agent vs 跨会话消息（第四种）的差别

| 维度 | 子 Agent | 跨会话消息（sessions_send） |
|------|---------|--------------------------|
| **生命周期** | 临时创建，任务完成即结束（可自动归档） | 发到**已有的**持久会话 |
| **会话** | 新建独立会话 `subagent:<uuid>` | 目标会话已存在 |
| **通信方向** | 父→子（派发任务），子→父（通告结果） | 任意 Agent 之间双向 |
| **人格** | 无 SOUL/IDENTITY/USER | 目标 Agent 有完整人格 |
| **工具权限** | 默认无 session 工具（防滥用） | 目标 Agent 有其完整工具集 |
| **阻塞** | 非阻塞，立即返回 | 非阻塞 |
| **结果回报** | 自动通告 + 统计（token/耗时/成本） | 无自动回报，需要目标 Agent 自己回复 |
| **配置** | 默认可用 | 默认关闭，需显式开启白名单 |

### 用类比来理解

- **子 Agent** ≈ 你开了一个临时协程/线程去做任务，做完把结果扔回来。它是个"工具人"，没有人格。
- **跨会话消息** ≈ 你给另一个同事发了一封邮件/Slack 消息。那个同事有自己的完整上下文、人格、记忆，自己决定怎么回复。

### 什么时候用哪个？

| 场景 | 选择 |
|------|------|
| 并行抓 10 个页面 | 子 Agent |
| 把分析结果转给另一个专业 Agent 处理 | 跨会话消息 |
| 后台跑长任务不阻塞用户 | 子 Agent |
| 两个 Agent 协作完成一个持续的工作流 | 跨会话消息 |
| 批量、一次性、可丢弃的任务 | 子 Agent |
| 需要对方完整人格和记忆的对话 | 跨会话消息 |
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b50be87840ca0c3335dd7a5997d6",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Mon 2026-05-04 22:26 GMT+8"
}
```

Sender (untrusted metadata):
```json
{
  "label": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "name": "ou_5984d8f20adcac5cc0ee74bf3dae2c54"
}
```

[message_id: om_x100b50be87840ca0c3335dd7a5997d6]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: 我现在想测试跨会话消息的多agent能力，我希望你跟另一个agent Weaver协作完成一个任务。请你策划一下，把策划方案给我，如果需要我提供什么信息就告诉我。
assistant: 好，先摸清当前环境配置，看看跨 Agent 消息是否可用。
assistant: 好了，环境摸清了。整理一下关键信息：

---

## 环境状态

- ✅ **跨 Agent 消息已启用**（`agentToAgent.enabled: true`）
- ✅ **Weaver 存在**，workspace 完整，有独立人格
- Weaver 的定位：**创作者型 Agent**，擅长 PPT、图片生成、文档写作
- 我的定位：**金融分析师**，擅长数据分析和市场研究

## 协作方案

### 任务设计：「A股 AI 板块深度研究报告」

这个任务天然适合分工协作：

**角色分工：**

| 阶段 | 执行者 | 内容 |
|------|--------|------|
| ① 数据调研 | Eden（我） | 搜索 A 股 AI 板块核心公司、行情数据、行业政策、最新动态 |
| ② 数据传递 | Eden → Weaver | 将整理好的结构化分析结果发送给 Weaver |
| ③ 报告制作 | Weaver | 制作一份专业的图文研究报告（PPT 或飞书文档） |

**通信流程：**

```
你 → Eden: "开始执行"
Eden → 搜索/分析 AI 板块数据
Eden → Weaver (sessions_send): 发送结构化数据
Weaver → 制作报告
Weaver → Eden (sessions_send): 报告完成通知
Eden → 你: 汇总结果
```

### 需要你确认的 3 个问题

1. **报告形式：** PPT（Weaver 擅长）还是飞书文档？还是都要？
2. **AI 板块范围：** 是泛 AI 概念（包括算力、大模型、应用），还是聚焦某个细分方向？
3. **报告深度：** 简要行业概览（10 分钟内完成），还是每家公司都深入分析（可能需要 20-30 分钟）？

确认后我立即执行。
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b50be922284acc43a102d2c509bc",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Mon 2026-05-04 22:31 GMT+8"
}
```

Sender (untrusted metadata):
```json
{
  "label": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "name": "ou_5984d8f20adcac5cc0ee74bf3dae2c54"
}
```

[message_id: om_x100b50be922284acc43a102d2c509bc]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: 1.PPT。2.聚焦在AI芯片。3.行业概览和深入的头部公司分析。
让Weaver根据它以往的经验使用多agents的方式去撰写PPT。
assistant: 好，先做 AI 芯片板块的数据调研，然后把结构化结果发给 Weaver。
assistant: 数据收集完毕，现在把结构化分析结果发送给 Weaver。
assistant: 消息已发送给 Weaver。我来确认一下是否送达成功。
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b50beb9cda8a4c45c6b69cf1917e",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Mon 2026-05-04 22:38 GMT+8"
}
```

Sender (untrusted metadata):
```json
{
  "label": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "name": "ou_5984d8f20adcac5cc0ee74bf3dae2c54"
}
```

[message_id: om_x100b50beb9cda8a4c45c6b69cf1917e]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: 情况怎么样
assistant: PPT 已经完成了！Weaver 刚刚通知我。

**《A股AI芯片行业深度研究报告》** 已生成，18页，深色科技金融报告风格。

**文件路径：** `/home/admin/.openclaw/workspace/output/AI芯片行业深度研究报告.pptx`

**完整结构：**
1. 封面
2. 目录
3. 行业概览（市场空间 + 三阶段发展）
4. 产业链全景图（上游/中游/下游）
5-6. 寒武纪（公司概况 + 核心优势与风险）
7-8. 海光信息（公司概况 + 生态壁垒）
9-10. 景嘉微（公司概况 + 转型战略）
11. 工业富联
12. 四大标的财务数据对比表
13. AI芯片竞争格局全景（四赛道）
14. 行业四大趋势
15. 核心风险提示
16. 综合评估与投资建议
17. 数据来源与免责声明
18. 封底

Weaver 自检评分 96/100，已修复了货币单位、风险提示、财务对比表等细节。

需要我把文件发给你，或者有什么要调整的？
