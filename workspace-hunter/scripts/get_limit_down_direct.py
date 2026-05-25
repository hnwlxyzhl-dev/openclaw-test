#!/usr/bin/env python3.11
import sys
import akshare as ak

def get_today_limit_down():
    """获取今日A股跌停股票列表"""
    try:
        # 获取今日所有A股行情数据
        stock_data = ak.stock_zh_a_spot()
        
        # 筛选跌停股票（跌幅>=-9.99%）
        limit_down_stocks = stock_data[stock_data['涨跌幅'] <= -9.99]
        
        if len(limit_down_stocks) == 0:
            return []
        
        # 格式化返回结果
        result = []
        for _, row in limit_down_stocks.iterrows():
            result.append({
                'code': row['代码'],
                'name': row['名称'],
                'pct_chg': row['涨跌幅'],
                'price': row['最新价'],
                'volume': row['成交量']
            })
        
        return result
        
    except Exception as e:
        print(f"获取跌停股数据失败: {e}")
        return []

if __name__ == "__main__":
    limit_down = get_today_limit_down()
    if limit_down:
        print(f"📉 今日跌停股（共{len(limit_down)}只）:")
        for stock in limit_down:
            print(f"{stock['code']} {stock['name']} 跌幅: {stock['pct_chg']}%")
    else:
        print("📉 今日A股无跌停股票")