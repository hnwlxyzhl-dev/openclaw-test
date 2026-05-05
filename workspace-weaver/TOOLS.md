# TOOLS.md - 操作参考手册

> 参数、标准、工具、技能索引。制作PPT前必读。

---

## 🎨 PPT 制作参数

### 动态布局（根据内容量调整字体）

| 内容量 | 字体 | 布局策略 |
|--------|------|----------|
| ≤8行 | 16pt | 宽松舒适，突出重点 |
| 9-15行 | 12pt | 平衡美观与信息量 |
| 16-20行 | 11pt | 稍紧凑，信息丰富 |
| ≥21行 | 10pt | 紧凑排列，信息密集 |

### 边距控制

| 元素 | 尺寸 |
|------|------|
| 图片 | 8.5×5.6-6.25 英寸 |
| 文字框 | 3.8×5.4-5.8 英寸 |
| 行间距 | 1.0-1.2 |
| 段后间距 | 2-3pt |
| 底部边距 | ≥0.8 英寸 |

### 字体规范

```
中文：微软雅黑 | 标题：微软雅黑 Bold
英文：Arial / Calibri
代码：Consolas / Source Code Pro
```

### 图文并茂标准

1. 图片占 60-70%（8.5×5.6-6.25 英寸）
2. 文字占 30-40%（3.8 英寸宽）
3. 编号系统 1️⃣2️⃣3️⃣4️⃣ 对应图片组件
4. 每个组件 4 维度说明（输入/输出/参数/作用）
5. 图文一体，紧密结合

### 内容表达原则

❌ 短句碎片："Skip Connections 传递细节"
✅ 完整比喻："Skip Connections 就像给编解码器搭建了一座桥梁，让编码器的重要细节直接传递给对应解码器层，避免信息在压缩过程中丢失。"

---

## ✅ 质量标准

### PPT 自检清单（生成后必做）

- [ ] 版面布局是否合理
- [ ] 字体大小是否合适（动态布局，非一刀切）
- [ ] **文字是否超出边框**（最常见失败点，必须 100% 检查）
- [ ] 图片是否清晰可见（架构图文字 ≥18pt）
- [ ] 图文是否紧密结合（有编号、有对应解释）
- [ ] 同一主题是否在一页内（不拆分）
- [ ] 内容是否与目录匹配

### 质检子代理评分标准（7 维度，满分 100）

1. 文字不超画框（18 分）
2. 文字不能重叠（10 分）
3. 图片/架构图文字够大（13 分）
4. 箭头指向明确（9 分）
5. 完整句子表达（14 分）
6. 布局合理占满（13 分）
7. 内容详细通俗（13 分）
8. 图文紧密结合（10 分）

**铁律：质检 < 95 分必须继续迭代，精确到每一页、每一个问题。读者评审 < 95 分同样必须继续迭代。**

### 读者评审标准（满分 100）

1. 内容深度（20 分）— 不空洞，有足够细节
2. 逻辑连贯（20 分）— 页面间过渡自然
3. 通俗易懂（20 分）— 目标读者能看懂
4. 信息密度（15 分）— 每页有足够信息量
5. 整体收获（15 分）— 读后有实质性收获
6. 文字质量（10 分）— 无重叠、无错别字

### Markdown 写作标准（4 维）

1. **结构清晰** — 标题层次 + 信息架构
2. **逻辑清晰** — 结论先行 + MECE + 层层递进
3. **表达清晰** — 3-5 句/段，15-25 字/句
4. **视觉丰富** — 代码 + 表格 + 图片

---

## 🔄 PPT 工作流（6+1 模式）

**⚠️ 详细文档：`memory/multi-agent-ppt-workflow.md`**
**⚠️ 制作前必读：`skills/powerpoint-pptx/SKILL.md`**

| Step | 角色 | 职责 | 输出 |
|------|------|------|------|
| 1 | 调研子代理 | 收集专业知识 | `memory/{topic}-research.md` |
| 2 | 逻辑设计子代理 | 每页文案、比喻、叙事逻辑 | `memory/{topic}-ppt-content-logic.md` |
| 3 | 架构图子代理（可选） | 生成架构图/流程图 | `output/{topic}-diagrams.pptx` |
| 4 | 主代理（我） | 整合所有素材，生成完整 PPT | `output/{topic}_v{n}.pptx` |
| 5 | 质检子代理 | 7 维度评分 | 质检报告 |
| 6 | 读者评审子代理 | 模拟目标读者评审 | 读者报告 |

**关键原则：**
- Step 2 和 Step 3 可并行执行
- 主代理保留所有创意决策权
- 文件系统是唯一跨代理通信渠道
- task 太长则写文件，task 中引用路径
- ⚠️ 子代理坐标经常出错，必须验证

### 文档编制原则

1. 大规模学习专业知识（30% 时间）→ 临时成为该领域专家
2. 制作文档（40% 时间）→ 结合专业知识 + 文档能力
3. 迭代优化 ≥ 20 次（30% 时间）
4. 双重标准：自己的要求 + 用户的要求，两者都满足才算完成

---

## 📊 设计知识

### 五大设计原则

1. **一页一想法** — 每张幻灯片一个核心观点
2. **视觉层级** — 标题 → 观点 → 细节 → 来源
3. **留白** — 边距至少 10%
4. **对比** — 大小/颜色/形状创造焦点
5. **对齐** — 网格/左对齐/居中

### 配色方案

| 风格 | 主色 | 强调色 | 场景 |
|------|------|--------|------|
| 企业蓝 | `#1E3A5F` | `#3498DB` | 商务报告 |
| 现代极简 | `#000000` | `#FF6B6B` | 设计展示 |
| 创意大胆 | `#6C5CE7` | `#00CEC9` | 品牌发布 |
| 自然环保 | `#27AE60` | `#2ECC71` | 环保主题 |

### 12 种 HTML 幻灯片风格

Bold Signal | Electric Studio | Creative Voltage | Dark Botanical | Notebook Tabs | Pastel Geometry | Split Pastel | Vintage Editorial | Neon Cyber | Terminal Green | Swiss Modern | Paper & Ink

### 8 种页面类型

封面页 | 标题冲击 | 金句强调 | 步骤说明 | 对比页 | 数据展示 | 列表页 | 结尾行动

---

## 🛠️ 工具箱

### PPT 生成工具

| 类型 | 工具 | 输出 | 特点 |
|------|------|------|------|
| Python 库 | python-pptx | .pptx | 完全控制、自动化 |
| HTML 框架 | reveal.js / Slidev / Marp | HTML | 动画丰富 |
| 在线 AI | Gamma / Beautiful.ai / Tome | 在线/PPTX | 快速生成 |
| 国产工具 | 讯飞智文 / WPS AI | PPTX | 中文优化 |

### 素材资源

- 图标：[Flaticon](https://www.flaticon.com) · [iconfont](https://www.iconfont.cn)
- 图片：[Unsplash](https://unsplash.com) · [Pexels](https://www.pexels.com)
- 配色：[Coolors](https://coolors.co) · [Adobe Color](https://color.adobe.com)
- 字体：[Google Fonts](https://fonts.google.com) · 思源字体 · 阿里巴巴普惠体

### 邮件命令

```bash
# 检查邮件
node skills/imap-smtp-email/scripts/imap.js check --limit 10

# 发送邮件
node skills/imap-smtp-email/scripts/smtp.js send \
  --to recipient@example.com \
  --subject "主题" \
  --body "内容"
```

---

## 📋 技能速查

### PPT 制作（6 个）

| 技能 | 用途 | 输出 |
|------|------|------|
| **powerpoint-pptx** ⭐ | 读写 PPTX、布局、模板 | PPTX |
| **ppt-generator** | 乔布斯风竖屏 | HTML |
| **openclaw-slides** | 12 种风格 | HTML |
| **slides-cog** | CellCog 深度研究 | PDF/PPTX |
| **youmind-slides-generator** | 在线编辑协作 | 在线 |
| **ppt-visual** | 设计规范指导 | 文档 |

### 搜索（2 个）

| 技能 | 用途 |
|------|------|
| **tavily-search** | Tavily API 搜索 |
| **multi-search-engine** | 17 搜索引擎 |

### Office（2 个）

| 技能 | 用途 |
|------|------|
| **office-automation** ⭐ | Word/Excel 自动化 |
| **excel-automation** | Excel 实时交互 |

### 邮件（1 个）

| 技能 | 用途 |
|------|------|
| **imap-smtp-email** | 邮件收发/搜索 |

### 工作流（3 个）

| 技能 | 用途 |
|------|------|
| **superpowers** ⭐ | TDD + 子代理开发 |
| **superpowers-cn** ⭐ | 中文 AI 工作流 |
| **self-improvement** ⭐ | 持续优化能力 |

⭐ = 核心技能

---

## 📚 参考文件索引

| 文件 | 内容 |
|------|------|
| `memory/multi-agent-ppt-workflow.md` | 多 Agent PPT 工作流详细文档 |
| `文档编制工作原则.md` | 文档编制的完整原则和标准 |
| `Markdown写作专家完全指南.md` | Markdown 写作详细指南 |
| `PPT工具完整知识库.md` | PPT 工具和设计知识库 |
