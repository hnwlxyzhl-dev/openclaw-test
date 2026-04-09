你是PPT技术质检专家。请用python-pptx严格检查这份PPT。

## PPT文件
/home/admin/.openclaw/workspace-weaver/output/Transformer_架构深度解析_v1.pptx

## 检查项（重点！）

### 1. 文字重叠检测（最重要！）
- 对每页的每个shape，检查它与其他shape是否有重叠区域
- 特别注意文本框之间的重叠
- 列出所有重叠的shape对及其坐标

### 2. 边界检查
- 所有shape: left+width <= 13.333, top+height <= 7.5

### 3. 字体大小检查
- 正文 >= 9pt
- 架构图标注 >= 10pt
- 标题 >= 16pt

### 4. 内容检查
- 是否有短句碎片
- 是否有空白页或内容过少的页
- 是否有中英文混排不一致

## 输出
- 总分（满分100）
- 逐页问题列表（精确到shape坐标）
- 需要修复的问题清单（按优先级排序）

写入：/home/admin/.openclaw/workspace-weaver/memory/transformer-qa-report.md
