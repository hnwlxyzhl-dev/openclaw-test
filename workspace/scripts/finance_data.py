#!/usr/bin/env python3.11
"""
统一金融数据获取工具

按优先级依次尝试不同数据源，直到成功获取数据。
优先级：akshare > tushare > yahoo-finance > scrapling爬虫

用法：
    python3.11 scripts/finance_data.py quote 002637           # 获取A股实时行情
    python3.11 scripts/finance_data.py quote AAPL --us        # 获取美股行情
    python3.11 scripts/finance_data.py index                  # 获取所有主要指数
    python3.11 scripts/finance_data.py index nasdaq           # 获取纳斯达克指数
    python3.11 scripts/finance_data.py limit-down             # 获取今日跌停股
    python3.11 scripts/finance_data.py news 赞宇科技          # 搜索金融新闻
    python3.11 scripts/finance_data.py --help                 # 查看帮助

支持的指数代码：
    A股: sh(上证), sz(深证), cyb(创业板), hs300(沪深300), sz50(上证50), kc50(科创50)
    美股: dji(道琼斯), sp500(标普500), nasdaq(纳斯达克)
    港股: hsi(恒生指数)
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# ============================================================================
# 数据源优先级配置
# ============================================================================

DATA_SOURCES = {
    "a_stock_quote": ["akshare", "tushare", "eastmoney_api"],
    "us_stock_quote": ["yahoo_finance", "eastmoney_api"],
    "limit_down": ["eastmoney_api", "akshare", "tushare"],
    "news": ["searxng", "eastmoney_api"],
    "fundamentals": ["akshare", "tushare", "yahoo_finance"],
    "index": ["eastmoney_api", "akshare"],
}

# 指数代码映射（东方财富 secid）
INDEX_MAPPING = {
    # A股指数
    "sh": {"name": "上证指数", "secid": "1.000001"},
    "sz": {"name": "深证成指", "secid": "0.399001"},
    "cyb": {"name": "创业板指", "secid": "0.399006"},
    "hs300": {"name": "沪深300", "secid": "1.000300"},
    "sz50": {"name": "上证50", "secid": "1.000016"},
    "kc50": {"name": "科创50", "secid": "1.000688"},
    "zz500": {"name": "中证500", "secid": "1.000905"},
    "zz1000": {"name": "中证1000", "secid": "1.000852"},
    # 美股指数
    "dji": {"name": "道琼斯", "secid": "100.DJI"},
    "sp500": {"name": "标普500", "secid": "100.SPX"},
    "nasdaq": {"name": "纳斯达克", "secid": "100.NDX"},
    "ixic": {"name": "纳斯达克综合", "secid": "100.IXIC"},
    # 港股指数
    "hsi": {"name": "恒生指数", "secid": "100.HSI"},
    "hscei": {"name": "恒生国企", "secid": "100.HSCEI"},
    # 其他
    "vix": {"name": "VIX波动率", "secid": "100.VIX"},
    "dxy": {"name": "美元指数", "secid": "100.DXY"},
    # 别名
    "上证": "sh",
    "深证": "sz",
    "创业板": "cyb",
    "沪深300": "hs300",
    "上证50": "sz50",
    "科创50": "kc50",
    "中证500": "zz500",
    "道琼斯": "dji",
    "标普": "sp500",
    "纳斯达克": "nasdaq",
    "恒指": "hsi",
    "恒生": "hsi",
}


# ============================================================================
# AkShare 数据源
# ============================================================================

def akshare_get_quote(code: str) -> dict:
    """使用 akshare 获取A股实时行情"""
    try:
        import akshare as ak
        
        # 实时行情
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == code]
        
        if len(stock) == 0:
            return None
        
        row = stock.iloc[0]
        return {
            "source": "akshare",
            "code": code,
            "name": row['名称'],
            "price": float(row['最新价']),
            "pct_chg": float(row['涨跌幅']),
            "change": float(row['涨跌额']),
            "volume": int(row['成交量']),
            "amount": float(row['成交额']),
            "high": float(row['最高']),
            "low": float(row['最低']),
            "open": float(row['今开']),
            "pre_close": float(row['昨收']),
            "is_limit_down": float(row['涨跌幅']) <= -9.9,
            "is_limit_up": float(row['涨跌幅']) >= 9.9,
        }
    except Exception as e:
        return {"error": f"akshare: {str(e)}"}


def akshare_get_index(index_code: str) -> dict:
    """
    使用 akshare 获取A股指数行情
    
    Args:
        index_code: 指数代码或别名
    
    Returns:
        指数行情数据
    """
    try:
        import akshare as ak
        
        # 解析指数代码
        index_info = INDEX_MAPPING.get(index_code.lower(), index_code)
        
        # 如果是别名，继续解析
        if isinstance(index_info, str):
            index_info = INDEX_MAPPING.get(index_info, {"name": index_code, "secid": None})
        
        if not isinstance(index_info, dict):
            return {"error": f"未知的指数代码: {index_code}"}
        
        name = index_info["name"]
        secid = index_info["secid"]
        
        # 只支持 A股指数
        if not secid or not secid.startswith(("1.", "0.")):
            return None  # 返回 None 让其他数据源处理
        
        # 提取纯代码
        code = secid.split(".")[1]
        
        # 获取实时指数数据
        df = ak.stock_zh_index_spot_sina()
        
        # 查找对应指数
        index_row = df[df['代码'] == f"sh{code}"]
        if len(index_row) == 0:
            index_row = df[df['代码'] == f"sz{code}"]
        
        if len(index_row) == 0:
            return None
        
        row = index_row.iloc[0]
        
        return {
            "source": "akshare",
            "code": index_code,
            "secid": secid,
            "name": name,
            "price": float(row['最新价']),
            "pct_chg": float(row['涨跌幅']),
            "change": float(row['涨跌额']),
            "volume": int(row['成交量']),
            "amount": float(row['成交额']),
        }
    except Exception as e:
        return {"error": f"akshare: {str(e)}"}


def akshare_get_limit_down() -> list:
    """使用 akshare 获取今日跌停股"""
    try:
        import akshare as ak
        
        df = ak.stock_zh_a_spot_em()
        limit_down = df[df['涨跌幅'] <= -9.9]
        
        result = []
        for _, row in limit_down.iterrows():
            result.append({
                "code": row['代码'],
                "name": row['名称'],
                "price": float(row['最新价']),
                "pct_chg": float(row['涨跌幅']),
                "amount": float(row['成交额']),
            })
        
        return {"source": "akshare", "count": len(result), "stocks": result}
    except Exception as e:
        return {"error": f"akshare: {str(e)}"}


# ============================================================================
# Tushare 数据源（指数）
# ============================================================================

TUSHARE_TOKEN_FILE = Path.home() / ".tushare_token"


def get_tushare_token() -> str:
    """获取 tushare token"""
    if TUSHARE_TOKEN_FILE.exists():
        return TUSHARE_TOKEN_FILE.read_text().strip()
    return None


def tushare_get_index(index_code: str) -> dict:
    """
    使用 tushare 获取A股指数行情
    
    Args:
        index_code: 指数代码或别名
    
    Returns:
        指数行情数据
    """
    try:
        import tushare as ts
        
        token = get_tushare_token()
        if not token:
            return None  # 没有 token，跳过
        
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 解析指数代码
        index_info = INDEX_MAPPING.get(index_code.lower(), index_code)
        
        # 如果是别名，继续解析
        if isinstance(index_info, str):
            index_info = INDEX_MAPPING.get(index_info, {"name": index_code, "secid": None})
        
        if not isinstance(index_info, dict):
            return None
        
        name = index_info["name"]
        secid = index_info["secid"]
        
        # 只支持 A股指数
        if not secid or not secid.startswith(("1.", "0.")):
            return None  # 返回 None 让其他数据源处理
        
        # 提取纯代码和市场
        market_code, code = secid.split(".")
        
        # 转换为 tushare 格式
        # market_code: 1 = 上海, 0 = 深圳
        if market_code == "1":
            ts_code = f"{code}.SH"
        else:
            ts_code = f"{code}.SZ"
        
        # 获取指数日线数据（最新一天）
        from datetime import date, timedelta
        today = date.today()
        start_date = (today - timedelta(days=7)).strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")
        
        df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df is None or len(df) == 0:
            return None
        
        # 取最新一条
        row = df.iloc[0]
        
        return {
            "source": "tushare",
            "code": index_code,
            "secid": secid,
            "name": name,
            "price": float(row['close']),
            "pct_chg": float(row['pct_chg']),
            "change": float(row['change']),
            "volume": int(row['vol']) if 'vol' in row else 0,
            "amount": float(row['amount']) if 'amount' in row else 0,
        }
    except Exception as e:
        return {"error": f"tushare: {str(e)}"}
        
        result = []
        for _, row in limit_down.iterrows():
            result.append({
                "code": row['代码'],
                "name": row['名称'],
                "price": float(row['最新价']),
                "pct_chg": float(row['涨跌幅']),
                "amount": float(row['成交额']),
            })
        
        return {"source": "akshare", "count": len(result), "stocks": result}
    except Exception as e:
        return {"error": f"akshare: {str(e)}"}


# ============================================================================
# Tushare 数据源
# ============================================================================

def tushare_get_quote(code: str) -> dict:
    """使用 tushare 获取A股实时行情"""
    try:
        import tushare as ts
        
        df = ts.get_realtime_quotes(code)
        if df is None or len(df) == 0:
            return None
        
        row = df.iloc[0]
        price = float(row['price'])
        pre_close = float(row['pre_close'])
        pct_chg = (price - pre_close) / pre_close * 100
        
        return {
            "source": "tushare",
            "code": code,
            "name": row['name'],
            "price": price,
            "pct_chg": round(pct_chg, 2),
            "volume": int(row['volume']),
            "amount": float(row['amount']),
            "high": float(row['high']),
            "low": float(row['low']),
            "open": float(row['open']),
            "pre_close": pre_close,
            "is_limit_down": pct_chg <= -9.9,
            "is_limit_up": pct_chg >= 9.9,
        }
    except Exception as e:
        return {"error": f"tushare: {str(e)}"}


def tushare_get_limit_down() -> list:
    """使用 tushare 获取今日跌停股"""
    try:
        import tushare as ts
        from datetime import date
        
        pro = ts.pro_api()
        today = date.today().strftime('%Y%m%d')
        
        # 获取当日跌停股票
        df = pro.limit_list(trade_date=today, limit_type='D')
        
        if df is None or len(df) == 0:
            return {"source": "tushare", "count": 0, "stocks": []}
        
        result = []
        for _, row in df.iterrows():
            result.append({
                "code": row['ts_code'].split('.')[0],
                "name": row['name'],
                "price": float(row['close']),
                "pct_chg": float(row['pct_chg']),
                "amount": float(row.get('amount', 0)),
            })
        
        return {"source": "tushare", "count": len(result), "stocks": result}
    except Exception as e:
        return {"error": f"tushare: {str(e)}"}


# ============================================================================
# Yahoo Finance 数据源（美股）
# ============================================================================

def yahoo_get_quote(code: str) -> dict:
    """使用 yahoo-finance 获取美股行情"""
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(code)
        info = ticker.info
        
        return {
            "source": "yahoo_finance",
            "code": code,
            "name": info.get('shortName', code),
            "price": info.get('currentPrice', info.get('regularMarketPrice', 0)),
            "pct_chg": round((info.get('currentPrice', 0) - info.get('previousClose', 0)) / info.get('previousClose', 1) * 100, 2),
            "market_cap": info.get('marketCap', 0),
            "pe_ratio": info.get('trailingPE', 0),
            "volume": info.get('volume', 0),
        }
    except Exception as e:
        return {"error": f"yahoo_finance: {str(e)}"}


# ============================================================================
# 东方财富 API（爬虫兜底）
# ============================================================================

def eastmoney_get_index(index_code: str) -> dict:
    """
    使用东方财富 API 获取指数行情
    
    Args:
        index_code: 指数代码或别名 (如 sh, nasdaq, dji, hsi)
    
    Returns:
        指数行情数据
    """
    try:
        from scrapling import StealthyFetcher
        import json as json_module
        
        # 解析指数代码
        index_info = INDEX_MAPPING.get(index_code.lower(), index_code)
        
        # 如果是别名，继续解析
        if isinstance(index_info, str):
            index_info = INDEX_MAPPING.get(index_info, {"name": index_code, "secid": None})
        
        if not isinstance(index_info, dict) or not index_info.get("secid"):
            return {"error": f"未知的指数代码: {index_code}"}
        
        secid = index_info["secid"]
        name = index_info["name"]
        
        fetcher = StealthyFetcher()
        
        # 使用东方财富指数 API
        api_url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids={secid}&fields=f2,f3,f4,f12,f13,f14"
        
        page = fetcher.fetch(api_url)
        text = page.css("body")[0].get_all_text()
        data = json_module.loads(text)
        
        if not data.get('data') or not data['data'].get('diff'):
            return {"error": f"无法获取指数数据: {index_code}"}
        
        diff = data['data']['diff'][0]
        
        price = float(diff.get('f2', 0))
        pct_chg = float(diff.get('f3', 0))
        change = float(diff.get('f4', 0))
        
        return {
            "source": "eastmoney_api",
            "code": index_code,
            "secid": secid,
            "name": name,
            "price": price,
            "pct_chg": pct_chg,
            "change": change,
        }
    except Exception as e:
        return {"error": f"eastmoney_api: {str(e)}"}


def eastmoney_get_all_indexes() -> dict:
    """
    获取所有主要指数行情
    
    Returns:
        所有主要指数的行情数据
    """
    indexes = {}
    
    # A股主要指数
    a_stock_indexes = ["sh", "sz", "cyb", "hs300", "sz50", "kc50", "zz500"]
    
    # 美股主要指数（移除 dji，因为东方财富 API 不支持）
    us_indexes = ["sp500", "nasdaq"]
    
    # 港股主要指数
    hk_indexes = ["hsi"]
    
    all_indexes = a_stock_indexes + us_indexes + hk_indexes
    
    for idx in all_indexes:
        result = eastmoney_get_index(idx)
        if "error" not in result:
            indexes[idx] = result
    
    return {
        "source": "eastmoney_api",
        "indexes": indexes,
        "count": len(indexes),
    }


def eastmoney_get_quote(code: str, is_us: bool = False) -> dict:
    """使用东方财富 API 获取行情（Scrapling 爬虫）"""
    try:
        from scrapling import StealthyFetcher
        import json as json_module
        
        fetcher = StealthyFetcher()
        
        if is_us:
            # 美股
            api_url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=105.{code}&fields=f57,f58,f43,f169,f170,f44,f45,f47"
        else:
            # A股
            market = "1" if code.startswith("6") else "0"
            api_url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f57,f58,f43,f169,f170,f44,f45,f47"
        
        page = fetcher.fetch(api_url)
        text = page.css("body")[0].get_all_text()
        data = json_module.loads(text)
        
        if not data.get('data'):
            return None
        
        d = data['data']
        price = d.get('f43', 0) / 100
        pre_close = price - d.get('f169', 0) / 100
        pct_chg = d.get('f170', 0) / 100
        
        return {
            "source": "eastmoney_api",
            "code": code,
            "name": d.get('f58', ''),
            "price": price,
            "pct_chg": pct_chg,
            "high": d.get('f44', 0) / 100,
            "low": d.get('f45', 0) / 100,
            "volume": d.get('f47', 0),
            "is_limit_down": pct_chg <= -9.9,
            "is_limit_up": pct_chg >= 9.9,
        }
    except Exception as e:
        return {"error": f"eastmoney_api: {str(e)}"}


# ============================================================================
# 统一接口
# ============================================================================

def get_quote(code: str, is_us: bool = False) -> dict:
    """
    获取股票行情（自动选择数据源）
    
    Args:
        code: 股票代码
        is_us: 是否美股
    
    Returns:
        行情数据字典
    """
    sources = DATA_SOURCES["us_stock_quote"] if is_us else DATA_SOURCES["a_stock_quote"]
    
    for source in sources:
        result = None
        
        if source == "akshare" and not is_us:
            result = akshare_get_quote(code)
        elif source == "tushare" and not is_us:
            result = tushare_get_quote(code)
        elif source == "yahoo_finance" and is_us:
            result = yahoo_get_quote(code)
        elif source == "eastmoney_api":
            result = eastmoney_get_quote(code, is_us)
        
        if result and "error" not in result:
            return result
    
    return {"error": "所有数据源均获取失败"}


def get_limit_down() -> dict:
    """
    获取今日跌停股（自动选择数据源）
    """
    sources = DATA_SOURCES["limit_down"]
    
    for source in sources:
        result = None
        
        if source == "akshare":
            result = akshare_get_limit_down()
        elif source == "tushare":
            result = tushare_get_limit_down()
        
        if result and "error" not in result:
            return result
    
    return {"error": "所有数据源均获取失败"}


def get_index(index_code: str = None) -> dict:
    """
    获取指数行情（自动选择数据源）
    
    优先级：tushare (A股) > akshare (A股) > eastmoney_api
    
    Args:
        index_code: 指数代码 (如 sh, nasdaq, dji, hsi)。如果为 None，返回所有主要指数
    
    Returns:
        指数行情数据
    """
    if index_code:
        # 单个指数：按优先级尝试
        # 1. tushare（需要 token，只支持 A股）
        result = tushare_get_index(index_code)
        if result and "error" not in result:
            return result
        
        # 2. akshare（只支持 A股）
        result = akshare_get_index(index_code)
        if result and "error" not in result:
            return result
        
        # 3. eastmoney_api（兜底，支持所有指数）
        return eastmoney_get_index(index_code)
    else:
        # 所有指数：使用 eastmoney_api（更稳定）
        return eastmoney_get_all_indexes()


def get_announcement(code: str) -> dict:
    """
    获取公司公告（优先东方财富，巨潮资讯网备用）
    
    数据源优先级：东方财富（最新） > 巨潮资讯网（历史）
    
    Args:
        code: 股票代码
    
    Returns:
        公告列表
    """
    from datetime import date, timedelta
    
    # 1. 尝试东方财富（最新数据）
    try:
        import akshare as ak
        
        # 搜索最近7天的公告
        today = date.today()
        announcements = []
        
        for i in range(7):
            search_date = (today - timedelta(days=i)).strftime("%Y%m%d")
            try:
                df = ak.stock_notice_report(symbol='全部', date=search_date)
                stock_df = df[df['代码'] == code]
                
                for _, row in stock_df.iterrows():
                    announcements.append({
                        "code": row['代码'],
                        "name": row['名称'],
                        "title": row['公告标题'],
                        "date": str(row['公告日期']),
                        "type": row['公告类型'],
                        "url": row['网址'],
                    })
            except:
                pass
        
        if announcements:
            # 按日期排序，最新的在前面
            announcements.sort(key=lambda x: x['date'], reverse=True)
            return {
                "source": "eastmoney",
                "code": code,
                "count": len(announcements),
                "announcements": announcements[:20],
            }
    except Exception as e:
        pass
    
    # 2. 回退到巨潮资讯网（历史数据）
    try:
        import akshare as ak
        
        df = ak.stock_zh_a_disclosure_report_cninfo(symbol=code)
        
        if df is None or len(df) == 0:
            return {"error": "未获取到公告信息"}
        
        announcements = []
        for _, row in df.head(20).iterrows():
            announcements.append({
                "code": row['代码'],
                "name": row['简称'],
                "title": row['公告标题'],
                "date": str(row['公告时间']),
                "url": row['公告链接'],
            })
        
        return {
            "source": "cninfo",
            "code": code,
            "count": len(announcements),
            "announcements": announcements,
        }
    except Exception as e:
        return {"error": f"get_announcement: {str(e)}"}


def search_news(keyword: str) -> dict:
    """
    搜索金融新闻
    
    Args:
        keyword: 搜索关键词
    """
    try:
        from scrapling import StealthyFetcher
        import json as json_module
        
        fetcher = StealthyFetcher()
        
        # 使用东方财富搜索 API
        api_url = f"https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch?keyword={keyword}&type=news&pageIndex=1&pageSize=10"
        
        page = fetcher.fetch(api_url)
        text = page.css("body")[0].get_all_text()
        data = json_module.loads(text)
        
        if data.get('Data'):
            news_list = []
            for item in data['Data'][:10]:
                news_list.append({
                    "title": item.get('Title', ''),
                    "source": item.get('Source', ''),
                    "date": item.get('Date', ''),
                    "url": item.get('Url', ''),
                })
            return {"source": "eastmoney_api", "keyword": keyword, "news": news_list}
        
        return {"source": "eastmoney_api", "keyword": keyword, "news": []}
    except Exception as e:
        return {"error": f"search_news: {str(e)}"}


# ============================================================================
# 港股财报数据
# ============================================================================

def get_hk_financial_indicators(code: str, period: str = "年度") -> dict:
    """
    获取港股财务分析主要指标（营收、净利润、ROE、毛利率等）
    
    Args:
        code: 港股代码（纯数字，如 00700、01810）
        period: "年度" 或 "报告期"
    """
    try:
        import akshare as ak
        
        df = ak.stock_financial_hk_analysis_indicator_em(symbol=code, indicator=period)
        
        if df is None or len(df) == 0:
            return {"error": f"未找到 {code} 的财务指标数据"}
        
        records = []
        for _, row in df.iterrows():
            report_date = str(row.get('REPORT_DATE', ''))[:10]
            records.append({
                "report_date": report_date,
                "fiscal_year": row.get('FISCAL_YEAR', ''),
                "currency": row.get('CURRENCY', ''),
                "revenue": row.get('OPERATE_INCOME'),           # 营业收入
                "revenue_yoy": round(row.get('OPERATE_INCOME_YOY', 0), 2),  # 营收同比%
                "net_profit": row.get('HOLDER_PROFIT'),         # 归母净利润
                "net_profit_yoy": round(row.get('HOLDER_PROFIT_YOY', 0), 2), # 净利润同比%
                "gross_profit": row.get('GROSS_PROFIT'),        # 毛利
                "gross_profit_yoy": round(row.get('GROSS_PROFIT_YOY', 0), 2), # 毛利同比%
                "gross_margin": round(row.get('GROSS_PROFIT_RATIO', 0), 2),   # 毛利率%
                "net_margin": round(row.get('NET_PROFIT_RATIO', 0), 2),       # 净利率%
                "roe": round(row.get('ROE_AVG', 0), 2),                      # ROE(平均)%
                "roa": round(row.get('ROA', 0), 2),                           # ROA%
                "eps": row.get('BASIC_EPS'),                 # 基本EPS
                "bps": row.get('BPS'),                      # 每股净资产
                "debt_ratio": round(row.get('DEBT_ASSET_RATIO', 0), 2),       # 资产负债率%
                "current_ratio": round(row.get('CURRENT_RATIO', 0), 2),       # 流动比率
                "ocf_per_share": round(row.get('PER_NETCASH_OPERATE', 0), 2), # 每股经营现金流
            })
        
        stock_name = df.iloc[0].get('SECURITY_NAME_ABBR', '') if len(df) > 0 else ''
        
        return {
            "source": "akshare_eastmoney",
            "code": code,
            "name": stock_name,
            "period": period,
            "count": len(records),
            "records": records,
        }
    except Exception as e:
        return {"error": f"get_hk_financial_indicators: {str(e)}"}


def get_hk_financial_report(code: str, report_type: str = "利润表", period: str = "年度") -> dict:
    """
    获取港股三大财务报表
    
    Args:
        code: 港股代码（纯数字，如 00700）
        report_type: "资产负债表" / "利润表" / "现金流量表"
        period: "年度" 或 "报告期"
    """
    try:
        import akshare as ak
        
        df = ak.stock_financial_hk_report_em(stock=code, symbol=report_type, indicator=period)
        
        if df is None or len(df) == 0:
            return {"error": f"未找到 {code} 的{report_type}数据"}
        
        stock_name = df.iloc[0].get('SECURITY_NAME_ABBR', '') if len(df) > 0 else ''
        
        # 按报告日期分组，每期转为字典
        dates = df['REPORT_DATE'].unique()
        records = []
        for date in dates:
            date_df = df[df['REPORT_DATE'] == date]
            items = []
            for _, row in date_df.iterrows():
                items.append({
                    "item": row.get('STD_ITEM_NAME', ''),
                    "code": row.get('STD_ITEM_CODE', ''),
                    "amount": row.get('AMOUNT'),
                })
            records.append({
                "report_date": str(date)[:10],
                "items": items,
            })
        
        return {
            "source": "akshare_eastmoney",
            "code": code,
            "name": stock_name,
            "report_type": report_type,
            "period": period,
            "count": len(records),
            "records": records,
        }
    except Exception as e:
        return {"error": f"get_hk_financial_report: {str(e)}"}


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="统一金融数据获取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3.11 scripts/finance_data.py quote 002637           # A股行情
  python3.11 scripts/finance_data.py quote AAPL --us        # 美股行情
  python3.11 scripts/finance_data.py index                  # 所有指数
  python3.11 scripts/finance_data.py index nasdaq           # 单个指数
  python3.11 scripts/finance_data.py announcement 002637    # 公司公告
  python3.11 scripts/finance_data.py limit-down             # 今日跌停股
  python3.11 scripts/finance_data.py news 赞宇科技          # 搜索新闻
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # quote 命令
    quote_parser = subparsers.add_parser("quote", help="获取股票行情")
    quote_parser.add_argument("code", help="股票代码")
    quote_parser.add_argument("--us", action="store_true", help="美股")
    quote_parser.add_argument("--json", action="store_true", help="JSON输出")
    
    # limit-down 命令
    ld_parser = subparsers.add_parser("limit-down", help="获取今日跌停股")
    ld_parser.add_argument("--json", action="store_true", help="JSON输出")
    
    # index 命令
    index_parser = subparsers.add_parser("index", help="获取指数行情")
    index_parser.add_argument("code", nargs="?", default=None, help="指数代码 (sh/sz/cyb/hs300/dji/sp500/nasdaq/hsi)，不填则返回所有")
    index_parser.add_argument("--json", action="store_true", help="JSON输出")
    
    # announcement 命令
    ann_parser = subparsers.add_parser("announcement", help="获取公司公告（巨潮资讯网）")
    ann_parser.add_argument("code", help="股票代码")
    ann_parser.add_argument("--json", action="store_true", help="JSON输出")
    
    # news 命令
    news_parser = subparsers.add_parser("news", help="搜索金融新闻")
    news_parser.add_argument("keyword", help="搜索关键词")
    news_parser.add_argument("--json", action="store_true", help="JSON输出")
    
    # hk-finance 命令（港股财报）
    hk_parser = subparsers.add_parser("hk-finance", help="港股财报数据")
    hk_parser.add_argument("code", help="港股代码（纯数字，如 00700、01810）")
    hk_parser.add_argument("--type", dest="report_type", default="indicators",
                          choices=["indicators", "balance", "income", "cashflow"],
                          help="indicators(财务指标,默认) / balance(资产负债表) / income(利润表) / cashflow(现金流量表)")
    hk_parser.add_argument("--period", default="年度", choices=["年度", "报告期"],
                          help="年度(默认) / 报告期")
    hk_parser.add_argument("--json", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    if args.command == "quote":
        result = get_quote(args.code, args.us)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n📊 {result['name']}({result['code']})")
                print(f"   数据源: {result['source']}")
                print(f"   现价: {result['price']}  涨跌幅: {result['pct_chg']:+.2f}%")
                if 'high' in result:
                    print(f"   最高: {result['high']}  最低: {result['low']}")
                if 'volume' in result:
                    vol = result['volume']
                    vol_str = f"{vol/10000:.1f}万" if vol < 100000000 else f"{vol/100000000:.2f}亿"
                    print(f"   成交量: {vol_str}")
                if result.get('is_limit_down'):
                    print("   ⚠️ 跌停中!")
                elif result.get('is_limit_up'):
                    print("   🔥 涨停!")
    
    elif args.command == "limit-down":
        result = get_limit_down()
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n📉 今日跌停股（共{result['count']}只）- 数据源: {result['source']}\n")
                for stock in result['stocks'][:20]:
                    print(f"  {stock['code']} {stock['name']}  {stock['price']}  {stock['pct_chg']:+.2f}%")
                if result['count'] > 20:
                    print(f"\n  ... 还有 {result['count'] - 20} 只")
    
    elif args.command == "index":
        result = get_index(args.code)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
            elif "indexes" in result:
                # 显示所有指数
                print(f"\n📊 全球主要指数 - 数据源: {result['source']}\n")
                
                # A股指数
                print("【A股指数】")
                for code in ["sh", "sz", "cyb", "hs300", "sz50", "kc50", "zz500"]:
                    if code in result["indexes"]:
                        idx = result["indexes"][code]
                        pct = idx['pct_chg']
                        emoji = "🔴" if pct < 0 else "🟢" if pct > 0 else "⚪"
                        print(f"  {emoji} {idx['name']}: {idx['price']:,.2f}  ({pct:+.2f}%)")
                
                # 美股指数
                print("\n【美股指数】")
                for code in ["dji", "sp500", "nasdaq"]:
                    if code in result["indexes"]:
                        idx = result["indexes"][code]
                        pct = idx['pct_chg']
                        emoji = "🔴" if pct < 0 else "🟢" if pct > 0 else "⚪"
                        print(f"  {emoji} {idx['name']}: {idx['price']:,.2f}  ({pct:+.2f}%)")
                
                # 港股指数
                print("\n【港股指数】")
                for code in ["hsi"]:
                    if code in result["indexes"]:
                        idx = result["indexes"][code]
                        pct = idx['pct_chg']
                        emoji = "🔴" if pct < 0 else "🟢" if pct > 0 else "⚪"
                        print(f"  {emoji} {idx['name']}: {idx['price']:,.2f}  ({pct:+.2f}%)")
            else:
                # 单个指数
                pct = result['pct_chg']
                emoji = "🔴" if pct < 0 else "🟢" if pct > 0 else "⚪"
                print(f"\n📊 {result['name']}")
                print(f"   数据源: {result['source']}")
                print(f"   {emoji} 现价: {result['price']:,.2f}  涨跌幅: {pct:+.2f}%")
    
    elif args.command == "announcement":
        result = get_announcement(args.code)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                source_name = "东方财富" if result['source'] == 'eastmoney' else "巨潮资讯网"
                print(f"\n📄 {args.code} 公司公告（共{result['count']}条）- 数据源: {source_name}\n")
                for i, ann in enumerate(result.get('announcements', []), 1):
                    date_str = ann['date'].split()[0] if ' ' in ann['date'] else ann['date']
                    print(f"  {i}. [{date_str}] {ann['title']}")
                    print(f"     {ann['url']}")
                    print()
    
    elif args.command == "news":
        result = search_news(args.keyword)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n📰 \"{args.keyword}\" 相关新闻\n")
                for i, news in enumerate(result.get('news', []), 1):
                    print(f"  {i}. {news['title']}")
                    print(f"     {news['source']} | {news['date']}")
                    print()
    
    elif args.command == "hk-finance":
        if args.report_type == "indicators":
            result = get_hk_financial_indicators(args.code, args.period)
        else:
            type_map = {"balance": "资产负债表", "income": "利润表", "cashflow": "现金流量表"}
            result = get_hk_financial_report(args.code, type_map[args.report_type], args.period)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
            elif args.report_type == "indicators":
                name = result.get('name', '')
                print(f"\n📊 {name}({result['code']}) 财务指标 - 数据源: {result['source']}\n")
                print(f"  {'报告期':<12} {'营收(亿)':<14} {'营收同比':<10} {'净利润(亿)':<14} {'净利润同比':<10} {'毛利率':<8} {'ROE':<8} {'负债率':<8}")
                print(f"  {'─'*84}")
                for r in result['records']:
                    rev = f"{r['revenue']/1e8:,.1f}" if r['revenue'] else "N/A"
                    rev_yoy = f"{r['revenue_yoy']:+.1f}%" if r['revenue_yoy'] else "N/A"
                    profit = f"{r['net_profit']/1e8:,.1f}" if r['net_profit'] else "N/A"
                    profit_yoy = f"{r['net_profit_yoy']:+.1f}%" if r['net_profit_yoy'] else "N/A"
                    gm = f"{r['gross_margin']}%" if r['gross_margin'] else "N/A"
                    roe = f"{r['roe']}%" if r['roe'] else "N/A"
                    dr = f"{r['debt_ratio']}%" if r['debt_ratio'] else "N/A"
                    print(f"  {r['report_date']:<12} {rev:<14} {rev_yoy:<10} {profit:<14} {profit_yoy:<10} {gm:<8} {roe:<8} {dr:<8}")
            else:
                # 报表类型
                type_map = {"资产负债表": "资产负债表", "利润表": "利润表", "现金流量表": "现金流量表"}
                rt = result.get('report_type', '')
                print(f"\n📊 {result.get('name', '')}({result['code']}) {rt} - 数据源: {result['source']}\n")
                for r in result['records'][:3]:  # 最多显示3期
                    print(f"  【{r['report_date']}】")
                    for item in r['items']:
                        amount = item['amount']
                        if amount is not None:
                            if abs(amount) >= 1e8:
                                amount_str = f"{amount/1e8:,.2f}亿"
                            elif abs(amount) >= 1e4:
                                amount_str = f"{amount/1e4:,.2f}万"
                            else:
                                amount_str = f"{amount:,.2f}"
                        else:
                            amount_str = "N/A"
                        print(f"    {item['item']}: {amount_str}")
                    print()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
