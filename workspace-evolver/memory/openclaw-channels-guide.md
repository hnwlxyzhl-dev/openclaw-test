# OpenClaw 渠道配置指南

> Evolver 整理的 OpenClaw 渠道配置知识

---

## 1. 渠道概述

OpenClaw 支持多种消息渠道，统一接入同一个 Gateway。

### 1.1 支持的渠道

| 渠道 | 类型 | 特点 |
|-----|------|------|
| **WhatsApp** | 内置 | Baileys Web，个人/商业 |
| **Telegram** | 内置 | Bot API，支持流式 |
| **Discord** | 内置 | Bot，支持语音 |
| **Slack** | 内置 | Socket Mode / HTTP |
| **Signal** | 内置 | 隐私优先 |
| **iMessage** | 内置 | macOS only |
| **Feishu** | 扩展 | 飞书机器人 |
| **Google Chat** | 内置 | 服务账号 |
| **Mattermost** | 插件 | 企业协作 |
| **IRC** | 扩展 | 传统协议 |
| **Microsoft Teams** | 扩展 | 企业 IM |

---

## 2. 访问控制

### 2.1 DM 策略

| 策略 | 说明 |
|-----|------|
| `pairing` | 默认，需要配对码确认 |
| `allowlist` | 只有白名单用户 |
| `open` | 允许所有（需 `allowFrom: ["*"]`） |
| `disabled` | 禁用私聊 |

### 2.2 群组策略

| 策略 | 说明 |
|-----|------|
| `allowlist` | 默认，只有白名单群组 |
| `open` | 允许所有群组 |
| `disabled` | 禁用群组 |

### 2.3 提及门控

群组默认需要 @ 提及才响应：

```json5
{
  channels: {
    whatsapp: {
      groups: {
        "*": { requireMention: true }
      }
    }
  },
  agents: {
    list: [{
      id: "main",
      groupChat: {
        mentionPatterns: ["@bot", "bot", "hey bot"]
      }
    }]
  }
}
```

---

## 3. WhatsApp

### 3.1 基本配置

```json5
{
  channels: {
    whatsapp: {
      dmPolicy: "pairing",
      allowFrom: ["+15555550123"],
      sendReadReceipts: true,
      mediaMaxMb: 50,
      groups: {
        "*": { requireMention: true }
      }
    }
  }
}
```

### 3.2 多账号

```json5
{
  channels: {
    whatsapp: {
      accounts: {
        personal: {},
        biz: {}
      }
    }
  }
}
```

登录：
```bash
openclaw channels login --channel whatsapp --account personal
```

---

## 4. Telegram

### 4.1 基本配置

```json5
{
  channels: {
    telegram: {
      enabled: true,
      botToken: "your-bot-token",
      dmPolicy: "pairing",
      historyLimit: 50,
      streaming: "partial",
      linkPreview: true,
      groups: {
        "*": { requireMention: true },
        "-1001234567890": {
          topics: {
            "99": { requireMention: false }
          }
        }
      }
    }
  }
}
```

### 4.2 流式输出

- `off`: 禁用
- `partial`: 部分流式（推荐）
- `block`: 块流式
- `progress`: 进度条

### 4.3 自定义命令

```json5
{
  channels: {
    telegram: {
      customCommands: [
        { command: "backup", description: "Git backup" },
        { command: "generate", description: "Create image" }
      ]
    }
  }
}
```

---

## 5. Discord

### 5.1 基本配置

```json5
{
  channels: {
    discord: {
      enabled: true,
      token: "your-bot-token",
      dmPolicy: "pairing",
      historyLimit: 20,
      streaming: "partial",
      guilds: {
        "123456789012345678": {
          slug: "my-server",
          requireMention: false,
          channels: {
            general: { allow: true },
            help: { allow: true, requireMention: true }
          }
        }
      }
    }
  }
}
```

### 5.2 语音功能

```json5
{
  channels: {
    discord: {
      voice: {
        enabled: true,
        autoJoin: [{
          guildId: "123456789012345678",
          channelId: "234567890123456789"
        }],
        tts: {
          provider: "openai",
          openai: { voice: "alloy" }
        }
      }
    }
  }
}
```

### 5.3 线程绑定

```json5
{
  channels: {
    discord: {
      threadBindings: {
        enabled: true,
        idleHours: 24,
        maxAgeHours: 0,
        spawnSubagentSessions: false
      }
    }
  }
}
```

---

## 6. Slack

### 6.1 基本配置

```json5
{
  channels: {
    slack: {
      enabled: true,
      botToken: "xoxb-...",
      appToken: "xapp-...",
      dmPolicy: "pairing",
      historyLimit: 50,
      streaming: "partial",
      channels: {
        "C123": { allow: true, requireMention: true }
      }
    }
  }
}
```

### 6.2 线程隔离

```json5
{
  channels: {
    slack: {
      thread: {
        historyScope: "thread",  // thread | channel
        inheritParent: false
      }
    }
  }
}
```

---

## 7. Signal

```json5
{
  channels: {
    signal: {
      enabled: true,
      account: "+15555550123",
      dmPolicy: "pairing",
      allowFrom: ["+15551234567"],
      historyLimit: 50,
      reactionNotifications: "own"
    }
  }
}
```

---

## 8. iMessage

```json5
{
  channels: {
    imessage: {
      enabled: true,
      cliPath: "imsg",
      dbPath: "~/Library/Messages/chat.db",
      remoteHost: "user@gateway-host",
      dmPolicy: "pairing",
      allowFrom: ["+15555550123", "chat_id:123"],
      historyLimit: 50,
      mediaMaxMb: 16
    }
  }
}
```

**注意**：需要 Full Disk Access 权限访问 Messages 数据库。

---

## 9. Feishu (飞书)

```json5
{
  channels: {
    feishu: {
      enabled: true,
      appId: "cli_xxx",
      appSecret: "xxx",
      dmPolicy: "pairing",
      encryptKey: "xxx",
      verificationToken: "xxx"
    }
  }
}
```

---

## 10. 渠道模型覆盖

为特定渠道指定模型：

```json5
{
  channels: {
    modelByChannel: {
      discord: {
        "123456789012345678": "anthropic/claude-opus-4-6"
      },
      telegram: {
        "-1001234567890": "openai/gpt-4.1-mini"
      }
    }
  }
}
```

---

## 11. 历史限制

### 11.1 群组历史

```json5
{
  messages: {
    groupChat: { historyLimit: 50 }
  }
}
```

### 11.2 私聊历史

```json5
{
  channels: {
    telegram: {
      dmHistoryLimit: 30,
      dms: {
        "123456789": { historyLimit: 50 }
      }
    }
  }
}
```

---

## 12. 消息分块

```json5
{
  channels: {
    whatsapp: {
      textChunkLimit: 4000,
      chunkMode: "length"  // length | newline
    }
  }
}
```

---

## 13. 重试策略

```json5
{
  channels: {
    telegram: {
      retry: {
        attempts: 3,
        minDelayMs: 400,
        maxDelayMs: 30000,
        jitter: 0.1
      }
    }
  }
}
```

---

_持续更新中..._
