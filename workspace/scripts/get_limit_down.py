#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取今日跌停股票列表
"""
import os
import sys
import tushare as ts
import json

# 读取token
token = os.getenv('TUSHARE_TOKEN') or ts.get_token()
if not token:
    print("错误：未找到TUSHARE_TOKEN，请设置环境变量")
    sys.exit(1)

# 初始化pro接口
pro = ts.pro_api(token)

# 获取今日日期（格式：YYYYMMDD）
trade_date = '20260327'  # 2026年3月27日

# 如果今日没有数据，尝试前几个交易日
dates_to_try = ['20260327', '20260326', '20260325', '20260324', '20260321']

try:
    df = None
    
    # 尝试多个日期
    for date in dates_to_try:
        df = pro.limit_list_d(
            trade_date=date,
            limit_type='D',  # D表示跌停
            fields='ts_code,trade_date,name,close,pct_chg,industry,amount,float_mv,total_mv,turnover_ratio'
        )
        
        if not df.empty:
            trade_date = date
            break
    
    if df is None or df.empty:
        print(json.dumps({"count": 0, "stocks": []}, ensure_ascii=False))
    else:
        # 转换为JSON格式
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                'ts_code': row['ts_code'],
                'name': row['name'],
                'close': float(row['close']),
                'pct_chg': float(row['pct_chg']),
                'industry': row['industry'] if row['industry'] else '',
                'amount': float(row['amount']) if row['amount'] else 0,
                'float_mv': float(row['float_mv']) if row['float_mv'] else 0,
                'total_mv': float(row['total_mv']) if row['total_mv'] else 0,
                'turnover_ratio': float(row['turnover_ratio']) if row['turnover_ratio'] else 0
            })
        
        result = {
            "count": len(stocks),
            "trade_date": trade_date,
            "stocks": stocks
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

except Exception as e:
    print(json.dumps({"error": str(e)}, ensure_ascii=False))
    sys.exit(1)
