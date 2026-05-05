# TOOLS.md - 工具操作手册

_详细的使用方法、参数、代码示例。行为规则见 MEMORY.md。_

---

## 📊 金融数据统一工具

**脚本：** `scripts/finance_data.py`（必须用 `python3.11` 运行）

**用途：** A股/美股行情、指数、公告、新闻、跌停股

**命令行：**
```bash
# A股行情
python3.11 scripts/finance_data.py quote 002637

# 美股行情
python3.11 scripts/finance_data.py quote AAPL --us

# 指数行情（所有）
python3.11 scripts/finance_data.py index

# 指数行情（单个）
python3.11 scripts/finance_data.py index nasdaq
python3.11 scripts/finance_data.py index sh

# 公司公告
python3.11 scripts/finance_data.py announcement 002637

# 今日跌停股
python3.11 scripts/finance_data.py limit-down

# 搜索新闻
python3.11 scripts/finance_data.py news 赞宇科技
```

**Python 调用：**
```python
import sys
sys.path.insert(0, 'scripts')
from finance_data import get_quote, get_limit_down, search_news, get_index, get_announcement

quote = get_quote("002637")        # A股
quote = get_quote("AAPL", is_us=True)  # 美股
indexes = get_index()               # 所有指数
nasdaq = get_index("nasdaq")        # 单个指数
announcements = get_announcement("002637")
limit_down = get_limit_down()
news = search_news("赞宇科技")
```

**支持指数：**
- A股：sh, sz, cyb, hs300, sz50, kc50, zz500
- 美股：sp500, nasdaq
- 港股：hsi

**数据源优先级（工具内部自动处理）：**
- A股行情：akshare > tushare > eastmoney_api
- 美股行情：yahoo_finance > eastmoney_api
- 跌停股：akshare > tushare
- 指数：tushare > akshare > eastmoney_api
- 公告：东方财富（7天内） > 巨潮资讯网（历史）
- 新闻：tavily-search > multi-search-engine > searxng > eastmoney_api

---

## 📈 金融分析统一工具

**脚本：** `scripts/finance_analysis.py`（必须用 `python3.11` 运行）

**用途：** A股/美股分析、筛选、行业分析、组合管理、加密货币

**命令行：**
```bash
# A股个股分析
python3.11 scripts/finance_analysis.py stock 002637
python3.11 scripts/finance_analysis.py stock 002637 --level deep

# 美股分析
python3.11 scripts/finance_analysis.py stock AAPL --us

# 股票筛选
python3.11 scripts/finance_analysis.py screen --pe-max 15 --roe-min 15
python3.11 scripts/finance_analysis.py screen --scope hs300 --dividend-min 3

# 行业分析 / 股票对比 / 组合 / 加密货币 / 智能分析
python3.11 scripts/finance_analysis.py sector "白酒"
python3.11 scripts/finance_analysis.py compare 002637,600519
python3.11 scripts/finance_analysis.py portfolio
python3.11 scripts/finance_analysis.py crypto BTC-USD
python3.11 scripts/finance_analysis.py smart "分析贵州茅台"
```

**Python 调用：**
```python
import sys
sys.path.insert(0, 'scripts')
from finance_analysis import (
    analyze_a_stock, analyze_us_stock, screen_a_stocks,
    analyze_sector, compare_stocks, analyze_portfolio, analyze_crypto, smart_analyze
)
```

**分析能力：**
| 需求 | 底层工具 | 功能 |
|------|---------|------|
| A股价值分析/筛选 | china-stock-analysis | 杜邦分析、估值、风险检测 |
| A股技术面/板块 | akshare-stock | K线、资金流、板块轮动 |
| 美股/组合/加密 | stock-analysis | 8维度、情绪、时机 |

---

## 📈 A股实时行情

**脚本：** `scripts/realtime_quote.py`（必须用 `python3.11` 运行）

**用途：** A股盘中实时行情（非盘后数据）

```bash
python3.11 scripts/realtime_quote.py 002637
python3.11 scripts/realtime_quote.py 002637,600519,000001
python3.11 scripts/realtime_quote.py 002637 --json
```

**Python：**
```python
import sys
sys.path.insert(0, 'scripts')
from realtime_quote import get_realtime_quote
quotes = get_realtime_quote("002637")
```

**输出：** price, pct_chg, is_limit_up/down, open/high/low/pre_close, volume/amount

---

## 🦂 Scrapling 网页抓取

**脚本：** `scripts/scrapling_demo.py`（必须用 `python3.11` 运行）

**用途：** 高性能网页抓取，可绑过 Cloudflare 等反爬机制

```bash
python3.11 scripts/scrapling_demo.py https://example.com
```

**注意：** 方法名是 `fetch()` 不是 `get()`；`page.css("selector")` 返回列表

---

## 🔍 搜索工具

| 优先级 | 工具 | 用法 |
|--------|------|------|
| 1 | Tavily | `python3 skills/openclaw-tavily-search/scripts/tavily_search.py --query "..." --max-results 5 --format md` |
| 2 | Multi Search Engine | `web_fetch({"url": "https://www.google.com/search?q=keyword"})`（支持17个引擎，详见 skill 文档） |
| 3 | SearXNG | 本地隐私搜索实例 |
| 4 | web_search | Brave API |

---

## 📋 股票监控列表

**文件：** `data/stock_watchlist.json`（直接编辑此文件增删股票）

每个交易日 21:00 自动检索新闻和公告。

---

## 🔐 凭证与配置

- **GitHub**：用户名 `hnwlxyzhl-dev`，SSH `~/.ssh/id_ed25519`，Token `~/.config/github-token`
- **ClawHub**：Token 存储在本地（已登录），详见 `clawhub` skill

---

## 📋 Cron 任务

查看当前任务：`cat ~/.openclaw/cron/jobs.json | jq '.jobs[] | {name, schedule}'`

任务列表是动态的，实时查询 jobs.json 才是最新状态，不要写死。

---

## ⚙️ 运维规范

- **备份命名**：`openclaw.json.bak.YYYYMMDD_HHMMSS`，禁止不带日期的通用备份名
- **问题排查顺序**：认证状态 → 权限/配额 → 网络连接 → 服务端问题。表面错误信息不一定反映根本原因
