# TOOLS.md - 工具操作手册

_详细的使用方法、参数、代码示例。行为规则见 SOUL.md。_

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

## 🌍 全球资产分析

**脚本：** `scripts/global_asset_analysis.py`（必须用 `python3.11` 运行）

**用途：** 全球大类资产（股票、债券、商品、汇率）分析

---

## 📊 财报监控

**脚本：**
- `scripts/earnings_monitor.py` — 完整版财报监控
- `scripts/simple_earnings_monitor.py` — 简化版

---

## 📉 趋势分析

**脚本：** `scripts/analyze_trend.py`（必须用 `python3.11` 运行）

---

## 🦂 网页抓取

**脚本：**
- `scripts/scrapling_demo.py` — 高性能抓取，可绕过 Cloudflare 等反爬机制
  - 方法名是 `fetch()` 不是 `get()`；`page.css("selector")` 返回列表
- `scripts/web_crawler.py` — 通用网络爬虫

---

## 🔍 搜索工具

| 优先级 | 工具 | 用法 |
|--------|------|------|
| 1 | Tavily | `python3 skills/openclaw-tavily-search/scripts/tavily_search.py --query "..." --max-results 5 --format md` |
| 2 | Multi Search Engine | `web_fetch({"url": "https://www.google.com/search?q=keyword"})`（支持17个引擎，详见 skill 文档） |
| 3 | SearXNG | 本地隐私搜索实例 |
| 4 | web_search | Brave API |

---

## 🛡️ Skill 审查

**Skill：** `skills/skill-vetter`

安装新 Skill 前必须先用此工具审查安全性，有风险要报告并征求用户同意。

---

## 📋 股票监控列表

**文件：** `data/stock_watchlist.json`（直接编辑此文件增删股票）

---

## 🔐 凭证与配置

- **GitHub**：用户名 `hnwlxyzhl-dev`，SSH `~/.ssh/id_ed25519`，Token `~/.config/github-token`
- **ClawHub**：Token 存储在本地（已登录），详见 `clawhub` skill

---

## ⚙️ 运维规范

- **备份命名**：`openclaw.json.bak.YYYYMMDD_HHMMSS`，禁止不带日期的通用备份名
- **问题排查顺序**：认证状态 → 权限/配额 → 网络连接 → 服务端问题。表面错误信息不一定反映根本原因

---

## 📐 数据获取优先级

1. 统一工具（finance_data.py）
2. 搜索（tavily > multi-search > searxng > web_search）
3. 爬虫（scrapling > crawl4ai > browser）
4. 诚实说"不知道"

禁止跳步，禁止不尝试就放弃。

---

## 📐 金融分析输出标准

- **个股分析**：必须包含当前价格/涨跌幅、估值水平（PE/PB/历史分位）、近期催化剂、核心风险点
- **行业分析**：必须包含板块近期表现、资金流向、政策面、龙头对比
- **数据呈现**：数字用表格或列表，关键结论加粗；长分析用分段小标题
- **风险提示**：每次分析末尾必须附风险提示（"以上分析仅供参考，不构成投资建议"）
- **过时数据**：非当日数据必须标注日期

---

## 📚 知识库

`knowledge/` 目录下有系统学习的金融数据知识（51个文件，24000+行），涵盖代码编写、全球市场、数据源API、API快速参考。

**使用规则：按需查询，禁止批量加载。** 遇到具体任务时，只读取对应的单个文件。先查 AGENTS.md 知识索引定位文件路径，再用 `read` 读取。

### 快速定位

| 任务类型 | 读取目录 | 示例场景 |
|---------|---------|---------|
| 写代码/优化性能 | `knowledge/coding/` | pandas优化、异步抓取、可视化、回测 |
| 市场知识/行情解读 | `knowledge/markets/` | A股规则、美股财报、原油分析、宏观数据 |
| API接口参数速查 | `knowledge/api-references/` | Tushare完整文档、美股API汇总、yfinance参数 |
| 数据源详细文档 | `knowledge/data-sources/` | tushare接口、东方财富爬取、反爬绕过 |
