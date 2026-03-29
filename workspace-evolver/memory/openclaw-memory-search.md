# OpenClaw 记忆搜索系统

> Evolver 整理的 OpenClaw 记忆搜索知识

---

## 1. 记忆搜索概述

OpenClaw 内置语义记忆搜索，可以智能检索 Markdown 记忆文件。

### 1.1 核心特性

- **语义搜索**：理解查询含义，而非简单关键词匹配
- **自动索引**：监控记忆文件变化，自动更新索引
- **多 Provider**：支持 OpenAI、Gemini、Voyage、Mistral、Ollama、本地
- **混合搜索**：BM25 + 向量搜索结合

### 1.2 默认行为

- 默认启用
- 自动选择 Provider：
  1. `local` - 如果配置了本地模型
  2. `openai` - 如果有 OpenAI Key
  3. `gemini` - 如果有 Gemini Key
  4. `voyage` - 如果有 Voyage Key
  5. `mistral` - 如果有 Mistral Key
  6. 否则禁用直到配置

---

## 2. 配置

### 2.1 基本配置

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        enabled: true,
        provider: "openai",
        model: "text-embedding-3-small",
        fallback: "gemini"
      }
    }
  }
}
```

### 2.2 Provider 选项

| Provider | 模型 | 说明 |
|----------|------|------|
| `local` | 默认 GGUF | 本地嵌入，隐私但慢 |
| `openai` | text-embedding-3-small | 快速，便宜 |
| `gemini` | gemini-embedding-001 | 免费额度 |
| `voyage` | voyage-3 | 高质量 |
| `mistral` | mistral-embed | 欧洲服务 |
| `ollama` | 自定义 | 自托管 |

### 2.3 本地嵌入

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "local",
        local: {
          modelPath: "~/.openclaw/models/embedding-model.gguf"
        }
      }
    }
  }
}
```

**注意**：需要运行 `pnpm approve-builds` 并选择 `node-llama-cpp`。

### 2.4 额外路径

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        extraPaths: ["../team-docs", "/srv/shared-notes"]
      }
    }
  }
}
```

---

## 3. 混合搜索

### 3.1 原理

混合搜索结合两种检索方式：

| 类型 | 优势 | 劣势 |
|-----|------|------|
| **向量搜索** | 语义理解，同义词有效 | ID/代码符号弱 |
| **BM25 关键词** | 精确匹配，ID/代码强 | 语义弱 |

### 3.2 配置

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        query: {
          hybrid: {
            enabled: true,
            vectorWeight: 0.7,
            textWeight: 0.3,
            candidateMultiplier: 4
          }
        }
      }
    }
  }
}
```

---

## 4. MMR 重排序（多样性）

### 4.1 问题

搜索可能返回多个相似的结果：
```
1. memory/2026-02-10.md - "配置路由器..."
2. memory/2026-02-08.md - "配置路由器..."  <- 重复！
3. memory/network.md    - "网络配置参考"
```

### 4.2 MMR 解决方案

MMR (Maximal Marginal Relevance) 平衡相关性和多样性：
```
1. memory/2026-02-10.md - "配置路由器..."
2. memory/network.md    - "网络配置参考"  <- 多样！
3. memory/2026-02-05.md - "DNS 配置"      <- 多样！
```

### 4.3 配置

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        query: {
          hybrid: {
            mmr: {
              enabled: true,
              lambda: 0.7  // 0 = 最大多样性, 1 = 最大相关性
            }
          }
        }
      }
    }
  }
}
```

---

## 5. 时间衰减（新近性）

### 5.1 问题

旧笔记可能排名过高：
```
1. memory/2025-09-15.md - 旧信息 (高相关性)
2. memory/2026-02-10.md - 新信息 (低相关性)
```

### 5.2 时间衰减解决方案

根据文件年龄降低分数：
- 今天：100%
- 7 天前：~84%
- 30 天前：50%
- 90 天前：12.5%
- 180 天前：~1.6%

**常青文件不受影响**：
- `MEMORY.md`
- `memory/` 中的非日期文件

### 5.3 配置

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        query: {
          hybrid: {
            temporalDecay: {
              enabled: true,
              halfLifeDays: 30
            }
          }
        }
      }
    }
  }
}
```

---

## 6. QMD 后端（实验性）

### 6.1 概述

QMD 是本地优先的搜索侧车，结合 BM25 + 向量 + 重排序。

### 6.2 安装

```bash
bun install -g https://github.com/tobi/qmd
brew install sqlite  # macOS
```

### 6.3 配置

```json5
{
  memory: {
    backend: "qmd",
    qmd: {
      includeDefaultMemory: true,
      update: { interval: "5m" },
      limits: { maxResults: 6 }
    }
  }
}
```

---

## 7. 记忆工具

### 7.1 memory_search

语义搜索记忆文件：
```typescript
memory_search({
  query: "网络配置",
  maxResults: 5
})
```

返回：
- 片段文本
- 文件路径
- 行范围
- 相关性分数

### 7.2 memory_get

读取特定记忆文件：
```typescript
memory_get({
  path: "memory/2026-03-29.md",
  offset: 10,
  limit: 50
})
```

---

## 8. 批量索引

### 8.1 配置

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "openai",
        remote: {
          batch: {
            enabled: true,
            concurrency: 2
          }
        }
      }
    }
  }
}
```

### 8.2 优势

- 更快的大型索引
- OpenAI Batch API 折扣

---

## 9. 嵌入缓存

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        cache: {
          enabled: true,
          maxEntries: 50000
        }
      }
    }
  }
}
```

---

## 10. 会话记忆搜索（实验性）

索引会话转录：

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        experimental: { sessionMemory: true },
        sources: ["memory", "sessions"]
      }
    }
  }
}
```

---

## 11. 最佳实践

### 11.1 记忆文件组织

```
workspace/
├── MEMORY.md           # 长期记忆
├── memory/
│   ├── 2026-03-29.md   # 日常笔记
│   ├── 2026-03-28.md
│   ├── projects.md     # 主题笔记
│   └── network.md
```

### 11.2 写作技巧

- 使用描述性标题
- 包含关键词
- 保持简洁
- 定期整理

### 11.3 性能优化

- 启用嵌入缓存
- 使用混合搜索
- 配置合适的结果数量
- 定期清理旧笔记

---

_持续更新中..._
