#!/usr/bin/env python3.11
"""
简化的财报监控工具 - 不使用tqdm进度条
"""

import sys
import json
import os
import re
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# ============================================================================
# 配置
# ============================================================================

TUSHARE_TOKEN_FILE = Path.home() / ".tushare_token"

def get_tushare_token() -> str:
    """获取 tushare token"""
    if TUSHARE_TOKEN_FILE.exists():
        return TUSHARE_TOKEN_FILE.read_text().strip()
    return None

def extract_percentage(text) -> Optional[float]:
    """从文本中提取百分比数字"""
    if not text or text == 'nan' or text == 'None':
        return None
    
    text = str(text).strip()
    text = text.replace('%', '').strip()
    
    is_negative = '降' in text or '跌' in text or '亏损' in text
    
    numbers = re.findall(r'[-+]?\d+\.?\d*', text)
    
    if numbers:
        try:
            value = float(numbers[0])
            if is_negative and value > 0:
                value = -value
            return value
        except:
            return None
    
    return None

def akshare_get_earnings_reports() -> List[Dict]:
    """获取 A股 业绩预告/快报（东方财富）"""
    try:
        import akshare as ak
        
        reports = []
        today = date.today()
        
        # 1. 业绩预告
        try:
            df_forecast = ak.stock_em_yjyg(date=today.strftime("%Y%m%d"))
            if df_forecast is not None and len(df_forecast) > 0:
                for _, row in df_forecast.iterrows():
                    try:
                        profit_change = row.get('净利润变动幅度', '')
                        revenue_change = row.get('营业收入变动幅度', '')
                        
                        profit_pct = extract_percentage(profit_change)
                        revenue_pct = extract_percentage(revenue_change)
                        
                        reports.append({
                            "code": row.get('股票代码', ''),
                            "name": row.get('股票简称', ''),
                            "type": "业绩预告",
                            "date": today.strftime("%Y-%m-%d"),
                            "period": row.get('报告日期', ''),
                            "revenue_change": revenue_pct,
                            "profit_change": profit_pct,
                            "revenue_change_str": str(revenue_change),
                            "profit_change_str": str(profit_change),
                            "summary": row.get('业绩预告摘要', ''),
                            "market": "A股",
                            "source": "akshare",
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            pass
        
        # 2. 业绩快报
        try:
            df_quick = ak.stock_em_yjkb(date=today.strftime("%Y%m%d"))
            if df_quick is not None and len(df_quick) > 0:
                for _, row in df_quick.iterrows():
                    try:
                        profit_change = row.get('净利润同比增长', '')
                        revenue_change = row.get('营业收入同比增长', '')
                        
                        profit_pct = extract_percentage(profit_change)
                        revenue_pct = extract_percentage(revenue_change)
                        
                        reports.append({
                            "code": row.get('股票代码', ''),
                            "name": row.get('股票简称', ''),
                            "type": "业绩快报",
                            "date": today.strftime("%Y-%m-%d"),
                            "period": row.get('报告期', ''),
                            "revenue_change": revenue_pct,
                            "profit_change": profit_pct,
                            "revenue_change_str": str(revenue_change),
                            "profit_change_str": str(profit_change),
                            "revenue": row.get('营业收入', ''),
                            "profit": row.get('净利润', ''),
                            "market": "A股",
                            "source": "akshare",
                        })
                    except Exception as e:
                        continue
        except Exception as e:
            pass
        
        return reports
    except Exception as e:
        return []

def tushare_get_earnings_forecast() -> List[Dict]:
    """使用 tushare 获取业绩预告"""
    try:
        import tushare as ts
        
        token = get_tushare_token()
        if not token:
            return []
        
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 获取今天的业绩预告
        today = date.today().strftime("%Y%m%d")
        
        df = pro.forecast(ann_date=today)
        
        if df is None or len(df) == 0:
            return []
        
        reports = []
        for _, row in df.iterrows():
            try:
                # 解析净利润变化
                profit_change = row.get('p_change_max', None)
                
                reports.append({
                    "code": row['ts_code'].split('.')[0],
                    "name": row.get('ann_name', row['ts_code']),
                    "type": "业绩预告",
                    "date": today,
                    "period": row.get('end_date', ''),
                    "revenue_change": None,  # 预告通常没有营收数据
                    "profit_change": float(profit_change) if profit_change else None,
                    "revenue_change_str": "N/A",
                    "profit_change_str": f"{profit_change}%" if profit_change else "N/A",
                    "summary": row.get('summary', ''),
                    "market": "A股",
                    "source": "tushare",
                })
            except Exception as e:
                continue
        
        return reports
    except Exception as e:
        return []

def tushare_get_earnings_express() -> List[Dict]:
    """使用 tushare 获取业绩快报"""
    try:
        import tushare as ts
        
        token = get_tushare_token()
        if not token:
            return []
        
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 获取今天的业绩快报
        today = date.today().strftime("%Y%m%d")
        
        df = pro.express(ann_date=today)
        
        if df is None or len(df) == 0:
            return []
        
        reports = []
        for _, row in df.iterrows():
            try:
                # 计算同比增长率
                revenue = row.get('revenue', 0)
                revenue_yoy = row.get('or_growth_yoy', None)
                profit = row.get('profit', 0)
                profit_yoy = row.get('op_yoy', None)
                
                reports.append({
                    "code": row['ts_code'].split('.')[0],
                    "name": row.get('ann_name', row['ts_code']),
                    "type": "业绩快报",
                    "date": today,
                    "period": row.get('end_date', ''),
                    "revenue": float(revenue) if revenue else None,
                    "profit": float(profit) if profit else None,
                    "revenue_change": float(revenue_yoy) if revenue_yoy else None,
                    "profit_change": float(profit_yoy) if profit_yoy else None,
                    "revenue_change_str": f"{revenue_yoy:.2f}%" if revenue_yoy else "N/A",
                    "profit_change_str": f"{profit_yoy:.2f}%" if profit_yoy else "N/A",
                    "market": "A股",
                    "source": "tushare",
                })
            except Exception as e:
                continue
        
        return reports
    except Exception as e:
        return []

def deduplicate_reports(reports: List[Dict]) -> List[Dict]:
    """去重：同一只股票可能有多个数据源"""
    seen = {}
    
    for report in reports:
        code = report.get('code', '')
        if not code:
            continue
        
        source = report.get('source', '')
        
        # 如果已存在，检查优先级
        if code in seen:
            existing_source = seen[code].get('source', '')
            
            # tushare 优先级最高
            if source == 'tushare':
                seen[code] = report
            # akshare 次之
            elif source == 'akshare' and existing_source != 'tushare':
                seen[code] = report
        else:
            seen[code] = report
    
    return list(seen.values())

def classify_reports(reports: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """分类财报"""
    type1 = []  # 营收或净利润同比下降
    type2 = []  # 营收和净利润同比都增长
    
    for report in reports:
        revenue_change = report.get('revenue_change')
        profit_change = report.get('profit_change')
        
        # 如果没有数据，跳过
        if revenue_change is None and profit_change is None:
            continue
        
        # 分类
        if revenue_change is not None and profit_change is not None:
            if revenue_change > 0 and profit_change > 0:
                type2.append(report)
            else:
                type1.append(report)
        elif profit_change is not None:
            if profit_change > 0:
                type2.append(report)
            else:
                type1.append(report)
        elif revenue_change is not None:
            if revenue_change > 0:
                type2.append(report)
            else:
                type1.append(report)
    
    return type1, type2

def monitor_earnings_simple() -> Dict:
    """简化的财报监控"""
    today = date.today().strftime("%Y-%m-%d")
    
    all_reports = []
    
    # 1. Tushare 数据源
    all_reports.extend(tushare_get_earnings_forecast())
    all_reports.extend(tushare_get_earnings_express())
    
    # 2. Akshare 数据源
    all_reports.extend(akshare_get_earnings_reports())
    
    # 去重
    all_reports = deduplicate_reports(all_reports)
    
    # 分类
    type1, type2 = classify_reports(all_reports)
    
    return {
        "date": today,
        "total": len(all_reports),
        "type1_count": len(type1),
        "type2_count": len(type2),
        "type2_reports": type2,
        "has_reports": len(all_reports) > 0,
    }

if __name__ == "__main__":
    result = monitor_earnings_simple()
    print(json.dumps(result, ensure_ascii=False, indent=2))