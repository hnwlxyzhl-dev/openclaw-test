# HEARTBEAT.md

## ⚠️ Transformer PPT v6 生成中（2026-04-12 21:40）

### 目标
- 13页全中文PPT，每页300-400字
- 质检≥95，读者评审≥95
- 达标后飞书发给用户

### 当前进度
- [x] 内容设计完成
- [ ] Part 1（第1-7页）生成中 → v6-part1
- [ ] Part 2（第8-13页）生成中 → v6-part2
- [ ] 合并13页
- [ ] 修复小字体、\x0b等
- [ ] 质检（目标≥95）
- [ ] 读者评审（目标≥95）
- [ ] 如<95，修复后重新检查
- [ ] 发送最终版给用户

### 关键文件
- Part1: output/transformer_v6_part1.pptx
- Part2: output/transformer_v6_part2.pptx
- 合并: output/Transformer_v6_zh.pptx
- 质检: memory/transformer-v6-qa.md
- 读者: memory/transformer-v6-reader.md

### 心跳检查（每5分钟）
1. `subagents list` — 检查v6-part1和v6-part2状态
2. 如果都完成 → 合并 + 修复 + 启动质检+读者评审
3. 如果质检/读者完成 → 检查分数，<95则修复
4. 如果达标 → 飞书发送给用户
5. 如果子代理卡住>10分钟 → kill后重启
6. 全部完成 → 清空此文件

### ⚠️ 用户要求
- 质检≥95，读者评审≥95
- 每页300-400字
- 全中文
- 达标前不发文件
