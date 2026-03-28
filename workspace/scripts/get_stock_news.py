#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取股票相关新闻
"""
import os
import sys
import tushare as ts
import json

# 读取token
token = os.getenv('TUSHARE_TOKEN') or ts.get_token()
if not token:
    print("错误：未找到TUSHARE_TOKEN，请设置环境变量")
    sys.exit(1)

# 初始化pro接口
pro = ts.pro_api(token)

# 股票代码列表
stocks = [
    ('000533.SZ', '顺钠股份'),
    ('000890.SZ', '法尔胜'),
    ('002796.SZ', '世嘉科技'),
    ('002859.SZ', '洁美科技'),
    ('002961.SZ', '瑞达期货'),
    ('601330.SH', '绿色动力'),
    ('603778.SH', '国晟科技'),
    ('603817.SH', '海峡环保')
]

try:
    # 获取新闻数据
    # 使用major_news接口获取长篇新闻
    df = pro.major_news(
        start_date='20260320',
        end_date='20260327'
    )
    
    if not df.empty:
        # 搜索包含股票名称的新闻
        news_results = {}
        for ts_code, name in stocks:
            # 搜索新闻标题或内容中包含股票名称的
            mask = df['title'].str.contains(name, na=False) | df['content'].str.contains(name, na=False)
            stock_news = df[mask].head(5)
            
            if not stock_news.empty:
                news_list = []
                for _, row in stock_news.iterrows():
                    news_list.append({
                        'title': row['title'],
                        'pub_time': row['pub_time'] if 'pub_time' in row else '',
                        'src': row['src'] if 'src' in row else ''
                    })
                news_results[name] = news_list
        
        print(json.dumps(news_results, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "没有找到新闻数据"}, ensure_ascii=False))

except Exception as e:
    # 如果major_news接口不可用，尝试news接口
    try:
        df = pro.news(
            start_date='20260320',
            end_date='20260327'
        )
        
        if not df.empty:
            news_results = {}
            for ts_code, name in stocks:
                mask = df['title'].str.contains(name, na=False) | df['content'].str.contains(name, na=False)
                stock_news = df[mask].head(5)
                
                if not stock_news.empty:
                    news_list = []
                    for _, row in stock_news.iterrows():
                        news_list.append({
                            'title': row['title'],
                            'datetime': row['datetime'] if 'datetime' in row else ''
                        })
                    news_results[name] = news_list
            
            print(json.dumps(news_results, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "没有找到新闻数据"}, ensure_ascii=False))
    except Exception as e2:
        print(json.dumps({"error": f"获取新闻失败: {str(e)}, {str(e2)}"}, ensure_ascii=False))
