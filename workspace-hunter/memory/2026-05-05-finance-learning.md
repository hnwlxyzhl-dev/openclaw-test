# 2026-05-05 金融知识大规模学习

## 背景
老板要求大规模学习金融知识，至少1000篇文档，固化为知识文件。

## 第一轮子代理研究（已完成）
启动了5个并行子代理研究金融API：
1. **tushare-research** — 完成（但输出可能不完整，仅35s运行）
2. **akshare-research** — 完成（使用tavily搜索）
3. **yfinance-research** — 完成（25s，输出3.8k tokens，偏短）
4. **us-api-research** — 完成
5. **cn-finance-research** — 完成（32s，42.5k tokens，但实际输出422）

## 知识文件产出
- `knowledge/us_market_apis.md` — 1261行，39KB（us-api-research 产出）
- 其余知识文件尚未生成（子代理输出质量不足，需要补做）

## 问题与教训
- **子代理输出质量参差不齐**：多数子代理运行时间短（25-35s），token输出少，知识文件未成功生成
- **context window exceeded**：GLM-5-turbo 配置 contextWindow=1,048,576（1M tokens），实际使用中因子代理返回大量工具结果导致溢出
- **compaction配置**：mode=rolling，无 reserveTokensFloor 设置
- **用户指示**：如果tavily受限，用其他搜索方法（multi-search-engine、searxng等）

## 待办
- [ ] 重新评估第一轮产出，补做质量不足的知识文件
- [ ] 启动第二轮：港股/日股API、期货/大宗商品/贵金属API、汇率/利率/宏观经济API
- [ ] 每个子代理需要更具体的指令和更长的运行时间
- [ ] 总目标1000篇文档，目前仅完成约1篇高质量文件
