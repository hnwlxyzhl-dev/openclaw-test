# Transformer PPT v3 — 重构主计划

> **创建日期：** 2026-04-12
> **目标：** 完全重构 Transformer PPT，采用用户指定的新架构（5大模块），使用多Agent流水线

---

## 一、新架构（用户指定）

### 模块1：为什么需要 Transformer
- 现有机制（RNN和LSTM）的问题
- Transformer 能解决什么问题

### 模块2：Transformer 架构概述
- 整体架构（编码器和解码器）
- 各个模块的功能介绍

### 模块3：Transformer 训练阶段（详细讲解）
- 编码器：
  - 嵌入矩阵
  - 词嵌入
  - KQV 矩阵
  - Attention 模块的计算
  - 归一化（Layer Norm）
  - MLP/FFN 模块的计算
- 解码器：
  - 解码器的输入和输出
  - 掩码自注意力机制
  - 交叉注意力机制
- 损失函数和训练过程

### 模块4：Transformer 推理阶段（详细讲解）
- 参考训练阶段的讲解模式
- 推理时编码器和解码器的行为
- 自回归生成过程
- 训练 vs 推理的关键差异

### 模块5：典型应用
- ChatGPT、BERT、T5 等怎么使用 Transformer
- 从原始论文到现代大模型的演进

---

## 二、多Agent流水线

### Step 1: 调研Agent（researcher）
- **标签：** transformer-v3-research
- **输入：** 主题 + 新架构大纲 + 已有调研文档
- **输出：** memory/transformer-v3-research.md
- **重点：** 基于已有调研文档补充更新，聚焦新架构的知识点

### Step 2: 架构规划Agent（planner）
- **标签：** transformer-v3-plan
- **输入：** 调研文档 + 用户指定的新架构
- **输出：** memory/transformer-v3-ppt-plan.md（含每页详细内容设计）
- **重点：** 参考用户架构设计PPT结构，设计每页内容

### Step 3: 绘图Agent（diagram-designer）
- **标签：** transformer-v3-diagrams
- **输入：** 调研文档 + 架构规划
- **输出：** scripts/transformer-v3-diagrams.py + output/transformer-v3-diagrams.pptx
- **重点：** 用 python-pptx 绘制架构图、流程图

### Step 4: 主代理制作（Weaver自己）
- **输入：** 调研文档 + 架构规划 + 架构图
- **输出：** output/Transformer_架构深度解析_v3.pptx
- **重点：** 整合所有素材，生成完整PPT

### Step 5: 质检Agent（qa-inspector）
- **标签：** transformer-v3-qa
- **输入：** v3 PPT 文件
- **输出：** memory/transformer-v3-qa-report.md
- **重点：** 技术质量检查

### Step 6: 读者评审Agent（reader-reviewer）
- **标签：** transformer-v3-reader
- **输入：** v3 PPT 文件
- **输出：** memory/transformer-v3-reader-review.md
- **重点：** 内容质量和可读性评审

---

## 三、设计规范

- 幻灯片尺寸: 13.333 x 7.5 英寸
- 所有 shape: left+width <= 13.2, top+height <= 7.3
- 字体: 中文微软雅黑，英文Arial
- 配色: #1E3A5F(深海蓝) + #3498DB(科技蓝) + #E74C3C(强调红) + #2ECC71(成功绿) + #F39C12(橙色)
- 受众: 非AI背景人员（学过高等数学和线性代数，无机器学习经验）
- 比喻驱动: 每个技术概念必须有通俗比喻

---

## 四、文件结构

```
workspace-weaver/
├── memory/
│   ├── transformer-v3-master-plan.md     # 本文件（主计划）
│   ├── transformer-v3-research.md        # Step1: 调研
│   ├── transformer-v3-ppt-plan.md        # Step2: 架构规划+内容设计
│   ├── transformer-v3-qa-report.md       # Step5: 质检报告
│   └── transformer-v3-reader-review.md   # Step6: 读者评审
├── scripts/
│   ├── transformer-v3-diagrams.py        # Step3: 架构图脚本
│   └── generate_transformer_ppt_v3.py    # Step4: 主PPT脚本
└── output/
    ├── transformer-v3-diagrams.pptx      # Step3: 架构图
    └── Transformer_架构深度解析_v3.pptx  # 最终输出
```

---

## 五、当前状态

- [ ] Step 1: 调研Agent
- [ ] Step 2: 架构规划Agent
- [ ] Step 3: 绘图Agent
- [ ] Step 4: 主代理制作
- [ ] Step 5: 质检Agent
- [ ] Step 6: 读者评审Agent
