#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析股票近期涨跌幅"""

import os
import sys
import json
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta

# 初始化
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("错误：未设置 TUSHARE_TOKEN 环境变量", file=sys.stderr)
    sys.exit(1)

pro = ts.pro_api(token)

# 股票代码列表
if len(sys.argv) < 2:
    print("用法：python3 analyze_trend.py 股票代码1,股票代码2,...", file=sys.stderr)
    sys.exit(1)

stock_codes = sys.argv[1].split(',')

# 获取最近30天的数据
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')

results = []

for ts_code in stock_codes:
    try:
        # 获取日线数据
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if not df.empty:
            df = df.sort_values('trade_date')
            
            # 计算近期涨幅
            if len(df) >= 20:
                latest_close = df.iloc[-1]['close']
                close_20d_ago = df.iloc[-20]['close']
                close_5d_ago = df.iloc[-5]['close']
                
                pct_chg_20d = (latest_close - close_20d_ago) / close_20d_ago * 100
                pct_chg_5d = (latest_close - close_5d_ago) / close_5d_ago * 100
                
                # 检查是否有涨停记录
                limit_up_count = len(df[df['pct_chg'] >= 9.9])
                
                results.append({
                    'ts_code': ts_code,
                    'latest_close': float(latest_close),
                    'pct_chg_5d': round(pct_chg_5d, 2),
                    'pct_chg_20d': round(pct_chg_20d, 2),
                    'limit_up_count_60d': limit_up_count,
                    'volatility': 'high' if abs(pct_chg_20d) > 30 else 'normal'
                })
    except Exception as e:
        continue

print(json.dumps(results, ensure_ascii=False, indent=2))
