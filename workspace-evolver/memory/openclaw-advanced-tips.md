# OpenClaw 高级技巧

> Evolver 整理的 OpenClaw 使用技巧

---

## 1. 配置技巧

### 1.1 配置拆分 ($include)

大型配置可以拆分成多个文件：

```json5
// ~/.openclaw/openclaw.json
{
  agents: { $include: "./agents.json5" },
  channels: { $include: "./channels.json5" },
  bindings: { $include: "./bindings.json5" }
}
```

### 1.2 环境变量替换

配置中引用环境变量：
```json5
{
  models: {
    providers: {
      custom: {
        apiKey: "${CUSTOM_API_KEY}",
        baseUrl: "${API_BASE}/v1"
      }
    }
  }
}
```

### 1.3 热重载

- 大部分配置变更自动生效
- `gateway.reload.mode`:
  - `hybrid` (默认): 安全变更热加载，需要重启的自动重启
  - `hot`: 只热加载，不自动重启
  - `restart`: 任何变更都重启
  - `off`: 禁用热重载

---

## 2. 多智能体高级配置

### 2.1 按发送者路由

```json5
{
  agents: {
    list: [
      { id: "personal", default: true },
      { id: "work" }
    ]
  },
  bindings: [
    {
      agentId: "personal",
      match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551230001" } }
    },
    {
      agentId: "work",
      match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551230002" } }
    }
  ]
}
```

### 2.2 按群组路由

```json5
{
  bindings: [
    {
      agentId: "family",
      match: {
        channel: "whatsapp",
        peer: { kind: "group", id: "120363...@g.us" }
      }
    }
  ]
}
```

### 2.3 按 Discord 角色路由

```json5
{
  bindings: [
    {
      agentId: "admin",
      match: {
        channel: "discord",
        guildId: "123456",
        roles: ["admin", "moderator"]
      }
    }
  ]
}
```

### 2.4 按账号路由

```json5
{
  channels: {
    whatsapp: {
      accounts: {
        personal: {},
        biz: {}
      }
    }
  },
  bindings: [
    { agentId: "home", match: { channel: "whatsapp", accountId: "personal" } },
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } }
  ]
}
```

---

## 3. 沙箱高级配置

### 3.1 自定义镜像

```json5
{
  agents: {
    defaults: {
      sandbox: {
        docker: {
          image: "my-custom-sandbox:v1",
          setupCommand: "apt-get update && apt-get install -y git curl"
        }
      }
    }
  }
}
```

### 3.2 网络访问

```json5
{
  agents: {
    defaults: {
      sandbox: {
        docker: {
          network: "bridge",  // 允许网络
          dns: ["1.1.1.1", "8.8.8.8"]
        }
      }
    }
  }
}
```

### 3.3 资源限制

```json5
{
  agents: {
    defaults: {
      sandbox: {
        docker: {
          memory: "1g",
          cpus: 1,
          pidsLimit: 256,
          ulimits: {
            nofile: { soft: 1024, hard: 2048 }
          }
        }
      }
    }
  }
}
```

### 3.4 沙箱浏览器

```json5
{
  agents: {
    defaults: {
      sandbox: {
        browser: {
          enabled: true,
          cdpPort: 9222,
          noVncPort: 6080,
          enableNoVnc: true
        }
      }
    }
  }
}
```

---

## 4. 消息处理技巧

### 4.1 入站消息防抖

合并连续快速消息：
```json5
{
  messages: {
    inbound: {
      debounceMs: 2000,
      byChannel: {
        whatsapp: 5000,
        telegram: 3000
      }
    }
  }
}
```

### 4.2 出站消息队列

当 Agent 正在运行时处理新消息：
```json5
{
  messages: {
    queue: {
      mode: "collect",  // steer | followup | collect | interrupt
      debounceMs: 1000,
      cap: 20,
      drop: "summarize"  // old | new | summarize
    }
  }
}
```

### 4.3 自定义前缀

```json5
{
  messages: {
    responsePrefix: "[{model}]",  // 或 "auto" 使用 Agent 名
    ackReaction: "👀",
    ackReactionScope: "group-mentions",
    removeAckAfterReply: false
  }
}
```

### 4.4 群组提及模式

```json5
{
  agents: {
    list: [{
      id: "main",
      groupChat: {
        mentionPatterns: ["@bot", "bot", "hey bot"]
      }
    }]
  },
  channels: {
    whatsapp: {
      groups: { "*": { requireMention: true } }
    }
  }
}
```

---

## 5. 子智能体 (Subagents)

### 5.1 启动子智能体

```json5
// 通过工具调用
sessions_spawn({
  task: "分析这个代码库并生成文档",
  runtime: "subagent",
  mode: "run",  // 或 "session" (持久)
  model: "anthropic/claude-opus-4-6",
  timeoutSeconds: 600
})
```

### 5.2 子智能体配置

```json5
{
  agents: {
    defaults: {
      subagents: {
        model: "anthropic/claude-sonnet-4-5",
        maxConcurrent: 1,
        archiveAfterMinutes: 60
      }
    }
  }
}
```

### 5.3 ACP 编码智能体

```json5
sessions_spawn({
  task: "修复这个 bug",
  runtime: "acp",
  agentId: "claude-code",  // 或 "codex", "gemini"
  thread: true,  // Discord 线程绑定
  mode: "session"
})
```

---

## 6. 浏览器自动化

### 6.1 多 Profile 配置

```json5
{
  browser: {
    defaultProfile: "work",
    profiles: {
      personal: { cdpPort: 18800, color: "#FF4500" },
      work: { cdpPort: 18801, color: "#0066CC" },
      remote: { cdpUrl: "http://10.0.0.42:9222" }
    }
  }
}
```

### 6.2 浏览器工具流程

1. `browser` → `status` / `start`
2. `snapshot` (获取页面结构)
3. `act` (执行操作)
4. `screenshot` (可选确认)

### 6.3 远程浏览器

```json5
{
  browser: {
    profiles: {
      remote: {
        cdpUrl: "http://remote-server:9222",
        attachOnly: true  // 只附加，不管理
      }
    }
  }
}
```

---

## 7. 定时任务 (Cron)

### 7.1 配置

```json5
{
  cron: {
    enabled: true,
    maxConcurrentRuns: 2,
    sessionRetention: "24h"
  }
}
```

### 7.2 创建任务

```json5
cron({
  action: "add",
  job: {
    id: "daily-summary",
    schedule: "0 9 * * *",  // 每天 9 点
    agentId: "main",
    prompt: "生成每日摘要",
    target: { channel: "telegram", chatId: "123" }
  }
})
```

---

## 8. Web 搜索与抓取

### 8.1 配置

```json5
{
  tools: {
    web: {
      search: {
        enabled: true,
        apiKey: "${BRAVE_API_KEY}",
        maxResults: 5
      },
      fetch: {
        enabled: true,
        maxChars: 50000
      }
    }
  }
}
```

### 8.2 Firecrawl 回退

```json5
{
  tools: {
    web: {
      fetch: {
        firecrawl: {
          enabled: true,
          apiKey: "${FIRECRAWL_API_KEY}"
        }
      }
    }
  }
}
```

---

## 9. 媒体处理

### 9.1 语音转文字

```json5
{
  tools: {
    media: {
      audio: {
        enabled: true,
        models: [
          { provider: "openai", model: "gpt-4o-mini-transcribe" },
          { provider: "groq", model: "whisper-large-v3-turbo" }
        ]
      }
    }
  }
}
```

### 9.2 视频理解

```json5
{
  tools: {
    media: {
      video: {
        enabled: true,
        models: [{ provider: "google", model: "gemini-2.5-flash" }]
      }
    }
  }
}
```

### 9.3 图片分析

```json5
{
  tools: {
    media: {
      image: {
        enabled: true,
        maxBytes: "10MB",
        models: [
          { provider: "anthropic" },
          { provider: "openai" }
        ]
      }
    }
  }
}
```

---

## 10. TTS 语音合成

### 10.1 配置

```json5
{
  messages: {
    tts: {
      auto: "always",  // off | always | inbound | tagged
      provider: "elevenlabs",
      elevenlabs: {
        apiKey: "${ELEVENLABS_API_KEY}",
        voiceId: "voice_id",
        modelId: "eleven_multilingual_v2"
      }
    }
  }
}
```

### 10.2 临时触发

```
/tts on    // 开启
/tts off   // 关闭
```

---

_持续更新中..._
