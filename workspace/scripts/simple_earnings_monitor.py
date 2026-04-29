#!/usr/bin/env python3.11
"""
简化版财报监控工具
"""
import sys
import json
from datetime import date

def simple_earnings_monitor():
    """简化的财报监控"""
    today = date.today().strftime("%Y-%m-%d")
    
    # 使用tushare获取数据
    try:
        import tushare as ts
        token = "dde651506e87c13c30474693d2c4091345f987a2b8bfffad4989530c"
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 获取业绩预告
        df_forecast = pro.forecast(ann_date=today)
        if df_forecast is not None and len(df_forecast) > 0:
            type2_reports = []
            for _, row in df_forecast.iterrows():
                profit_change = row.get('p_change_max', None)
                if profit_change and float(profit_change) > 0:
                    type2_reports.append({
                        "code": row['ts_code'].split('.')[0],
                        "name": row.get('ann_name', row['ts_code']),
                        "type": "业绩预告",
                        "profit_change": float(profit_change),
                        "revenue_change": None
                    })
            
            return {
                "date": today,
                "type2_count": len(type2_reports),
                "type2_reports": type2_reports,
                "has_reports": True
            }
    except Exception as e:
        print(f"tushare error: {e}", file=sys.stderr)
    
    # 使用akshare获取数据
    try:
        import akshare as ak
        # 尝试不同的接口名称
        interfaces = [
            ('stock_em_earnings预告', '净利润变动幅度'),
            ('stock_em_yjyg', '净利润变动幅度'),
            ('stock_em_yjyg_detail', '净利润变动幅度'),
            ('stock_em_yjyg_forecast', '净利润变动幅度')
        ]
        
        for interface_name, profit_field in interfaces:
            try:
                df = getattr(ak, interface_name)(date=today)
                if df is not None and len(df) > 0:
                    type2_reports = []
                    for _, row in df.iterrows():
                        profit_change = row.get(profit_field, '')
                        profit_pct = extract_percentage(profit_change)
                        if profit_pct and profit_pct > 0:
                            type2_reports.append({
                                "code": row.get('股票代码', ''),
                                "name": row.get('股票简称', ''),
                                "type": "业绩预告",
                                "profit_change": profit_pct,
                                "revenue_change": None
                            })
                    
                    return {
                        "date": today,
                        "type2_count": len(type2_reports),
                        "type2_reports": type2_reports,
                        "has_reports": True
                    }
            except AttributeError:
                continue
            except Exception as e:
                print(f"akshare {interface_name} error: {e}", file=sys.stderr)
                continue
    except Exception as e:
        print(f"akshare error: {e}", file=sys.stderr)
    
    # 如果都没有数据，返回空结果
    return {
        "date": today,
        "type2_count": 0,
        "type2_reports": [],
        "has_reports": False
    }

def extract_percentage(text):
    """从文本中提取百分比数字"""
    if not text or text == 'nan':
        return None
    text = str(text).replace('%', '').strip()
    numbers = extract_numbers(text)
    if numbers:
        try:
            value = float(numbers[0])
            # 检查是否为下降
            if '降' in text or '跌' in text or '亏损' in text:
                value = -abs(value)
            return value
        except:
            return None
    return None

def extract_numbers(text):
    """提取数字"""
    import re
    return re.findall(r'[-+]?\d+\.?\d*', text)

if __name__ == "__main__":
    result = simple_earnings_monitor()
    print(json.dumps(result, ensure_ascii=False, indent=2))