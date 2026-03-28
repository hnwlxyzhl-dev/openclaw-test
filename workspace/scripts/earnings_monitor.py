#!/usr/bin/env python3.11
"""
财报监控工具

功能：
1. 检索当天发布的 A股和港股财报/预告/快报
2. 分类：
   - 第一类：营收或净利润同比下降的
   - 第二类：营收和净利润同比都增长的
3. 只输出第二类的总结

数据源优先级：
1. tushare（财报/快报/预告）
2. akshare 东方财富接口（预告/快报）
3. 东方财富爬虫（补充）

使用方法：
    python3.11 scripts/earnings_monitor.py
    python3.11 scripts/earnings_monitor.py --json
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


# ============================================================================
# 数据源1: Tushare（财报/快报/预告）
# ============================================================================

def tushare_get_earnings_forecast() -> List[Dict]:
    """
    使用 tushare 获取业绩预告
    
    接口：forecast
    """
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
        print(f"tushare forecast error: {e}", file=sys.stderr)
        return []


def tushare_get_earnings_express() -> List[Dict]:
    """
    使用 tushare 获取业绩快报
    
    接口：express
    """
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
        print(f"tushare express error: {e}", file=sys.stderr)
        return []


def tushare_get_income_statement() -> List[Dict]:
    """
    使用 tushare 获取正式财报
    
    注：正式财报数据通常已在预告/快报中体现，此接口作为补充
    """
    # tushare 的 disclosure 接口需要高级权限，暂时跳过
    # 预告和快报已经覆盖了大部分情况
    return []


# ============================================================================
# 数据源2: Akshare 东方财富接口（预告/快报/财报公告）
# ============================================================================

def akshare_get_earnings_reports() -> List[Dict]:
    """
    获取 A股 业绩预告/快报（东方财富）
    """
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


def akshare_get_formal_reports() -> List[Dict]:
    """
    获取 A股 正式财报公告（年度报告/季度报告/半年度报告）
    
    并查询对应的财务数据（营收同比、净利润同比）
    """
    try:
        import akshare as ak
        import tushare as ts
        
        reports = []
        today = date.today()
        
        # 获取当天公告
        try:
            df = ak.stock_notice_report(symbol="全部", date=today.strftime("%Y%m%d"))
            if df is None or len(df) == 0:
                return []
            
            # 筛选正式财报（排除预告、快报）
            keywords = ['年度报告', '季度报告', '半年度报告']
            exclude_keywords = ['预告', '快报', '摘要', '说明会', '进展', '修订']
            
            for _, row in df.iterrows():
                title = str(row.get('公告标题', ''))
                
                # 必须包含财报关键词
                if not any(kw in title for kw in keywords):
                    continue
                
                # 排除非正式财报
                if any(kw in title for kw in exclude_keywords):
                    continue
                
                code = row.get('代码', '')
                name = row.get('名称', '')
                
                # 确定报告类型和期间
                report_type = "财报"
                period = None
                
                if '年度报告' in title and '半年度' not in title:
                    report_type = "年度报告"
                    period = f"{today.year - 1}1231"  # 去年年报
                elif '半年度报告' in title:
                    report_type = "半年度报告"
                    period = f"{today.year - 1}0630" if today.month < 8 else f"{today.year}0630"
                elif '一季度' in title or '第一季度' in title:
                    report_type = "一季报"
                    period = f"{today.year}0331"
                elif '三季度' in title or '第三季度' in title:
                    report_type = "三季报"
                    period = f"{today.year}0931"
                elif '半年度' not in title and '季度' in title:
                    report_type = "季报"
                    # 根据月份推断
                    if today.month <= 5:
                        period = f"{today.year}0331"
                    elif today.month <= 9:
                        period = f"{today.year}0630"
                    else:
                        period = f"{today.year}0931"
                
                # 查询财务数据
                revenue_change = None
                profit_change = None
                
                if period and code:
                    try:
                        # 获取 tushare token
                        token = get_tushare_token()
                        if token:
                            ts.set_token(token)
                            pro = ts.pro_api()
                            
                            # 确定市场
                            market = 'SH' if code.startswith('6') else 'SZ' if code.startswith(('0', '3')) else 'BJ'
                            ts_code = f"{code}.{market}"
                            
                            # 查询财务指标
                            df_fina = pro.fina_indicator(ts_code=ts_code, period=period, fields='ts_code,tr_yoy,or_yoy,netprofit_yoy')
                            
                            if df_fina is not None and len(df_fina) > 0:
                                r = df_fina.iloc[0]
                                # tr_yoy = 营收同比, or_yoy = 营业收入同比, netprofit_yoy = 净利润同比
                                revenue_change = r.get('tr_yoy', r.get('or_yoy', None))
                                profit_change = r.get('netprofit_yoy', None)
                                
                                if revenue_change is not None and str(revenue_change) != 'nan':
                                    revenue_change = float(revenue_change)
                                else:
                                    revenue_change = None
                                
                                if profit_change is not None and str(profit_change) != 'nan':
                                    profit_change = float(profit_change)
                                else:
                                    profit_change = None
                    except Exception as e:
                        pass
                
                reports.append({
                    "code": code,
                    "name": name,
                    "type": report_type,
                    "date": today.strftime("%Y-%m-%d"),
                    "title": title,
                    "url": row.get('网址', ''),
                    "market": "A股",
                    "revenue_change": revenue_change,
                    "profit_change": profit_change,
                    "revenue_change_str": f"{revenue_change:.1f}%" if revenue_change is not None else "N/A",
                    "profit_change_str": f"{profit_change:.1f}%" if profit_change is not None else "N/A",
                    "source": "akshare_notice",
                })
        except Exception as e:
            print(f"akshare notice error: {e}", file=sys.stderr)
        
        return reports
    except Exception as e:
        return []


def akshare_get_hk_reports() -> List[Dict]:
    """
    获取港股财报
    """
    try:
        import akshare as ak
        
        reports = []
        today = date.today()
        
        # 港股业绩公告
        try:
            df = ak.stock_hk_announcement()
            if df is not None and len(df) > 0:
                # 筛选今天的业绩公告
                today_str = today.strftime("%Y-%m-%d")
                today_reports = df[df['公告日期'].str.contains(today_str, na=False)]
                
                for _, row in today_reports.iterrows():
                    title = str(row.get('公告标题', ''))
                    # 只关注业绩相关的公告
                    if any(kw in title for kw in ['业绩', '财务', '盈利', '亏损', '收益', '财报', '全年业绩', '中期业绩']):
                        reports.append({
                            "code": row.get('证券代码', ''),
                            "name": row.get('证券简称', ''),
                            "type": "业绩公告",
                            "date": today_str,
                            "title": title,
                            "market": "港股",
                            "revenue_change": None,
                            "profit_change": None,
                            "source": "akshare",
                        })
        except Exception as e:
            pass
        
        return reports
    except Exception as e:
        return []


# ============================================================================
# 数据源3: 东方财富爬虫（补充）
# ============================================================================

def eastmoney_crawl_earnings() -> List[Dict]:
    """
    使用东方财富爬虫获取财报（兜底）
    """
    try:
        from scrapling import StealthyFetcher
        import json as json_module
        
        reports = []
        today = date.today()
        fetcher = StealthyFetcher()
        
        # 东方财富业绩预告 API
        api_url = f"https://datainterface.eastmoney.com/EM_DataCenter/JS.aspx?type=SR&sty=YJYG&fd={today.strftime('%Y-%m-%d')}&st=2&sr=1&p=1&ps=500"
        
        try:
            page = fetcher.fetch(api_url)
            text = page.css("body")[0].get_all_text()
            
            # 解析数据
            if text and text != 'null':
                # 提取数据
                matches = re.findall(r'"([^"]*)"', text)
                for match in matches[:100]:  # 限制数量
                    parts = match.split(',')
                    if len(parts) >= 6:
                        try:
                            code = parts[1] if len(parts) > 1 else ''
                            name = parts[2] if len(parts) > 2 else ''
                            
                            if code and name:
                                reports.append({
                                    "code": code,
                                    "name": name,
                                    "type": "业绩预告",
                                    "date": today.strftime("%Y-%m-%d"),
                                    "market": "A股",
                                    "source": "eastmoney_crawl",
                                })
                        except:
                            continue
        except Exception as e:
            pass
        
        return reports
    except Exception as e:
        return []


# ============================================================================
# 工具函数
# ============================================================================

def extract_percentage(text) -> Optional[float]:
    """
    从文本中提取百分比数字
    """
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


def deduplicate_reports(reports: List[Dict]) -> List[Dict]:
    """
    去重：同一只股票可能有多个数据源
    优先级：tushare > akshare > eastmoney_crawl
    """
    seen = {}  # code -> report
    
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
            elif source == 'akshare' and existing_source == 'eastmoney_crawl':
                seen[code] = report
        else:
            seen[code] = report
    
    return list(seen.values())


def classify_reports(reports: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    分类财报
    
    返回：(第一类-下降的, 第二类-双增长的)
    """
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


def format_summary(reports: List[Dict]) -> str:
    """
    格式化总结
    """
    if not reports:
        return "无"
    
    lines = []
    for report in reports:
        line = f"• {report['name']}({report['code']}) - {report['type']}"
        
        if report.get('revenue_change') is not None:
            revenue_sign = "+" if report['revenue_change'] > 0 else ""
            line += f" | 营收{revenue_sign}{report['revenue_change']:.1f}%"
        
        if report.get('profit_change') is not None:
            profit_sign = "+" if report['profit_change'] > 0 else ""
            line += f" | 净利{profit_sign}{report['profit_change']:.1f}%"
        
        if report.get('summary'):
            line += f" | {report['summary'][:50]}"
        
        lines.append(line)
    
    return "\n".join(lines)


# ============================================================================
# 主函数
# ============================================================================

def monitor_earnings() -> Dict:
    """
    主函数：监控当日财报
    
    Returns:
        {
            "date": "2026-03-22",
            "total": 10,
            "type1_count": 6,
            "type2_count": 4,
            "type2_reports": [...],
            "has_reports": True,
        }
    """
    today = date.today().strftime("%Y-%m-%d")
    
    all_reports = []
    
    # 1. Tushare 数据源
    print("📊 正在获取 tushare 数据...", file=sys.stderr)
    all_reports.extend(tushare_get_earnings_forecast())
    all_reports.extend(tushare_get_earnings_express())
    all_reports.extend(tushare_get_income_statement())
    
    # 2. Akshare 数据源
    print("📊 正在获取 akshare 数据...", file=sys.stderr)
    all_reports.extend(akshare_get_earnings_reports())
    all_reports.extend(akshare_get_formal_reports())  # 正式财报（含财务数据）
    all_reports.extend(akshare_get_hk_reports())
    
    # 3. 东方财富爬虫（兜底）
    print("📊 正在获取东方财富爬虫数据...", file=sys.stderr)
    all_reports.extend(eastmoney_crawl_earnings())
    
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
        "summary": format_summary(type2) if type2 else "无",
    }


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="财报监控工具")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    args = parser.parse_args()
    
    result = monitor_earnings()
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n📅 {result['date']} 财报监控报告\n")
        print(f"📊 统计：共{result['total']}家公司发布财报/预告/快报")
        print(f"   - 营收或净利下降：{result['type1_count']}家")
        print(f"   - 营收净利双增：{result['type2_count']}家\n")
        
        if result['type2_count'] > 0:
            print("✅ 【营收净利双增的公司】\n")
            print(result['summary'])
        else:
            if result['has_reports']:
                print("ℹ️ 今天有财报发布，但没有营收净利双增的公司")
            else:
                print("ℹ️ 今天没有公司发布财报/预告/快报")


if __name__ == "__main__":
    main()
