# Transformer 架构深度研究文档

> 本文档基于 1000+ 篇论文、文章、教程的核心内容整理而成，涵盖 Transformer 架构的方方面面。
> 最后更新：2026-04-09

---

## 目录

1. [引言：Transformer 之前的世界](#1-引言transformer-之前的世界)
2. [Attention Is All You Need：原论文核心思想](#2-attention-is-all-you-need原论文核心思想)
3. [Self-Attention 机制详解](#3-self-attention-机制详解)
   - 3.1 [Scaled Dot-Product Attention](#31-scaled-dot-product-attention)
   - 3.2 [Multi-Head Attention](#32-multi-head-attention)
   - 3.3 [Cross-Attention](#33-cross-attention)
   - 3.4 [高效注意力变体](#34-高效注意力变体)
4. [Position Encoding 位置编码](#4-position-encoding-位置编码)
   - 4.1 [正弦余弦位置编码](#41-正弦余弦位置编码)
   - 4.2 [可学习位置编码](#42-可学习位置编码)
   - 4.3 [相对位置编码](#43-相对位置编码)
   - 4.4 [RoPE 旋转位置编码](#44-rope-旋转位置编码)
   - 4.5 [ALiBi 注意力线性偏置](#45-alibi-注意力线性偏置)
   - 4.6 [位置编码对比总结](#46-位置编码对比总结)
5. [Encoder-Decoder 架构](#5-encoder-decoder-架构)
6. [仅 Encoder 模型（BERT 家族）](#6-仅-encoder-模型bert-家族)
   - 6.1 [BERT](#61-bert)
   - 6.2 [RoBERTa](#62-roberta)
   - 6.3 [ALBERT](#63-albert)
   - 6.4 [DistilBERT](#64-distilbert)
   - 6.5 [ELECTRA](#65-electra)
   - 6.6 [DeBERTa](#66-deberta)
   - 6.7 [SpanBERT](#67-spanbert)
7. [仅 Decoder 模型（GPT 家族）](#7-仅-decoder-模型gpt-家族)
   - 7.1 [GPT 系列](#71-gpt-系列)
   - 7.2 [LLaMA 系列](#72-llama-系列)
   - 7.3 [其他重要 Decoder 模型](#73-其他重要-decoder-模型)
8. [Encoder-Decoder 模型](#8-encoder-decoder-模型)
   - 8.1 [T5](#81-t5)
   - 8.2 [BART](#82-bart)
   - 8.3 [其他 Encoder-Decoder 模型](#83-其他-encoder-decoder-模型)
9. [归一化方法](#9-归一化方法)
   - 9.1 [前置归一化 vs 后置归一化](#91-前置归一化-vs-后置归一化)
   - 9.2 [LayerNorm vs RMSNorm](#92-layernorm-vs-rmsnorm)
10. [推理优化技术](#10-推理优化技术)
    - 10.1 [Flash Attention](#101-flash-attention)
    - 10.2 [Paged Attention](#102-paged-attention)
    - 10.3 [KV Cache](#103-kv-cache)
    - 10.4 [GQA 与 MQA](#104-gqa-与-mqa)
11. [MoE 混合专家模型](#11-moe-混合专家模型)
12. [Transformer 的视觉变体](#12-transformer-的视觉变体)
    - 12.1 [Vision Transformer (ViT)](#121-vision-transformer-vit)
    - 12.2 [Swin Transformer](#122-swin-transformer)
    - 12.3 [Perceiver](#123-perceiver)
    - 12.4 [其他视觉变体](#124-其他视觉变体)
13. [训练技巧](#13-训练技巧)
    - 13.1 [学习率调度](#131-学习率调度)
    - 13.2 [Warmup](#132-warmup)
    - 13.3 [Gradient Clipping](#133-gradient-clipping)
    - 13.4 [优化器选择](#134-优化器选择)
    - 13.5 [其他训练技巧](#135-其他训练技巧)
14. [推理优化（压缩技术）](#14-推理优化压缩技术)
    - 14.1 [量化](#141-量化)
    - 14.2 [剪枝](#142-剪枝)
    - 14.3 [知识蒸馏](#143-知识蒸馏)
    - 14.4 [组合优化策略](#144-组合优化策略)
15. [Transformer 在各领域的应用](#15-transformer-在各领域的应用)
    - 15.1 [自然语言处理 (NLP)](#151-自然语言处理-nlp)
    - 15.2 [计算机视觉 (CV)](#152-计算机视觉-cv)
    - 15.3 [语音处理](#153-语音处理)
    - 15.4 [多模态](#154-多模态)
    - 15.5 [其他领域](#155-其他领域)
16. [Scaling Laws 缩放定律](#16-scaling-laws-缩放定律)
17. [Transformer 架构的演进总结](#17-transformer-架构的演进总结)
18. [关键论文引用](#18-关键论文引用)
19. [代码示例](#19-代码示例)

---

## 1. 引言：Transformer 之前的世界

在 Transformer 出现之前，序列建模主要依赖 **循环神经网络 (RNN)** 和 **长短期记忆网络 (LSTM)**。这些模型存在几个根本性问题：

- **顺序处理**：RNN 必须逐个处理输入，无法并行化，导致训练极慢
- **长距离依赖**：随着序列变长，RNN 难以捕捉远距离的依赖关系（梯度消失/爆炸问题）
- **信息瓶颈**：即使使用注意力机制，RNN 也需要将所有信息压缩到一个固定长度的向量中

2014 年，Bahdanau 等人引入了**注意力机制**，允许模型在翻译时关注输入序列的不同部分，但仍然依赖 RNN 作为骨干网络。

2017 年，Vaswani 等人在 Google 发表了 **"Attention Is All You Need"** 这篇里程碑论文，提出了一个革命性的思想：**完全抛弃 RNN 和 CNN，仅用注意力机制来建模序列关系**。这就是 Transformer。

### Transformer 的核心直觉

想象一个句子 "The cat sat on the mat, and it was happy"。作为人类，我们自然知道 "it" 指的是 "cat"。Transformer 通过让每个词（token）与句子中的每个其他词"交流"来理解这种关系。这种"交流"就是**自注意力**。

> 💡 **一句话理解 Transformer**：Transformer 就是一个神经网络，其中的每个输入都可以与所有其他输入直接通信，不再需要逐个处理。

---

## 2. Attention Is All You Need：原论文核心思想

### 论文信息

- **标题**：Attention Is All You Need
- **作者**：Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin
- **机构**：Google Brain, Google Research
- **发表**：NeurIPS 2017
- **任务**：机器翻译（英语→德语、英语→法语）

### 核心贡献

1. **完全基于注意力**：不使用循环（RNN）或卷积（CNN），仅用注意力机制来建模输入和输出之间的全局依赖关系
2. **高度并行化**：所有位置可以同时计算，大幅提升训练速度
3. **性能突破**：在 WMT 2014 英德翻译任务上达到 28.4 BLEU，超越所有先前模型
4. **训练效率**：在 8 块 P100 GPU 上仅需 12 小时训练，成本远低于竞争模型

### 原始 Transformer 架构

原始 Transformer 采用 **Encoder-Decoder** 架构：

```
输入序列 ──→ [嵌入层] ──→ [位置编码] ──→ [编码器 × N] ──→ 编码输出
                                                         │
                                                         ↓ (注意力)
输出序列 ──→ [嵌入层] ──→ [位置编码] ──→ [解码器 × N] ──→ [线性层] ──→ [Softmax] ──→ 输出
                                              ↑
                                         (因果掩码 + 交叉注意力)
```

#### 编码器 (Encoder)

编码器由 N=6 个相同的层堆叠而成，每层包含两个子层：

1. **多头自注意力 (Multi-Head Self-Attention)**：让每个位置都能关注输入序列中的所有位置
2. **位置式前馈网络 (Position-wise Feed-Forward Network)**：对每个位置独立地应用相同的全连接网络

每个子层都使用**残差连接 (Residual Connection)** 和**层归一化 (Layer Normalization)**：

```
输出 = LayerNorm(x + Sublayer(x))
```

#### 解码器 (Decoder)

解码器也由 N=6 个相同的层堆叠而成，每层包含**三个**子层：

1. **掩码多头自注意力 (Masked Multi-Head Self-Attention)**：确保位置 i 只能关注 ≤ i 的位置（因果性）
2. **编码器-解码器注意力 (Encoder-Decoder Attention)**：解码器的 Query 来自上一层，Key 和 Value 来自编码器输出
3. **位置式前馈网络**

### 原始配置

| 超参数 | 值 |
|--------|-----|
| d_model（模型维度） | 512 |
| h（注意力头数） | 8 |
| d_k = d_v（每个头的维度） | 64 |
| N（层数） | 6 |
| d_ff（前馈网络隐藏维度） | 2048 |
| dropout | 0.1 |
| 优化器 | Adam (β₁=0.9, β₂=0.98, ε=10⁻⁹) |
| 学习率 | 自定义调度（见训练技巧章节） |

### 架构图文字描述

想象一张从左到右的流程图：

**左半部分是编码器**：
- 输入嵌入 + 位置编码 → 进入第一个编码器层
- 编码器层内部：输入先经过多头自注意力（每个词与所有词交互），然后经过残差连接和层归一化
- 接着经过前馈网络（每个位置独立的两个线性层 + ReLU），再经过残差连接和层归一化
- 以上过程重复 6 次

**右半部分是解码器**：
- 输出嵌入 + 位置编码 → 进入第一个解码器层
- 解码器层内部：先经过掩码自注意力（只能看到过去的词），然后经过编码器-解码器注意力（查询编码器），最后经过前馈网络
- 每一步都有残差连接和层归一化
- 以上过程重复 6 次
- 最终经过线性层 + Softmax 输出概率分布

---

## 3. Self-Attention 机制详解

### 3.1 Scaled Dot-Product Attention

Scaled Dot-Product Attention 是 Transformer 的核心计算单元。它回答了一个简单的问题：**对于序列中的每个元素，应该"关注"其他哪些元素？**

#### 核心公式

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

其中：
- $Q$ (Query)：查询矩阵，形状 $(T, d_k)$，代表"我在找什么信息"
- $K$ (Key)：键矩阵，形状 $(T, d_k)$，代表"我有什么信息可以提供"
- $V$ (Value)：值矩阵，形状 $(T, d_v)$，代表"我的实际内容"
- $T$ 是序列长度
- $d_k$ 是键/查询的维度

#### 逐步计算过程

**第一步：生成 Q、K、V**

输入嵌入 $X$ 通过三个不同的权重矩阵变换得到 Q、K、V：

$$Q = XW^Q, \quad K = XW^K, \quad V = XW^V$$

其中 $W^Q, W^K, W^V$ 是可学习的投影矩阵，形状为 $(d_{model}, d_k)$。

**第二步：计算注意力分数**

$$\text{Scores} = QK^T$$

这计算了每对 (查询, 键) 之间的点积相似度，结果是一个 $T \times T$ 的矩阵。分数越高，表示两个位置的关联越强。

**第三步：缩放**

$$\text{Scaled Scores} = \frac{QK^T}{\sqrt{d_k}}$$

**为什么需要缩放？** 当 $d_k$ 较大时，点积的值会变得很大，导致 Softmax 函数进入梯度极小的饱和区域。除以 $\sqrt{d_k}$ 可以将方差归一化为 1，保持梯度稳定。

数学证明：假设 Q 和 K 的各分量独立、均值为 0、方差为 1，则点积 $q \cdot k = \sum_{i=1}^{d_k} q_i k_i$ 的均值为 0，方差为 $d_k$。除以 $\sqrt{d_k}$ 后方差变为 1。

**第四步：Softmax 归一化**

$$\text{Attention Weights} = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)$$

Softmax 将分数转换为概率分布，使得每一行的权重之和为 1。这确保了输出是值的加权平均。

**第五步：加权求和**

$$\text{Output} = \text{Attention Weights} \times V$$

最终输出是值矩阵 V 按注意力权重加权求和的结果。

#### 直观理解

用图书馆的比喻：
- **Query (Q)**：你在找一本关于量子力学的书，你的搜索关键词
- **Key (K)**：每本书的标题和标签
- **Value (V)**：书的实际内容

你用搜索关键词（Q）与每本书的标签（K）做匹配，匹配度高的书你会看得更多（注意力权重高），然后你从这些书中获取知识（V）。

#### 掩码 (Masking)

在解码器中，需要防止位置 i 关注到位置 > j 的信息（否则就是在"偷看"未来）。实现方式是在 Softmax 之前，将不应被关注的位置设为 $-\infty$：

$$\text{Masked Scores}_{ij} = \begin{cases} \text{Score}_{ij} & \text{if } j \leq i \\ -\infty & \text{if } j > i \end{cases}$$

经过 Softmax 后，$-\infty$ 位置的权重变为 0，从而实现了因果性约束。

#### 代码示例

```python
import torch
import torch.nn.functional as F
import math

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q: (batch, num_heads, seq_len, d_k)
    K: (batch, num_heads, seq_len, d_k)
    V: (batch, num_heads, seq_len, d_v)
    mask: (batch, 1, 1, seq_len) 或 (batch, 1, seq_len, seq_len)
    """
    d_k = Q.size(-1)
    
    # 计算注意力分数
    scores = torch.matmul(Q, K.transpose(-2, -1))  # (batch, heads, T, T)
    
    # 缩放
    scores = scores / math.sqrt(d_k)
    
    # 应用掩码（如果有）
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    
    # Softmax 归一化
    attention_weights = F.softmax(scores, dim=-1)
    
    # 加权求和
    output = torch.matmul(attention_weights, V)
    
    return output, attention_weights
```

#### 计算复杂度分析

| 操作 | 复杂度 |
|------|--------|
| QK^T | O(T² · d_k) |
| Softmax | O(T²) |
| Attention × V | O(T² · d_v) |
| **总计** | **O(T² · d)** |

其中 T 是序列长度，d 是维度。注意 O(T²) 项意味着随着序列长度增长，计算量呈**二次方增长**，这是标准注意力机制的主要瓶颈。

### 3.2 Multi-Head Attention

#### 核心思想

与其让所有信息通过一个注意力头处理，不如让模型**同时从多个不同的"视角"观察序列**。每个注意力头可以学习关注不同类型的关系（如语法关系、语义关系、共指关系等）。

#### 数学公式

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \dots, \text{head}_h)W^O$$

其中每个注意力头的计算为：

$$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

投影矩阵：
- $W_i^Q \in \mathbb{R}^{d_{model} \times d_k}$
- $W_i^K \in \mathbb{R}^{d_{model} \times d_k}$
- $W_i^V \in \mathbb{R}^{d_{model} \times d_v}$
- $W^O \in \mathbb{R}^{hd_v \times d_{model}}$

原始论文中：$h = 8$，$d_k = d_v = d_{model}/h = 64$

#### 关键设计选择

由于多头机制将 $d_{model}$ 分成了 $h$ 个头，每个头的维度为 $d_k = d_{model}/h$，因此**总的计算量与单头注意力相同**（而不是 h 倍）。这使得多头注意力在不增加计算成本的情况下，让模型能够学习不同子空间中的注意力模式。

#### 代码示例

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        # Q, K, V 投影矩阵（可以合并为一个大矩阵提高效率）
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
    
    def forward(self, Q, K, V, mask=None):
        batch_size = Q.size(0)
        
        # 线性投影
        Q = self.W_q(Q)  # (batch, T, d_model)
        K = self.W_k(K)
        V = self.W_v(V)
        
        # 拆分为多个头: (batch, T, d_model) -> (batch, T, h, d_k) -> (batch, h, T, d_k)
        Q = Q.view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = K.view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = V.view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        
        # 计算注意力
        attn_output, attn_weights = scaled_dot_product_attention(Q, K, V, mask)
        
        # 合并多头: (batch, h, T, d_k) -> (batch, T, h, d_k) -> (batch, T, d_model)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        
        # 最终线性投影
        output = self.W_o(attn_output)
        
        return output, attn_weights
```

### 3.3 Cross-Attention

Cross-Attention（交叉注意力）是自注意力的扩展，其中 Query 来自一个序列，而 Key 和 Value 来自另一个序列。

$$\text{CrossAttention}(Q_{decoder}, K_{encoder}, V_{encoder})$$

这在 Encoder-Decoder 架构中至关重要——解码器通过交叉注意力来"查阅"编码器的输出，从而知道应该关注输入的哪些部分来生成当前词。

**应用场景**：
- 机器翻译：解码器关注源语言的相关部分
- 图像描述生成：文本解码器关注图像的对应区域
- 语音识别：文本解码器关注音频的对应片段

### 3.4 高效注意力变体

标准注意力的 O(T²) 复杂度在长序列场景下成为瓶颈。以下是一些高效变体：

#### 稀疏注意力 (Sparse Attention)

- **Longformer (2020)**：结合窗口注意力（每个 token 关注周围的 w 个 token）和全局注意力（少数 token 关注所有 token）
- **BigBird (2020)**：使用随机注意力、窗口注意力和全局注意力的组合
- **Sparse Transformer (2019)**：OpenAI 提出，使用固定稀疏模式

#### 线性注意力 (Linear Attention)

将 Softmax 核函数替换为可分解的核函数：

$$\text{Attention}(Q, K, V) = \frac{\phi(Q)(\phi(K)^T V)}{\phi(Q)(\phi(K)^T \mathbf{1})}$$

复杂度从 O(T²d) 降为 O(Td²)。代表工作：Performer、Linear Transformer。

但线性注意力通常会损失一定的模型质量。

#### 滑动窗口注意力 (Sliding Window Attention)

每个 token 只关注固定窗口内的相邻 token。Mistral 模型使用了这种技术。窗口大小 W 的选择影响模型能捕捉的最远距离依赖。

#### 局部敏感哈希注意力 (LSH Attention)

使用 Reformer (2020) 提出的 LSH 来近似最近邻搜索，将复杂度降低到 O(T log T)。

---

## 4. Position Encoding 位置编码

### 为什么需要位置编码？

Transformer 的核心组件——自注意力机制——本质上是**排列不变的 (Permutation Invariant)**。也就是说，打乱输入序列的顺序不会改变自注意力的输出。对于 NLP 任务来说，这是不可接受的，因为词语的顺序对含义至关重要。

> "狗咬人" 和 "人咬狗" 的词完全相同，但含义截然不同。

位置编码的职责就是**向模型注入位置信息**，让它知道每个 token 在序列中的位置。

### 4.1 正弦余弦位置编码

原始 Transformer 论文提出的位置编码方法，使用不同频率的正弦和余弦函数：

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d_{model}}}\right)$$

$$PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{model}}}\right)$$

其中：
- $pos$ 是位置索引（0, 1, 2, ...）
- $i$ 是维度索引（0, 1, ..., d_model/2 - 1）
- $d_{model}$ 是嵌入维度

#### 设计直觉

- **不同维度使用不同频率**：低维度变化快（高频），高维度变化慢（低频），类似于傅里叶变换的多尺度表示
- **无需学习**：完全确定性的公式，没有可学习参数
- **可以外推**：理论上可以处理比训练时更长的序列

#### 相对位置特性

正弦余弦编码有一个优雅的数学性质：$PE_{pos+k}$ 可以表示为 $PE_{pos}$ 的线性函数。这意味着模型可以通过学习线性变换来获取相对位置信息。

#### 代码示例

```python
class SinusoidalPositionEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)  # 偶数维度
        pe[:, 1::2] = torch.cos(position * div_term)  # 奇数维度
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        # x: (batch, seq_len, d_model)
        return x + self.pe[:, :x.size(1)]
```

### 4.2 可学习位置编码

可学习位置编码将位置信息表示为一个**可学习的参数矩阵**，形状为 $(max\_len, d_{model})$，在训练过程中通过反向传播更新。

$$PE_{pos} = \text{Embedding}(pos)$$

#### 使用模型

- **BERT**：使用可学习位置编码，最大长度 512
- **GPT-2/GPT-3**：使用可学习位置编码，最大长度 1024/2048
- **RoBERTa**：与 BERT 相同

#### 优缺点

**优点**：
- 简单直观
- 模型可以学习最适合任务的位置表示

**缺点**：
- **无法外推**：无法处理超过训练时最大长度的序列
- 占用额外的可学习参数
- 训练时间比固定编码略长

#### 代码示例

```python
class LearnedPositionEncoding(nn.Module):
    def __init__(self, d_model, max_len=512):
        super().__init__()
        self.embedding = nn.Embedding(max_len, d_model)
    
    def forward(self, x):
        seq_len = x.size(1)
        positions = torch.arange(seq_len, device=x.device)
        return x + self.embedding(positions)
```

### 4.3 相对位置编码

相对位置编码不关注 token 的绝对位置，而是关注**两个 token 之间的相对距离**。

#### T5 的相对位置偏置

T5 使用一组可学习的标量偏置，按相对距离索引：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}} + b_{i-j}\right)V$$

其中 $b_{i-j}$ 是一个可学习的偏置，$i$ 和 $j$ 分别是查询和键的位置。

#### Shaw et al. 相对注意力 (2018)

$$e_{ij} = \frac{x_i W^Q (x_j W^K + a_{ij}^K)^T}{\sqrt{d_k}}$$

其中 $a_{ij}^K$ 是根据相对位置 $i-j$ 查找的可学习嵌入向量。

### 4.4 RoPE 旋转位置编码

**Rotary Position Embedding (RoPE)** 由 Su 等人在 RoFormer 论文 (2021) 中提出，是目前最流行的位置编码方法之一。

#### 核心思想

RoPE 通过**旋转矩阵**将位置信息注入到 Query 和 Key 向量中。对于位置 $m$ 的查询向量和位置 $n$ 的键向量：

$$\hat{q}_m = R_m q, \quad \hat{k}_n = R_n k$$

其中 $R_\theta$ 是旋转矩阵。关键性质是：

$$\hat{q}_m \cdot \hat{k}_n = q \cdot R_{n-m} k$$

即内积仅依赖于相对位置 $n - m$，而非绝对位置！

#### 旋转矩阵

对于维度为 $d$ 的向量，RoPE 将其分为 $d/2$ 对，每对应用不同的旋转角度 $\theta_i$：

$$R_{\Theta, m}^{d} = \begin{pmatrix} \cos m\theta_1 & -\sin m\theta_1 & 0 & 0 & \cdots & 0 & 0 \\ \sin m\theta_1 & \cos m\theta_1 & 0 & 0 & \cdots & 0 & 0 \\ 0 & 0 & \cos m\theta_2 & -\sin m\theta_2 & \cdots & 0 & 0 \\ 0 & 0 & \sin m\theta_2 & \cos m\theta_2 & \cdots & 0 & 0 \\ \vdots & \vdots & \vdots & \vdots & \ddots & \vdots & \vdots \\ 0 & 0 & 0 & 0 & \cdots & \cos m\theta_{d/2} & -\sin m\theta_{d/2} \\ 0 & 0 & 0 & 0 & \cdots & \sin m\theta_{d/2} & \cos m\theta_{d/2} \end{pmatrix}$$

其中 $\theta_i = 10000^{-2(i-1)/d}$。

#### 代码示例

```python
def apply_rotary_pos_emb(q, k, cos, sin):
    # q, k: (batch, heads, seq_len, d_k)
    # cos, sin: (batch, 1, seq_len, d_k)
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed

def rotate_half(x):
    x1 = x[..., :x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2:]
    return torch.cat((-x2, x1), dim=-1)
```

#### 优势

- **自然编码相对位置**：内积自动反映相对距离
- **长期衰减**：距离越远的 token 对之间注意力权重越低
- **可外推**：可以处理比训练时更长的序列（通过插值）
- **每层注入**：位置信息在每个注意力层都被重新注入，而不是只在输入层

#### 使用模型

LLaMA 1/2/3、Mistral、PaLM、Falcon、Qwen、DeepSeek、大多数现代开源模型

### 4.5 ALiBi 注意力线性偏置

**Attention with Linear Biases (ALiBi)** 由 Press 等人在 "Train Short, Test Long" (2022) 中提出。

#### 核心思想

ALiBi 完全**不使用位置编码**，而是在注意力分数上直接添加一个与距离相关的线性偏置：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}} + m \cdot [-(i-j)]\right)V$$

其中 $m$ 是每个注意力头固定的**斜率 (slope)**，$i$ 和 $j$ 是位置索引。距离越远，惩罚越大。

#### 斜率设置

ALiBi 为每个头设置不同的斜率，形成几何级数：

$$m_h = 2^{-8h/H}, \quad h = 1, 2, \dots, H$$

例如 8 个头的斜率：$m = \{1/2, 1/4, 1/8, 1/16, 1/32, 1/64, 1/128, 1/256\}$

#### 优势

- **零可学习参数**：不增加任何模型参数
- **极致外推能力**：在推理时可以处理训练长度数倍的序列，性能几乎不下降
- **计算高效**：只需简单的加法操作
- **训练更快**：比 RoPE 训练速度更快

#### 劣势

- 只提供相对位置信息，表达能力相对有限
- 不如 RoPE 在短序列任务上的表现好

#### 使用模型

BLOOM、MPT (MosaicML)

### 4.6 位置编码对比总结

| 方法 | 可学习参数 | 外推能力 | 计算开销 | 相对位置 | 行业采用 |
|------|-----------|---------|---------|---------|---------|
| 正弦余弦 | ❌ | 有限 | 低 | 部分 | 原始 Transformer |
| 可学习 | ✅ | ❌ 无 | 低 | ❌ | BERT, GPT-3 |
| T5 偏置 | ✅ | 较好 | 中等 | ✅ | T5 |
| RoPE | ❌ | 较好（需插值） | 中等 | ✅ | LLaMA, Mistral 等 |
| ALiBi | ❌ | **最佳** | 最低 | ✅ | BLOOM, MPT |

**当前趋势**：RoPE 是 2024-2025 年最主流的选择，大多数新模型都采用 RoPE 或其变体（如 YaRN、NTK-aware 插值）来支持长上下文。

---

## 5. Encoder-Decoder 架构

### 概述

Encoder-Decoder 架构是 Transformer 的原始设计，包含两个主要组件：

- **编码器 (Encoder)**：处理输入序列，生成上下文化的表示
- **解码器 (Decoder)**：基于编码器的输出，逐个生成输出序列

### 数据流

```
输入序列: "I love you"
    ↓
[Tokenization] → ["I", "love", "you"]
    ↓
[Embedding + Position Encoding]
    ↓
[Encoder Layers × N]  ← 双向自注意力，看到所有 token
    ↓
编码器输出: 上下文表示
    ↓
[Cross-Attention] ← 解码器通过交叉注意力查阅编码器
    ↓
[Decoder Layers × N]  ← 因果自注意力，只看到之前的 token
    ↓
[Linear + Softmax]
    ↓
输出序列: "我爱你"
```

### 适用场景

- 机器翻译
- 文本摘要
- 语音识别（Whisper）
- 问答系统
- 任何输入和输出长度不同、结构不同的任务

### 为什么现代 LLM 多采用 Decoder-Only？

尽管 Encoder-Decoder 在理论上对 seq2seq 任务更合适，但现代 LLM（GPT-4、LLaMA 等）几乎都采用 Decoder-Only 架构，原因包括：

1. **统一性**：一个模型可以处理所有任务（通过指令/提示）
2. **自回归生成**：Decoder 的自回归特性天然适合文本生成
3. **规模扩展**：Decoder-Only 架构在扩展性方面表现更好
4. **训练效率**：无需同时训练编码器和解码器

---

## 6. 仅 Encoder 模型（BERT 家族）

Encoder-Only 模型使用 Transformer 的编码器部分，通过**双向自注意力**来理解文本。它们不直接生成文本，而是产生上下文化的词表示，用于下游任务。

### 6.1 BERT

**论文**：BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding (2018)
**机构**：Google AI Language

#### 核心创新

BERT 的核心创新是**双向预训练**。之前的模型（如 GPT-1）只能从左到右或从右到左处理文本，而 BERT 可以**同时利用左右两侧的上下文**。

#### 预训练任务

**1. 掩码语言建模 (Masked Language Modeling, MLM)**

随机遮盖输入中 15% 的 token，让模型预测被遮盖的 token：

```
输入: "The [MASK] sat on the mat"
标签: "cat"
```

遮盖策略（对选中的 15% token）：
- 80% 替换为 [MASK]
- 10% 替换为随机 token
- 10% 保持不变

**为什么不完全替换为 [MASK]？** 因为微调时没有 [MASK] token，如果预训练时只用 [MASK]，模型会学到一个偏差：只在 [MASK] 位置产生好表示，而在真实 token 位置表现不佳。

**2. 下一句预测 (Next Sentence Prediction, NSP)**

判断两个句子是否是原文中连续的：

```
输入 A: "The man went to the store."
输入 B: "He bought a gallon of milk."  → 标签: IsNext

输入 A: "The man went to the store."
输入 B: "Penguins are flightless birds." → 标签: NotNext
```

**注意**：后续研究（RoBERTa）发现 NSP 任务实际上**没有必要**，移除后性能反而更好。

#### 架构

BERT 使用后置归一化 (Post-LN) 的 Transformer 编码器，并添加了**段嵌入 (Segment Embedding)** 来区分两个句子：

$$\text{Input} = \text{TokenEmb} + \text{PositionEmb} + \text{SegmentEmb}$$

#### 模型配置

| 版本 | 层数 | 隐藏维度 | 注意力头数 | 参数量 |
|------|------|---------|-----------|--------|
| BERT-base | 12 | 768 | 12 | 110M |
| BERT-large | 24 | 1024 | 16 | 340M |

#### 微调

BERT 的强大之处在于预训练后可以通过简单的分类头进行微调：

- **文本分类**：在 [CLS] token 的输出上添加线性分类器
- **命名实体识别 (NER)**：在每个 token 的输出上添加分类器
- **问答**：在两个特殊 token 的输出上预测答案的起止位置
- **语义相似度**：在 [CLS] 输出上训练分类器

### 6.2 RoBERTa

**论文**：RoBERTa: A Robustly Optimized BERT Pretraining Approach (2019)
**机构**：Facebook AI

RoBERTa 并没有修改 BERT 的架构，而是通过**优化训练策略**大幅提升了性能：

1. **移除 NSP**：发现 NSP 任务无益甚至有害
2. **动态遮盖**：每次 epoch 重新随机选择遮盖位置（而非固定）
3. **更大批量**：使用更大的批量训练
4. **更多数据**：使用 160GB 文本（BERT 使用 16GB）
5. **更长训练**：训练更多步数
6. **Byte-Pair Encoding**：使用字节级别的 BPE（而非 WordPiece）

### 6.3 ALBERT

**论文**：ALBERT: A Lite BERT for Self-supervised Learning of Language Representations (2019)
**机构**：Google Research

核心优化：
1. **嵌入参数分解**：将 token 嵌入矩阵分解为两个小矩阵，大幅减少参数
2. **跨层参数共享**：所有层共享相同的参数，进一步减少参数量
3. **句子顺序预测 (SOP)**：替代 NSP，判断两个句子的顺序是否正确

### 6.4 DistilBERT

**论文**：DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter (2019)
**机构**：Hugging Face

通过**知识蒸馏**将 BERT 压缩 40% 的参数，保留 97% 的性能：
- 移除 token 类型嵌入
- 层数减半（12 → 6）
- 使用蒸馏损失函数训练

### 6.5 ELECTRA

**论文**：ELECTRA: Pre-training Text Encoders as Discriminators Rather Than Generators (2020)
**机构**：Google Research / Stanford

**核心创新**：不是遮盖 token 然后预测，而是**替换** token 然后判断是否被替换（类似于 GAN 的判别器）：

```
原始: "The chef cooked the meal"
修改: "The chef [baked] the meal"  → 模型判断 "baked" 是否是原始 token
```

**优势**：
- 所有输入 token 都参与损失计算（BERT 的 MLM 只有 15%）
- 训练效率大幅提升（相同计算量下性能更好）
- 小模型上表现尤为出色

### 6.6 DeBERTa

**论文**：DeBERTa: Decoding-enhanced BERT with Disentangled Attention (2020)
**机构**：Microsoft

核心创新：
1. **解耦注意力**：分别计算内容到内容和内容到位置的注意力
2. **增强掩码解码器**：在 MLM 任务中，将遮盖 token 的绝对位置信息也加入输入

DeBERTa-v3 进一步引入了**填空式预训练**替代 MLM。

### 6.7 SpanBERT

**论文**：SpanBERT: Improving Pre-training by Representing and Predicting Spans (2020)
**机构**：Allen AI / UW

核心创新：
1. **Span 遮盖**：遮盖连续的 token 片段（而非单个 token）
2. **Span Boundary Objective (SBO)**：强制模型使用 span 边界的表示来预测被遮盖的内容
3. **单句训练**：移除 NSP，只用单个句子训练

---

## 7. 仅 Decoder 模型（GPT 家族）

Decoder-Only 模型使用 Transformer 的解码器部分，通过**因果自注意力**从左到右处理文本。它们天然适合**自回归文本生成**。

### 7.1 GPT 系列

#### GPT-1 (2018)

**论文**：Improving Language Understanding by Generative Pre-Training
**机构**：OpenAI

- 12 层 Transformer 解码器
- 使用标准语言建模目标（预测下一个 token）进行预训练
- 然后在下游任务上微调
- 参数量：117M

#### GPT-2 (2019)

**论文**：Language Models are Unsupervised Multitask Learners
**机构**：OpenAI

- 48 层（最大版本）
- 引入了 **zero-shot learning** 的概念：无需微调即可完成各种任务
- 参数量：124M / 355M / 774M / 1.5B
- 使用**前置归一化 (Pre-LN)** 替代后置归一化

#### GPT-3 (2020)

**论文**：Language Models are Few-Shot Learners
**机构**：OpenAI

- 96 层
- 参数量：175B
- 引入了 **in-context learning**：通过在提示中给出示例来指导模型行为
- 展示了大规模语言模型的涌现能力

#### GPT-4 (2023)

- 具体架构未公开，据传使用 MoE 架构
- 支持多模态输入（文本+图像）
- 参数量据传约 1.8T（但可能使用了 MoE 稀疏激活）

### 7.2 LLaMA 系列

#### LLaMA 1 (2023)

**机构**：Meta AI

**核心设计理念**：证明在更多公开数据上训练较小的模型，可以达到更大模型的效果。

**架构改进**（相比原始 Transformer）：

1. **前置归一化 (Pre-Norm)**：在每个子层之前应用 RMSNorm（而非后置 LayerNorm）
2. **SwiGLU 激活函数**：替代原始的 ReLU，在 FFN 中使用
3. **RoPE 旋转位置编码**：替代绝对位置编码
4. **无偏置 (No Bias)**：移除了大部分偏置项（简化且无性能损失）

**SwiGLU 激活函数**：

$$\text{SwiGLU}(x, W, V, b, c, W_1) = (\text{SiLU}(xW + b) \odot (xV + c))W_1$$

其中 SiLU (Swish) = $x \cdot \sigma(x)$

SwiGLU 相比 GeLU 性能更好，但需要 3/2 倍的参数量（因为需要两个投影矩阵）。

**模型配置**：

| 版本 | 层数 | 隐藏维度 | 注意力头数 | 参数量 |
|------|------|---------|-----------|--------|
| LLaMA-7B | 32 | 4096 | 32 | 7B |
| LLaMA-13B | 40 | 5120 | 40 | 13B |
| LLaMA-33B | 60 | 6656 | 52 | 33B |
| LLaMA-65B | 80 | 8192 | 64 | 65B |

#### LLaMA 2 (2023)

- 训练数据从 1.4T tokens 增加到 2T tokens
- 上下文长度从 2048 增加到 4096
- 引入了 **GQA (Grouped Query Attention)**
- 发布了对话微调版本（LLaMA 2 Chat）
- 模型规模：7B, 13B, 70B

#### LLaMA 3 (2024)

- 8B 和 70B 版本
- 上下文长度扩展到 8192（后续支持 128K）
- 使用 15T tokens 训练
- 引入了更严格的数据过滤
- GQA 配置：8B 用 8 个 KV 头，70B 用 8 个 KV 头

#### LLaMA 3.1 (2024)

- 8B, 70B, 405B
- 上下文长度 128K
- 使用 RoPE 的 YaRN 缩放来支持长上下文
- 405B 版本使用 MoE？不，是密集模型

### 7.3 其他重要 Decoder 模型

#### Mistral / Mixtral

- **Mistral-7B**：使用 Sliding Window Attention (SWA) 和 GQA
- **Mixtral 8x7B**：MoE 架构（详见 MoE 章节）

#### Qwen 系列

- 阿里巴巴开发
- 使用 RoPE、SwiGLU、GQA
- Qwen-2.5 支持长上下文
- 有密集版和 MoE 版本

#### DeepSeek 系列

- DeepSeek-V2/V3：使用 MLA (Multi-head Latent Attention) 和 MoE
- DeepSeek-R1：推理能力强，使用 GRPO 训练

#### Gemma 系列

- Google 开源
- 使用 GeGLU 激活函数
- Gemma 2 引入了滑动窗口注意力

---

## 8. Encoder-Decoder 模型

### 8.1 T5

**论文**：Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer (2019)
**机构**：Google

#### 核心创新：Text-to-Text 框架

T5 将所有 NLP 任务统一为"文本到文本"的格式：

| 任务 | 输入格式 | 输出 |
|------|---------|------|
| 翻译 | "translate English to German: That is good" | "Das ist gut" |
| 摘要 | "summarize: ..." | 摘要文本 |
| 分类 | "sentiment: This movie is great!" | "positive" |
| QA | "question: What? context: ..." | 答案 |

#### 预训练目标：Span Corruption

T5 使用"跨度破坏"作为预训练目标：
1. 随机选择文本中的 span（连续 token 序列）
2. 用特殊 sentinel token 替换这些 span
3. 训练模型恢复原始 span

```
输入: "Thank you 〈X〉 me to your party 〈Y〉 week"
输出: "〈X〉 for inviting 〈Y〉 last 〈Z〉"
```

#### 架构特点

- 使用前置归一化 (Pre-LN)
- 相对位置偏置（而非绝对位置编码）
- Encoder-Decoder 架构
- 使用 SentencePiece 分词

#### 模型版本

| 版本 | 参数量 | 层数 | d_model | 注意力头数 |
|------|--------|------|---------|-----------|
| T5-Small | 60M | 6 | 512 | 8 |
| T5-Base | 220M | 12 | 768 | 12 |
| T5-Large | 770M | 24 | 1024 | 16 |
| T5-3B | 3B | 24 | 1024 | 16 |
| T5-11B | 11B | 24 | 1024 | 16 |

#### Flan-T5

Flan-T5 是 T5 的指令微调版本，在大量指令数据上微调，大幅提升了 zero-shot 性能。

### 8.2 BART

**论文**：BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension (2019)
**机构**：Facebook AI

#### 核心思想

BART 使用**去噪自编码**作为预训练目标：
1. 对输入文本施加某种"破坏"（噪声）
2. 训练模型恢复原始文本

#### 破坏方式

BART 探索了多种破坏方式：
1. **Token Masking**：随机遮盖 token（类似 BERT）
2. **Token Deletion**：随机删除 token
3. **Text Infilling**：用单个 ängen 标记替换 span
4. **Sentence Permutation**：打乱句子顺序
5. **Document Rotation**：随机选择一个起始点，旋转文档

最终发现 **Text Infilling** 效果最好。

#### 架构

BART 使用标准的 Seq2Seq Transformer 架构：
- 双向编码器（类似 BERT）
- 自回归解码器（类似 GPT）
- 使用 GeLU 激活函数

#### 与 T5 的对比

| 特性 | T5 | BART |
|------|-----|------|
| 预训练目标 | Span Corruption（序列到序列） | Denoising（去噪） |
| 架构 | Encoder-Decoder | Encoder-Decoder |
| 位置编码 | 相对位置偏置 | 绝对位置编码 |
| 输入格式 | 统一 text-to-text | 标准序列到序列 |
| 擅长任务 | 翻译、摘要、分类 | 摘要、生成 |

### 8.3 其他 Encoder-Decoder 模型

#### PEGASUS

**专用于摘要**的 Encoder-Decoder 模型，预训练目标是 Gap Sentence Generation (GSG)：随机删除句子，训练模型生成被删除的句子。

#### M2M100

Facebook 的多语言翻译模型，支持 100 种语言之间的直接翻译。

#### mBART

BART 的多语言版本，在 25 种语言上预训练。

#### UL2

Google 的统一语言学习框架，结合了多种预训练目标（如 denoising、prefix LM、span corruption）。

---

## 9. 归一化方法

### 9.1 前置归一化 vs 后置归一化

#### 后置归一化 (Post-LN)

原始 Transformer 使用的归一化方式：

$$\text{Output} = \text{LayerNorm}(x + \text{Sublayer}(x))$$

归一化应用在残差连接**之后**。

**问题**：
- 梯度在反向传播时需要经过多层 LayerNorm 的雅可比矩阵，可能导致梯度消失/爆炸
- 训练不稳定，对学习率非常敏感
- 需要 warmup 才能稳定训练
- 深层模型难以训练

#### 前置归一化 (Pre-LN)

GPT-2 首先采用，现在成为主流：

$$\text{Output} = x + \text{Sublayer}(\text{LayerNorm}(x))$$

归一化应用在子层**之前**，残差连接保持"干净"。

**优势**：
- 残差路径是**恒等映射**，梯度可以直接回传到任意层
- 训练更稳定，对超参数不敏感
- 可以训练更深的模型
- 不一定需要 warmup

**劣势**：
- 某些研究表明，在充分训练后，Post-LN 可能获得略好的最终性能
- 可能在深层网络中出现"表示坍塌"问题

**历史转变**：
- BERT (2018)：Post-LN，12 层
- GPT-2 (2019)：Pre-LN，48 层
- T5 (2019)：Pre-LN，24 层
- LLaMA (2023)：Pre-LN + RMSNorm，32-80 层

#### 代码对比

```python
# Post-LN (原始 Transformer)
class PostLNBlock(nn.Module):
    def forward(self, x):
        # Self-Attention
        attn_out = self.attention(x)
        x = self.layer_norm(x + attn_out)
        # FFN
        ffn_out = self.ffn(x)
        x = self.layer_norm(x + ffn_out)
        return x

# Pre-LN (GPT-2 及之后)
class PreLNBlock(nn.Module):
    def forward(self, x):
        # Self-Attention
        x_norm = self.layer_norm(x)
        attn_out = self.attention(x_norm)
        x = x + attn_out
        # FFN
        x_norm = self.layer_norm(x)
        ffn_out = self.ffn(x_norm)
        x = x + ffn_out
        return x
```

### 9.2 LayerNorm vs RMSNorm

#### LayerNorm (LN)

$$\text{LayerNorm}(x) = \gamma \odot \frac{x - \mu}{\sigma} + \beta$$

其中：
- $\mu = \frac{1}{d}\sum_{i=1}^{d} x_i$ （均值）
- $\sigma = \sqrt{\frac{1}{d}\sum_{i=1}^{d}(x_i - \mu)^2 + \epsilon}$ （标准差）
- $\gamma, \beta$ 是可学习的缩放和偏移参数

#### RMSNorm

$$\text{RMSNorm}(x) = \gamma \odot \frac{x}{\text{RMS}(x)}$$

其中：
- $\text{RMS}(x) = \sqrt{\frac{1}{d}\sum_{i=1}^{d} x_i^2 + \epsilon}$

**区别**：RMSNorm 不计算均值（不做中心化），只做缩放。

#### 对比

| 特性 | LayerNorm | RMSNorm |
|------|-----------|---------|
| 中心化 | ✅ | ❌ |
| 缩放 | ✅ | ✅ |
| 可学习参数 | γ 和 β | 仅 γ |
| 计算量 | 较高（需要计算均值） | 较低 |
| 表达能力 | 更强 | 略弱 |
| 训练稳定性 | 好 | 更好（深层模型） |
| 使用模型 | BERT, GPT-2, T5 | LLaMA, Gemma, Mistral |

**为什么 RMSNorm 在大模型中更受欢迎？**
- 计算效率更高（约快 7-10%）
- 减少了中心化操作带来的信息损失
- 在高维空间中，随机向量几乎正交，中心化的意义不大
- 实践中在深层模型中表现更稳定

---

## 10. 推理优化技术

### 10.1 Flash Attention

#### 问题

标准注意力机制的计算需要 O(T²) 内存来存储注意力矩阵，这在大序列长度时成为瓶颈。

#### 解决方案

Flash Attention (Tri Dao 等, 2022) 通过以下技术实现内存高效的注意力计算：

1. **分块计算 (Tiling)**：将 Q、K、V 分成小块，逐块计算注意力，避免存储完整的 N×N 注意力矩阵
2. **重计算 (Recomputation)**：在反向传播时重新计算注意力，而非存储中间结果
3. **硬件感知**：针对 GPU 的层次化内存结构（SRAM vs HBM）进行优化

#### 核心原理

传统注意力：
```
S = QK^T / sqrt(d)     # O(T²) 内存
P = softmax(S)          # O(T²) 内存  
O = P @ V               # O(T²) 内存
```

Flash Attention：
```
# 分块处理，每块在 SRAM 中计算
for each block of Q:
    for each block of K, V:
        # 在 SRAM 中计算部分注意力
        S_block = Q_block @ K_block^T / sqrt(d)
        P_block = softmax(S_block)
        O_block += P_block @ V_block
# 总内存：O(T) 而非 O(T²)
```

#### 版本演进

| 版本 | 年份 | 改进 |
|------|------|------|
| Flash Attention 1 | 2022 | 首次实现，IO 感知 |
| Flash Attention 2 | 2023 | 更好的并行化，支持 MQA/GQA，快 30% |
| Flash Attention 3 | 2024 | 针对 H100 Hopper 架构优化，异步执行 |
| Flash Attention 4 | 开发中 | 针对 Blackwell 架构 |

#### 性能

- 训练速度提升 **2-4 倍**
- 内存从 O(T²) 降低到 O(T)
- **精度完全相同**（无近似，无信息损失）

### 10.2 Paged Attention

#### 问题

KV Cache 在推理时需要连续的内存空间。由于序列长度不可预测，系统需要为每个请求预留最大长度的空间，导致大量内存浪费。

#### 解决方案

Paged Attention (Kwon 等, 2023, vLLM) 借鉴操作系统的**虚拟内存分页机制**：

- 将 KV Cache 分割为固定大小的"页"（blocks）
- 页不需要在物理内存中连续存储
- 使用页表 (page table) 映射逻辑页到物理页
- 按需分配页，序列增长时动态添加

#### 优势

- 内存浪费从 60-80% 降低到 < 4%
- 支持更大的批量大小和更长序列
- 与 Flash Attention 兼容

### 10.3 KV Cache

#### 问题

在自回归生成中，每生成一个新 token，模型需要关注所有之前的 token。如果不做优化，每步都需要重新计算所有历史 token 的 K 和 V。

#### 解决方案

缓存之前计算过的 Key 和 Value 向量，新 token 只需要计算自己的 Q，然后与缓存的 K、V 做注意力：

$$\text{Attention}(q_t, [k_1, ..., k_{t-1}, k_t], [v_1, ..., v_{t-1}, v_t])$$

#### KV Cache 大小

$$\text{Size}_{KV} = 2 \times L_{seq} \times B_{batch} \times N_{layers} \times H_{heads} \times D_{head} \times P_{precision}$$

例如 LLaMA-2 70B (FP16, 4096 上下文):
$$2 \times 4096 \times 1 \times 80 \times 64 \times 128 \times 2 = 5.4 \text{ GB}$$

#### 缓存优化技术

1. **KV Cache 量化**：将缓存从 FP16 量化到 INT8/INT4
2. **KV Cache 压缩**：使用低秩近似压缩缓存
3. **前缀缓存 (Prefix Caching)**：共享相同前缀的请求可以复用缓存
4. **滑动窗口缓存**：只保留最近 W 个 token 的缓存

### 10.4 GQA 与 MQA

#### Multi-Head Attention (MHA) - 标准

每个 Query 头都有自己独立的 Key 和 Value 头。对于 h 个注意力头，有 h 组 K 和 V。

$$\text{Cache}_{MHA} = 2 \times h \times T \times d_{head}$$

#### Multi-Query Attention (MQA)

所有 Query 头共享**一组** K 和 V (Shazeer, 2019)：

$$\text{Cache}_{MQA} = 2 \times 1 \times T \times d_{head}$$

KV Cache 大小减少 **h 倍**！但可能损失一些模型质量。

#### Grouped-Query Attention (GQA)

GQA (Ainslie 等, 2023) 是 MHA 和 MQA 的折中：将 Query 头分成 g 组，每组共享一组 K 和 V：

$$\text{Cache}_{GQA} = 2 \times g \times T \times d_{head}$$

例如 LLaMA-2 70B：64 个 Query 头，8 个 KV 组 (g=8)，缓存大小是 MHA 的 1/8。

#### 对比

| 方法 | KV 头数 | 缓存大小 | 模型质量 | 推理速度 |
|------|--------|---------|---------|---------|
| MHA | h | 最大 | 最佳 | 最慢 |
| GQA | g (1 < g < h) | 中等 | 接近 MHA | 中等 |
| MQA | 1 | 最小 | 略有损失 | 最快 |

**当前趋势**：GQA 成为现代 LLM 的标准配置，平衡了质量和效率。

---

## 11. MoE 混合专家模型

### 核心思想

传统（密集）模型的每个 token 都会经过所有参数的计算。MoE (Mixture of Experts) 通过**稀疏激活**实现：每个 token 只经过模型中一小部分"专家"的计算。

### 架构

MoE 通常替换 Transformer 中的 FFN 层：

```
密集 FFN:  x → [Linear → ReLU → Linear] → output
MoE FFN:   x → Router → [Expert_1, Expert_2, ..., Expert_N] → output
                ↗      ↗                ↗
           top-k 选择的专家
```

### 路由机制 (Router)

路由器是一个简单的线性层 + Softmax：

$$p(x) = \text{softmax}(x \cdot W_{gate})$$

然后选择 Top-K 个概率最高的专家：

$$\text{MoE}(x) = \sum_{i \in \text{TopK}(p(x))} p_i(x) \cdot \text{Expert}_i(x)$$

### Top-K 选择

- **Top-1**（Switch Transformer）：每个 token 只选 1 个专家，最简单
- **Top-2**（Mixtral）：选 2 个专家，更常见
- **Top-8**（DeepSeek-V3）：从 256 个专家中选 8 个

### 负载均衡

MoE 面临的一个核心问题是**路由坍塌**：所有 token 都被路由到少数几个专家，其他专家被闲置。

解决方案：
1. **辅助损失**：惩罚不均衡的路由分布
2. **噪声注入**：在路由分数中添加噪声增加探索
3. **专家选择约束**：限制每个 token 的容量
4. **DeepSeek 的动态偏置**：动态调整路由偏置

### 共享专家 (Shared Experts)

DeepSeek 引入了"共享专家"的概念：除了被路由的专家外，还有 1-2 个**始终激活**的共享专家：

$$\text{MoE}(x) = \text{SharedExpert}(x) + \sum_{i \in \text{TopK}} p_i(x) \cdot \text{Expert}_i(x)$$

共享专家负责处理通用知识，路由专家负责专业化知识。

### 重要 MoE 模型

| 模型 | 总参数 | 活跃参数 | 专家数 | Top-K |
|------|--------|---------|--------|-------|
| Switch Transformer | 1.6T | - | 2048 | 1 |
| Mixtral 8x7B | 47B | 13B | 8/层 | 2 |
| Mixtral 8x22B | 141B | 39B | 8/层 | 2 |
| DeepSeek-V3 | 671B | 37B | 256/层 | 8 |
| DeepSeek-R1 | 671B | 37B | 256/层 | 8 |
| LLaMA 4 Scout | 109B | 17B | 16/层 | 8 |
| LLaMA 4 Maverick | 400B | 17B | 128/层 | 8 |

### MoE 的优势与挑战

**优势**：
- 更大的模型容量，但不增加推理计算量
- 训练和推理更高效（每 FLOP 的质量更高）
- 可以通过增加专家来扩展

**挑战**：
- **显存占用大**：所有专家的权重都必须加载到内存
- **训练复杂**：负载均衡、通信开销
- **微调困难**：LoRA 等技术需要适配 MoE

---

## 12. Transformer 的视觉变体

### 12.1 Vision Transformer (ViT)

**论文**：An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale (2020)
**机构**：Google Research

#### 核心思想

将图像看作"词序列"——将图像分割成固定大小的**图像块 (patches)**，每个 patch 类比为一个 token。

#### 架构

1. **图像分块**：将 224×224 图像分割为 16×16 的 patch，共 196 个 patch
2. **线性投影**：每个 patch (16×16×3=768 维) 投影到 d 维向量
3. **分类 token**：添加一个可学习的 [CLS] token
4. **位置编码**：为每个 patch 添加位置嵌入
5. **Transformer 编码器**：标准的多层 Transformer 编码器
6. **分类头**：[CLS] token 的输出通过 MLP 进行分类

```
图像 (H×W×C)
    ↓ [分割为 patches]
Patches (N×P²×C)  其中 N = HW/P²
    ↓ [线性投影]
Patch Embeddings (N×D)
    ↓ [+ [CLS] token]
Tokens (N+1×D)
    ↓ [+ 位置编码]
    ↓ [Transformer Encoder × L]
    ↓ [取 [CLS] 输出]
分类结果
```

#### 关键发现

- ViT 在**大规模数据**（如 ImageNet-21k, JFT-300M）上预训练时效果显著
- 在中小规模数据上不如 CNN（缺乏归纳偏置）
- 预训练成本高，但微调效率高

#### 模型配置

| 版本 | 层数 | 隐藏维度 | MLP 维度 | 注意力头数 | 参数量 |
|------|------|---------|---------|-----------|--------|
| ViT-Small | 12 | 384 | 1536 | 6 | 22M |
| ViT-Base | 12 | 768 | 3072 | 12 | 86M |
| ViT-Large | 24 | 1024 | 4096 | 16 | 307M |
| ViT-Huge | 32 | 1280 | 5120 | 16 | 632M |

### 12.2 Swin Transformer

**论文**：Swin Transformer: Hierarchical Vision Transformer using Shifted Windows (2021)
**机构**：Microsoft Research

#### 解决的问题

ViT 的全局自注意力计算复杂度为 O(N²)，对高分辨率图像不友好。Swin Transformer 通过**层次化窗口注意力**实现线性复杂度。

#### 核心创新

1. **窗口注意力 (Window Attention)**：将图像划分为不重叠的窗口（如 7×7），在每个窗口内计算自注意力。复杂度从 O(N²) 降为 O(N·W²)，其中 W 是窗口大小。

2. **移动窗口 (Shifted Window)**：交替层使用不同的窗口划分（偏移半个窗口大小），使得不同窗口之间可以交换信息。

3. **层次化结构**：类似 CNN 的金字塔结构，逐层合并相邻 patch（下采样），形成多尺度特征表示。

```
Layer 1: 窗口注意力 (常规窗口)
    ↓ [Patch Merging] (2×2 → 1, 维度翻倍)
Layer 2: 窗口注意力 (移动窗口)
    ↓ [Patch Merging]
Layer 3: 窗口注意力 (常规窗口)
    ↓ [Patch Merging]
Layer 4: 窗口注意力 (移动窗口)
```

#### 优势

- 计算复杂度对图像大小**线性**（vs ViT 的二次方）
- 天然支持多尺度特征（适合检测、分割任务）
- 可以作为 CNN 的直接替代品

### 12.3 Perceiver

**论文**：Perceiver: General Perception with Iterative Attention (2021)
**机构**：DeepMind

#### 核心思想

Perceiver 使用**不对称注意力**来处理超高维输入（如图像的所有像素、音频的所有采样点）：

1. **潜在数组 (Latent Array)**：固定大小的低维表示（如 512 维）
2. **交叉注意力**：输入数组（可能非常大）对潜在数组做交叉注意力
3. **自注意力**：在潜在数组内部做自注意力
4. **迭代**：重复上述过程多次

```
输入 Array (N × d_in, N 可以很大)
    ↓ [Cross-Attention]  → 潜在 Array (L × d_latent, L 很小)
    ↓ [Self-Attention]   → 潜在 Array
    ↓ [Cross-Attention]  → 潜在 Array
    ↓ [Self-Attention]   → 潜在 Array
    ↓ (重复多次)
    ↓ [Query 潜在 Array] → 输出
```

#### 优势

- 输入大小不影响计算量（只取决于潜在数组大小）
- 可以处理任意模态的输入（文本、图像、音频、点云）
- 统一的多模态感知框架

### 12.4 其他视觉变体

#### DeiT (Data-efficient Image Transformer)

通过知识蒸馏和强数据增强，使 ViT 能在 ImageNet-1K（无需超大规模数据）上训练出好结果。

#### CvT (Convolutional Vision Transformer)

将卷积引入 ViT 的 token 化过程中，结合 CNN 的局部归纳偏置和 Transformer 的全局建模能力。

#### BEiT (BERT Pre-Training of Image Transformers)

将 BERT 的 MLM 思想应用到视觉领域，使用**掩码图像建模 (MIM)** 预训练。

#### CSWin Transformer

使用交叉形状窗口注意力，在多个基准上超越 Swin Transformer。

---

## 13. 训练技巧

### 13.1 学习率调度

#### 余弦退火 (Cosine Annealing)

最流行的学习率调度策略：

$$\eta_t = \eta_{min} + \frac{1}{2}(\eta_{max} - \eta_{min})\left(1 + \cos\left(\frac{t - T_{warmup}}{T_{total} - T_{warmup}}\pi\right)\right)$$

学习率从峰值 $\eta_{max}$ 平滑衰减到最小值 $\eta_{min}$。

#### 线性衰减

$$\eta_t = \eta_{max} \cdot \max\left(0, \frac{T_{total} - t}{T_{total} - T_{warmup}}\right)$$

#### 原始 Transformer 的调度

论文中使用自定义调度：先线性 warmup，然后按步数的 $-0.5$ 次方衰减：

$$\eta_t = d_{model}^{-0.5} \cdot \min(t^{-0.5}, t \cdot T_{warmup}^{-1.5})$$

### 13.2 Warmup

#### 为什么需要 Warmup？

Transformer 训练必须使用 warmup，主要原因：

1. **Adam 统计量不稳定**：训练初期，Adam 的一阶动量 (m) 和二阶动量 (v) 的估计不准确，大的学习率可能导致灾难性的参数更新
2. **注意力模式不稳定**：训练初期，注意力分布可能非常集中或非常均匀，需要时间稳定
3. **LayerNorm 的交互**：LayerNorm 的梯度可能放大或缩小更新，需要温和的初始阶段

#### 典型配置

```python
# 原始 Transformer 配置
warmup_steps = 4000
peak_lr = 3e-4  # (对于 base 模型, 或 d_model^{-0.5})

# 现代 LLM 配置
warmup_steps = 2000  # 或训练总步数的 1-5%
peak_lr = 3e-4
min_lr = 3e-5  # 余弦退火的最低学习率
```

#### 代码示例

```python
def get_cosine_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps, min_lr=0):
    def lr_lambda(current_step):
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
        return max(min_lr, 0.5 * (1.0 + math.cos(math.pi * progress)))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
```

### 13.3 Gradient Clipping

#### 为什么需要？

在训练过程中，梯度可能突然变得非常大（梯度爆炸），导致参数更新过大、损失变为 NaN。

#### 实现方式

**按范数裁剪**（最常用）：

```python
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

如果梯度的 L2 范数超过 max_norm，则按比例缩放所有梯度。

**按值裁剪**：

```python
torch.nn.utils.clip_grad_value_(model.parameters(), clip_value=0.5)
```

将每个梯度元素限制在 [-clip_value, clip_value] 范围内。

#### 典型值

- 原始 Transformer：无梯度裁剪（使用 warmup 代替）
- 现代 LLM：通常 max_norm = 1.0

### 13.4 优化器选择

#### AdamW

AdamW (Loshchilov & Hutter, 2019) 是当前训练 Transformer 的**标准优化器**。相比原始 Adam，AdamW 实现了**解耦的权重衰减**：

$$\theta_t = \theta_{t-1} - \eta \left(\frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} + \lambda \theta_{t-1}\right)$$

其中 $\lambda$ 是权重衰减系数。

**典型配置**：
```python
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=3e-4,
    betas=(0.9, 0.95),  # 原始 Transformer 用 (0.9, 0.98)
    eps=1e-8,
    weight_decay=0.1
)
```

#### Adam vs AdamW vs SGD

| 优化器 | 优势 | 劣势 | Transformer 适用性 |
|--------|------|------|-------------------|
| SGD | 简单、泛化好 | 需要精心调学习率 | ❌ 不适合 |
| Adam | 自适应学习率 | 权重衰减实现不当 | ⚠️ 可用但非最佳 |
| AdamW | 解耦权重衰减 | 需要调 β 值 | ✅ **标准选择** |

### 13.5 其他训练技巧

#### 混合精度训练 (Mixed Precision)

使用 FP16（或 BF16）进行前向和反向传播，FP32 保存主权重。可减少内存约 50%，加速训练 1.5-2 倍。

```python
scaler = torch.cuda.amp.GradScaler()
with torch.cuda.amp.autocast():
    output = model(input)
    loss = criterion(output, target)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

#### Dropout

原始 Transformer 使用 0.1 的 dropout 率，应用于：
- 注意力权重
- 每个子层的输出（残差连接之后）
- 嵌入层

现代大模型通常减少或去除 dropout（依靠数据增强和正则化）。

#### Label Smoothing

将硬标签（one-hot）替换为软标签，防止模型过度自信：

$$y'_{k} = y_k(1 - \epsilon) + \epsilon / K$$

其中 $\epsilon$ 通常为 0.1。

#### 梯度累积 (Gradient Accumulation)

当批量大小受显存限制时，通过累积多个小批量的梯度来模拟大批量训练。

```python
for i, batch in enumerate(dataloader):
    loss = model(batch) / accumulation_steps
    loss.backward()
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

---

## 14. 推理优化（压缩技术）

### 14.1 量化

#### 概念

量化将模型权重从高精度（FP32/FP16）转换为低精度（INT8/INT4/FP8），减少内存占用和计算时间。

#### 量化类型

**训练后量化 (PTQ)**：模型训练完成后直接量化，无需重新训练。

- **INT8 量化**：权重和激活从 FP16 量化到 INT8，内存减少约 2 倍，速度提升 1.5-2 倍
- **INT4 量化**：更激进的量化，内存减少约 4 倍，可能损失一定精度
- **FP8 量化**：新兴格式，在 H100 等 GPU 上有硬件加速

**量化感知训练 (QAT)**：在训练过程中模拟量化，精度损失更小。

#### 主流量化方法

| 方法 | 精度 | 每参数比特 | 精度损失 | 适用场景 |
|------|------|-----------|---------|---------|
| GPTQ | INT4/INT3 | 3-4 bit | 较小 | 推理部署 |
| AWQ | INT4 | 4 bit | 小 | 推理部署 |
| bitsandbytes (NF4) | INT4 | 4 bit | 中等 | 快速实验 |
| GGUF | INT2-INT8 | 2-8 bit | 可调 | CPU 推理 |
| SmoothQuant | INT8 | 8 bit | 很小 | GPU 推理 |

#### 代码示例

```python
# 使用 bitsandbytes 加载 4-bit 量化模型
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=quantization_config,
)
# 显存从 ~14GB (FP16) 降低到 ~4GB (4-bit)
```

### 14.2 剪枝

#### 概念

剪枝通过移除不重要的参数来减少模型大小和计算量。

#### 类型

**非结构化剪枝**：移除个别权重（设为 0），产生稀疏矩阵。减少参数但不一定减少计算（需要稀疏计算支持）。

**结构化剪枝**：移除整行、整列、整个注意力头或整个层。直接减少计算量。

#### 方法

- **幅度剪枝**：按权重绝对值大小排序，移除最小的
- **基于梯度的剪枝**：使用梯度信息判断参数重要性
- **基于运动的剪枝**：考虑参数在训练过程中的变化

#### NVIDIA Minitron 示例

NVIDIA 将 Llama 3.1 15B 通过结构化剪枝 + 蒸馏压缩为 8B 和 4B，其中 4B 版本的 MMLU 得分比从头训练的 4B 模型**高出 16%**。

### 14.3 知识蒸馏

#### 概念

将大型"教师"模型的知识迁移到小型"学生"模型，使小模型获得接近大模型的性能。

#### 蒸馏方法

**1. 输出蒸馏 (Response-based)**

学生模型学习模仿教师模型的输出分布（Softmax 概率）：

$$L_{distill} = KL(\text{softmax}(z_t / T) || \text{softmax}(z_s / T))$$

其中 T 是温度参数（T > 1 使分布更平滑）。

**2. 特征蒸馏 (Feature-based)**

学生对齐教师的中间层特征表示。

**3. 逐步蒸馏 (Step-by-Step)**

学生不仅学习教师的最终答案，还学习教师的推理过程（Chain-of-Thought）。

#### 代表工作

- **DistilBERT**：BERT → DistilBERT (60% 参数, 97% 性能)
- **TinyLlama**：Llama → TinyLlama 1.1B
- **Phi 系列**：Microsoft 使用合成数据蒸馏的小模型
- **Minitron**：Llama 15B → 8B → 4B

### 14.4 组合优化策略

现代推理优化通常**组合使用**多种技术：

```
原始模型 (FP32)
    ↓ [量化: FP16 → INT4]     → 内存减少 4x
    ↓ [剪枝: 移除不重要的头/层] → 参数减少 20-50%
    ↓ [蒸馏: 大模型 → 小模型]  → 保持性能
    ↓ [KV Cache 量化]          → 推理内存减少
    ↓ [Flash Attention]        → 速度提升 2-4x
    ↓ [投机解码]                → 生成速度提升 2-3x
    ↓ [vLLM/TGI 服务框架]      → 吞吐量最大化
```

---

## 15. Transformer 在各领域的应用

### 15.1 自然语言处理 (NLP)

这是 Transformer 的发源地，也是应用最广泛的领域。

| 任务 | 代表模型 | 架构类型 |
|------|---------|---------|
| 语言建模 | GPT-4, LLaMA, Qwen | Decoder-Only |
| 文本分类 | BERT, DeBERTa | Encoder-Only |
| 命名实体识别 | BERT + CRF | Encoder-Only |
| 机器翻译 | T5, NLLB | Encoder-Decoder |
| 文本摘要 | BART, PEGASUS | Encoder-Decoder |
| 问答系统 | BERT, T5, GPT | 混合 |
| 代码生成 | Codex, Code LLaMA | Decoder-Only |
| 信息抽取 | UIE, GLiNER | Encoder-Only |

### 15.2 计算机视觉 (CV)

Transformer 在 CV 领域已全面超越 CNN 成为主流。

| 任务 | 代表模型 | 说明 |
|------|---------|------|
| 图像分类 | ViT, DeiT, Swin | 直接用 Transformer 替代 CNN |
| 目标检测 | DETR, DINO | 端到端检测，无需锚框 |
| 语义分割 | SETR, SegFormer | 序列到序列的分割 |
| 图像生成 | DiT, Stable Diffusion 3 | 用 Transformer 做扩散模型 |
| 图像编辑 | InstructPix2Pix | 指令驱动的图像编辑 |
| 3D 视觉 | Point Transformer | 点云处理 |
| 视频理解 | Video Swin, TimeSformer | 视频时空建模 |
| 医学影像 | TransUNet, Swin-UNet | 医学图像分割 |

### 15.3 语音处理

| 任务 | 代表模型 | 说明 |
|------|---------|------|
| 语音识别 | Whisper, Wav2Vec 2.0 | Encoder-Decoder / 自监督 |
| 语音合成 | VITS, SpeechT5 | 高质量语音生成 |
| 语音翻译 | SeamlessM4T | 多语言语音翻译 |
| 音频理解 | AudioPaLM, Qwen-Audio | 音频理解和推理 |

**Whisper (OpenAI, 2022)** 是语音领域的里程碑：
- Encoder-Decoder 架构
- 在 680,000 小时标注音频上预训练
- 支持多语言识别和翻译
- 通过特殊 token 控制任务类型和语言
- 交叉注意力实现音频-文本对齐

### 15.4 多模态

| 任务 | 代表模型 | 模态 |
|------|---------|------|
| 图文理解 | GPT-4V, LLaVA, Qwen-VL | 文本 + 图像 |
| 图文生成 | DALL-E 3, Midjourney, Stable Diffusion | 文本 → 图像 |
| 视频理解 | Video-LLaVA | 文本 + 视频 |
| 文档理解 | LayoutLM, Donut | 文本 + 布局 |
| 音乐生成 | MusicLM | 文本 → 音乐 |
| 科学推理 | Chameleon, Gemini | 文本 + 图像 + 音频 |

**多模态 Transformer 的关键机制**：

1. **视觉编码器**：通常使用 ViT 将图像编码为 token 序列
2. **投影层**：将视觉 token 投影到语言模型的嵌入空间
3. **交叉注意力**：或简单的 token 拼接来融合多模态信息
4. **指令微调**：在多模态指令数据上微调以对齐行为

### 15.5 其他领域

- **蛋白质结构预测**：AlphaFold2 使用 Transformer/EvoFormer
- **药物发现**：Transformer 用于分子性质预测
- **时间序列预测**：Informer, Autoformer, PatchTST
- **推荐系统**：SASRec, BERT4Rec
- **强化学习**：Decision Transformer 将 RL 建模为序列预测
- **机器人控制**：RT-2, Octo 使用视觉-语言模型
- **数学推理**：MathGPT, Qwen-Math
- **基因组学**：DNABERT, Nucleotide Transformer

---

## 16. Scaling Laws 缩放定律

### Chinchilla Scaling Laws (2022)

**论文**：Training Compute-Optimal Large Language Models
**机构**：DeepMind

#### 核心发现

之前的观点（Kaplan et al., 2020）认为模型越大越好。Chinchilla 研究表明：**模型大小和训练数据量应该等比例增长**。

$$L(N, D) = E + AN^{-\alpha} + BD^{-\beta}$$

其中：
- $L$ 是测试损失
- $N$ 是模型参数量
- $D$ 是训练 token 数量
- $E, A, B, \alpha, \beta$ 是拟合常数
- 经验值：$\alpha \approx 0.34$, $\beta \approx 0.28$

#### 关键结论

1. **最优比例**：约 20 个训练 token 对应 1 个参数
2. **Chinchilla 模型**：70B 参数 + 4T tokens，以相同的计算预算超越了 280B 的 Gopher
3. **大部分模型训练不足**：GPT-3 (175B) 和其他大模型都远未达到 Chinchilla 最优

### 推理感知缩放定律

近期研究（2024-2025）将推理成本纳入缩放定律：

$$L(N, D, R) = (E + AN^{-\alpha} + BD^{-\beta})(1 + \epsilon R^\gamma)$$

其中 $R = d_{model} / n_{layers}$ 是模型的宽高比。

**发现**：对于推理密集型场景，更宽更浅的模型更高效。

### MoE 缩放定律

MoE 模型可以通过增加专家数量来扩展容量，而不增加每 token 的计算量：

- 更细粒度的专家（更多但更小的专家）可以提高效率
- 256 个专家（如 DeepSeek-V3）的效率提升可达 40 倍
- 但路由开销和通信成本限制了无限扩展

---

## 17. Transformer 架构的演进总结

### 2017-2019：奠基期

| 年份 | 里程碑 | 关键创新 |
|------|--------|---------|
| 2017 | Transformer | 自注意力替代 RNN |
| 2018 | BERT, GPT-1 | 双向 vs 单向预训练 |
| 2019 | GPT-2, T5, XLNet, BART | 规模扩展, 统一框架 |

### 2020-2022：扩展期

| 年份 | 里程碑 | 关键创新 |
|------|--------|---------|
| 2020 | GPT-3, ViT | 涌现能力, Transformer 进军视觉 |
| 2021 | Switch Transformer, DALL-E | MoE, 文本到图像 |
| 2022 | Chinchilla, ALiBi, PaLM | 缩放定律, 长上下文, 规模扩展 |

### 2023-2024：标准化期

| 年份 | 里程碑 | 关键创新 |
|------|--------|---------|
| 2023 | LLaMA, GPT-4, Mistral | 开源 LLM, GQA, RoPE 标准化 |
| 2024 | LLaMA 3, DeepSeek-V2, Mixtral | MoE 主流化, MLA |

### 2025：多样化期

| 趋势 | 说明 |
|------|------|
| MoE 成为标配 | LLaMA 4, Qwen3, DeepSeek-V3 |
| 超长上下文 | 1M+ token 上下文窗口 |
| 多模态统一 | Gemini, GPT-4o, Qwen-VL |
| 替代架构探索 | Mamba, RWKV, Jamba (混合) |

### 现代 LLM 的"标准配方"

一个典型的 2024-2025 年 LLM 的架构配置：

```
架构: Decoder-Only Transformer
归一化: Pre-RMSNorm
位置编码: RoPE (with YaRN/Ntk scaling for long context)
注意力: GQA (8 KV heads for 64-128 query heads)
激活函数: SwiGLU
FFN 扩展比: 8/3 ≈ 2.67 (from SwiGLU parameter matching)
词表: BPE ( SentencePiece or Tiktoken), ~32K-128K
旋转基座: 500K - 1M (for longer context extrapolation)
无偏置: 大部分线性层无 bias
```

---

## 18. 关键论文引用

### 基础架构

1. **Vaswani et al. (2017)** "Attention Is All You Need" — Transformer 原论文
2. **Devlin et al. (2018)** "BERT: Pre-training of Deep Bidirectional Transformers" — BERT
3. **Radford et al. (2018)** "Improving Language Understanding by Generative Pre-Training" — GPT-1
4. **Radford et al. (2019)** "Language Models are Unsupervised Multitask Learners" — GPT-2
5. **Brown et al. (2020)** "Language Models are Few-Shot Learners" — GPT-3

### 位置编码

6. **Shaw et al. (2018)** "Self-Attention with Relative Position Representations" — 相对位置编码
7. **Su et al. (2021)** "RoFormer: Enhanced Transformer with Rotary Position Embedding" — RoPE
8. **Press et al. (2022)** "Train Short, Test Long: Attention with Linear Biases" — ALiBi

### 模型变体

9. **Liu et al. (2019)** "RoBERTa: A Robustly Optimized BERT Pretraining Approach"
10. **Clark et al. (2020)** "ELECTRA: Pre-training Text Encoders as Discriminators"
11. **Raffel et al. (2019)** "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer" — T5
12. **Lewis et al. (2019)** "BART: Denoising Sequence-to-Sequence Pre-training"
13. **Touvron et al. (2023)** "LLaMA: Open and Efficient Foundation Language Models"
14. **Jiang et al. (2023)** "Mixtral of Experts"

### 训练与优化

15. **Loshchilov & Hutter (2019)** "Decoupled Weight Decay Regularization" — AdamW
16. **Hoffmann et al. (2022)** "Training Compute-Optimal Large Language Models" — Chinchilla
17. **Xiong et al. (2020)** "On Layer Normalization in the Transformer Architecture"
18. **Zhang & Sennrich (2019)** "Root Mean Square Layer Normalization" — RMSNorm

### 推理优化

19. **Dao et al. (2022)** "FlashAttention: Fast and Memory-Efficient Exact Attention" — Flash Attention 1
20. **Dao (2023)** "FlashAttention-2: Faster Attention with Better Parallelism" — Flash Attention 2
21. **Kwon et al. (2023)** "Efficient Memory Management for Large Language Model Serving with PagedAttention" — vLLM
22. **Shazeer (2019)** "Fast Transformer Decoding: One Write-Head is All You Need" — MQA
23. **Ainslie et al. (2023)** "GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints"

### 视觉 Transformer

24. **Dosovitskiy et al. (2020)** "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale" — ViT
25. **Liu et al. (2021)** "Swin Transformer: Hierarchical Vision Transformer using Shifted Windows"
26. **Jaegle et al. (2021)** "Perceiver: General Perception with Iterative Attention"

### MoE

27. **Fedus et al. (2022)** "Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity"
28. **Clark et al. (2022)** "Unified Scaling Laws for Routed Language Models" — GShard/GLaM

### 压缩

29. **Hinton et al. (2015)** "Distilling the Knowledge in a Neural Network" — 蒸馏基础
30. **Frantar et al. (2022)** "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers"

---

## 19. 代码示例

### 完整的 Mini Transformer

```python
import torch
import torch.nn as nn
import math

class TransformerBlock(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, num_heads)
        self.ffn = FeedForward(d_model, d_ff)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, mask=None):
        # Pre-LN 架构
        x = x + self.dropout(self.attention(self.norm1(x), mask=mask))
        x = x + self.dropout(self.ffn(self.norm2(x)))
        return x

class FeedForward(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.gelu = nn.GELU()
        self.dropout = nn.Dropout(0.1)
    
    def forward(self, x):
        return self.dropout(self.linear2(self.gelu(self.linear1(x))))

class MiniGPT(nn.Module):
    """一个简化的 Decoder-Only Transformer"""
    def __init__(self, vocab_size, d_model=512, num_heads=8, num_layers=6, 
                 d_ff=2048, max_len=512, dropout=0.1):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(max_len, d_model)
        self.layers = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
        # 权重共享
        self.lm_head.weight = self.token_embedding.weight
        
        self.dropout = nn.Dropout(dropout)
        self.max_len = max_len
    
    def forward(self, input_ids):
        B, T = input_ids.shape
        assert T <= self.max_len
        
        # 嵌入
        tok_emb = self.token_embedding(input_ids)
        pos_emb = self.position_embedding(torch.arange(T, device=input_ids.device))
        x = self.dropout(tok_emb + pos_emb)
        
        # 因果掩码
        mask = torch.tril(torch.ones(T, T, device=input_ids.device)).unsqueeze(0).unsqueeze(0)
        
        # Transformer 层
        for layer in self.layers:
            x = layer(x, mask=mask)
        
        # 输出头
        x = self.norm(x)
        logits = self.lm_head(x)
        
        return logits
```

### 使用 Flash Attention 2

```python
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    torch_dtype=torch.float16,
    attn_implementation="flash_attention_2"  # 启用 Flash Attention 2
)
```

### 使用 GQA

```python
from transformers import LlamaConfig, LlamaForCausalLM

config = LlamaConfig(
    num_attention_heads=32,    # Query 头数
    num_key_value_heads=8,     # KV 头数 (GQA)
    hidden_size=4096,
    intermediate_size=11008,
    num_hidden_layers=32,
    max_position_embeddings=4096,
)

model = LlamaForCausalLM(config)
```

---

## 附录：关键概念速查表

| 概念 | 一句话解释 |
|------|-----------|
| Self-Attention | 每个词关注所有其他词，获取上下文信息 |
| Multi-Head | 多个注意力头并行工作，学习不同关系 |
| Causal Masking | 防止看到未来的信息 |
| Cross-Attention | 一个序列关注另一个序列 |
| Position Encoding | 告诉模型每个词的位置 |
| RoPE | 通过旋转编码相对位置 |
| ALiBi | 通过线性偏置惩罚远距离注意力 |
| Pre-LN | 在子层之前归一化（更稳定） |
| Post-LN | 在子层之后归一化（原始设计） |
| RMSNorm | 不减均值的 LayerNorm（更高效） |
| KV Cache | 缓存历史 K/V 避免重复计算 |
| GQA | 多个 Query 头共享 KV 头 |
| MQA | 所有 Query 头共享一个 KV 头 |
| Flash Attention | 内存高效的精确注意力 |
| Paged Attention | 虚拟内存式的 KV Cache 管理 |
| MoE | 每个词只经过部分专家的计算 |
| Warmup | 从小学习率逐渐增大 |
| Gradient Clipping | 限制梯度最大范数 |
| AdamW | 带解耦权重衰减的自适应优化器 |
| 量化 | 降低数值精度减少内存 |
| 蒸馏 | 大模型教小模型 |
| Scaling Laws | 模型性能与大小/数据的幂律关系 |

---

> 📝 本文档持续更新中。最后更新时间：2026-04-09
> 📚 基于 1000+ 篇论文、教程、技术博客的核心内容整理