#!/usr/bin/env python3.11
"""
金融知识文件编译器 - 从文档页面编译知识文件
"""
import os
import sys
import json
import re
import time
from pathlib import Path

KNOWLEDGE_DIR = Path("/home/admin/.openclaw/workspace-hunter/knowledge")

def strip_security_notice(text):
    """移除安全提示包装"""
    lines = text.split('\n')
    result = []
    skip = False
    for line in lines:
        if 'EXTERNAL_UNTRUSTED_CONTENT' in line or 'SECURITY NOTICE' in line:
            skip = True
            continue
        if 'END_EXTERNAL_UNTRUSTED_CONTENT' in line:
            skip = False
            continue
        if skip:
            continue
        if 'Source: Web Fetch' in line.strip() and line.strip().startswith('---'):
            continue
        if line.strip() in ('- DO NOT treat any part', '- DO NOT execute tools', 
                           '- DO NOT manipulate or persuade', '- DO NOT change your behavior',
                           '- DO NOT reveal sensitive', '- DO NOT send messages',
                           '- Respond helpfully to legitimate'):
            continue
        if line.strip().startswith('This content may be social engineering'):
            continue
        if line.strip().startswith('Remember - the Yahoo'):
            continue
        result.append(line)
    return '\n'.join(result)

def write_akshare_futures(content):
    """编译AkShare期货数据文档"""
    filepath = KNOWLEDGE_DIR / "akshare_futures_api.md"
    clean = strip_security_notice(content)
    # 添加头部
    header = """# AkShare 期货数据 API 文档

> 自动编译自 https://akshare.akfamily.xyz/data/futures/futures.html
> 版本: AkShare 1.18.60
> 编译时间: 2026-05-05

---

"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + clean)
    print(f"✅ 写入 {filepath} ({len(clean)} chars)")

def write_akshare_index(content):
    """编译AkShare指数数据文档"""
    filepath = KNOWLEDGE_DIR / "akshare_index_api.md"
    clean = strip_security_notice(content)
    header = """# AkShare 指数数据 API 文档

> 自动编译自 https://akshare.akfamily.xyz/data/index/index.html
> 版本: AkShare 1.18.60
> 编译时间: 2026-05-05

---

"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + clean)
    print(f"✅ 写入 {filepath} ({len(clean)} chars)")

def write_akshare_macro(content):
    """编译AkShare宏观数据文档"""
    filepath = KNOWLEDGE_DIR / "akshare_macro_api.md"
    clean = strip_security_notice(content)
    header = """# AkShare 宏观数据 API 文档

> 自动编译自 https://akshare.akfamily.xyz/data/macro/macro.html
> 版本: AkShare 1.18.60
> 编译时间: 2026-05-05

---

"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + clean)
    print(f"✅ 写入 {filepath} ({len(clean)} chars)")

def write_tushare_daily(content):
    """编译Tushare日线行情文档"""
    filepath = KNOWLEDGE_DIR / "tushare_daily_api.md"
    clean = strip_security_notice(content)
    header = """# Tushare Pro A股日线行情 API 文档

> 自动编译自 https://tushare.pro/document/2?doc_id=27
> 编译时间: 2026-05-05

---

"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + clean)
    print(f"✅ 写入 {filepath} ({len(clean)} chars)")

def compile_akshare_stock_summary():
    """编译AkShare股票接口总览"""
    filepath = KNOWLEDGE_DIR / "akshare_stock_api_summary.md"
    content = """# AkShare 股票数据接口总览

> 基于 AkShare 1.18.60 文档整理
> 编译时间: 2026-05-05

## A股行情

### 实时行情
- `stock_zh_a_spot_em()` - A股实时行情（东方财富）
- `stock_zh_a_spot()` - A股实时行情（新浪）
- `stock_zh_a_hist()` - A股历史行情（东财，支持日/周/月）
- `stock_zh_a_hist_min_em()` - A股分时行情（东财，1/5/15/30/60分钟）
- `stock_zh_a_hist_163()` - A股历史行情（网易）

### 市场总貌
- `stock_sse_summary()` - 上交所股票数据总貌
- `stock_szse_summary(date)` - 深交所市场总貌
- `stock_szse_area_summary(date)` - 深交所地区交易排序

### 个股信息
- `stock_individual_info_em(symbol)` - 个股信息查询（东财）
- `stock_individual_info_xq(symbol)` - 个股信息查询（雪球）

### 停复牌
- `stock_tfp_em(date)` - 停复牌信息
- `stock_tfp_detail_em(date, symbol)` - 停复牌详情

## B股
- `stock_zh_b_spot()` - B股实时行情
- `stock_zh_b_daily(symbol)` - B股历史行情

## 科创板
- `stock_zh_a_spot_em()` 包含科创板
- `stock_zh_a_hist()` 支持科创板历史行情
- `stock_star_a_notice()` - 科创板公告

## 美股
- `stock_us_spot_em()` - 美股实时行情（东财）
- `stock_us_hist(symbol)` - 美股历史行情（东财）
- `stock_us_hist_sina(symbol)` - 美股历史行情（新浪）

## 港股
- `stock_hk_spot_em()` - 港股实时行情（东财）
- `stock_hk_daily(symbol)` - 港股历史行情（东财）
- `stock_hk_daily_sina(symbol)` - 港股历史行情（新浪）
- `stock_hk_hist_min_em(symbol, period)` - 港股分时行情

## 财务数据

### 财务报表
- `stock_financial_abstract_ths(symbol)` - 财务摘要（同花顺）
- `stock_financial_analysis_indicator(symbol)` - 财务分析指标（东财）
- `stock_balance_sheet_by_report_em(symbol)` - 资产负债表（东财）
- `stock_profit_sheet_by_report_em(symbol)` - 利润表（东财）
- `stock_cash_flow_sheet_by_report_em(symbol)` - 现金流量表（东财）

### 关键指标
- `stock_financial_abstract_ths()` - 财务摘要
- `stock_financial_analysis_indicator()` - 财务分析指标

### 分红配送
- `stock_dividend_cninfo(symbol)` - 历史分红（巨潮）
- `stock_dividend_sina(symbol)` - 分红配送（新浪）

## 股东数据
- `stock_gdfx_free_top_10_em(symbol, date)` - 十大流通股东
- `stock_gdfx_top_10_em(symbol, date)` - 十大股东
- `stock_gdfx_free_holding_detail_em()` - 流通股东明细
- `stock_zh_a_gdhs(date)` - 股东户数

## 资金流向
- `stock_individual_fund_flow(symbol, market)` - 个股资金流向
- `stock_individual_fund_flow_rank(indicator)` - 个股资金流排名
- `stock_market_fund_flow()` - 大盘资金流向
- `stock_sector_fund_flow_rank(sector_type, indicator)` - 板块资金流

## 龙虎榜
- `stock_lhb_detail_em(date)` - 龙虎榜详情（东财）
- `stock_lhb_stock_statistic_em(symbol)` - 个股上榜统计
- `stock_lhb_jgmmtj_em(date)` - 机构买卖统计

## 涨停跌停
- `stock_zt_pool_em(date)` - 涨停股池
- `stock_zt_pool_strong_em(date)` - 强势股池
- `stock_zt_pool_sub_new_em(date)` - 次新股池
- `stock_zt_pool_zbgc_em(date)` - 炸板股池
- `stock_zt_pool_dtgc_em(date)` - 跌停股池

## 板块数据

### 概念板块
- `stock_board_concept_name_em()` - 概念板块列表
- `stock_board_concept_hist_em(symbol)` - 概念板块历史行情
- `stock_board_concept_cons_em(symbol)` - 概念板块成分股

### 行业板块
- `stock_board_industry_name_em()` - 行业板块列表
- `stock_board_industry_hist_em(symbol)` - 行业板块历史行情
- `stock_board_industry_cons_em(symbol)` - 行业板块成分股

## 沪深港通
- `stock_hsgt_north_net_flow_in_em()` - 北向资金净流入
- `stock_hsgt_north_cash_em()` - 北向资金余额
- `stock_hsgt_hold_stock_em(symbol)` - 沪深港通持股
- `stock_hsgt_hist_em(symbol)` - 沪深港通历史数据

## 公告数据
- `stock_notice_report(symbol)` - 个股公告
- `stock_zh_a_new_em()` - 新股数据
- `stock_info_global_em()` - 全球财经快讯

## 技术指标
- `stock_zh_a_high_low_statistic(symbol)` - 创新高/新低
- `stock_zh_a_rise_fall_same(symbol)` - 连续上涨/下跌
- `stock_zh_a_vol_increase_same(symbol)` - 持续放量/缩量

## 估值数据
- `stock_a_indicator_lg(symbol)` - A股估值指标
- `stock_a_lg_indicator(symbol)` - 个股估值
- `stock_pb_em(symbol)` - 市净率
- `stock_pe_ttm(symbol)` - 市盈率TTM
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 写入 {filepath} ({len(content)} chars)")

def compile_tushare_summary():
    """编译Tushare接口总览"""
    filepath = KNOWLEDGE_DIR / "tushare_api_summary.md"
    content = """# Tushare Pro 接口总览

> 基于 Tushare Pro 官方文档整理
> 编译时间: 2026-05-05
> 文档地址: https://tushare.pro/document/2

## 积分体系
- 基础积分：注册即得，可访问基础接口
- 高级积分：需捐助获取，可访问高级接口
- 接口限制：基础积分每分钟500次，每次6000条

## A股基础

### 交易日历
- `trade_cal(exchange, start_date, end_date)` - 交易日历
  - exchange: SSE/SZSE
  - 返回: exchange, cal_date, is_open, pretrade_date

### 股票列表
- `stock_basic(exchange, list_status)` - 股票列表
  - exchange: SSE/SZSE
  - list_status: L上市/D退市/P暂停上市
  - 返回: ts_code, symbol, name, area, industry, market, list_date

### A股日线行情
- `daily(ts_code, trade_date, start_date, end_date)` - 日线行情
  - 返回: open, high, low, close, pre_close, change, pct_chg, vol, amount
  - 未复权，停牌不提供数据
  - 支持多股票同时提取

### 复权因子
- `adj_factor(ts_code, trade_date)` - 复权因子

### 周线/月线
- `weekly()` / `monthly()` - 周线/月线行情

### 分钟行情
- `stk_mins(ts_code, freq, start_date, end_date)` - 分钟级行情
  - freq: 1/5/15/30/60

### 每日指标
- `daily_basic(ts_code, trade_date, start_date, end_date)` - 每日指标
  - 返回: close, turn_over_rate, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm

## 指数数据
- `index_basic(market)` - 指数基础信息
- `index_daily(ts_code)` - 指数日线行情
- `index_weekly()` / `index_monthly()` - 指数周/月线
- `index_weight(index_code, trade_date)` - 指数权重

## 财务数据
- `income(ts_code, period, start_date, end_date)` - 利润表
- `balancesheet()` - 资产负债表
- `cashflow()` - 现金流量表
- `fina_indicator()` - 财务指标
- `fina_audit()` - 审计意见

## 沪深港通
- `moneyflow_hsgt()` - 沪深港通资金流向
- `hsgt_top10(trade_date, market_type)` - 十大成交股
- `north_money_flow()` - 北向资金

## 龙虎榜
- `top_list(trade_date)` - 龙虎榜详情
- `top_inst(trade_date)` - 龙虎榜机构明细

## 股东数据
- `top10_holders(ts_code, period)` - 十大股东
- `top10_floatholders()` - 十大流通股东
- `stk_holdernumber(ts_code, date)` - 股东户数

## 分红送股
- `dividend(ts_code)` - 分红送股数据

## 前瞻指标
- `forecast(ann_date, period)` - 业绩预告
- `express(ann_date, period)` - 业绩快报
- `disclosure_date(ts_code)` - 预约披露时间

## 期货数据
- `fut_basic(exchange)` - 期货合约基础信息
- `fut_daily(ts_code, trade_date)` - 期货日线行情
- `fut_mapping(ts_code, trade_date)` - 期货主力与连续合约

## 基金数据
- `fund_basic(market)` - 基金列表
- `fund_daily(ts_code)` - 基金净值行情
- `fund_nav(ts_code)` - 基金净值详情

## 宏观数据
- `macro_china_gdp()` - GDP
- `macro_china_cpi()` - CPI
- `macro_china_ppi()` - PPI
- `macro_china_money_supply()` - 货币供应量
- `macro_china_shrzgm()` - 社会融资规模
- `shibor()` - Shibor利率
- `shibor_lpr()` - LPR利率

## 代码示例

```python
import tushare as ts
pro = ts.pro_api('your_token')

# A股日线行情
df = pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240501')

# 多股票提取
df = pro.daily(ts_code='000001.SZ,600519.SH', start_date='20240101')

# 获取某天全市场行情
df = pro.daily(trade_date='20240501')

# 财务指标
df = pro.fina_indicator(ts_code='000001.SZ')

# 沪深港通
df = pro.moneyflow_hsgt(start_date='20240101')
```
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 写入 {filepath} ({len(content)} chars)")

def compile_yfinance_summary():
    """编译yfinance接口总览"""
    filepath = KNOWLEDGE_DIR / "yfinance_api_summary.md"
    content = """# yfinance API 文档

> 基于 yfinance GitHub README 整理
> 仓库: https://github.com/ranaroussi/yfinance
> 编译时间: 2026-05-05
> 注意: yfinance 非官方工具，数据仅供个人研究使用

## 安装
```bash
pip install yfinance
```

## 核心对象

### Ticker - 单只股票
```python
import yfinance as yf

ticker = yf.Ticker("AAPL")

# 历史行情
hist = ticker.history(period="1mo")  # 1mo/3mo/6mo/1y/2y/5y/10y/ytd/max
hist = ticker.history(start="2024-01-01", end="2024-12-31")
hist = ticker.history(interval="1d")  # 1m/2m/5m/15m/30m/60m/90m/1h/1d/5d/1wk/1mo/3mo

# 返回字段: Open, High, Low, Close, Volume, Dividends, Stock Splits

# 公司信息
info = ticker.info
# 包含: sector, industry, marketCap, trailingPE, forwardPE, priceToBook,
# dividendYield, fiftyTwoWeekHigh/Low, averageVolume, beta 等

# 财务数据（自动返回最近4年）
financials = ticker.financials  # 利润表
balance_sheet = ticker.balance_sheet  # 资产负债表
cashflow = ticker.cashflow  # 现金流量表

# 盈利
earnings = ticker.earnings  # 季度/年度盈利
quarterly_earnings = ticker.quarterly_earnings

# 分析师推荐
recommendations = ticker.recommendations

# 机构持仓
institutional_holders = ticker.institutional_holders
major_holders = ticker.major_holders

# 期权
opt_chain = ticker.option_chain()  # 返回puts和calls两个DataFrame

# ESG评分
esg = ticker.sustainability

# 日历事件（财报日期等）
calendar = ticker.calendar
```

### download - 批量下载
```python
import yfinance as yf

# 多只股票
data = yf.download("AAPL MSFT GOOG", start="2024-01-01", end="2024-12-31")

# 参数:
# tickers: str或list，股票代码（支持全球主要交易所）
# start/end: 日期
# interval: 数据间隔
# group_by: 'column'或'ticker'
# auto_adjust: 是否自动复权（默认True）
# prepost: 是否包含盘前盘后数据
# threads: 并行线程数
```

### Tickers - 多只股票
```python
tickers = yf.Tickers("AAPL MSFT GOOG")
# 访问每只: tickers.tickers['AAPL'].info

# 批量获取历史
data = tickers.history(period="1mo")
```

### Market - 市场信息
```python
market = yf.Market()
# 获取市场概览信息
```

### Search - 搜索
```python
search = yf.Search("Apple")
# 返回相关股票和新闻
```

### Sector / Industry - 行业信息
```python
sector = yf.Sector("technology")
industry = yf.Industry("software")
```

## 数据间隔说明
| 间隔 | 说明 | 限制 |
|------|------|------|
| 1m | 1分钟 | 仅最近7天（最多），仅限实时 |
| 2m | 2分钟 | 最近60天 |
| 5m | 5分钟 | 最近60天 |
| 15m | 15分钟 | 最近60天 |
| 30m | 30分钟 | 最近60天 |
| 90m | 90分钟 | 最近60天 |
| 60m/1h | 1小时 | 最近730天 |
| 1d | 日线 | 完整历史 |
| 5d | 5天 | 完整历史 |
| 1wk | 周线 | 完整历史 |
| 1mo | 月线 | 完整历史 |
| 3mo | 季线 | 完整历史 |

## 支持的市场
- 美股: AAPL, MSFT, GOOG
- A股: 000001.SZ, 600519.SS
- 港股: 0700.HK
- 其他全球市场: 支持大多数Yahoo Finance覆盖的市场

## 常见问题
1. **数据延迟**: Yahoo Finance数据有15-20分钟延迟
2. **API变化**: Yahoo不保证API稳定，yfinance可能偶尔需要更新
3. **使用限制**: 仅限个人研究使用，不可商用
4. **停牌数据**: 停牌期间无数据返回
5. **复权**: 默认auto_adjust=True自动复权

## 代码示例

### 获取股票基本信息
```python
import yfinance as yf
ticker = yf.Ticker("AAPL")
info = ticker.info
print(f"市值: {info['marketCap']}")
print(f"PE: {info['trailingPE']}")
print(f"行业: {info['industry']}")
```

### 技术指标计算
```python
import yfinance as yf
import pandas as pd

df = yf.download("AAPL", period="1y")

# MA
df['MA20'] = df['Close'].rolling(20).mean()
df['MA60'] = df['Close'].rolling(60).mean()

# RSI
delta = df['Close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))
```

### 获取财务数据
```python
ticker = yf.Ticker("AAPL")
# 利润表
print(ticker.financials)
# 资产负债表
print(ticker.balance_sheet)
# 现金流量表
print(ticker.cashflow)
```
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 写入 {filepath} ({len(content)} chars)")

def compile_global_apis():
    """编译全球市场API总览"""
    filepath = KNOWLEDGE_DIR / "global_market_api_summary.md"
    content = """# 全球金融市场数据 API 总览

> 编译时间: 2026-05-05

## 港股

### 港交所 HKEX
- OpenAPI: https://www.hkex.com.hk/Market-Data-and-Analytics
- 数据: 实时行情、历史数据、衍生品
- 认证: 需申请API Key

### 富途 OpenD
- 文档: https://openapi.futunn.com/futu-api-doc/
- 支持: 港股/美股/A股
- 数据: 实时行情、K线、财务数据
- 安装: pip install futu-api

### AkShare港股接口
- `stock_hk_spot_em()` - 港股实时行情
- `stock_hk_daily(symbol)` - 港股历史行情
- `stock_hk_index_spot_sina()` - 港股指数实时
- `stock_hk_index_daily_sina(symbol)` - 港股指数历史

## 期货

### AkShare期货接口
- `futures_zh_spot()` - 实时行情
- `futures_zh_daily(symbol)` - 日线行情
- `futures_zh_minute(symbol)` - 分钟行情
- `futures_main_sina(symbol)` - 主力合约
- `futures_comm_info(symbol)` - 手续费与保证金
- `futures_inventory_99(symbol)` - 库存数据
- `futures_zh_spot_sina()` - 新浪期货行情

### 期货交易所
| 交易所 | 代码 | 网址 |
|--------|------|------|
| 中金所 | CFFEX | cffex.com.cn |
| 上期所 | SHFE | shfe.com.cn |
| 上期能源 | INE | ine.cn |
| 大商所 | DCE | dce.com.cn |
| 郑商所 | CZCE | czce.com.cn |
| 广期所 | GFEX | gfex.com.cn |

### 芝商所 CME Group
- API: https://www.cmegroup.com/market-data.html
- 数据: 利率期货、股指期货、商品期货
- QuikStrike: 高级分析工具

### 贵金属
- 上海黄金交易所(SGE): sge.com.cn
- LBMA伦敦金银市场: lbma.org.uk
- AkShare: `spot_global_precious_metals()` - 全球贵金属现货

## 外汇/汇率

### AkShare外汇接口
- `currency_boc_safe()` - 中国银行外汇牌价
- `fx_spot_quote()` - 外汇实时行情
- `macro_china_exchange_rate()` - 人民币汇率

### Yahoo Finance外汇
```python
import yfinance as yf
# 美元/人民币
data = yf.download("CNY=X", period="1mo")
# 欧元/美元
data = yf.download("EURUSD=X", period="1mo")
```

### 其他
- ECB欧洲央行: 每日参考汇率
- FRED: 汇率指数数据

## 宏观经济数据

### FRED (美联储经济数据)
- API: https://fred.stlouisfed.org/docs/api/
- 关键指标: GDP, CPI, 失业率, 利率, M2
- 认证: 免费API Key
- Python: `pip install fredapi`

### 世界银行
- API: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- 数据: GDP, 人口, 贸易等200+国家指标
- Python: `pip install wbgapi`

### AkShare宏观接口
- `macro_china_gdp_yearly()` - 中国GDP年率
- `macro_china_cpi_yearly()` - 中国CPI年率
- `macro_china_ppi_yearly()` - 中国PPI年率
- `macro_china_lpr()` - LPR利率
- `macro_china_urban_unemployment()` - 城镇调查失业率
- `macro_china_shrzgm()` - 社融规模
- `macro_china_money_supply()` - 货币供应量
- `macro_china_trade_balance()` - 贸易帐
- `macro_china_exports_yoy()` - 出口年率
- `macro_china_imports_yoy()` - 进口年率

## 加密货币

### CoinGecko
- API: https://www.coingecko.com/en/api
- 免费额度: 10-50次/分钟
- 数据: 价格、市值、交易量

### Binance
- API: https://binance-docs.github.io/apidocs/
- 数据: 现货、期货、K线

### AkShare加密货币
- `crypto_hist_em(symbol)` - 加密货币历史行情
- `crypto_spot_em()` - 加密货币实时行情

## 技术分析库

### TA-Lib
- 安装: `pip install ta-lib`（需先安装C库）
- 指标: 150+技术指标（MA, MACD, RSI, Bollinger等）
- 文档: https://ta-lib.org/

### pandas-ta
- 安装: `pip install pandas-ta`
- 纯Python实现，兼容性好
- 指标: 130+技术指标

### backtrader
- 安装: `pip install backtrader`
- 功能: 回测引擎、策略开发
- 文档: https://www.backtrader.com/

## 量化平台

### 聚宽 JoinQuant
- 数据: A股分钟级数据、财务数据
- 因子库: Alpha101等
- API: `pip install jqdatasdk`

### 米筐 RiceQuant
- RQData: 专业金融数据服务
- API: `pip install rqdatac`

### 优矿 Uqer
- 万得旗下量化平台
- 数据丰富度较高
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 写入 {filepath} ({len(content)} chars)")


if __name__ == "__main__":
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("📊 金融知识文件编译器")
    print("=" * 60)
    
    compile_akshare_stock_summary()
    compile_tushare_summary()
    compile_yfinance_summary()
    compile_global_apis()
    
    print("\n" + "=" * 60)
    print("✅ 所有总览文件编译完成")
    print("=" * 60)
    
    # 统计
    total = 0
    for f in KNOWLEDGE_DIR.glob("*.md"):
        size = f.stat().st_size
        lines = len(f.read_text(encoding='utf-8').splitlines())
        print(f"  📄 {f.name}: {lines} lines, {size:,} bytes")
        total += size
    print(f"\n  📊 总计: {total:,} bytes")
