你是PPT架构图设计专家。请用 python-pptx 创建 Transformer 架构图和流程图的PPT页面。

## 必读文件
1. /home/admin/.openclaw/workspace-weaver/memory/transformer-research.md（专业知识）
2. /home/admin/.openclaw/workspace-weaver/memory/transformer-ppt-plan.md（15页大纲和设计规范）

## 需要生成的架构图页面（共5页）

### 页面1：Self-Attention Q/K/V 概念图
- 展示一个句子 "The cat sat on the mat, and it was happy"
- 用连线展示 "it" 如何关注 "cat"（注意力权重可视化）
- 同时展示 Q（搜索词）、K（标签）、V（内容）的概念
- 用图书馆比喻的图示

### 页面2：Self-Attention 5步计算流程图
- 流程图展示：
  1. 输入 → 生成 Q、K、V（三个箭头分叉）
  2. Q × K^T → 计算注意力分数（矩阵乘法图示）
  3. ÷ √d_k → 缩放（用温度计比喻）
  4. Softmax → 转成概率（柱状图比喻）
  5. × V → 加权求和（加权平均图示）
- 每步用方框+箭头连接

### 页面3：Multi-Head Attention 架构图
- 展示：输入 → 拆分8份 → 8个独立注意力头 → Concat → 线性投影 → 输出
- 每个注意力头用不同颜色
- 标注 "8个不同的视角"

### 页面4：Transformer 整体架构图（Encoder-Decoder）
- 左边：编码器堆叠（6层）
  - 每层：多头自注意力 → Add&Norm → FFN → Add&Norm
- 右边：解码器堆叠（6层）
  - 每层：掩码自注意力 → Add&Norm → 交叉注意力 → Add&Norm → FFN → Add&Norm
- 中间：交叉注意力的连接箭头
- 底部：Embedding + Position Encoding
- 顶部：Linear + Softmax
- 用不同颜色区分：注意力层（蓝色）、FFN（绿色）、归一化（橙色）

### 页面5：训练 vs 推理 对比图
- 左半：训练阶段（Teacher Forcing）
  - 输入：完整句子
  - 每步都能看到正确答案
  - 标注 "带答案做练习题"
- 右半：推理阶段
  - 输入：一个词一个词生成
  - 每步只能看到之前生成的词
  - 标注 "闭卷考试"
- 用虚线框对比

## 技术要求

### 幻灯片参数
- 尺寸: 13.333 x 7.5 英寸（宽屏16:9）
- 使用 slide_layouts[6]（空白布局）

### 绘图要求
- 使用 pptx.util.Inches 进行定位
- 使用 pptx.enum.shapes.MSO_SHAPE 绘制方框、圆角矩形、箭头
- 所有形状必须有明确的 fill color 和 line color
- 箭头使用 MSO_SHAPE.RIGHT_ARROW 或 connector

### 颜色方案
- 编码器区域: #3498DB（蓝色系）
- 解码器区域: #E74C3C（红色系）
- 注意力层: #3498DB
- FFN层: #27AE60（绿色）
- 归一化层: #F39C12（橙色）
- 文字色: #FFFFFF（白色，在深色背景上）或 #333333（深灰）
- 背景色: #FFFFFF
- 箭头: #555555

### 字体要求
- 中文: 微软雅黑
- 英文: Arial
- 架构图内文字: ≥ 11pt（确保可读）
- 组件名称: ≥ 12pt Bold
- 比喻说明: 11pt

### 边界控制（极其重要！）
- 所有形状: left + width ≤ 13.2
- 所有形状: top + height ≤ 7.3
- 每个形状创建后立即验证边界！

### 代码要求
- 脚本保存到: /home/admin/.openclaw/workspace-weaver/scripts/transformer_diagrams.py
- 输出文件: /home/admin/.openclaw/workspace-weaver/output/transformer_diagrams.pptx
- 代码中必须有详细的中文注释
- 使用 python3 执行脚本

### 常见陷阱（必须避免！）
1. ❌ 不要用中文引号（""），只用ASCII引号（""）
2. ❌ 不要让坐标超出幻灯片边界
3. ❌ 不要让文字太小（< 10pt）
4. ❌ 不要用过于复杂的嵌套结构
5. ✅ 每个形状创建后打印坐标验证
6. ✅ 执行完后打印所有shapes的边界信息

## 执行步骤
1. 先写 Python 脚本到 scripts/transformer_diagrams.py
2. 执行脚本生成 output/transformer_diagrams.pptx
3. 用 python-pptx 读取生成的文件，逐页检查所有shapes的边界
4. 如果有问题，修复后重新生成
5. 输出最终验证报告
