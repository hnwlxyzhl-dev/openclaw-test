# 孤立森林 PPT v1 质检任务

## 任务
你是 PPT 质检专家。请严格检查孤立森林 v1 PPT 文件的质量。

## 必读文件
1. `/home/admin/.openclaw/workspace-weaver/output/isolation-forest_v1.pptx` — 待检查的 PPT
2. `/home/admin/.openclaw/workspace-weaver/memory/isolation-forest-ppt-content-logic.md` — 原始内容逻辑设计

## 检查方法
用 python-pptx 读取 PPTX 文件，逐页逐个 shape 检查。

## 7 维度检查标准（满分 100）

1. **文字不超画框**（18 分）— 文本框 left+width ≤ 13.3, top+height ≤ 7.4
2. **文字不重叠**（10 分）— 同一页内文本框之间是否有重叠
3. **图片/架构图文字够大**（13 分）— 架构图标注 ≥ 10pt
4. **箭头指向明确**（9 分）— 箭头和连接线位置合理
5. **完整句子表达**（14 分）— 不是短句碎片，用完整句子
6. **布局合理占满**（13 分）— 每页内容是否充分占满空间，不空洞
7. **内容详细通俗**（13 分）— 有具体数字、有比喻、内容详实
8. **图文紧密结合**（10 分）— 图和文字有编号对应关系

## 边界检查（必须！）
- 幻灯片尺寸: 13.333 × 7.5 英寸
- 所有 shape: left + width ≤ 13.3, top + height ≤ 7.4
- font_size ≥ 9pt（正文）、≥ 10pt（架构图标注）
- 文本框 height 不能超过 5 英寸（通常是 bug）

## 输出要求
1. 用 python-pptx 读取每一页、每一个 shape，记录详细信息
2. 对每个维度逐项打分
3. 列出所有具体问题（带页码和 shape 编号）
4. 给出总分
5. 总分 ≥ 95 可以交付，< 95 列出具体修复建议

## 输出位置
将质检报告写入 `/home/admin/.openclaw/workspace-weaver/memory/isolation-forest-qa-report.md`
