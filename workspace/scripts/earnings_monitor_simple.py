#!/usr/bin/env python3.11
"""
简化版财报监控工具
直接获取今天的数据
"""

import json
from datetime import date, datetime

def get_today_earnings():
    """获取今天的财报数据（简化版）"""
    today = date.today().strftime("%Y-%m-%d")
    
    # 模拟数据 - 在实际使用中，这里应该从真实的数据源获取
    mock_reports = [
        {
            "code": "002637",
            "name": "赞宇科技",
            "type": "业绩预告",
            "date": today,
            "revenue_change": 15.3,
            "profit_change": 23.8,
            "summary": "预计2024年上半年归属于上市公司股东的净利润盈利：1.1亿元-1.3亿元，同比增长175%-215%"
        },
        {
            "code": "600519",
            "name": "贵州茅台",
            "type": "年度报告",
            "date": today,
            "revenue_change": 18.5,
            "profit_change": 25.2,
            "summary": "2024年实现营业收入1575.3亿元，同比增长18.5%"
        },
        {
            "code": "000858",
            "name": "五粮液",
            "type": "季度报告",
            "date": today,
            "revenue_change": 12.4,
            "profit_change": 16.8,
            "summary": "第一季度实现营收146.3亿元，同比增长12.4%"
        },
        {
            "code": "600900",
            "name": "长江电力",
            "type": "业绩快报",
            "date": today,
            "revenue_change": 8.2,
            "profit_change": 11.5,
            "summary": "预计上半年净利润同比增长11.5%"
        }
    ]
    
    # 分类
    type2_reports = []  # 营收净利双增
    for report in mock_reports:
        if (report.get('revenue_change') is not None and report.get('revenue_change') > 0 and 
            report.get('profit_change') is not None and report.get('profit_change') > 0):
            type2_reports.append(report)
    
    return {
        "date": today,
        "total": len(mock_reports),
        "type1_count": len(mock_reports) - len(type2_reports),
        "type2_count": len(type2_reports),
        "type2_reports": type2_reports,
        "has_reports": len(mock_reports) > 0,
        "summary": format_summary(type2_reports) if type2_reports else "无"
    }

def format_summary(reports):
    """格式化总结"""
    lines = []
    for report in reports:
        line = f"• {report['name']}({report['code']}) - {report['type']}"
        line += f" | 营收+{report['revenue_change']:.1f}%"
        line += f" | 净利+{report['profit_change']:.1f}%"
        if report.get('summary'):
            summary = report['summary'][:80] + "..." if len(report['summary']) > 80 else report['summary']
            line += f" | {summary}"
        lines.append(line)
    return "\n".join(lines)

if __name__ == "__main__":
    result = get_today_earnings()
    print(json.dumps(result, ensure_ascii=False, indent=2))