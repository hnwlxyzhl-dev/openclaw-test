# AI 模型选择与 Token 优化指南

> Evolver 整理的模型选择和成本优化技巧

---

## 1. 主流大模型对比

### 1.1 能力层级

| 层级 | 模型 | 特点 | 适用场景 |
|-----|------|------|---------|
| **顶级** | Claude Opus 4.6 | 最强推理，支持 extended thinking | 复杂分析、代码架构 |
| **顶级** | GPT-5.2 | 通用最强，生态完善 | 通用任务 |
| **高级** | Claude Sonnet 4.5 | 性价比高，能力强 | 日常对话、代码 |
| **高级** | Gemini 2.5 Pro | 多模态强，长上下文 | 图像分析、长文档 |
| **中级** | GLM-5 / Qwen3 Max | 中文优化，思考模式 | 中文场景 |
| **经济** | GPT-5-mini / Sonnet Mini | 快速响应 | 简单任务 |
| **免费** | OpenRouter 免费模型 | 零成本 | 测试、非关键任务 |

### 1.2 模型特性对比

| 模型 | 上下文 | 推理 | 代码 | 多模态 | 成本 |
|-----|-------|------|------|--------|------|
| Claude Opus 4.6 | 200K | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$$$ |
| Claude Sonnet 4.5 | 200K | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ |
| GPT-5.2 | 128K | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$$ |
| Gemini 2.5 Pro | 1M | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $$ |
| GLM-5 | 128K | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | $ |
| Qwen3 Max | 32K | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 免费额度 |

---

## 2. Token 优化策略

### 2.1 OpenClaw 内置优化

#### 2.1.1 Prompt Caching (Anthropic)
- **效果**：缓存重复上下文，减少 90% 输入成本
- **配置**：
```json5
{
  agents: {
    defaults: {
      models: {
        "anthropic/claude-opus-4-6": {
          params: { cacheRetention: "long" }  // 1小时
        }
      }
    }
  }
}
```
- **适用场景**：长对话、重复 system prompt

#### 2.1.2 Context Pruning (工具结果裁剪)
- **效果**：自动裁剪旧工具输出，减少 30-50% token
- **模式**：
  - `adaptive`: 超过阈值时裁剪（推荐）
  - `aggressive`: 始终裁剪旧结果
```json5
{
  agents: {
    defaults: {
      contextPruning: {
        mode: "adaptive",
        keepLastAssistants: 3,
        softTrimRatio: 0.3,    // 30% 时软裁剪
        hardClearRatio: 0.5    // 50% 时硬清除
      }
    }
  }
}
```

#### 2.1.3 Compaction (对话压缩)
- **效果**：压缩长对话历史，保留关键信息
- **触发**：上下文接近模型限制时
- **配置**：
```json5
{
  agents: {
    defaults: {
      compaction: {
        mode: "safeguard",    // 或 "default"
        reserveTokensFloor: 20000,
        memoryFlush: {
          enabled: true,      // 压缩前保存记忆
          softThresholdTokens: 4000
        }
      }
    }
  }
}
```

#### 2.1.4 Block Streaming (分块发送)
- **效果**：减少短消息的重复开销
- **配置**：
```json5
{
  agents: {
    defaults: {
      blockStreamingDefault: "on",
      blockStreamingChunk: { minChars: 800, maxChars: 1200 },
      blockStreamingCoalesce: { idleMs: 1000 }
    }
  }
}
```

### 2.2 Prompt 设计优化

#### 2.2.1 System Prompt 精简
- 移除不必要的装饰性文字
- 使用简洁的指令格式
- 合并重复说明

#### 2.2.2 历史限制
```json5
{
  channels: {
    whatsapp: {
      historyLimit: 30,       // 群聊历史
      dmHistoryLimit: 50      // 私聊历史
    }
  },
  messages: {
    groupChat: { historyLimit: 50 }
  }
}
```

#### 2.2.3 Skills 数量控制
- 每个 Skill ≈ 97 字符 + 名称/描述
- 只启用必要的 Skills
- 使用 `skills.allowBundled` 白名单

### 2.3 图像优化

```json5
{
  agents: {
    defaults: {
      imageMaxDimensionPx: 1200,  // 默认 1200
      models: {
        "anthropic/*": {
          params: { imageMaxDimensionPx: 800 }  // 降得更低
        }
      }
    }
  }
}
```

---

## 3. 模型选择决策树

```
任务类型？
├── 复杂推理/分析
│   ├── 需要思考过程 → Claude Opus 4.6 (thinking)
│   └── 常规分析 → Claude Sonnet 4.5 / GPT-5.2
│
├── 代码任务
│   ├── 架构设计 → Claude Opus 4.6
│   ├── 日常编码 → Claude Sonnet 4.5 / GPT-5.2
│   └── 快速原型 → GPT-5-mini / Sonnet Mini
│
├── 中文任务
│   ├── 正式文档 → GLM-5 / Qwen3 Max
│   ├── 日常对话 → GLM-4.7 / Qwen3
│   └── 成本敏感 → Qwen (免费额度)
│
├── 多模态任务
│   ├── 图像分析 → Gemini 2.5 Pro / Claude
│   ├── 视频理解 → Gemini 2.5 Pro
│   └── 文档 OCR → Claude / GPT-4o
│
└── 成本敏感
    ├── 有免费额度 → Qwen / Gemini Flash
    └── 无预算 → OpenRouter 免费模型
```

---

## 4. Fallback 策略

### 4.1 多层 Fallback

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-opus-4-6",
        fallbacks: [
          "anthropic/claude-sonnet-4-5",   // 第一备选
          "openai/gpt-5.2",                // 第二备选
          "google/gemini-2.5-flash",       // 第三备选
          "openrouter/meta-llama/llama-3.3-70b-instruct:free"  // 最后备选
        ]
      }
    }
  }
}
```

### 4.2 按 Provider Fallback

- 每个 Provider 内部有 Auth Profile 轮换
- 限流时自动切换到下一个 Profile
- Profile 耗尽才切换到下一个模型

### 4.3 按任务类型 Fallback

```json5
{
  agents: {
    list: [
      {
        id: "coding",
        model: { primary: "anthropic/claude-opus-4-6" }
      },
      {
        id: "chat",
        model: { primary: "anthropic/claude-sonnet-4-5" }
      }
    ]
  }
}
```

---

## 5. 成本估算

### 5.1 OpenClaw 请求结构

单次请求 Token 组成：
```
总 Token = System Prompt + Skills + 历史上下文 + 当前消息
         ≈ 2000-5000 + (97 × Skills数) + 变长 + 变长
```

### 5.2 成本控制策略

1. **高频轻量任务** → 小模型 + 严格历史限制
2. **低频复杂任务** → 大模型 + 完整上下文
3. **混合场景** → Fallback 策略

### 5.3 监控用量

```bash
openclaw models status     # 查看模型状态
openclaw logs              # 查看日志
```

---

## 6. 模型特定技巧

### 6.1 Anthropic (Claude)

**Extended Thinking**:
- 自动启用（adaptive 模式）
- `/think high/low/off` 手动控制
- 适合复杂推理

**Prompt Caching**:
- 自动应用于 system prompt
- 配置 `cacheRetention: "long"` 延长缓存

**1M 上下文**:
```json5
{
  agents: {
    defaults: {
      models: {
        "anthropic/claude-opus-4-6": {
          params: { context1m: true }
        }
      }
    }
  }
}
```

### 6.2 OpenAI

**Server Compaction**:
- 自动压缩长上下文
- OpenAI Responses API 特性
```json5
{
  agents: {
    defaults: {
      models: {
        "openai/gpt-5.2": {
          params: {
            responsesServerCompaction: true,
            responsesCompactThreshold: 120000
          }
        }
      }
    }
  }
}
```

**WebSocket Warmup**:
- 默认启用，减少首字延迟
- 可禁用：`openaiWsWarmup: false`

### 6.3 Qwen

**免费 OAuth**:
- 每天 2000 次请求
- 支持代码和视觉模型
```bash
openclaw plugins enable qwen-portal-auth
openclaw models auth login --provider qwen-portal --set-default
```

### 6.4 GLM

**思考模式**:
- 自动启用（除非设 `thinking: off`）
- 适合复杂中文任务
```json5
{
  agents: {
    defaults: {
      models: {
        "zai/glm-5": {
          params: { thinking: { type: "enabled" } }
        }
      }
    }
  }
}
```

---

## 7. 本地模型

### 7.1 LM Studio 集成

1. 在 LM Studio 中启动模型
2. 配置 OpenAI 兼容端点：
```json5
{
  models: {
    providers: {
      "lm-studio": {
        baseUrl: "http://localhost:1234/v1",
        api: "openai-completions",
        models: [{ id: "local-model", ... }]
      }
    }
  }
}
```

### 7.2 推荐本地模型

- **MiniMax M2.1**: 高质量，需要好硬件
- **Llama 3.3 70B**: 开源最强
- **Qwen 2.5**: 中文优化

---

_持续更新中..._
