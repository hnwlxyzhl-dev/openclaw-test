# TOOLS.md - 工具操作手册

_详细的使用方法、参数、代码示例。行为规则见 SOUL.md。知识库见 MEMORY.md 索引。_

---

## 📚 知识库索引（按需加载，不预加载）

遇到相关任务时，先用 `read` 读取对应文件，再执行任务。

### 代码测试知识 (`knowledge/testing/`)

| 文件 | 内容 | 何时读取 |
|------|------|---------|
| `01-软件测试基础.md` | 测试分类、用例设计方法、测试流程 | 任何测试任务开始前 |
| `02-金融系统测试专项.md` | 精度测试、并发测试、合规性测试、容灾测试 | 测试金融相关程序时 |
| `03-数据质量测试.md` | 数据完整性/一致性/准确性/时效性验证 | 验证数据接口或爬虫输出时 |
| `04-API测试方法.md` | RESTful API测试、参数边界、异常输入、性能 | 测试 API 接口时 |
| `05-自动化测试框架.md` | pytest/unittest、Mock/Stub、覆盖率、CI/CD | 编写自动化测试脚本时 |
| `06-回测系统测试.md` | 时间序列、复权、滑点、涨跌停、收益率验证 | 测试量化回测系统时 |
| `07-性能与压力测试.md` | 负载/压力测试、locust、内存泄漏检测 | 进行性能测试时 |
| `08-测试报告编写.md` | 报告结构、缺陷分类、度量指标、Allure | 输出测试报告时 |

### 金融知识 (`knowledge/finance/`)

| 文件 | 内容 | 何时读取 |
|------|------|---------|
| `01-A股交易规则.md` | T+1、涨跌停、集合竞价、融资融券、退市、费用 | 验证A股交易相关逻辑时 |
| `02-A股指数体系.md` | 上证/深证/沪深300/中证500等编制规则与估值 | 验证指数数据或计算时 |
| `03-A股财务分析.md` | 三大报表、杜邦分析、估值方法、造假识别 | 验证财务数据或分析结果时 |
| `04-复权与除权.md` | 前复权/后复权计算、除权除息、各数据源差异 | **任何涉及价格数据时必读** |
| `05-美股交易规则.md` | T+0/PDT、熔断、ADR、期权、NYSE vs NASDAQ | 验证美股相关逻辑时 |
| `06-港股交易规则.md` | T+0/T+2、碎股、暗盘、港股通、窝轮牛熊证 | 验证港股相关逻辑时 |
| `07-日本股市规则.md` | TSE分层、日经225编制、外国投资者规则 | 验证日股相关逻辑时 |
| `08-期货市场.md` | 合约要素、商品/金融期货、基差、套期保值 | 验证期货数据或策略时 |
| `09-黄金市场.md` | 定价机制、黄金ETF/期货对比、与美元关系 | 验证黄金相关数据时 |
| `10-原油市场.md` | WTI/布伦特、OPEC+、炼油利润 | 验证原油相关数据时 |
| `11-汇率市场.md` | 即期/远期/掉期、人民币在岸离岸、利差交易 | 验证汇率数据时 |
| `12-利率与债券.md` | 收益率曲线、久期/凸性、国债/企业债/可转债 | 验证利率或债券数据时 |
| `13-宏观经济指标.md` | GDP/CPI/PMI/非农/M2等指标解读 | 验证宏观数据或分析时 |

### 数据源接口 (`knowledge/data-sources/`) — 来源：Forger

| 文件 | 内容 | 何时读取 |
|------|------|---------|
| `akshare-api.md` | AkShare 接口详解（行情/财务/资金流） | 验证 AkShare 数据源调用时 |
| `tushare-api.md` | Tushare Pro 接口详解（参数/字段/积分） | 验证 Tushare 数据源调用时 |
| `yahoo-finance-api.md` | yfinance 接口详解（Ticker/download/期权） | 验证 yfinance 数据源调用时 |
| `alpha-vantage-api.md` | Alpha Vantage 接口（美股/外汇/技术指标） | 验证 Alpha Vantage 调用时 |
| `fred-macro-api.md` | FRED 宏观经济数据接口 | 验证美国宏观数据源时 |
| `sec-edgar-api.md` | SEC EDGAR 财报/公告接口 | 验证美股财报数据源时 |
| `cn-macro-data.md` | 中国宏观经济数据接口（统计局/央行） | 验证中国宏观数据源时 |
| `scrapy-framework.md` | Scrapy 爬虫框架使用指南 | 测试爬虫程序时 |

### API 快速参考 (`knowledge/api-references/`) — 来源：Hunter

| 文件 | 内容 | 何时读取 |
|------|------|---------|
| `tushare_full_api.md` | Tushare Pro 完整接口文档（2000+行） | 深度验证 Tushare 接口参数/返回值时 |
| `tushare_api_summary.md` | Tushare 接口快速索引 | 快速查找 Tushare 接口名时 |
| `yfinance_api_summary.md` | yfinance API 总览 | 快速查找 yfinance 用法时 |
| `akshare_stock_api_summary.md` | AkShare 股票接口总览 | 快速查找 AkShare 接口函数名时 |
| `us_market_apis.md` | 美股数据 API（Alpha Vantage/FRED/SEC） | 验证美股多数据源时 |
| `global_market_api_summary.md` | 全球市场 API（港股/期货/外汇/宏观） | 验证跨市场数据源时 |

### 编程与工程 (`knowledge/coding/`) — 来源：Forger

| 文件 | 内容 | 何时读取 |
|------|------|---------|
| `02_async_concurrent_scraping.md` | 异步并发爬虫技术 | 测试爬虫性能/并发逻辑时 |
| `03_database_financial_data.md` | 金融数据库设计与操作 | 测试数据库相关金融程序时 |
| `04_api_design_patterns.md` | API 设计模式（RESTful/限流/缓存） | 测试 API 接口设计合理性时 |
| `09_numpy_advanced.md` | NumPy 高级用法（广播/向量化） | 验证数值计算性能/精度时 |
| `11_tech_analysis_libs.md` | 技术分析库（TA-Lib/pandas-ta/Backtrader/VeighNa） | 测试量化/技术分析程序时 |

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

**用途：** 高性能网页抓取，可绕过 Cloudflare 等反爬机制

```bash
python3.11 scripts/scrapling_demo.py https://example.com
```

**注意：** 方法名是 `fetch()` 不是 `get()`；`page.css("selector")` 返回列表

---

## 🕷️ 通用网页爬虫

**脚本：** `scripts/web_crawler.py`

**用途：** 通用网页爬取（requests + BeautifulSoup）、财经数据（tushare）、JSON API 获取

---

## 📈 涨跌幅趋势分析

**脚本：** `scripts/analyze_trend.py`

**用途：** 分析股票近期涨跌幅（基于 Tushare，需设置 `TUSHARE_TOKEN`）

```bash
python3.11 scripts/analyze_trend.py 002637
python3.11 scripts/analyze_trend.py 002637,600519,000001
```

---

## 📊 财报监控

**脚本：** `scripts/earnings_monitor.py`（完整版）/ `scripts/simple_earnings_monitor.py`（简化版）

**用途：** 检索当天发布的 A股/港股财报/预告/快报，自动分类：
- 第一类：营收或净利润同比下降
- 第二类：营收和净利润同比都增长（输出重点）

```bash
python3.11 scripts/earnings_monitor.py
python3.11 scripts/earnings_monitor.py --json
```

---

## 🌍 全球资产分析

**脚本：** `scripts/global_asset_analysis.py`

**用途：** 全球大类资产分位分析（期货、股市、黄金、原油），判断当前处于历史高位/低位/中位

**覆盖品种：** 沪金、沪铜、铁矿石、原油、螺纹钢、沪铝、沪锌、沪镍、白银、A股指数、美股指数、黄金、原油

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

## 🧪 测试验证工具箱（Sentinel 专属）

**核心能力：** 用以上金融数据工具作为基准数据源，对被测程序进行交叉验证。

### 测试流程

1. **获取基准数据** — 用 `finance_data.py` 或 `finance_analysis.py` 获取已知正确的结果
2. **运行被测程序** — 获取被测程序的输出
3. **交叉比对** — 逐字段比对，记录差异
4. **金融常识校验** — 检查结果是否符合金融逻辑（复权、T+1、涨跌停、交易成本等）
5. **输出测试报告** — 明确通过/失败/待确认

### 常见验证场景

| 场景 | 基准工具 | 验证要点 |
|------|---------|---------|
| A股行情接口 | finance_data.py quote | 价格、涨跌幅、成交量、复权价格 |
| 美股行情接口 | finance_data.py quote --us | 美元价格、汇率换算 |
| 指数数据 | finance_data.py index | 点位、涨跌幅 |
| 分析计算结果 | finance_analysis.py stock | 估值指标、财务比率的准确性 |
| 数据爬虫 | scrapling_demo.py + finance_data.py | 完整性、准确性、时效性 |
| 回测策略 | 多工具交叉验证 | 收益率、最大回撤、夏普比率的合理性 |

---

## ⚙️ 运维规范

- **备份命名**：`openclaw.json.bak.YYYYMMDD_HHMMSS`，禁止不带日期的通用备份名
- **问题排查顺序**：认证状态 → 权限/配额 → 网络连接 → 服务端问题。表面错误信息不一定反映根本原因
