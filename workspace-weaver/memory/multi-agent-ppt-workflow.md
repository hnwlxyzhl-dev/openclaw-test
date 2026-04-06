# 多Agent PPT 制作工作流

> **版本：** v1.1 | **创建日期：** 2026-04-06
> **定位：** 经过实战验证的 PPT 制作标准流程，基于 Stable Diffusion 技术解析 PPT 项目总结
> **核心原则：** 调研→规划→制作→质检，四个阶段各由不同角色负责
> **必备 Skill：** 制作PPT前必须先读 `~/.openclaw/workspace-weaver/skills/powerpoint-pptx/SKILL.md`

---

## 一、为什么用多Agent？

### 单Agent的痛点
- **上下文溢出**：一次对话中写50000字节代码+检查1000行文件，容易超过模型上下文窗口
- **检查盲区**：自己写的代码自己检查，容易放过自己的错误（v3版本U-Net架构图坐标bug就是例子）
- **角色混淆**：创作者和质检者是同一个人，难以保持客观

### 多Agent的优势
- **上下文隔离**：每个子代理有独立上下文，不会互相污染
- **专业分工**：调研、设计、质检各有专长
- **质量保证**：质检子代理没有创作情感，能客观评分
- **文件系统共享**：通过workspace文件传递上下文，不需要实时通信

### 实战数据
| 指标 | 单Agent(v1-v11) | 多Agent(v3-v5) |
|------|-----------------|----------------|
| 迭代次数 | 11次 | 3次(v3→v4→v5) |
| 质检评分 | 无量化 | 52→87→95+ |
| 发现的bug | 用户指出 | 子代理自动发现 |

---

## 二、标准流程（4+1模式）

```
┌─────────────────────────────────────────────────────┐
│                   主代理 (Weaver)                     │
│  负责整体协调、决策、最终整合、bug修复                  │
│  所有创意决策由主代理做，子代理只做辅助                 │
└──────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │
   ┌───▼───┐  ┌──▼───┐  ┌──▼───┐  ┌──▼───┐
   │调研Agent│  │设计Agent│  │制作Agent│  │质检Agent│
   │(Sub)   │  │(Sub)   │  │(主代理) │  │(Sub)   │
   └────────┘  └────────┘  └────────┘  └────────┘
      Step1       Step2      Step3       Step4
```

### Step 1: 调研子代理（Sub-Agent A）

**职责：** 收集、整理、补充PPT所需的专业知识

**输入：**
- PPT主题和目标受众
- 已有的相关知识（MEMORY.md中的经验）
- 需要覆盖的章节列表

**输出：**
- `memory/{topic}-research.md` — 结构化的调研文档

**Task模板：**
```
你是{主题}领域的调研专家。请基于已有知识进行补充和更新调研。

## 必读文件
1. /path/to/MEMORY.md（已有经验）
2. （其他参考资料）

## 输出要求
将调研结果写入 /path/to/memory/{topic}-research.md
包含{N}个章节，每个章节覆盖：
- 核心概念（用通俗语言解释）
- 具体数字和参数
- 形象比喻（面向非专业受众）
- 与其他章节的逻辑关联

## 格式
每个章节用完整句子，不是短句碎片。有具体数字、有比喻、有例子。
```

**实战经验：**
- 调研文档质量直接决定PPT质量，这一步不能省
- 要求子代理先读已有经验再补充，避免从零开始
- 调研文档长度控制在60000-80000字节，太长子代理处理不了

### Step 2: 设计/规划子代理（Sub-Agent B，可选）

**职责：** 设计架构图、流程图等视觉元素

**输入：**
- 调研文档（Step 1的输出）
- PPT设计规范（字体、颜色、布局）

**输出：**
- `scripts/{topic}-diagrams.py` — 生成架构图页面的Python脚本
- `output/{topic}-diagrams.pptx` — 独立的架构图PPTX文件

**Task模板：**
```
你的任务是用 python-pptx 创建包含精美架构图和流程图的PPT页面。

## 必读文件
1. /path/to/memory/{topic}-research.md
2. /path/to/scripts/generate_{topic}_ppt.py（参考风格）

## 需要生成的页面
1. {页面A描述}
2. {页面B描述}
...

## 技术要求
- 使用 MSO_SHAPE 绘制图形
- 幻灯片尺寸: 13.333 x 7.5 英寸
- 颜色方案: ...
- 中文字体: 微软雅黑
- 架构图标注文字≥10pt
- **所有元素必须在幻灯片边界内！**

## 输出
脚本写入 /path/to/scripts/{topic}_diagrams.py
执行生成 /path/to/output/{topic}_diagrams.pptx
```

**实战经验：**
- ⚠️ 子代理生成的坐标经常出错！必须质检后修复
- python-pptx的Inches()和EMU单位容易混淆
- 建议子代理生成独立文件，由主代理审核后再整合

### Step 2.5: 先读 powerpoint-pptx Skill（Main Agent，必须！）

**⚠️ 这一步不能跳过！** 在写任何PPT代码之前，先读 skill 文档。

```python
# 必读 Skill 文件路径
~/.openclaw/workspace-weaver/skills/powerpoint-pptx/SKILL.md
```

**为什么必须读？**
- Skill 里有最新的 API 用法、最佳实践、常见陷阱
- 每次更新后可能有新的功能或修复
- 避免用过时的方法导致bug

**读完后：**
- 把关键的 API 用法记录到本次项目的脚本注释中
- 特别注意：slide布局、字体设置、图片插入、表格操作等常用功能

### Step 3: 主代理制作PPT（Main Agent）

**职责：** 整合所有素材，生成完整PPT

**输入：**
- 调研文档（Step 1）
- 架构图文件（Step 2，如有）
- 设计规范和历史经验

**输出：**
- `output/{topic}_v{n}.pptx` — 完整PPT

**整合方法：**
```python
# 方法：从多个PPTX中挑选页面，组装成新PPT
from pptx import Presentation
import copy

main = Presentation("main.pptx")
diag = Presentation("diagrams.pptx")

source_plan = [
    ("main", 0),   # 封面
    ("main", 1),   # 目录
    ("diag", 0),   # 架构图（替换main的第4页）
    ("main", 3),   # CLIP
    ...
]

new_prs = Presentation()
for src_type, src_idx in source_plan:
    src_slide = (main if src_type == "main" else diag).slides[src_idx]
    new_slide = new_prs.slides.add_slide(new_prs.slide_layouts[6])
    # 复制shapes...
```

**实战经验：**
- 主代理保留所有创意决策权（内容选择、页面分组、风格把控）
- 子代理只做辅助（调研、绘图、质检）
- 这是血泪教训：把创意决策交给子代理会导致内容碎片化

### Step 4: 质检子代理（Sub-Agent C）

**职责：** 客观评估PPT质量，给出具体修复建议

**输入：**
- 完成的PPT文件
- 质检标准文件

**输出：**
- 质检报告（7维度评分 + 具体修复建议）

**Task模板：**
```
你是PPT质检专家。请严格检查这个PPT文件。

## 必读文件
1. /path/to/memory/{topic}-quality-standards.md
2. /path/to/output/{topic}_v{n}.pptx

## 检查方法
用 python-pptx 读取文件，逐页逐个文本框检查。

## 7维度检查（满分100分）
1. 文字不超画框（20分）
2. 图片/架构图文字够大（15分）
3. 箭头指向明确（10分）
4. 完整句子表达（15分）
5. 布局合理占满（15分）
6. 内容详细通俗（15分）
7. 图文紧密结合（10分）

## 边界检查（必须！）
- left + width ≤ 13.333
- top + height ≤ 7.5
- font_size ≥ 9pt（正文）、≥ 10pt（架构图标注）
- height 不能超过 5 英寸（通常是bug）

## 输出格式
总分 + 逐页检查 + 需修复问题列表
总分≥95可以交付，<95需列出具体修复建议
```

**质检标准文件模板：** `memory/{topic}-quality-standards.md`
```markdown
# {主题} PPT 质检标准

## 边界控制
- 幻灯片尺寸: 13.333 x 7.5 英寸
- 所有文本框: left+width ≤ 13.3, top+height ≤ 7.4
- 底部安全区: top ≥ 7.15 保留给页脚

## 字体标准
- 正文: ≥ 9pt
- 架构图标注: ≥ 10pt
- 标题: ≥ 12pt
- 封面标题: ≥ 28pt

## 内容标准
- 必须用完整句子，不是短句碎片
- 必须有具体数字
- 必须有形象比喻（面向非专业受众）
- 架构图和文字说明必须对应

## 历史教训（必须避免！）
- {记录之前犯过的错误}
```

### Step 4.5: 修复循环（Main Agent）

**触发条件：** 质检总分 < 95

**流程：**
1. 主代理阅读质检报告
2. 优先修复P0问题（坐标异常、元素缺失）
3. 修复后保存新版本
4. 重新启动质检子代理
5. 循环直到 ≥ 95

**实战数据：**
| 轮次 | 分数 | 主要问题 | 修复方法 |
|------|------|---------|---------|
| 第1轮 | 52分 | 90个shape坐标飞出幻灯片 | Python脚本批量修复EMU值 |
| 第2轮 | 87分 | 训练流程图缺2个箭头 | 移动重叠箭头到正确位置 |
| 第3轮 | 95+分 | - | 通过 |

---

## 三、关键踩坑记录

### 坑1: 子代理坐标计算错误（严重！）
**现象：** 架构图中的shape的top值变成天文数字（731,521英寸）
**原因：** 子代理在循环中累加偏移量时，把EMU值当英寸用了
**修复：** 主代理用Python脚本批量修正坐标
**预防：** 要求子代理生成后自行验证所有shape的边界

### 坑2: 中文引号导致语法错误
**现象：** Python脚本中 `"中文"内容"` 导致 SyntaxError
**原因：** 中文双引号（\u201c \u201d）和ASCII双引号（"）混用
**修复：** 批量替换中文引号为空
**预防：** Python字符串中只用ASCII引号

### 坑3: tb()函数参数遗漏
**现象：** TypeError: missing 1 required positional argument
**原因：** tb(slide, left, top, width, height, text, ...) 中漏了height
**修复：** 检查函数调用签名
**预防：** 使用代码检查工具

### 坑4: pptx整合时slide顺序错乱
**现象：** 删除+插入slide后顺序不对
**原因：** python-pptx的slide操作是原地修改list，索引会变
**修复：** 用全新的Presentation，按source_plan逐页复制
**预防：** 先确定source_plan，再执行复制

### 坑5: 文本框高度异常
**现象：** 目录页文本框height=28英寸
**原因：** v3脚本中tb()函数的height参数传入了错误的值
**修复：** 批量修正height为合理值（0.3英寸）
**预防：** 质检时检查所有shape的height值

---

## 四、子代理管理经验

### sessions_spawn 参数
```python
sessions_spawn(
    label="sd-ppt-qa",        # 可读标签，方便追踪
    mode="run",               # run=一次性, session=持久
    runtime="subagent",       # subagent=独立上下文
    task="...",               # 任务描述（注意长度限制）
    # task太长时：把详细指令写到文件，task中只引用文件路径
)
```

### 上下文隔离意味着
- 子代理**无法读取**主代理的对话历史
- 子代理**无法访问**其他子代理的输出（除非写入文件）
- 子代理**没有**MEMORY.md等workspace context（除非task中明确要求读取）
- **文件系统是唯一的通信渠道**

### Task长度限制
- task参数有长度限制，不能放太详细的指令
- **正确做法：** 把详细指令写到文件，task中引用文件路径
- 例如：`task="请读取 /path/to/instructions.md 并执行其中的任务"`

---

## 五、适用场景

### 适合多Agent的任务
- ✅ 内容密集型PPT（10+章节，每章需要专业知识）
- ✅ 需要架构图/流程图的PPT
- ✅ 对质量要求高（需要独立质检）
- ✅ 上下文可能溢出的情况（代码量大）

### 不需要多Agent的任务
- ❌ 简单PPT（<5页，内容明确）
- ❌ 纯文字排版（不需要复杂图形）
- ❌ 快速修改现有PPT

---

## 六、性能指标

| 指标 | 数值 |
|------|------|
| 总耗时（SD PPT项目） | ~2小时（含调研+制作+2轮质检修复） |
| 子代理数量 | 4个（调研+设计+质检×2） |
| 质检轮次 | 2轮（52→87→95+） |
| 最终质量 | 95+/100 |
| 总页数 | 15页 |
| 架构图页面 | 4页（整体架构+U-Net+训练流程+推理流程） |

---

## 七、文件结构模板

```
workspace-weaver/
├── memory/
│   ├── {topic}-research.md          # Step1: 调研文档
│   ├── {topic}-quality-standards.md # Step4: 质检标准
│   └── multi-agent-ppt-workflow.md  # 本文件
├── scripts/
│   ├── generate_{topic}_ppt.py      # Step3: 主PPT生成脚本
│   └── {topic}_diagrams.py          # Step2: 架构图生成脚本
└── output/
    ├── {topic}_diagrams.pptx         # Step2: 架构图独立文件
    ├── {topic}_v3.pptx               # Step3: 初版
    ├── {topic}_v4.pptx               # Step4: 质检修复版
    └── {topic}_v5.pptx               # 最终版
```

---

**维护说明：**
- 每次完成PPT项目后更新此文档
- 记录新的踩坑经验和性能指标
- 根据实际情况调整流程步骤

**创建者：** Weaver 🎨
**最后更新：** 2026-04-06
