# AI 框架与 RAG 指南

> Evolver 整理的 AI 框架和 RAG 知识

---

## 1. 主流 AI 框架

### 1.1 框架概览

| 框架 | 类型 | 特点 | 适用场景 |
|-----|------|------|---------|
| **LangChain** | 通用框架 | 组件丰富，生态完善 | 通用 LLM 应用 |
| **LangGraph** | 工作流 | 有状态图，可控 | 复杂编排 |
| **LlamaIndex** | RAG 专用 | 数据连接，检索优化 | 知识库应用 |
| **AutoGen** | 多智能体 | 微软，对话式 | 协作场景 |
| **CrewAI** | 多智能体 | 角色扮演，企业级 | 团队模拟 |
| **DSPy** | Prompt 优化 | 声明式，自动优化 | Prompt 工程 |
| **Haystack** | RAG 框架 | 生产就绪 | 企业搜索 |
| **Flowise** | 低代码 | 可视化拖拽 | 快速原型 |

### 1.2 LangChain

**核心组件**：
- **Chains** - 顺序执行的组件链
- **Agents** - 动态决策的智能体
- **Tools** - 外部工具集成
- **Memory** - 对话记忆
- **Retrievers** - 检索器

**特点**：
- 组件最丰富
- 社区最活跃
- 学习曲线中等

### 1.3 LangGraph

**核心概念**：
- **State** - 状态对象
- **Nodes** - 处理节点
- **Edges** - 状态转移
- **Conditional Edges** - 条件分支

**优势**：
- 有状态工作流
- 可视化调试
- 精确控制流程

**示例**：
```python
from langgraph.graph import StateGraph

def node_a(state):
    return {"step": "a_done"}

def node_b(state):
    return {"step": "b_done"}

graph = StateGraph(State)
graph.add_node("a", node_a)
graph.add_node("b", node_b)
graph.add_edge("a", "b")
```

### 1.4 LlamaIndex

**核心组件**：
- **Data Connectors** - 数据连接器（API, PDF, SQL 等）
- **Data Indexes** - 数据索引
- **Query Engines** - 查询引擎
- **Chat Engines** - 对话引擎
- **Agents** - 智能体
- **Workflows** - 工作流

**5 行代码示例**：
```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("问题")
```

**LlamaCloud 服务**：
- LlamaParse - 文档解析
- LlamaExtract - 结构化提取
- 索引/检索管理

### 1.5 AutoGen

**核心概念**：
- **Agents** - 智能体
- **Conversations** - 对话
- **Human-in-the-loop** - 人类参与

**特点**：
- 微软研究院出品
- 多智能体对话
- 自动化工作流

### 1.6 CrewAI

**核心概念**：
- **Agents** - 角色智能体
- **Tasks** - 任务
- **Crew** - 团队
- **Process** - 执行流程

**特点**：
- 角色扮演设计
- 企业级部署（AMP）
- 可视化编辑器
- Fortune 500 60% 在用

**示例**：
```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role="研究员",
    goal="研究主题",
    backstory="专家研究员"
)

writer = Agent(
    role="作家",
    goal="撰写文章",
    backstory="专业作家"
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task]
)
```

---

## 2. RAG (Retrieval-Augmented Generation)

### 2.1 RAG 概述

**定义**：RAG 通过检索外部知识增强 LLM 的生成能力。

**流程**：
```
用户问题 → 检索相关文档 → 组合上下文 → LLM 生成 → 输出
```

**优势**：
- 无需重新训练
- 实时知识更新
- 减少幻觉
- 可追溯来源

### 2.2 RAG 范式演进

| 范式 | 特点 | 局限 |
|-----|------|------|
| **Naive RAG** | 简单检索+生成 | 低精度、低召回 |
| **Advanced RAG** | 优化检索质量 | 仍有限制 |
| **Modular RAG** | 模块化，灵活 | 复杂度高 |

### 2.3 Naive RAG

**流程**：
1. 索引：分块 → 嵌入 → 向量存储
2. 检索：查询嵌入 → 相似度搜索
3. 生成：上下文 + 查询 → LLM

**问题**：
- 低精度：检索不相关内容
- 低召回：遗漏相关内容
- 过时信息
- 冗余重复

### 2.4 Advanced RAG

#### 预检索优化

| 技术 | 说明 |
|-----|------|
| 增强数据粒度 | 优化数据质量 |
| 优化索引结构 | 更好的索引策略 |
| 添加元数据 | 便于过滤和排序 |
| 混合检索 | 关键词 + 向量 |

#### 检索优化

| 技术 | 说明 |
|-----|------|
| 微调嵌入模型 | 领域适配 |
| 动态嵌入 | 上下文感知 |
| 查询重写 | 改进查询表达 |

#### 后检索优化

| 技术 | 说明 |
|-----|------|
| 重排序 | 优化结果顺序 |
| 提示压缩 | 减少噪声 |
| 上下文窗口管理 | 控制长度 |

### 2.5 Modular RAG

**扩展模块**：

| 模块 | 功能 |
|-----|------|
| **Search** | 相似度检索 |
| **Memory** | 记忆管理 |
| **Fusion** | 多路融合 |
| **Routing** | 路由决策 |
| **Predict** | 预测增强 |
| **Task Adapter** | 任务适配 |

**优化技术**：

1. **混合搜索**：关键词 + 语义
2. **递归检索**：小块 → 大块
3. **StepBack Prompting**：抽象推理
4. **子查询**：分解复杂问题
5. **HyDE**：生成假设文档检索

### 2.6 RAG 关键组件

#### 检索器 (Retriever)

**优化方向**：
- 分块策略：句子/段落/文档
- 嵌入模型：通用 vs 领域专用
- 查询对齐：重写、转换
- 检索器-LLM 对齐：微调、适配器

**分块策略**：

| 策略 | 适用场景 |
|-----|---------|
| 固定大小 | 通用 |
| 句子分割 | 精确匹配 |
| 段落分割 | 主题完整 |
| 语义分割 | 内容相关 |

#### 生成器 (Generator)

**优化方向**：
- 后检索处理：压缩、重排序
- LLM 微调：领域适配
- 格式控制：输出结构化

#### 增强策略 (Augmentation)

**增强阶段**：
- Pre-training：预训练阶段
- Fine-tuning：微调阶段
- Inference：推理阶段

**增强过程**：
- **迭代检索**：多次检索循环
- **递归检索**：递归深入
- **自适应检索**：动态决定

### 2.7 RAG vs Fine-tuning

| 特性 | RAG | Fine-tuning |
|-----|-----|-------------|
| 知识更新 | ✅ 实时 | ❌ 需重训 |
| 成本 | 低 | 高 |
| 定制化 | 中 | 高 |
| 可解释性 | ✅ 高 | ❌ 低 |
| 适用场景 | 知识密集 | 格式/风格 |

**组合使用**：
- RAG 提供实时知识
- Fine-tuning 优化格式/风格

### 2.8 RAG 评估

**质量评分**：

| 指标 | 说明 |
|-----|------|
| 上下文相关性 | 检索内容的精确性 |
| 答案忠实度 | 回答与上下文一致性 |
| 答案相关性 | 回答与问题的相关性 |

**能力评估**：

| 能力 | 说明 |
|-----|------|
| 噪声鲁棒性 | 处理噪声文档 |
| 负面拒绝 | 无相关内容时拒绝 |
| 信息整合 | 多文档综合 |
| 反事实鲁棒性 | 处理错误信息 |

**评估工具**：
- RAGAS - 自动评估
- ARES - 自动评估
- TruLens - 可观测性
- RGB - 基准测试
- RECALL - 基准测试

### 2.9 RAG 挑战与未来

**挑战**：
- 上下文长度限制
- 鲁棒性
- RAG + Fine-tuning 混合
- LLM 角色扩展
- 缩放定律
- 生产就绪
- 多模态 RAG
- 评估方法

**未来方向**：
- 更长的上下文利用
- 更好的检索-生成对齐
- 实时知识更新
- 多模态支持

---

## 3. 框架选择指南

### 3.1 按场景选择

| 场景 | 推荐框架 |
|-----|---------|
| 知识库问答 | LlamaIndex |
| 复杂工作流 | LangGraph |
| 多智能体协作 | AutoGen / CrewAI |
| 快速原型 | Flowise |
| Prompt 优化 | DSPy |
| 企业搜索 | Haystack |

### 3.2 按复杂度选择

| 复杂度 | 推荐 |
|-------|------|
| 简单 RAG | LlamaIndex 5 行代码 |
| 中等复杂 | LangChain Chains |
| 复杂流程 | LangGraph |
| 多智能体 | CrewAI / AutoGen |

### 3.3 与 OpenClaw 集成

**OpenClaw 优势**：
- 多渠道统一接入
- 持久会话
- 路由机制
- 沙箱隔离

**集成方式**：
- 通过 Skills 调用框架
- 通过 MCP 接入工具
- 通过 Hooks 触发工作流

---

## 4. 最佳实践

### 4.1 RAG 优化清单

- [ ] 选择合适的分块策略
- [ ] 优化嵌入模型（必要时微调）
- [ ] 实现混合检索
- [ ] 添加重排序
- [ ] 管理上下文窗口
- [ ] 实现查询重写
- [ ] 添加元数据过滤
- [ ] 评估和监控

### 4.2 框架使用建议

- 从简单开始，按需增加复杂度
- 先用 Naive RAG，再优化
- 持续评估，数据驱动
- 关注生产就绪性

---

_持续更新中..._
