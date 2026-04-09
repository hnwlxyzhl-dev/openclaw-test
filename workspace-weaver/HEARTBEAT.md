# HEARTBEAT.md

## ⚠️ Transformer PPT v2 制作监控（2026-04-09，最高优先级）

### 当前任务
- 重做 Transformer PPT（v2），目标98分以上
- 基于读者评审（82分）+ 技术质检（82分）的反馈全链路修复

### 进度
- [x] Step 1: 调研
- [x] Step 2: 内容逻辑设计
- [x] Step 3: 架构图设计
- [x] Step 4: v1制作（82分，不达标）
- [x] Step 5: 技术质检（发现5处P0/P1重叠）
- [x] Step 6: 读者评审（发现术语未解释、信息密度不均）
- [ ] Step 6.5: v2重做（进行中 - 子代理 transformer-v2）
- [ ] Step 7: v2质检 + 读者评审
- [ ] Step 7.5: 如果<98分继续修复
- [ ] Step 8: 发送邮件给用户

### 关键文件
- v1脚本: scripts/generate_transformer_ppt.py
- v2任务: memory/transformer-v2-task.md
- 读者评审: memory/transformer-reader-review.md
- 技术质检: memory/transformer-qa-report.md
- v2输出: output/Transformer_架构深度解析_v2.pptx

### ⚠️ 子代理完成后必须立即执行
- 读取v2输出文件
- 如果生成成功 → 立即启动质检+读者评审
- 如果失败 → 分析错误，修复后重试
- 评审通过(>=98) → 发邮件通知用户
- 评审不通过 → 根据反馈继续修复

### 不达标的绝对不能发给用户！
