#!/usr/bin/env python3.11
"""
Test script to get limit-down stocks using akshare
"""
import akshare as ak
import pandas as pd

try:
    # Get A-share spot data
    df = ak.stock_zh_a_spot_em()
    
    # Filter for limit-down stocks (涨跌幅 <= -9.9)
    limit_down = df[df['涨跌幅'] <= -9.9]
    
    print(f"今日跌停股票数量: {len(limit_down)}")
    print("=" * 50)
    
    if len(limit_down) > 0:
        for _, row in limit_down.iterrows():
            print(f"股票代码: {row['代码']}")
            print(f"股票名称: {row['名称']}")
            print(f"最新价格: {row['最新价']}")
            print(f"涨跌幅: {row['涨跌幅']}%")
            print(f"成交额: {row['成交额']}")
            print("-" * 30)
    else:
        print("今日无跌停股票")
        
except Exception as e:
    print(f"Error: {e}")