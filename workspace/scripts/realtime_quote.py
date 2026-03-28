#!/usr/bin/env python3
"""
实时股价查询工具
使用 tushare 的 get_realtime_quotes 接口获取A股实时行情

用法：
    python realtime_quote.py 002637           # 单只股票
    python realtime_quote.py 002637,600519    # 多只股票
    python realtime_quote.py --json 002637    # JSON输出
"""

import sys
import json
import tushare as ts
import pandas as pd


def get_realtime_quote(codes):
    """
    获取实时行情数据
    
    Args:
        codes: 股票代码，可以是字符串或列表
               - "002637" 单只
               - "002637,600519" 多只用逗号分隔
               - ["002637", "600519"] 列表
    
    Returns:
        list: 行情数据列表，每个元素是一个字典
    """
    if isinstance(codes, list):
        code_list = codes
    else:
        code_list = [c.strip() for c in codes.split(",") if c.strip()]
    
    # 逐个查询避免 tushare 多股票查询的 bug
    all_quotes = []
    for code in code_list:
        try:
            df = ts.get_realtime_quotes(code)
            if df is not None and len(df) > 0:
                all_quotes.append(df)
        except Exception as e:
            print(f"查询 {code} 出错: {e}", file=sys.stderr)
    
    if not all_quotes:
        return []
    
    df = pd.concat(all_quotes, ignore_index=True)
    
    if df is None or len(df) == 0:
        return []
    
    result = []
    for _, row in df.iterrows():
        price = float(row['price']) if row['price'] else 0
        pre_close = float(row['pre_close']) if row['pre_close'] else 0
        pct_chg = ((price - pre_close) / pre_close * 100) if pre_close > 0 else 0
        
        result.append({
            'code': row['code'],
            'name': row['name'],
            'price': price,
            'open': float(row['open']) if row['open'] else 0,
            'high': float(row['high']) if row['high'] else 0,
            'low': float(row['low']) if row['low'] else 0,
            'pre_close': pre_close,
            'pct_chg': round(pct_chg, 2),
            'volume': int(row['volume']) if row['volume'] else 0,
            'amount': float(row['amount']) if row['amount'] else 0,
            'date': row['date'],
            'time': row['time'],
            'is_limit_down': pct_chg <= -9.9,  # 是否跌停
            'is_limit_up': pct_chg >= 9.9,     # 是否涨停
        })
    
    return result


def print_quote(quotes):
    """格式化打印行情"""
    if not quotes:
        print("无数据")
        return
    
    for q in quotes:
        # 涨跌状态
        if q['is_limit_down']:
            status = "⬇️ 跌停"
        elif q['is_limit_up']:
            status = "⬆️ 涨停"
        elif q['pct_chg'] < 0:
            status = "📉 下跌"
        elif q['pct_chg'] > 0:
            status = "📈 上涨"
        else:
            status = "➡️ 平盘"
        
        print(f"\n{q['name']}({q['code']}) {status}")
        print(f"  现价: {q['price']:.2f}  涨跌幅: {q['pct_chg']:+.2f}%")
        print(f"  今开: {q['open']:.2f}  最高: {q['high']:.2f}  最低: {q['low']:.2f}")
        print(f"  昨收: {q['pre_close']:.2f}")
        print(f"  成交量: {q['volume']:,}  成交额: {q['amount']:,.0f}")
        print(f"  时间: {q['date']} {q['time']}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = [a for a in sys.argv[1:] if a.startswith("-")]
    
    if not args:
        print(__doc__)
        sys.exit(1)
    
    codes = args[0]
    output_json = "--json" in flags or "-j" in flags
    
    quotes = get_realtime_quote(codes)
    
    if output_json:
        print(json.dumps(quotes, ensure_ascii=False, indent=2))
    else:
        print_quote(quotes)


if __name__ == "__main__":
    main()
