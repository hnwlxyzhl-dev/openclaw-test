#!/usr/bin/env python3
"""
每日跌停股票分析任务
- 获取当日跌停股票
- 搜索跌停原因
- 分类分析
"""

import os
import sys
import json
import tushare as ts
from datetime import datetime

# 初始化 tushare
TOKEN = os.getenv('TUSHARE_TOKEN')
if TOKEN:
    ts.set_token(TOKEN)
    pro = ts.pro_api()
else:
    pro = None

def get_trade_date():
    """获取最近的交易日"""
    if not pro:
        return None
    from datetime import timedelta
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
    
    cal = pro.trade_cal(exchange='SSE', is_open=1, 
                       start_date=start_date, end_date=end_date)
    if not cal.empty:
        return cal['cal_date'].iloc[-1]
    return None

def get_limit_down_stocks():
    """获取跌停股票列表"""
    if not pro:
        return []
    
    trade_date = get_trade_date()
    if not trade_date:
        return []
    
    try:
        # 尝试获取跌停数据
        df = pro.limit_list_d(trade_date=trade_date, limit_type='D')
        if df.empty:
            # 如果没有数据，尝试从涨跌幅排行获取
            df_daily = pro.daily(trade_date=trade_date)
            if not df_daily.empty:
                # 筛选跌幅超过9.5%的
                df = df_daily[df_daily['pct_chg'] <= -9.5]
                if not df.empty:
                    return df[['ts_code', 'name', 'close', 'pct_chg', 'vol', 'amount']].to_dict('records')
        else:
            return df.to_dict('records')
    except Exception as e:
        print(f"获取跌停数据失败: {e}")
    
    return []

def categorize_reason(stock_code, stock_name):
    """
    根据股票代码和名称，初步判断可能的跌停原因类别
    实际原因需要结合新闻搜索
    """
    # 这里只是初步分类，实际需要搜索新闻来判断
    return "待分析"

if __name__ == '__main__':
    stocks = get_limit_down_stocks()
    trade_date = get_trade_date()
    
    result = {
        'trade_date': trade_date,
        'count': len(stocks),
        'stocks': stocks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
