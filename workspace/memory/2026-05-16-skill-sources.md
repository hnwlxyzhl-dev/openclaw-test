# Session: 2026-05-16 07:10:23 UTC

- **Session Key**: agent:eden:feishu:eden:direct:ou_5984d8f20adcac5cc0ee74bf3dae2c54
- **Session ID**: fa4c1ef1-e5cf-41af-9c00-4f261f01115a
- **Source**: feishu

## Conversation Summary

user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b6f4af044ec80b18c4668bf5fcec",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Sat 2026-05-16 12:00 GMT+8"
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

[message_id: om_x100b6f4af044ec80b18c4668bf5fcec]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: 你下载skills的源是哪些
assistant: 目前我安装 skills 的源有两个：

| 源 | 地址 | 安装方式 |
|---|---|---|
| **ClawHub** | https://clawhub.com | `clawhub install <skill>` |
| **skills.sh** | https://skills.sh/ | `npx skills add <owner/repo@skill>` |

ClawHub 已经配置了 token，可以直接用。skills.sh 是基于 GitHub 仓库的，用 `npx` 直接拉取。

需要安装什么新 skill 吗？
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b6fb57635cca4c4af00b247912a4",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Sat 2026-05-16 14:49 GMT+8"
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

[message_id: om_x100b6fb57635cca4c4af00b247912a4]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: 你安装了哪些生成skills的skill？
assistant: 让我查一下已安装的、跟"生成"相关的 skills。
assistant: 跟"生成"相关的 skills 有这些：

### 📊 演示文稿/PPT 生成
| Skill | 用途 |
|---|---|
| **ppt-generator** | 讲稿→乔布斯风极简科技感竖屏 HTML 演示稿 |
| **openclaw-slides** | 从零创建动画丰富的 HTML 演示文稿，或把 PPT 转成网页幻灯片 |
| **slides-cog** | CellCog 驱动，深度调研生成专业演示文稿（PDF/PPTX） |
| **ai-presentation-maker** | 面试驱动的 pitch deck 生成器，导出 Markdown/PPTX/PDF |
| **powerpoint-pptx** | 精确创建/编辑 .pptx 文件，支持模板、图表、布局 |
| **ppt-visual** | PPT 视觉设计和布局建议 |
| **youmind-slides-generator** | YouMind 风格幻灯片生成 |

### 📝 文档/办公生成
| Skill | 用途 |
|---|---|
| **office-automation** | Word/Excel 自动化处理 |
| **excel-automation** | Excel 专用自动化 |

### 🔧 Skill 本身生成
| Skill | 用途 |
|---|---|
| **skill-creator** | 创建/打包新的 AgentSkill |
| **openai-image-gen** | OpenAI 图片生成 |

总共 **11 个**跟"生成"相关的 skill。PPT 方向装得最多（7 个），各有侧重。需要我用哪个来做什么吗？
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b6fb573a168a0c3c317fdf54f1f7",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Sat 2026-05-16 14:51 GMT+8"
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

[message_id: om_x100b6fb573a168a0c3c317fdf54f1f7]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: skill-creator，的原理是什么？
assistant: **skill-creator** 的原理可以概括为：**一套结构化的方法论 + 辅助脚本，用来创建、打包、分发可复用的 Agent 技能包。**

## 核心原理

### 1. 技能 = 知识注入
Skill 本质上是一个 **给 AI 的"上岗培训手册"**。AI 本身很聪明，但缺乏特定领域的流程、工具用法、公司规范等"程序性知识"。Skill 就是把这些知识打包进去，让通用 AI 变成领域专家。

### 2. 渐进式加载（三级上下文管理）
不是一股脑全塞给 AI，而是分层按需加载：

| 层级 | 内容 | 何时加载 | 大小 |
|---|---|---|---|
| **元数据** | name + description | 始终在上下文中 | ~100 词 |
| **SKILL.md 正文** | 工作流指令 | 匹配到才加载 | <500 行 |
| **附属资源** | 脚本/参考文档/模板 | AI 判断需要时再读 | 无限制 |

这样做的目的是 **省 token**，避免无关技能占满上下文窗口。

### 3. 目录结构
```
skill-name/
├── SKILL.md          # 必须：YAML头 + Markdown指令
├── scripts/          # 可选：可执行脚本（确定性任务）
├── references/       # 可选：参考文档（按需加载）
└── assets/           # 可选：模板/图片等输出资源
```

### 4. 创建流程（6 步）
1. **理解需求** — 收集具体使用场景
2. **规划资源** — 分析哪些需要脚本、参考文档、模板
3. **初始化** — `init_skill.py` 生成骨架
4. **编辑实现** — 写 SKILL.md + 资源文件
5. **打包** — `package_skill.py` 验证 + 打成 `.skill` 分发包
6. **迭代** — 实际使用后优化

### 5. 自由度控制
- **高自由度**（纯文字指令）：多方案都可行时
- **中自由度**（伪代码/参数化脚本）：有最佳实践但需灵活调整时
- **低自由度**（精确脚本）：操作脆弱、必须严格按步骤时

简单来说：**skill-creator 不生成代码本身，它教你（AI）如何把经验沉淀成标准化的技能包，让其他 AI 实例能复用这些专业知识。**
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b6fb51cb158a8c44fd671b71977f",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Sat 2026-05-16 14:56 GMT+8"
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

[message_id: om_x100b6fb51cb158a8c44fd671b71977f]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: 也就是说：当用户说要制作skill的时候，大模型读取skill-creator，按照它的指示方法（也就是上面的3,4,5）制作skill？
assistant: 对，就是这个意思。

准确地说，skill-creator 的工作方式是：

1. **触发**：当用户说"做一个 skill"或类似需求时，AI 匹配到 skill-creator 的 description，加载 SKILL.md 正文
2. **执行**：AI 按照 SKILL.md 里写的 6 步流程来操作：
   - 第 1-2 步：跟用户确认需求、规划资源（纯对话）
   - 第 3 步：调用 `init_skill.py` 脚本生成骨架目录
   - 第 4 步：编辑 SKILL.md 和资源文件
   - 第 5 步：调用 `package_skill.py` 验证并打包成 `.skill` 文件
   - 第 6 步：实际使用后迭代

所以 **skill-creator 本身不"生成"什么东西，它是一份指导手册**，告诉 AI "你应该按这个流程、这个规范去帮用户做 skill"。真正干活的还是 AI 自己——写 SKILL.md、写脚本、组织目录结构。skill-creator 只是确保这个过程是标准化的、不会遗漏关键步骤。
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b6fb52af8e118c4ce075904b87b7",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Sat 2026-05-16 15:01 GMT+8"
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

[message_id: om_x100b6fb52af8e118c4ce075904b87b7]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: skill怎么跟MCP协同使用？
assistant: 好问题。让我说清楚：

## Skill 和 MCP 的关系

它们是**两个独立的概念**，解决的是不同层面的问题：

| | **Skill** | **MCP（Model Context Protocol）** |
|---|---|---|
| **是什么** | 给 AI 的知识手册 + 资源包 | 标准化的工具调用协议 |
| **解决什么** | AI "知道怎么做" | AI "能调用什么工具" |
| **内容** | 流程指南、脚本、模板、参考文档 | 工具定义、输入输出 schema、调用接口 |
| **运行方式** | AI 读取后按指引行动 | AI 通过协议调用外部服务 |

简单比喻：
- **Skill = 培训手册**（教你怎么做）
- **MCP = 工具箱**（提供实际可用的工具）

## 它们怎么协同

### 1. Skill 里可以调用 MCP 工具
Skill 的 SKILL.md 里可以写："当需要查询数据库时，用 `mcporter call db.query`"。这样 Skill 提供了流程知识，MCP 提供了实际的工具能力。

### 2. OpenClaw 里的桥梁：mcporter
OpenClaw 自带一个 **mcporter** skill，它是 MCP 的客户端/运行时：

```bash
# 列出可用的 MCP 服务器和工具
mcporter list

# 调用某个 MCP 工具
mcporter call linear.list_issues team=ENG limit:5

# 甚至可以直接调用远程 MCP 服务器
mcporter call https://api.example.com/mcp.fetch url=https://example.com
```

### 3. 典型协同场景

```
用户: "帮我从 Linear 里拉出所有紧急 bug"

→ AI 读取 bug-triage skill（知道流程：先拉数据→分类→排优先级）
→ 通过 mcporter 调用 Linear MCP 服务器（拿到实际数据）
→ 按 skill 里的流程处理数据，输出结果
```

**Skill 提供"怎么想"，MCP 提供"怎么干"，两者配合就是完整的执行链。**

想深入了解 mcporter 的具体配置吗？
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "om_x100b6fb53adee8acc2eb4f3fb665504",
  "sender_id": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "sender": "ou_5984d8f20adcac5cc0ee74bf3dae2c54",
  "timestamp": "Sat 2026-05-16 15:05 GMT+8"
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

[message_id: om_x100b6fb53adee8acc2eb4f3fb665504]
ou_5984d8f20adcac5cc0ee74bf3dae2c54: 具体怎么实现呢？
assistant: 让我先查一下当前环境的实际配置，用真实情况来说明。
assistant: 现在我有了完整的上下文，用实际运行机制来解释：

---

## Skill 和 MCP 的具体协同实现

整个链路分 **三层**：

### 第一层：OpenClaw 的工具系统

OpenClaw 内置了一批**一等公民工具**（如 `exec`、`web_search`、`browser`、`message` 等），这些直接暴露给 AI，是 AI 调用外部世界的主要方式。

### 第二层：Skill 提供知识

Skill 是一个文件夹（`SKILL.md` + 脚本/参考文档/模板），它告诉 AI **在什么场景下、按什么流程、用什么工具**。AI 读取 Skill 后，按照里面的指引去调用 OpenClaw 的工具。

### 第三层：MCP 扩展工具能力

MCP 是一个**标准化的工具协议**，让 AI 能调用外部服务（如 Linear、Notion、数据库等）。OpenClaw 通过 **mcporter** 这个 Skill 来桥接 MCP：

```
用户请求
  ↓
AI 匹配到某个 Skill，加载 SKILL.md
  ↓
Skill 说"用 mcporter 调用 linear MCP 服务器"
  ↓
AI 调用 exec 工具，执行：
  mcporter call linear.list_issues team=ENG limit:5
  ↓
mcporter 通过 MCP 协议连接 Linear 服务器，拿到数据
  ↓
AI 按 Skill 的流程处理数据，返回结果
```

### 具体代码层面

**1. 在 Skill 里引用 MCP 工具：**
```markdown
# bug-triage/SKILL.md
---
name: bug-triage
description: 从 Linear 拉取 bug 并分类
---

## 流程
1. 用 mcporter 拉取紧急 issue：
   `mcporter call linear.list_issues --args '{"team":"ENG","priority":"urgent"}'`
2. 按 references/triage-rules.md 的规则分类
3. 输出优先级排序的报告
```

**2. mcporter 配置 MCP 服务器：**
```bash
# 添加一个 MCP 服务器
mcporter config add linear --url https://mcp.linear.app

# 或者导入已有的 MCP 配置
mcporter config import ~/.config/claude/mcp.json
```

**3. AI 实际执行时：**
```
AI 读取 bug-triage skill
  → 匹配到用户需求
  → 按流程执行 exec("mcporter call linear.list_issues ...")
  → 拿到 JSON 数据
  → 按规则处理，输出结果
```

### 总结

| 层 | 角色 | 实现方式 |
|---|---|---|
| **Skill** | 教 AI 怎么做 | SKILL.md 加载到 AI 上下文 |
| **OpenClaw 工具** | 让 AI 能执行操作 | `exec`、`browser` 等内置工具 |
| **MCP** | 扩展可调用的外部服务 | mcporter 通过 `exec` 调用 MCP 服务器 |

**本质上就是：Skill 写流程 → AI 读 Skill → AI 用 exec 跑 mcporter → mcporter 通过 MCP 协议调外部工具。** 所有东西都通过 OpenClaw 的工具系统串联起来。
