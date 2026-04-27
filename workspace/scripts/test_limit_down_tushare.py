#!/usr/bin/env python3.11
"""
Test script to get limit-down stocks using tushare
"""
import tushare as ts
import pandas as pd
from pathlib import Path

# Get tushare token
TUSHARE_TOKEN_FILE = Path.home() / ".tushare_token"
token = TUSHARE_TOKEN_FILE.read_text().strip() if TUSHARE_TOKEN_FILE.exists() else None

if not token:
    print("No tushare token found")
    exit(1)

try:
    ts.set_token(token)
    pro = ts.pro_api()
    
    # Get A-share spot data
    df = pro.daily(trade_date='20260427')
    
    # Filter for limit-down stocks (pct_change <= -9.9)
    limit_down = df[df['pct_change'] <= -9.9]
    
    print(f"今日跌停股票数量: {len(limit_down)}")
    print("=" * 50)
    
    if len(limit_down) > 0:
        for _, row in limit_down.iterrows():
            print(f"股票代码: {row['ts_code']}")
            print(f"股票名称: {row['name'] if 'name' in row else 'N/A'}")
            print(f"涨跌幅: {row['pct_change']}%")
            print(f"成交额: {row['amount'] if 'amount' in row else 'N/A'}")
            print("-" * 30)
    else:
        print("今日无跌停股票")
        
except Exception as e:
    print(f"Error: {e}")