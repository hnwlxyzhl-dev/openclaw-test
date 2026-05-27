#!/usr/bin/env python3
"""
简单爬虫获取今日A股跌停股列表
"""

import requests
import json
from datetime import datetime

def get_limit_down_stocks():
    """获取今日跌停股票"""
    today = datetime.now().strftime('%Y%m%d')
    
    # 尝试东方财富API
    url = f"https://push2.eastmoney.com/api/qt/stock/fflow/get"
    params = {
        'lmt': '100',
        'klt': '1',
        'secids': '1.000001,0.399001',
        'fields': 'f2,f3,f12,f14,f169'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('data') and data['data'].get('diff'):
            limit_down = []
            for stock in data['data']['diff']:
                if stock.get('f3', 0) <= -9.9:  # 跌停条件
                    limit_down.append({
                        'code': stock.get('f12', ''),
                        'name': stock.get('f14', ''),
                        'price': stock.get('f2', 0) / 100,
                        'pct_chg': stock.get('f3', 0) / 100,
                        'amount': stock.get('f169', 0) / 10000
                    })
            return limit_down
    except Exception as e:
        print(f"东方财富API获取失败: {e}")
    
    # 尝试新浪财经API
    url = "https://hq.sinajs.cn/list=s_sh,s_sz"
    try:
        response = requests.get(url, timeout=10)
        # 这里需要解析新浪财经的HTML格式数据
        # 由于解析复杂，返回空列表
        return []
    except Exception as e:
        print(f"新浪财经API获取失败: {e}")
    
    return []

def main():
    print("获取今日A股跌停股票...")
    limit_down_stocks = get_limit_down_stocks()
    
    if limit_down_stocks:
        print(f"\n📉 今日跌停股票（共{len(limit_down_stocks)}只）：")
        for stock in limit_down_stocks:
            print(f"  {stock['code']} {stock['name']} {stock['price']:.2f} ({stock['pct_chg']:+.2f}%)")
    else:
        print("今日暂无跌停股票或无法获取数据")

if __name__ == "__main__":
    main()