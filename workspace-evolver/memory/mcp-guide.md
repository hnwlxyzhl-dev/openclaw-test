# MCP (Model Context Protocol) 指南

> Evolver 整理的 MCP 知识

---

## 1. MCP 概述

MCP (Model Context Protocol) 是一个开放协议，让 AI 模型能够与外部工具和数据源交互。

### 1.1 核心概念

| 概念 | 说明 |
|-----|------|
| **Server** | MCP 服务器，提供工具和资源 |
| **Client** | MCP 客户端，连接服务器 |
| **Tool** | 可调用的工具 |
| **Resource** | 可访问的资源 |
| **Prompt** | 预定义的提示模板 |

### 1.2 OpenClaw 中的 MCP

OpenClaw 支持 MCP 作为工具扩展机制：
- 自动发现 MCP 服务器
- 将 MCP 工具映射为 OpenClaw 工具
- 支持 stdio 和 HTTP 传输

---

## 2. MCP 服务器发现

### 2.1 发现位置

OpenClaw 自动从以下位置发现 MCP 服务器：

| 位置 | 说明 |
|-----|------|
| `~/.openclaw/mcp/` | 用户级 MCP 服务器 |
| `<workspace>/mcp/` | 工作区 MCP 服务器 |
| 配置文件 `mcp.servers` | 手动配置的服务器 |

### 2.2 服务器配置

```json5
{
  mcp: {
    servers: {
      "my-server": {
        command: "node",
        args: ["server.js"],
        env: {
          API_KEY: "xxx"
        },
        cwd: "/path/to/server"
      }
    }
  }
}
```

### 2.3 Discovery 命令

```bash
# 列出已发现的 MCP 服务器
openclaw mcp list

# 查看服务器详情
openclaw mcp info <server-id>

# 测试服务器连接
openclaw mcp test <server-id>
```

---

## 3. MCP 工具使用

### 3.1 自动映射

MCP 工具自动映射为 OpenClaw 工具：
- 工具名称：`mcp_<server>_<tool>`
- 参数：保持原有结构
- 返回值：自动解析

### 3.2 调用示例

```typescript
// MCP 工具自动可用
await mcp_filesystem_readFile({ path: "/tmp/test.txt" });
await mcp_github_searchRepos({ query: "openclaw" });
```

---

## 4. 创建 MCP 服务器

### 4.1 基本结构

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server(
  { name: "my-server", version: "1.0.0" },
  {
    capabilities: {
      tools: {},
      resources: {}
    }
  }
);

// 注册工具
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "my_tool",
      description: "工具描述",
      inputSchema: {
        type: "object",
        properties: {
          arg1: { type: "string" }
        }
      }
    }
  ]
}));

// 处理工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "my_tool") {
    return { content: [{ type: "text", text: "result" }] };
  }
});

// 启动服务器
const transport = new StdioServerTransport();
await server.connect(transport);
```

### 4.2 package.json

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "my-mcp-server": "./index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  }
}
```

---

## 5. 常用 MCP 服务器

### 5.1 官方服务器

| 服务器 | 功能 |
|-------|------|
| `@modelcontextprotocol/server-filesystem` | 文件系统访问 |
| `@modelcontextprotocol/server-github` | GitHub API |
| `@modelcontextprotocol/server-postgres` | PostgreSQL 数据库 |
| `@modelcontextprotocol/server-sqlite` | SQLite 数据库 |
| `@modelcontextprotocol/server-puppeteer` | 浏览器自动化 |
| `@modelcontextprotocol/server-slack` | Slack 集成 |

### 5.2 安装

```bash
# 安装 MCP 服务器
npm install -g @modelcontextprotocol/server-filesystem

# 配置 OpenClaw
openclaw mcp add filesystem --command "mcp-server-filesystem" --args "/path/to/allowed/dir"
```

---

## 6. Sampling (采样)

### 6.1 概述

Sampling 允许 MCP 服务器请求 LLM 生成文本：
- 服务器发起 LLM 调用
- 客户端控制是否允许
- 支持模型选择和参数配置

### 6.2 配置

```json5
{
  mcp: {
    sampling: {
      enabled: true,
      model: "anthropic/claude-sonnet-4-5",
      maxTokens: 1000,
      requiresApproval: false
    }
  }
}
```

---

## 7. 安全考虑

### 7.1 服务器信任

- MCP 服务器在 OpenClaw 进程内运行
- 需要信任服务器代码
- 限制网络访问

### 7.2 工具权限

- 使用 `tools.allow/deny` 控制 MCP 工具
- 敏感操作需要审批
- 审计日志记录

### 7.3 配置示例

```json5
{
  mcp: {
    servers: {
      "trusted-server": {
        command: "node",
        args: ["trusted.js"],
        timeout: 30000
      }
    }
  },
  tools: {
    allow: ["mcp_trusted-server_*"],
    deny: ["mcp_*_delete*", "mcp_*_write*"]
  }
}
```

---

## 8. 调试

### 8.1 日志

```bash
# 查看 MCP 日志
openclaw logs --filter mcp

# 启用调试模式
MCP_DEBUG=1 openclaw gateway start
```

### 8.2 常见问题

| 问题 | 解决方案 |
|-----|---------|
| 服务器未发现 | 检查配置路径 |
| 工具调用失败 | 检查参数格式 |
| 连接超时 | 增加超时时间 |
| 权限错误 | 检查工具权限配置 |

---

## 9. MCP vs Skills

| 特性 | MCP | Skills |
|-----|-----|--------|
| **来源** | 第三方协议 | OpenClaw 原生 |
| **开发** | TypeScript/Python | Markdown + 脚本 |
| **工具** | 自动映射 | 手动定义 |
| **发现** | 自动 | 配置驱动 |
| **适用** | 通用工具 | 领域知识 |

**建议**：
- 需要复杂工具能力 → MCP
- 需要提供领域知识/指南 → Skills
- 两者可以共存

---

_持续更新中..._
