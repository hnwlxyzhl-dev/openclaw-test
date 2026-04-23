#!/usr/bin/env python3.11
"""
简化版财报监控测试
"""

import json
from datetime import date

# 模拟数据，用于测试输出
result = {
    "date": date.today().strftime("%Y-%m-%d"),
    "total": 5,
    "type1_count": 2,
    "type2_count": 3,
    "type2_reports": [
        {
            "code": "600519",
            "name": "贵州茅台",
            "type": "业绩预告",
            "revenue_change": 15.2,
            "profit_change": 20.5,
            "revenue_change_str": "15.2%",
            "profit_change_str": "20.5%",
            "market": "A股",
            "source": "tushare"
        },
        {
            "code": "002637",
            "name": "赞宇科技",
            "type": "业绩快报",
            "revenue_change": 12.8,
            "profit_change": 18.3,
            "revenue_change_str": "12.8%",
            "profit_change_str": "18.3%",
            "market": "A股",
            "source": "akshare"
        },
        {
            "code": "300750",
            "name": "宁德时代",
            "type": "年度报告",
            "revenue_change": 35.6,
            "profit_change": 42.1,
            "revenue_change_str": "35.6%",
            "profit_change_str": "42.1%",
            "market": "A股",
            "source": "akshare_notice"
        }
    ],
    "has_reports": True,
    "summary": """• 贵州茅台(600519) - 业绩预告 | 营收+15.2% | 净利+20.5%
• 赞宇科技(002637) - 业绩快报 | 营收+12.8% | 净利+18.3%
• 宁德时代(300750) - 年度报告 | 营收+35.6% | 净利+42.1%"""
}

print(json.dumps(result, ensure_ascii=False, indent=2))