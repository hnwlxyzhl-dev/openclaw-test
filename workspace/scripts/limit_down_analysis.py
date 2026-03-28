#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今日A股跌停股票分析脚本
"""

import os
import sys
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
import json
import time

# 设置Tushare token
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

def get_latest_limit_down():
    """获取最近交易日跌停股票列表"""
    try:
        # 获取最近交易日的股票数据，通过涨跌幅判断跌停
        today = datetime.now()
        
        # 尝试获取最近几天的数据
        for i in range(3):
            trade_date = (today - timedelta(days=i)).strftime('%Y%m%d')
            
            try:
                # 获取每日指标数据
                df = pro.daily_basic(trade_date=trade_date)
                
                if not df.empty:
                    # 筛选跌停股票（涨跌幅<=-9.8%或>=9.8%，视具体股票而定）
                    limit_down_stocks = df[df['pct_chg'] <= -9.8][['ts_code', 'name', 'pct_chg']]
                    
                    if not limit_down_stocks.empty:
                        # 获取股票基本信息
                        stock_basic = pro.stock_basic()
                        limit_down_stocks = pd.merge(limit_down_stocks, stock_basic[['ts_code', 'name']], on=['ts_code', 'name'], how='left')
                        
                        print(f"最近交易日跌停股票数量: {len(limit_down_stocks)} (日期: {trade_date})")
                        return limit_down_stocks
                        
            except Exception as e:
                print(f"获取{trade_date}数据失败: {e}")
                continue
        
        print(f"最近几日没有跌停数据")
        return pd.DataFrame()
        
        if df.empty:
            print(f"今日({today})没有涨跌停数据")
            return pd.DataFrame()
        
        # 筛选跌停股票
        limit_down_stocks = df[df['limit_type'] == '跌停'][['ts_code', 'name']]
        
        print(f"今日跌停股票数量: {len(limit_down_stocks)}")
        return limit_down_stocks
        
    except Exception as e:
        print(f"获取跌停股票数据失败: {e}")
        return []

def search_news(stock_code, stock_name):
    """搜索股票相关新闻"""
    try:
        # 搜索新闻
        news_df = pro.news(ts_code=stock_code, start_date=datetime.now().strftime('%Y%m%d'), 
                         end_date=datetime.now().strftime('%Y%m%d'))
        
        if news_df.empty:
            return []
        
        # 简化新闻数据
        news_list = []
        for _, news in news_df.iterrows():
            news_list.append({
                'title': news.get('title', ''),
                'content': news.get('content', '')[:200],
                'time': news.get('created_at', '')
            })
        
        return news_list
        
    except Exception as e:
        print(f"搜索{stock_code}新闻失败: {e}")
        return []

def search_announcements(stock_code):
    """搜索股票相关公告"""
    try:
        # 搜索公告
        ann_df = pro.anns_d(ts_code=stock_code, start_date=datetime.now().strftime('%Y%m%d'), 
                           end_date=datetime.now().strftime('%Y%m%d'))
        
        if ann_df.empty:
            return []
        
        # 简化公告数据
        ann_list = []
        for _, ann in ann_df.iterrows():
            ann_list.append({
                'title': ann.get('title', ''),
                'type': ann.get('ann_type', ''),
                'time': ann.get('ann_time', '')
            })
        
        return ann_list
        
    except Exception as e:
        print(f"搜索{stock_code}公告失败: {e}")
        return []

def classify_reason(stock_code, stock_name, news, announcements):
    """分析跌停原因并分类"""
    reasons = []
    
    # 分析新闻和公告内容
    all_text = ""
    if news:
        for n in news:
            all_text += n['title'] + " " + n['content'] + " "
    
    if announcements:
        for a in announcements:
            all_text += a['title'] + " "
    
    # 基于关键词分析
    text_lower = all_text.lower()
    
    # A. 意外事件 - 需重点识别
    accident_keywords = ['事故', '火灾', '爆炸', '伤亡', '停产', '关闭', '破产', '重组', '被立案', '调查', '处罚', '警告', '欺诈', '造假', '违规', '违法']
    legal_keywords = ['诉讼', '纠纷', '官司', '法院', '判决', '赔偿', '债务违约', '违约']
    emergency_keywords = ['突发', '紧急', '意外', '黑天鹅', '重大利空']
    
    accident_reasons = []
    if any(keyword in text_lower for keyword in accident_keywords):
        accident_reasons.append("突发事故/监管处罚")
    if any(keyword in text_lower for keyword in legal_keywords):
        accident_reasons.append("法律纠纷")
    if any(keyword in text_lower for keyword in emergency_keywords):
        accident_reasons.append("黑天鹅事件")
    
    if accident_reasons:
        return 'A.意外事件', accident_reasons
    
    # B. 基本面变差
    fundamental_keywords = ['亏损', '业绩下滑', '净利润下降', '收入下降', '裁员', '降薪', '产能过剩', '需求下降', '营收减少']
    if any(keyword in text_lower for keyword in fundamental_keywords):
        return 'B.基本面变差', ['业绩下滑/亏损']
    
    # C. 股价回调 - 前期涨幅过大
    no_news_no_announcement = not news and not announcements
    if no_news_no_announcement:
        return 'C.股价回调', ['前期涨幅过大']
    
    # D. 其他原因
    return 'D.其他原因', ['市场情绪/行业调整']

def main():
    print(f"开始分析A股跌停股票 - {datetime.now().strftime('%Y-%m-%d')}")
    
    # 获取最近交易日跌停股票
    limit_down_stocks = get_latest_limit_down()
    
    if not limit_down_stocks.empty:
        analysis_results = []
        
        for _, stock in limit_down_stocks.iterrows():
            stock_code = stock['ts_code']
            stock_name = stock['name']
            
            print(f"\n分析股票: {stock_name} ({stock_code})")
            
            # 搜索相关新闻和公告
            news = search_news(stock_code, stock_name)
            announcements = search_announcements(stock_code)
            
            # 分析跌停原因
            category, reasons = classify_reason(stock_code, stock_name, news, announcements)
            
            result = {
                '股票代码': stock_code,
                '股票名称': stock_name,
                '分类': category,
                '原因': reasons,
                '新闻数量': len(news),
                '公告数量': len(announcements)
            }
            
            analysis_results.append(result)
            
            # 避免API调用过于频繁
            time.sleep(1)
        
        # 按分类整理结果
        category_results = {'A.意外事件': [], 'B.基本面变差': [], 'C.股价回调': [], 'D.其他原因': []}
        
        for result in analysis_results:
            category = result['分类']
            category_results[category].append(result)
        
        return category_results
    
    return None

if __name__ == "__main__":
    main()