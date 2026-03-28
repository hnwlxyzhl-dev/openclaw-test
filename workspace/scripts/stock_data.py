#!/usr/bin/env python3
"""
股票数据获取工具
支持：A股、港股、美股、国际指数
"""

import os
import sys
import json
import tushare as ts
from datetime import datetime, timedelta

# 初始化
TOKEN = os.getenv('TUSHARE_TOKEN')
if not TOKEN:
    print("错误: 未设置 TUSHARE_TOKEN 环境变量")
    sys.exit(1)

pro = ts.pro_api(TOKEN)


def get_us_stock(ts_code, days=30):
    """获取美股行情"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    df = pro.us_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return df.sort_values('trade_date', ascending=False)


def get_hk_stock(ts_code, days=30):
    """获取港股行情"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    df = pro.hk_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return df.sort_values('trade_date', ascending=False)


def get_a_stock(ts_code, days=30):
    """获取A股行情"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return df.sort_values('trade_date', ascending=False)


def get_global_index(ts_code=None, days=30):
    """获取国际指数行情"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    if ts_code:
        df = pro.index_global(ts_code=ts_code, start_date=start_date, end_date=end_date)
    else:
        df = pro.index_global(start_date=start_date, end_date=end_date)
    return df.sort_values('trade_date', ascending=False)


def get_nasdaq(days=30):
    """获取纳斯达克指数"""
    return get_global_index('IXIC', days)


def get_sp500(days=30):
    """获取标普500指数"""
    return get_global_index('SPX', days)


def get_hsi(days=30):
    """获取恒生指数"""
    return get_global_index('HSI', days)


# 指数代码映射
INDEX_CODES = {
    'nasdaq': 'IXIC',      # 纳斯达克
    'sp500': 'SPX',        # 标普500
    'dow': 'DJI',          # 道琼斯
    'hsi': 'HSI',          # 恒生指数
    'nikkei': 'N225',      # 日经225
    'ftse': 'FTSE',        # 英国富时
    'dax': 'GDAXI',        # 德国DAX
}


if __name__ == '__main__':
    # 命令行接口
    if len(sys.argv) < 2:
        print("用法: python stock_data.py <命令> [参数]")
        print("命令:")
        print("  us <代码> [天数]     - 美股行情，如 AAPL")
        print("  hk <代码> [天数]     - 港股行情，如 01810.HK")
        print("  a <代码> [天数]      - A股行情，如 000001.SZ")
        print("  index <名称> [天数]  - 指数行情，如 nasdaq, sp500, hsi")
        print("  indices              - 所有指数列表")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'us':
        code = sys.argv[2] if len(sys.argv) > 2 else 'AAPL'
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        df = get_us_stock(code, days)
        print(df.to_string())
    
    elif cmd == 'hk':
        code = sys.argv[2] if len(sys.argv) > 2 else '01810.HK'
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        df = get_hk_stock(code, days)
        print(df.to_string())
    
    elif cmd == 'a':
        code = sys.argv[2] if len(sys.argv) > 2 else '000001.SZ'
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        df = get_a_stock(code, days)
        print(df.to_string())
    
    elif cmd == 'index':
        name = sys.argv[2].lower() if len(sys.argv) > 2 else 'nasdaq'
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        if name in INDEX_CODES:
            df = get_global_index(INDEX_CODES[name], days)
            print(df.to_string())
        else:
            print(f"未知指数: {name}")
            print(f"支持的指数: {list(INDEX_CODES.keys())}")
    
    elif cmd == 'indices':
        df = get_global_index(days=1)
        print(df.to_string())
    
    else:
        print(f"未知命令: {cmd}")
