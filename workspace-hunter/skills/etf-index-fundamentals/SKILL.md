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

## Workflow

### 1. Identify target

Parse user message to extract:
- **ETF**: numeric code like `159206`, `563530`, `515880`
- **Index**: code like `000300.SH`, `931594.CSI`
- **Display name**: e.g. "卫星ETF永赢159206" or "沪深300"

### 2. Fetch latest constituents

```bash
# ETF — gets ALL holdings with real weights (not just top 10)
python3.11 skills/etf-index-fundamentals/scripts/fetch_constituents.py \
  --etf 159206 --output /tmp/stocks_159206.json

python3.11 skills/etf-index-fundamentals/scripts/fetch_constituents.py \
  --etf 515880 --output /tmp/stocks_515880.json

# Index — gets all constituents with weights
python3.11 skills/etf-index-fundamentals/scripts/fetch_constituents.py \
  --index 000300.SH --output /tmp/stocks_hs300.json

python3.11 skills/etf-index-fundamentals/scripts/fetch_constituents.py \
  --index 931594.CSI --output /tmp/stocks_931594.json
```

### 3. Run OnDemand_Index_PE_Push.py

```bash
python3.11 /home/admin/Hualin/OnDemand_Index_PE_Push.py \
  --name "卫星ETF永赢159206" \
  --code "159206.SZ" \
  --stocks /tmp/stocks_159206.json \
  --is-etf
```

### 4. Monitor and report

Takes 5-15 minutes. Success = 2 charts + 1 detail table pushed to WeChat.

## Data Characteristics

| Source | API | Components | Weight Sum | Update Frequency |
|--------|-----|-----------|-----------|-----------------|
| ETF持仓 | fund_portfolio | 全部持仓股票 | ~100% | 季报（滞后1-3个月） |
| 指数成分 | index_weight | 全部成分股 | ~100% | 月度调整 |

## Known ETF Reference

| ETF Code | ETF Name | Holdings | Report Period |
|----------|----------|----------|--------------|
| 159206 | 卫星ETF永赢 | 70只 | 2025Q4 |
| 515880 | 通信ETF国泰 | 91只 | 2025Q4 |
| 563530 | 卫星ETF易方达 | 10只⚠️ | 2025Q4（新基金，数据不完整） |

## Key Notes

- **ETF数据来自季报**，有1-3个月滞后（如5月查到的最新数据可能是上一年Q4）
- **563530等新ETF**可能只有少量持仓数据（建仓期），可改用底层指数 `--index 931594.CSI` 获取完整成分
- 脚本会自动检测权重合计是否偏低（<80%），并给出警告
- The calculation engine is identical to Index_PE_Push.py
