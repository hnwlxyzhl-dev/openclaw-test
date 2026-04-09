你是PPT制作专家。请基于现有v1脚本和两份评审报告，重写Transformer PPT生成脚本。

## 必读文件（按顺序读）
1. /home/admin/.openclaw/workspace-weaver/scripts/generate_transformer_ppt.py（v1脚本，54KB）
2. /home/admin/.openclaw/workspace-weaver/memory/transformer-reader-review.md（读者评审，82分）
3. /home/admin/.openclaw/workspace-weaver/memory/transformer-qa-report.md（技术质检，82分）
4. /home/admin/.openclaw/workspace-weaver/memory/transformer-ppt-content-logic.md（内容逻辑设计）
5. /home/admin/.openclaw/workspace-weaver/memory/transformer-quality-standards.md（质检标准）

## 目标
生成一份98分以上的PPT，输出到：
/home/admin/.openclaw/workspace-weaver/output/Transformer_架构深度解析_v2.pptx

## 必须修复的问题

### 排版修复（来自质检报告）
1. **Slide 3**: 右侧文字框(TextBox 29)覆盖了mat和RNN节点 → 把文字框left从7.5改为8.5
2. **Slide 5**: 书的内容V的Rounded Rectangle与TextBox重叠 → 调整位置
3. **Slide 9**: "原句："和"打乱："标签与字节点重叠 → 缩短标签宽度或调整位置
4. **Slide 9**: 表格标签与右侧说明文字重叠 → 调整表格和文字的间距
5. **Slide 15**: 底部感谢语与右侧面板重叠 → 缩短感谢语宽度

### 内容修复（来自读者评审）

**术语解释（每个术语首次出现时必须用括号解释一句）：**
1. **Slide 3**: "梯度消失" → 改为 "梯度消失（即信息在反向传播过程中逐渐衰减，就像传话游戏中传到最后信息面目全非）"
2. **Slide 5**: "权重矩阵" → 加解释 "（就是一组可学习的参数，决定如何从原始词向量中提取不同的信息）"
3. **Slide 5**: "512维" → 加类比 "（可以理解为每个词用512个数字来描述它的各种特征）"
4. **Slide 6**: "Softmax" → 加解释 "Softmax函数的作用是把任意一组数字转换成0到1之间的概率值，且总和等于100%。比如分数[8.5, 1.2, 0.3]变成概率[87%, 12%, 1%]"
5. **Slide 6**: "饱和区" → 加解释 "饱和区就是当分数差异太大时，Softmax会让最高分占据几乎全部注意力（比如99%），其他词被完全忽略。除以√dk就像给分数做标准化，让注意力分布更均匀"
6. **Slide 7**: "线性投影" → 改为 "线性投影（就是把拼接后的8个头的结果混合整理一下）"
7. **Slide 12**: "因果掩码" → 改为 "因果掩码（也叫掩码自注意力，第8页提到过，确保只能看到之前的词）"

**内容加深：**
8. **Slide 5**: 加一句 "为什么需要三个不同的向量？因为Q是主动搜索的一方，K是被搜索的特征，V是被提取的内容——角色不同，所以需要不同的表示"
9. **Slide 6**: 步骤2加具体数字例子 "比如it的Query与cat的Key点积=8.5（高关联），与the的点积=1.2（低关联）"
10. **Slide 9**: RoPE加直觉比喻 "想象把每个词向量当作时钟上的指针，不同位置的词旋转不同角度，距离越远的词旋转角度差异越大，这样注意力计算自然包含了词之间的距离信息"
11. **Slide 14**: "8年演进" → "9年演进"（2017-2026）

**衔接优化：**
12. **Slide 8开头**: 加过渡句 "到目前为止，我们讲的注意力都是在一个序列内部进行的。但翻译需要两个序列之间交流——这就需要交叉注意力"
13. **Slide 9开头**: 加过渡句 "注意力机制讲完了，但它有一个致命缺陷：它不知道词的先后顺序"

**内容增加：**
14. **Slide 15**: 加推荐阅读 "推荐阅读：原文论文《Attention Is All You Need》| 入门教程：Jay Alammar的《The Illustrated Transformer》"

## 技术要求
- 基于v1脚本重写，保留v1中做得好的部分（封面、目录、注意力可视化、训练vs推理对比）
- 幻灯片尺寸: 13.333 x 7.5 英寸
- 所有shape: left+width <= 13.2, top+height <= 7.3
- 字体: 中文微软雅黑，英文Arial
- 颜色方案保持一致
- 生成后用python-pptx自检所有shape边界和重叠
- 注意：Python字符串中只用ASCII引号（""），不要用中文引号（\u201c\u201d）
- Pt()值不要作为Inches参数传入（会导致值变成几万英寸）

## 输出
1. 脚本写入: /home/admin/.openclaw/workspace-weaver/scripts/generate_transformer_ppt_v2.py
2. 执行脚本生成: /home/admin/.openclaw/workspace-weaver/output/Transformer_架构深度解析_v2.pptx
3. 自检报告: 打印所有shape的边界检查结果
