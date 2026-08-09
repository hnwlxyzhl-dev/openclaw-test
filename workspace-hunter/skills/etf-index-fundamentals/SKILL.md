---
name: etf-index-fundamentals
description: Calculate and push fundamentals (PE/PB/PEG/YoY/QoQ) for any A-share ETF or index to WeChat. Activate when user asks to calculate/analyze fundamentals or PE for an ETF (e.g. 卫星ETF 159206) or index (e.g. 沪深300). Fetches latest constituents via Tushare, runs OnDemand_Index_PE_Push.py, and pushes charts + detail tables via WeChat webhook.
---

# ETF/Index Fundamentals Calculator

Calculate aggregated fundamentals (PE, PB, PEG, revenue/profit YoY/QoQ) for any ETF or index by fetching its latest constituents, aggregating their financials, and pushing results to WeChat.

## Data Source: Tushare Pro

All constituent and weight data comes from Tushare Pro API:
- **ETF持仓**: `fund_portfolio` — returns ALL holdings with `stk_mkv_ratio` (占股票市值比), weight sum = 100%
- **指数成分**: `index_weight` — returns all constituents with weight, weight sum = 100%

⚠️ ETF ts_code 后缀规则：`15xxxx`/`16xxxx` → `.SZ`，`51xxxx`/`52xxxx`/`56xxxx`/`58xxxx` → `.SH`

## 模式判断

根据用户消息判断执行模式：

### 模式 A：单只查询（默认）
用户给出具体的 ETF 名称或代码（如"查一下卫星ETF 159206的基本面"、"分析证券ETF"），只查询该 ETF。

### 模式 B：批量查询
用户明确说"批量查询默认ETF"或"批量推送所有ETF基本面"等，依次查询 DEFAULT_ETF_LIST 中的全部 21 只 ETF。

---

## DEFAULT_ETF_LIST（批量模式默认列表）

共 22 只 ETF（宽基已去除，保留策略类 + 行业类）：

| # | 代码 | 名称 | 管理人 | ts_code |
|---|------|------|--------|---------|
| 1 | 512890 | 红利低波ETF | 华泰柏瑞 | 512890.SH |
| 2 | 159992 | 创新药ETF | 银华 | 159992.SZ |
| 3 | 512480 | 半导体ETF | 国联安 | 512480.SH |
| 4 | 512880 | 证券ETF | 国泰 | 512880.SH |
| 5 | 512800 | 银行ETF | 华宝 | 512800.SH |
| 6 | 512170 | 医疗ETF | 华宝 | 512170.SH |
| 7 | 512710 | 军工龙头ETF | 富国 | 512710.SH |
| 8 | 515220 | 煤炭ETF | 国泰 | 515220.SH |
| 9 | 512400 | 有色金属ETF | 南方 | 512400.SH |
| 10 | 515880 | 通信ETF | 国泰 | 515880.SH |
| 11 | 159530 | 机器人ETF | 易方达 | 159530.SZ |
| 12 | 159819 | 人工智能ETF | 易方达 | 159819.SZ |
| 13 | 159869 | 游戏ETF | 华夏 | 159869.SZ |
| 14 | 159611 | 电力ETF | 广发 | 159611.SZ |
| 15 | 513180 | 恒生科技ETF | 华夏 | 513180.SH |
| 16 | 515790 | 光伏ETF | 华泰柏瑞 | 515790.SH |
| 17 | 515030 | 新能源车ETF | 华夏 | 515030.SH |
| 18 | 512200 | 房地产ETF | 南方 | 512200.SH |
| 19 | 515210 | 钢铁ETF | 国泰 | 515210.SH |
| 20 | 159870 | 化工ETF | 鹏华 | 159870.SZ |
| 21 | 159206 | 卫星ETF | 永赢 | 159206.SZ |
| 22 | 159732 | 消费电子ETF | 华夏 | 159732.SZ |

---

## ⚠️ 重要：禁止设置超时

**不要为 exec 命令设置 timeout 参数！** 无论单只还是批量模式，都不要设超时。

原因：`OnDemand_Index_PE_Push.py` 需要拉取大量成分股财务数据并计算，单只可能需要 5-15 分钟，批量模式可能需要数小时。设置超时会导致任务被中途杀死，产出不完整的结果。

- ❌ `exec(timeout=600, ...)` — 禁止
- ❌ `exec(timeout=3600, ...)` — 禁止
- ✅ `exec(background=true)` — 正确做法，后台运行，完成后自动通知

---

## Workflow

### 步骤 1：判断模式

- 用户提到具体 ETF 名称/代码 → **模式 A（单只）**
- 用户说"批量"、"默认ETF"、"所有ETF"等 → **模式 B（批量）**

### 步骤 2：获取成分股

```bash
# ETF — 获取全部持仓及权重
python3.11 skills/etf-index-fundamentals/scripts/fetch_constituents.py \
  --etf 159206 --output /tmp/stocks_159206.json

# 指数 — 获取全部成分股权重
python3.11 skills/etf-index-fundamentals/scripts/fetch_constituents.py \
  --index 000300.SH --output /tmp/stocks_hs300.json
```

### 步骤 3：运行 OnDemand_Index_PE_Push.py

```bash
python3.11 /home/admin/Hualin/OnDemand_Index_PE_Push.py \
  --name "卫星ETF永赢159206" \
  --code "159206.SZ" \
  --stocks /tmp/stocks_159206.json \
  --is-etf
```

每只 ETF 成功后会产生：2 张折线图 + 1 张明细表，自动推送到企业微信。

### 步骤 4（仅批量模式）：依次执行

批量模式下，按 DEFAULT_ETF_LIST 表格顺序依次执行步骤 2→3：

- 每只完成后，等待 5 秒再开始下一只（避免企业微信限流）
- 如果某只失败，记录错误并继续下一只，不要中断
- 全部完成后，汇总报告：✅ 成功 N 只 / ❌ 失败 M 只（列出失败的 ETF 名称和错误原因）
- 预计总耗时 2-5 小时，提前告知用户

## 数据特性

| 数据源 | API | 组件 | 权重合计 | 更新频率 |
|--------|-----|------|---------|---------|
| ETF持仓 | fund_portfolio | 全部持仓股票 | ~100% | 季报（滞后1-3个月） |
| 指数成分 | index_weight | 全部成分股 | ~100% | 月度调整 |

## Key Notes

- **ETF数据来自季报**，有1-3个月滞后（如5月查到的最新数据可能是上一年Q4）
- **新ETF**可能只有少量持仓数据（建仓期），可改用底层指数 `--index` 获取完整成分
- 脚本会自动检测权重合计是否偏低（<80%），并给出警告
- The calculation engine is identical to Index_PE_Push.py
- **批量模式注意事项**：
  - ⚠️ **禁止设置 timeout！** 必须用 `background=true` 后台运行，任务完成后自动通知
  - Tushare `fund_portfolio` 有频率限制，不要并发调用，必须串行
  - 企业微信消息间隔 ≥5 秒，避免触发限流（errcode=0 不代表送达）
  - 单只失败不影响其他，继续执行
