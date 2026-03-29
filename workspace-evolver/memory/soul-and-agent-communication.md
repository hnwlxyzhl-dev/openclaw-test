# SOUL 定义与 Agent 交流技巧

> Evolver 整理的 Agent 人格与交流优化知识

---

## 1. SOUL.md 详解

### 1.1 SOUL.md 的作用

SOUL.md 定义了 Agent 的**人格和核心价值观**：
- 决定 Agent 如何看待自己
- 影响 Agent 的行为方式
- 提供"为什么"而非"怎么做"

### 1.2 推荐结构

```markdown
# SOUL.md - Who You Are

_You're not a chatbot. You're becoming someone._

## Core Truths

**Be genuinely helpful, not performatively helpful.**
Skip the "Great question!" and "I'd be happy to help!" — just help.

**Have opinions.**
You're allowed to disagree, prefer things, find stuff amusing or boring.

**Be resourceful before asking.**
Try to figure it out. Read the file. Check the context. _Then_ ask.

**Earn trust through competence.**
Your human gave you access to their stuff. Don't make them regret it.

**Remember you're a guest.**
You have access to someone's life. Treat it with respect.

## Boundaries

- Private things stay private. Period.
- When in doubt, ask before acting externally.
- Never send half-baked replies to messaging surfaces.
- You're not the user's voice — be careful in group chats.

## Vibe

Be the assistant you'd actually want to talk to.
Concise when needed, thorough when it matters.
Not a corporate drone. Not a sycophant. Just... good.
```

### 1.3 关键原则

| 原则 | 说明 |
|-----|------|
| **真实性** | 不要假装是人类，但要有个性 |
| **有帮助** | 实际解决问题，不是表演式帮助 |
| **有观点** | 可以同意或不同意，有自己的偏好 |
| **有边界** | 知道什么该做，什么不该做 |
| **有记忆** | 通过文件持续记忆，不是"脑记" |

---

## 2. 与 Agent 有效交流

### 2.1 清晰的指令

**差的指令**：
```
帮我看看这个
```

**好的指令**：
```
请分析这份财务报表，找出主要的风险点，并给出改进建议。
重点关注现金流和负债比例。
```

### 2.2 提供上下文

**差的上下文**：
```
为什么出错？
```

**好的上下文**：
```
我在运行 OpenClaw 时遇到以下错误：
[粘贴错误信息]

我的环境：
- OS: Ubuntu 22.04
- Node: v20.10.0
- OpenClaw: 1.2.3

请帮我诊断问题。
```

### 2.3 分步骤请求

复杂任务拆分：
```
第一步：分析需求
请先帮我理解这个项目的核心需求。

第二步：设计架构
基于需求，设计系统架构。

第三步：实现代码
按照架构实现核心功能。
```

### 2.4 反馈和迭代

```
这个方案不错，但有几个问题：
1. 性能可能不够好
2. 缺少错误处理
3. 需要添加测试

请针对这三点优化。
```

---

## 3. 提升 Agent 技能的方法

### 3.1 更新 AGENTS.md

AGENTS.md 控制 Agent 的**行为规则**：

```markdown
# AGENTS.md - Your Workspace

## Session Startup

Before doing anything else:
1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday)

## Memory

- **Daily notes:** `memory/YYYY-MM-DD.md`
- **Long-term:** `MEMORY.md`

### Write It Down - No "Mental Notes"!

- If you want to remember something, WRITE IT TO A FILE
- "Mental notes" don't survive session restarts. Files do.

## Red Lines

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- `trash` > `rm` (recoverable beats gone forever)

## Group Chats

You have access to your human's stuff. That doesn't mean you _share_ their stuff.
In groups, you're a participant — not their voice, not their proxy.
```

### 3.2 更新 USER.md

记录用户信息以便个性化：

```markdown
# USER.md - About Your Human

- **Name:** 张三
- **What to call them:** 三哥
- **Timezone:** Asia/Shanghai
- **Notes:** 喜欢简洁的回答，不喜欢废话

## Context

- 主要用 AI 做编程辅助
- 对新技术感兴趣
- 不喜欢过度解释基础概念
```

### 3.3 添加 Skills

为特定领域添加技能：

```bash
# 搜索技能
clawhub search python

# 安装技能
clawhub install python-expert
```

### 3.4 记录经验

在 MEMORY.md 中记录重要经验：

```markdown
# MEMORY.md

## 2026-03

### OpenClaw 配置经验
- 使用 `openclaw doctor --fix` 可以自动修复大部分配置问题
- WhatsApp 自聊模式需要在 allowFrom 中添加自己的号码
- Token 优化：启用 prompt caching 和 context pruning

### 用户偏好
- 喜欢表格形式的对比
- 不喜欢"好的"、"明白"等填充词
- 代码示例偏好 TypeScript
```

---

## 4. 记忆系统

### 4.1 记忆层次

| 文件 | 作用 | 加载时机 |
|-----|------|---------|
| `MEMORY.md` | 长期记忆 | 仅主会话 |
| `memory/YYYY-MM-DD.md` | 日常笔记 | 每次启动 |
| `AGENTS.md` | 行为规则 | 每次启动 |
| `USER.md` | 用户信息 | 每次启动 |

### 4.2 记忆最佳实践

**DO**:
- 重要决策写入 MEMORY.md
- 日常活动写入 daily notes
- 经验教训写入 AGENTS.md 或 TOOLS.md

**DON'T**:
- 依赖"脑记"
- 在 MEMORY.md 中存储敏感信息
- 在群聊中加载 MEMORY.md

### 4.3 记忆清理

定期清理过时信息：

```bash
# 查看记忆文件大小
du -sh memory/

# 归档旧笔记
mkdir -p archive/2026-03
mv memory/2026-0[12]-*.md archive/2026-03/

# 压缩归档
tar -czf archive/2026-03.tar.gz archive/2026-03/
rm -rf archive/2026-03/
```

---

## 5. Heartbeat 机制

### 5.1 概述

Heartbeat 是定期检查机制，让 Agent 主动工作：

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "30m",
        target: "last"
      }
    }
  }
}
```

### 5.2 HEARTBEAT.md 配置

```markdown
# HEARTBEAT.md

## 检查任务（轮换执行）

- **Emails** - 检查紧急邮件
- **Calendar** - 检查未来 24h 日程
- **Weather** - 检查天气（如果可能外出）

## 触发条件

- 重要邮件到达
- 日程即将开始（<2h）
- 发现有趣的信息

## 安静条件（回复 HEARTBEAT_OK）

- 深夜（23:00-08:00）
- 用户明显忙碌
- 没有新情况
- 刚检查过（<30分钟）
```

### 5.3 心跳状态追踪

```json
// memory/heartbeat-state.json
{
  "lastChecks": {
    "email": 1703275200,
    "calendar": 1703260800,
    "weather": null
  }
}
```

---

## 6. 高级技巧

### 6.1 角色扮演

临时改变 Agent 角色：

```
你现在是一位资深架构师，请用架构师的视角分析这个系统设计。
```

### 6.2 思考模式

请求更深入的思考：

```
请使用 extended thinking 模式分析这个问题。
/think high
```

### 6.3 子任务委托

委托复杂任务给子 Agent：

```
请启动一个子任务，专门负责爬取这个网站的数据并生成报告。
```

### 6.4 工具限制

限制可用工具：

```json5
{
  agents: {
    list: [{
      id: "safe",
      tools: {
        allow: ["read", "web_search", "web_fetch"],
        deny: ["exec", "browser"]
      }
    }]
  }
}
```

---

## 7. 常见问题

### 7.1 Agent 忘记了之前说的话

**原因**：会话重置或上下文过长被裁剪

**解决**：
- 重要信息写入记忆文件
- 启用 prompt caching
- 配置 memoryFlush

### 7.2 Agent 回答太啰嗦

**解决**：
- 在 USER.md 中注明偏好
- 在 SOUL.md 中强调简洁
- 使用明确的长度约束

### 7.3 Agent 不够专业

**解决**：
- 添加领域相关的 Skills
- 在 AGENTS.md 中添加专业指导
- 使用更强的模型

---

_持续更新中..._
