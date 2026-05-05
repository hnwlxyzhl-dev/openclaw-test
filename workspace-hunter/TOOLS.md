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

## 📚 知识库（按需查阅，勿默认加载）

**目录：** `knowledge/`

需要调用API或分析特定市场时，先 `read` 对应文件获取具体接口和参数。

### API 接口文档（根目录）

| 文件 | 内容 | 何时查阅 |
|------|------|---------|
| `akshare_stock_api_summary.md` | AkShare股票接口总览（行情/财务/资金流/龙虎榜/板块/涨停） | 需要查AkShare A股接口函数名时 |
| `tushare_full_api.md` | Tushare Pro完整接口文档（2000+行） | 需要查Tushare接口参数/返回字段/积分要求时 |
| `tushare_api_summary.md` | Tushare接口快速索引 | 快速查找Tushare某个接口名时 |
| `yfinance_api_summary.md` | yfinance完整API（Ticker/download/多市场/期权） | 需要查yfinance用法时 |
| `us_market_apis.md` | 美股数据API（Alpha Vantage/FRED/SEC/财报） | 需要查美股数据源时 |
| `cn_finance_data_sources.md` | 中国金融数据源（交易所/东财/同花顺/Wind/BaoStock等） | 需要查非AkShare的中国数据源时 |
| `global_market_api_summary.md` | 全球市场API（港股/期货/外汇/宏观/加密） | 需要查港股、期货、外汇、宏观经济数据时 |
| `tech_analysis_libs.md` | 技术分析库（TA-Lib/pandas-ta/backtrader/vnpy等） | 需要做技术分析或回测时 |
| `financial_analysis_methods.md` | 财报分析方法（三大报表/杜邦分析/财务造假识别/健康度评分） | 需要分析财报或检查财务健康时 |
| `valuation_models.md` | 估值模型（PE/PB/PS/PEG/DCF/DDM/行业特有估值/综合评分） | 需要做估值分析或判断买卖时区时 |

### 市场知识与交易规则（`knowledge/markets/`）

来源：Sentinel（守望者）学习整理

| 文件 | 内容 | 何时查阅 |
|------|------|---------|
| `01-A股交易规则.md` | 沪深主板/创业板/科创板/北交所交易规则、涨跌停、T+1 | 需要了解A股交易机制时 |
| `02-A股指数体系.md` | 宽基/行业指数编制规则与估值方法 | 需要理解指数构成和计算时 |
| `03-A股财务分析.md` | 三大报表、杜邦分析、估值方法、造假识别 | 需要做深度财务分析时 |
| `04-复权与除权.md` | 复权原理、计算方法、数据源差异、回测注意 | 需要处理历史价格数据时 |
| `05-美股交易规则.md` | T+1结算、盘前盘后、熔断机制、做空规则 | 需要了解美股交易机制时 |
| `06-港股交易规则.md` | 港交所制度、碎股、窝轮牛熊证 | 需要了解港股交易机制时 |
| `07-日本股市规则.md` | JPX/TSE制度、交易单位、卖空限制 | 需要了解日股交易机制时 |
| `08-期货市场.md` | 期货合约、保证金、交割、主力合约 | 需要了解期货基础概念时 |
| `09-黄金市场.md` | 黄金定价、ETF、期货、影响因素 | 需要分析黄金市场时 |
| `10-原油市场.md` | 基准油价体系、供需、地缘影响 | 需要分析原油市场时 |
| `11-汇率市场.md` | 外汇基础、人民币汇率、影响因素 | 需要了解汇率机制时 |
| `12-利率与债券.md` | 利率体系、国债、信用债、收益率曲线 | 需要了解债券市场时 |
| `13-宏观经济指标.md` | GDP/CPI/PPI/PMI/就业/贸易等核心指标 | 需要解读宏观数据时 |

### 数据源接口（`knowledge/data-sources/`）

来源：Forger（锻造者）学习整理

| 文件 | 内容 | 何时查阅 |
|------|------|---------|
| `eastmoney-api.md` | 东方财富数据接口（行情/资金/公告） | 需要调东财接口获取数据时 |
| `cme-ice-futures-api.md` | CME/ICE期货交易所数据接口 | 需要获取海外期货数据时 |
| `cn-futures-exchanges.md` | 国内期货交易所数据接口（上期所/大商所/郑商所/中金所） | 需要获取国内期货数据时 |
| `cninfo-announcement.md` | 巨潮资讯公告接口 | 需要抓取历史公告时 |
| `finnhub-api.md` | Finnhub美股/外汇/加密实时数据 | 需要获取实时全球市场数据时 |
| `hkex-jpx-api.md` | 港交所/日交所数据接口 | 需要获取港股/日股原始数据时 |
| `sina-ths-api.md` | 新浪财经/同花顺数据接口 | 需要获取实时行情或资金流数据时 |
| `tradingview-api.md` | TradingView图表与数据接口 | 需要获取技术图表数据时 |
| `world-bank-imf-api.md` | 世界银行/IMF宏观经济数据 | 需要获取全球宏观数据时 |
| `scraping-anti-bot.md` | 反爬虫绕过策略汇总 | 爬虫被拦截时参考 |
| `playwright-scraping.md` | Playwright动态网页抓取指南 | 需要抓取JS渲染页面时 |

### 编程与工程（`knowledge/coding/`）

来源：Forger（锻造者）学习整理

| 文件 | 内容 | 何时查阅 |
|------|------|---------|
| `01_pandas_performance.md` | Pandas性能优化技巧 | 处理大数据量DataFrame卡顿时 |
| `05_data_cleaning_timeseries.md` | 时间序列数据清洗方法 | 处理金融时序数据缺失/异常时 |
| `06_backtesting_framework.md` | 回测框架对比与选型 | 需要搭建或选择回测系统时 |
| `07_financial_visualization.md` | 金融数据可视化最佳实践 | 需要制作专业图表时 |
| `10_financial_data_patterns.md` | 金融数据处理常用模式 | 编写金融数据管道时参考 |

**使用方式：** `read knowledge/markets/03-A股财务分析.md` → 按需搜索关键字段

**知识库维护：** 编译脚本 `scripts/compile_knowledge.py`，可批量生成/更新知识文件

---

## ⚙️ 运维规范

- **备份命名**：`openclaw.json.bak.YYYYMMDD_HHMMSS`，禁止不带日期的通用备份名
- **问题排查顺序**：认证状态 → 权限/配额 → 网络连接 → 服务端问题。表面错误信息不一定反映根本原因
