#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取股票公告"""

import os
import sys
import json
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
    print("用法：python3 get_announcements.py 股票代码1,股票代码2,...", file=sys.stderr)
    sys.exit(1)

stock_codes = sys.argv[1].split(',')

# 获取最近7天的公告
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

try:
    all_anns = []
    
    for ts_code in stock_codes[:3]:  # 限制只查前3只
        try:
            # 获取公告数据
            df = pro.anns_d(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if not df.empty:
                for _, row in df.iterrows():
                    all_anns.append({
                        'ts_code': ts_code,
                        'ann_date': str(row.get('ann_date', '')),
                        'ann_type': str(row.get('ann_type', '')),
                        'title': str(row.get('ann_type', '')),  # 公告类型
                    })
        except Exception as e:
            continue
    
    if all_anns:
        result = {
            'date_range': f"{start_date} - {end_date}",
            'total_anns': len(all_anns),
            'announcements': all_anns[:10]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"message": "未获取到公告数据"}, ensure_ascii=False))
        
except Exception as e:
    print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)
