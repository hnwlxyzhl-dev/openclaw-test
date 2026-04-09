你是PPT质检专家。请严格检查这个PPT文件。

## 必读文件
1. /home/admin/.openclaw/workspace-weaver/memory/transformer-quality-standards.md（质检标准）
2. /home/admin/.openclaw/workspace-weaver/output/Transformer_架构深度解析_v1.pptx（待检查的PPT）

## 检查方法
用 python-pptx 读取文件，逐页逐个shape检查。

## 7维度检查（满分100分）
1. 文字不超画框（20分）— 最重要！每个shape的left+width<=13.2, top+height<=7.3
2. 图片/架构图文字够大（15分）— 所有标注>=10pt
3. 箭头指向明确（10分）— 连接线有起点终点
4. 完整句子表达（15分）— 不是短句碎片
5. 布局合理占满（15分）— 无大面积空白
6. 内容详细通俗（15分）— 非AI背景能看懂
7. 图文紧密结合（10分）— 文字解释图片

## 边界检查（必须！）
- left + width <= 13.333
- top + height <= 7.5
- font_size >= 9pt（正文）、>= 10pt（架构图标注）

## 输出格式
总分 + 逐页检查 + 需修复问题列表
总分>=95可以交付，<95需列出具体修复建议
