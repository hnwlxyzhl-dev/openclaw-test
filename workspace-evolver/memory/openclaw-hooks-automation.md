# OpenClaw Hooks 与自动化

> Evolver 整理的 OpenClaw 自动化知识

---

## 1. Hooks 概述

Hooks 是 OpenClaw 的事件驱动系统，允许在特定事件发生时执行自定义脚本。

### 1.1 Hook 类型

| 类型 | 说明 |
|-----|------|
| **Hooks** | Gateway 内部事件触发（/new, /reset, /stop 等） |
| **Webhooks** | 外部 HTTP 请求触发 |
| **Plugin Hooks** | 插件内提供的钩子 |

### 1.2 常用场景

- 会话重置时保存记忆
- 记录命令审计日志
- 会话开始/结束触发自动化
- 写入文件到工作区或调用外部 API

---

## 2. 内置 Hooks

### 2.1 session-memory

**功能**：会话重置时保存上下文到记忆文件

**事件**：`command:new`, `command:reset`

**输出**：`<workspace>/memory/YYYY-MM-DD-slug.md`

**启用**：
```bash
openclaw hooks enable session-memory
```

### 2.2 command-logger

**功能**：记录所有命令到审计日志

**事件**：`command`

**输出**：`~/.openclaw/logs/commands.log`

**启用**：
```bash
openclaw hooks enable command-logger
```

### 2.3 bootstrap-extra-files

**功能**：注入额外的启动文件

**事件**：`agent:bootstrap`

**配置**：
```json5
{
  hooks: {
    internal: {
      entries: {
        "bootstrap-extra-files": {
          enabled: true,
          paths: ["packages/*/AGENTS.md", "packages/*/TOOLS.md"]
        }
      }
    }
  }
}
```

### 2.4 boot-md

**功能**：Gateway 启动时运行 BOOT.md

**事件**：`gateway:startup`

**启用**：
```bash
openclaw hooks enable boot-md
```

---

## 3. 事件类型

### 3.1 命令事件

| 事件 | 说明 |
|-----|------|
| `command` | 所有命令 |
| `command:new` | /new 命令 |
| `command:reset` | /reset 命令 |
| `command:stop` | /stop 命令 |

### 3.2 会话事件

| 事件 | 说明 |
|-----|------|
| `session:compact:before` | 压缩前 |
| `session:compact:after` | 压缩后 |
| `session:patch` | 会话属性修改 |

### 3.3 消息事件

| 事件 | 说明 |
|-----|------|
| `message` | 所有消息 |
| `message:received` | 接收消息 |
| `message:transcribed` | 语音转录后 |
| `message:preprocessed` | 预处理后 |
| `message:sent` | 发送消息后 |

### 3.4 Agent 事件

| 事件 | 说明 |
|-----|------|
| `agent:bootstrap` | Agent 启动引导 |

### 3.5 Gateway 事件

| 事件 | 说明 |
|-----|------|
| `gateway:startup` | Gateway 启动 |

---

## 4. 创建自定义 Hook

### 4.1 目录结构

```
my-hook/
├── HOOK.md          # 元数据 + 文档
└── handler.ts       # 处理函数
```

### 4.2 HOOK.md 格式

```markdown
---
name: my-hook
description: "钩子描述"
metadata:
  {
    "openclaw": {
      "emoji": "🔧",
      "events": ["command:new"],
      "requires": { "bins": ["node"] }
    }
  }
---

# My Hook

详细说明...
```

### 4.3 Handler 实现

```typescript
const handler = async (event) => {
  if (event.type !== "command" || event.action !== "new") {
    return;
  }

  console.log(`[my-hook] Triggered for session: ${event.sessionKey}`);

  // 自定义逻辑

  // 可选：发送消息给用户
  event.messages.push("✨ Hook executed!");
};

export default handler;
```

### 4.4 事件上下文

```typescript
{
  type: 'command' | 'session' | 'agent' | 'gateway' | 'message',
  action: string,
  sessionKey: string,
  timestamp: Date,
  messages: string[],
  context: {
    sessionEntry?: SessionEntry,
    commandSource?: string,
    senderId?: string,
    workspaceDir?: string,
    // ...
  }
}
```

---

## 5. Hook 发现位置

| 位置 | 优先级 | 说明 |
|-----|-------|------|
| Bundled | 低 | 内置钩子 |
| Plugin | 中 | 插件提供 |
| Managed (`~/.openclaw/hooks/`) | 高 | 用户安装 |
| Workspace (`<workspace>/hooks/`) | 最高 | 工作区本地 |

---

## 6. Hook Pack (npm 包)

### 6.1 package.json 格式

```json
{
  "name": "@acme/my-hooks",
  "version": "0.1.0",
  "openclaw": {
    "hooks": ["./hooks/my-hook", "./hooks/other-hook"]
  }
}
```

### 6.2 安装

```bash
openclaw plugins install @acme/my-hooks
```

---

## 7. CLI 命令

```bash
# 列出所有钩子
openclaw hooks list

# 只显示可用的钩子
openclaw hooks list --eligible

# 详细输出
openclaw hooks list --verbose

# JSON 输出
openclaw hooks list --json

# 查看钩子信息
openclaw hooks info session-memory

# 检查可用性
openclaw hooks check

# 启用/禁用
openclaw hooks enable session-memory
openclaw hooks disable command-logger
```

---

## 8. 配置

### 8.1 新格式（推荐）

```json5
{
  hooks: {
    internal: {
      enabled: true,
      entries: {
        "session-memory": { enabled: true },
        "command-logger": { enabled: false }
      }
    }
  }
}
```

### 8.2 额外目录

```json5
{
  hooks: {
    internal: {
      enabled: true,
      load: {
        extraDirs: ["/path/to/more/hooks"]
      }
    }
  }
}
```

### 8.3 Per-Hook 环境变量

```json5
{
  hooks: {
    internal: {
      entries: {
        "my-hook": {
          enabled: true,
          env: {
            "MY_CUSTOM_VAR": "value"
          }
        }
      }
    }
  }
}
```

---

## 9. 最佳实践

### 9.1 保持处理程序快速

Hooks 在命令处理期间运行，保持轻量：

```typescript
// ✓ 好 - 异步工作，立即返回
const handler = async (event) => {
  setImmediate(() => doHeavyWork());
};

// ✗ 差 - 阻塞处理
const handler = async (event) => {
  await doHeavyWork(); // 阻塞
};
```

### 9.2 错误处理

```typescript
const handler = async (event) => {
  try {
    await riskyOperation();
  } catch (err) {
    console.error("[my-hook] Error:", err);
    // 不要抛出 - 避免阻断主流程
  }
};
```

### 9.3 安全考虑

- 工作区 Hooks 默认禁用，需显式启用
- Hooks 在 Gateway 进程内运行，视为可信代码
- 避免在 Hooks 中处理敏感数据

---

_持续更新中..._
