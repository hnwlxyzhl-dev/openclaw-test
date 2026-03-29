# 多智能体协作指南

> Evolver 整理的多智能体协作知识

---

## 1. 什么是多智能体系统

### 1.1 定义

**Agentic Systems** 分为两类：

| 类型 | 说明 | 特点 |
|-----|------|------|
| **Workflows** | LLM 和工具通过预定义代码路径编排 | 可预测、一致性 |
| **Agents** | LLM 动态控制自己的流程和工具使用 | 灵活、自主决策 |

### 1.2 核心概念

| 概念 | 说明 |
|-----|------|
| **Agent** | 一个"大脑"，有独立的工作区、身份、会话 |
| **Workspace** | 独立的文件和配置（AGENTS.md, SOUL.md, USER.md） |
| **Session** | 独立的聊天历史和状态 |
| **Binding** | 路由规则，决定消息发给哪个 Agent |

---

## 2. Anthropic 推荐的模式

### 2.1 构建块：增强型 LLM

基础组件是增强了以下能力的 LLM：
- **检索 (Retrieval)** - 访问外部知识
- **工具 (Tools)** - 执行操作
- **记忆 (Memory)** - 保持上下文

### 2.2 Workflow 模式

#### 2.2.1 Prompt Chaining（提示链）

**原理**：将任务分解为顺序步骤，每步的输出是下一步的输入。

```
步骤1 → 检查点 → 步骤2 → 检查点 → 步骤3
```

**适用场景**：
- 营销文案生成 + 翻译
- 大纲生成 → 检查 → 文档编写

**代码示例**：
```python
# 步骤1：生成大纲
outline = llm("生成文档大纲", input=topic)

# 步骤2：检查大纲
if not validate(outline):
    return "大纲不符合要求"

# 步骤3：基于大纲写文档
document = llm("基于大纲写文档", outline=outline)
```

#### 2.2.2 Routing（路由）

**原理**：分类输入，路由到专门的后续任务。

```
输入 → 分类器 → 路由A / 路由B / 路由C
```

**适用场景**：
- 客服：一般问题 / 退款 / 技术支持
- 简单问题用小模型，复杂问题用大模型

**代码示例**：
```python
# 分类
category = classify(user_input)

# 路由到不同处理
if category == "refund":
    result = handle_refund(user_input)
elif category == "technical":
    result = handle_technical(user_input)
else:
    result = handle_general(user_input)
```

#### 2.2.3 Parallelization（并行化）

**两种变体**：
- **Sectioning**：任务分解为独立子任务并行执行
- **Voting**：同一任务多次执行，汇总结果

```
        ┌→ 子任务A →┐
输入 →──┼→ 子任务B →┼→ 汇总 → 输出
        └→ 子任务C →┘
```

**适用场景**：
- 护栏：一个模型处理请求，另一个检查安全性
- 代码审查：多个检查器并行运行
- 内容审核：多个评估器投票

**代码示例**：
```python
import asyncio

async def parallel_workflow(input):
    # 并行执行
    results = await asyncio.gather(
        check_security(input),
        check_quality(input),
        check_relevance(input)
    )
    return aggregate(results)
```

#### 2.2.4 Orchestrator-Workers（编排者-工作者）

**原理**：中央 LLM 动态分解任务，委托给工作者 LLM，综合结果。

```
             ┌→ Worker A →┐
用户 → 编排者 ─┼→ Worker B →┼→ 编排者 → 结果
             └→ Worker C →┘
```

**与并行化的区别**：子任务不是预定义的，由编排者根据输入动态决定。

**适用场景**：
- 编码产品：多文件修改
- 搜索任务：多源信息收集分析

**代码示例**：
```python
def orchestrator_workers(task):
    # 编排者分析任务
    subtasks = orchestrator.plan(task)

    # 工作者并行执行
    results = []
    for subtask in subtasks:
        results.append(worker(subtask))

    # 编排者综合结果
    return orchestrator.synthesize(results)
```

#### 2.2.5 Evaluator-Optimizer（评估者-优化者）

**原理**：一个 LLM 生成响应，另一个提供评估和反馈，循环迭代。

```
生成者 → 评估者 → 反馈 → 生成者 → ... → 最终结果
```

**适用场景**：
- 文学翻译：评估者提供细微差别反馈
- 复杂搜索：多轮搜索分析

**代码示例**：
```python
def evaluator_optimizer(task, max_iterations=3):
    response = generator(task)

    for i in range(max_iterations):
        evaluation = evaluator(task, response)

        if evaluation.is_good:
            return response

        response = generator.improve(task, response, evaluation.feedback)

    return response
```

### 2.3 Autonomous Agents（自主智能体）

**原理**：智能体从用户指令开始，规划并独立操作，可能需要时返回人类反馈。

```
用户指令 → 智能体规划 → 工具调用 → 评估 → 继续或完成
                      ↑                    │
                      └────────────────────┘
```

**适用场景**：
- 编码智能体（SWE-bench）
- 计算机使用智能体

**关键原则**：
1. **简单性**：智能体设计保持简单
2. **透明性**：明确展示规划步骤
3. **ACI 设计**：精心设计智能体-计算机接口（工具文档）

---

## 3. OpenClaw 多智能体实现

### 3.1 路由模式

#### 基本配置

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

#### 路由优先级

1. `peer` 匹配（精确 DM/群组/频道 ID）
2. `parentPeer` 匹配（线程继承）
3. `guildId + roles`（Discord 角色路由）
4. `guildId`（Discord 服务器）
5. `teamId`（Slack 团队）
6. `accountId` 匹配
7. `accountId: "*"`（渠道级别）
8. 默认 Agent

#### 按发送者路由

```json5
{
  bindings: [
    {
      agentId: "alex",
      match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551230001" } }
    },
    {
      agentId: "mia",
      match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551230002" } }
    }
  ]
}
```

#### 按渠道路由

```json5
{
  agents: {
    list: [
      { id: "chat", model: "anthropic/claude-sonnet-4-5" },
      { id: "opus", model: "anthropic/claude-opus-4-6" }
    ]
  },
  bindings: [
    { agentId: "chat", match: { channel: "whatsapp" } },
    { agentId: "opus", match: { channel: "telegram" } }
  ]
}
```

### 3.2 子智能体模式

#### 启动子智能体

```typescript
// 工具调用
sessions_spawn({
  task: "分析这个代码库并生成文档",
  runtime: "subagent",
  mode: "run",  // 或 "session"（持久）
  model: "anthropic/claude-sonnet-4-5",
  thinking: "medium",
  runTimeoutSeconds: 600
})
```

#### 嵌套子智能体（编排者模式）

```json5
{
  agents: {
    defaults: {
      subagents: {
        maxSpawnDepth: 2,           // 允许一层嵌套
        maxChildrenPerAgent: 5,     // 每个 Agent 最多 5 个子
        maxConcurrent: 8,           // 全局并发上限
        runTimeoutSeconds: 900
      }
    }
  }
}
```

**深度层级**：

| 深度 | 会话键 | 角色 | 可否生成子智能体 |
|-----|--------|------|-----------------|
| 0 | `agent:<id>:main` | 主智能体 | 始终可以 |
| 1 | `agent:<id>:subagent:<uuid>` | 子智能体（编排者） | 仅当 maxSpawnDepth >= 2 |
| 2 | `agent:<id>:subagent:<uuid>:subagent:<uuid>` | 子子智能体（工作者） | 从不 |

#### 子智能体命令

```bash
/subagents list
/subagents spawn <agentId> <task> --model <model>
/subagents kill <id|#|all>
/subagents log <id|#>
/subagents steer <id|#> <message>
```

### 3.3 线程绑定（Discord）

```json5
{
  channels: {
    discord: {
      threadBindings: {
        enabled: true,
        idleHours: 24,
        maxAgeHours: 0,
        spawnSubagentSessions: true
      }
    }
  }
}
```

**命令**：
```
/focus <subagent-label>   # 绑定线程到子智能体
/unfocus                  # 解绑
/agents                   # 列出活动运行和绑定状态
/session idle <duration>  # 设置空闲超时
```

---

## 4. 多智能体框架

### 4.1 主流框架

| 框架 | 特点 | 适用场景 |
|-----|------|---------|
| **Claude Agent SDK** | Anthropic 官方 | Claude 智能体 |
| **Strands Agents SDK** | AWS 官方 | AWS 生态集成 |
| **LangGraph** | 有状态工作流 | 复杂编排 |
| **AutoGen** | 微软，多智能体对话 | 协作场景 |
| **CrewAI** | 角色扮演智能体 | 团队模拟 |
| **Rivet** | 可视化拖拽 | 原型设计 |
| **Vellum** | GUI 工作流构建 | 企业级 |

### 4.2 OpenClaw vs 其他框架

| 特性 | OpenClaw | LangGraph | AutoGen | CrewAI |
|-----|----------|-----------|---------|--------|
| **多渠道** | ✅ | ❌ | ❌ | ❌ |
| **持久会话** | ✅ | 部分 | ❌ | ❌ |
| **子智能体** | ✅ | ✅ | ✅ | ✅ |
| **线程绑定** | ✅ | ❌ | ❌ | ❌ |
| **沙箱隔离** | ✅ | ❌ | ❌ | ❌ |
| **路由** | ✅ | ❌ | ❌ | ❌ |

---

## 5. 最佳实践

### 5.1 Anthropic 原则

1. **简单优先**：从简单提示开始，按需增加复杂度
2. **透明性**：明确展示智能体的规划步骤
3. **ACI 设计**：工具文档和测试要精心设计

### 5.2 何时使用多智能体

| 场景 | 推荐方案 |
|-----|---------|
| 简单任务 | 单个 LLM 调用 + 检索 |
| 固定步骤 | Prompt Chaining |
| 分类任务 | Routing |
| 可并行 | Parallelization |
| 动态分解 | Orchestrator-Workers |
| 需迭代优化 | Evaluator-Optimizer |
| 开放式任务 | Autonomous Agent |

### 5.3 成本优化

- 子智能体使用更便宜的模型
- 配置 `runTimeoutSeconds` 防止无限运行
- 使用 `maxConcurrent` 控制并发

```json5
{
  agents: {
    defaults: {
      subagents: {
        model: "anthropic/claude-sonnet-4-5",  // 子智能体用便宜模型
        maxConcurrent: 3
      }
    }
  }
}
```

### 5.4 安全考虑

- 子智能体默认无会话工具
- 沙箱隔离执行
- 工具权限分级

---

## 6. 示例场景

### 6.1 客服系统

```
用户消息 → 路由 → 退款 Agent / 技术 Agent / 一般 Agent
                    ↓
              子智能体（查询订单、执行退款）
                    ↓
              汇总回复用户
```

### 6.2 编码助手

```
用户请求 → 编排者 Agent
              ↓
         分析需要修改的文件
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
  Worker   Worker   Worker
  (文件1)  (文件2)  (文件3)
    ↓         ↓         ↓
    └─────────┼─────────┘
              ↓
         评估者检查
              ↓
         通过或重试
```

### 6.3 内容生产

```
主题 → 大纲生成器 → 内容编写 → 编辑审查 → 发布
           ↑________________↓
              反馈循环
```

---

_持续更新中..._
