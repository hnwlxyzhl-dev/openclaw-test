# OpenClaw 流式传输与 TTS 指南

> Evolver 整理的流式传输和语音合成知识

---

## 1. 流式传输概述

OpenClaw 有两个独立的流式层：

| 层级 | 说明 |
|-----|------|
| **Block Streaming** | 发送完成的消息块（渠道消息） |
| **Preview Streaming** | 更新临时预览消息（Telegram/Discord/Slack） |

**注意**：没有真正的 token-delta 流式传输到渠道消息。预览流式是基于消息的（发送 + 编辑/追加）。

---

## 2. Block Streaming

### 2.1 工作原理

```
Model output
  └─ text_delta/events
       ├─ (blockStreamingBreak=text_end)
       │    └─ chunker emits blocks as buffer grows
       └─ (blockStreamingBreak=message_end)
            └─ chunker flushes at message_end
                   └─ channel send (block replies)
```

### 2.2 配置

```json5
{
  agents: {
    defaults: {
      blockStreamingDefault: "on",  // on/off
      blockStreamingBreak: "text_end",  // text_end 或 message_end
      blockStreamingChunk: {
        minChars: 800,
        maxChars: 1200,
        breakPreference: "paragraph"  // paragraph/newline/sentence/whitespace
      },
      blockStreamingCoalesce: {
        minChars: 1500,
        maxChars: 4000,
        idleMs: 1000
      }
    }
  }
}
```

### 2.3 边界语义

| 模式 | 说明 |
|-----|------|
| `text_end` | 块准备好时就发送，每个 `text_end` 刷新 |
| `message_end` | 等待助手消息完成，然后刷新缓冲输出 |

### 2.4 分块算法

- **低边界**：缓冲区 >= `minChars` 才发送
- **高边界**：优先在 `maxChars` 前分割
- **分割偏好**：段落 → 换行 → 句子 → 空格 → 硬分割
- **代码块**：从不在代码块内分割；被迫时关闭+重开代码块

### 2.5 合并（Coalescing）

合并连续的流式块以减少"单行消息刷屏"：
- 等待空闲间隙（`idleMs`）后刷新
- 缓冲区超过 `maxChars` 时强制刷新
- `minChars` 防止小片段发送

### 2.6 人性化延迟

```json5
{
  agents: {
    defaults: {
      humanDelay: "natural"  // off | natural | { minMs: 800, maxMs: 2500 }
    }
  }
}
```

在块回复之间添加随机暂停（800-2500ms），使多气泡响应更自然。

---

## 3. Preview Streaming

### 3.1 模式

| 模式 | 说明 |
|-----|------|
| `off` | 禁用预览流式 |
| `partial` | 单个预览，替换为最新文本 |
| `block` | 预览以分块/追加步骤更新 |
| `progress` | 生成期间进度/状态预览，完成后最终答案 |

### 3.2 渠道支持

| 渠道 | off | partial | block | progress |
|-----|-----|---------|-------|----------|
| Telegram | ✅ | ✅ | ✅ | → partial |
| Discord | ✅ | ✅ | ✅ | → partial |
| Slack | ✅ | ✅ | ✅ | ✅ |

### 3.3 配置

```json5
{
  channels: {
    telegram: {
      streaming: "partial"  // off | partial | block | progress
    }
  }
}
```

---

## 4. 命令队列

### 4.1 为什么需要队列

- 自动回复运行可能昂贵（LLM 调用）
- 多个入站消息接近到达时可能冲突
- 序列化避免竞争共享资源

### 4.2 工作原理

- 基于 lane 的 FIFO 队列
- 按**会话键**排队，保证每个会话只有一个活动运行
- 全局 lane（`main`）控制总体并行度
- 打字指示器入队时立即触发

### 4.3 队列模式

| 模式 | 说明 |
|-----|------|
| `steer` | 立即注入当前运行 |
| `followup` | 排队等待下一个 agent 轮次 |
| `collect` | 合并所有排队消息为单个 followup（默认） |
| `steer-backlog` | 立即注入 + 保留消息用于 followup |
| `interrupt` | 中止当前运行，然后运行最新消息 |

### 4.4 配置

```json5
{
  messages: {
    queue: {
      mode: "collect",
      debounceMs: 1000,
      cap: 20,
      drop: "summarize",  // old | new | summarize
      byChannel: {
        discord: "collect"
      }
    }
  }
}
```

### 4.5 会话命令

```
/queue collect
/queue steer
/queue collect debounce:2s cap:25
/queue default
```

---

## 5. Text-to-Speech (TTS)

### 5.1 支持的服务

| 服务 | 特点 |
|-----|------|
| **ElevenLabs** | 高质量，多语言，需 API Key |
| **Microsoft** | 免费，通过 Edge TTS，无需 API Key |
| **OpenAI** | 高质量，需 API Key |

### 5.2 基本配置

```json5
{
  messages: {
    tts: {
      auto: "always",  // off | always | inbound | tagged
      provider: "elevenlabs",
      providers: {
        elevenlabs: {
          apiKey: "${ELEVENLABS_API_KEY}",
          voiceId: "voice_id",
          modelId: "eleven_multilingual_v2"
        }
      }
    }
  }
}
```

### 5.3 Auto 模式

| 模式 | 说明 |
|-----|------|
| `off` | 禁用自动 TTS |
| `always` | 所有回复转换为音频 |
| `inbound` | 只在收到语音消息后发送音频 |
| `tagged` | 只在回复包含 `[[tts]]` 标签时发送音频 |

### 5.4 OpenAI 配置

```json5
{
  messages: {
    tts: {
      provider: "openai",
      providers: {
        openai: {
          model: "gpt-4o-mini-tts",
          voice: "alloy"  // alloy | echo | fable | onyx | nova | shimmer
        }
      }
    }
  }
}
```

### 5.5 Microsoft 配置（免费）

```json5
{
  messages: {
    tts: {
      provider: "microsoft",
      providers: {
        microsoft: {
          voice: "en-US-MichelleNeural",
          outputFormat: "audio-24khz-48kbitrate-mono-mp3",
          rate: "+10%",
          pitch: "-5%"
        }
      }
    }
  }
}
```

### 5.6 模型驱动覆盖

模型可以发出 TTS 指令覆盖单个回复：

```
Here you go.

[[tts:voiceId=pMsXgVXv3BLzUgSXRplE model=eleven_v3 speed=1.1]]
[[tts:text]](laughs) Read the song once more.[[/tts:text]]
```

### 5.7 自动摘要

长回复自动摘要后转语音：

```json5
{
  messages: {
    tts: {
      summaryModel: "openai/gpt-4.1-mini",
      maxLength: 1500
    }
  }
}
```

### 5.8 Slash 命令

```
/tts off
/tts always
/tts inbound
/tts tagged
/tts status
/tts provider openai
/tts limit 2000
/tts summary off
/tts audio Hello from OpenClaw
```

---

## 6. 输出格式

### 6.1 固定格式

| 渠道 | 格式 |
|-----|------|
| Feishu/Matrix/Telegram/WhatsApp | Opus 语音消息 (48kHz/64kbps) |
| 其他渠道 | MP3 (44.1kHz/128kbps) |
| Microsoft | 配置的 `outputFormat` |

### 6.2 TTS 流程

```
Reply -> TTS enabled?
  no  -> send text
  yes -> has media / short?
          yes -> send text
          no  -> length > limit?
                   no  -> TTS -> attach audio
                   yes -> summary enabled?
                            no  -> send text
                            yes -> summarize -> TTS -> attach audio
```

---

## 7. 最佳实践

### 7.1 流式传输

- 大多数场景使用 `blockStreamingBreak: "text_end"`
- 配置合适的 `minChars` 和 `maxChars`
- 启用 `humanDelay` 使响应更自然

### 7.2 TTS

- 使用 `inbound` 模式进行语音对话
- 配置 `summaryModel` 处理长回复
- ElevenLabs 质量最高，Microsoft 免费

### 7.3 队列

- 默认 `collect` 模式适合大多数场景
- 高频消息使用 `debounceMs` 防止"继续，继续"
- 设置合适的 `cap` 防止队列过长

---

_持续更新中..._
