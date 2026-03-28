#!/usr/bin/env python3
"""
通用网页爬虫工具
功能：
1. 通用网页爬取 (requests + BeautifulSoup)
2. 财经数据 (使用 tushare)
3. JSON API 获取

注意：服务器环境可能限制部分外网访问
"""

import os
import sys
import json
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# 尝试导入 tushare
try:
    import tushare as ts
    TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')
    if TUSHARE_TOKEN:
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
    else:
        pro = None
except ImportError:
    pro = None

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 会话
session = requests.Session()
session.headers.update(HEADERS)


def fetch_page(url, timeout=30, encoding=None):
    """获取网页内容"""
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        if encoding:
            resp.encoding = encoding
        else:
            resp.encoding = resp.apparent_encoding or 'utf-8'
        return {'success': True, 'html': resp.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def parse_html(html, selector=None, attr=None):
    """
    解析 HTML，提取内容
    selector: CSS 选择器
    attr: 要提取的属性，None 表示提取文本
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        if not selector:
            # 移除脚本和样式
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            return soup.get_text(separator='\n', strip=True)
        
        elements = soup.select(selector)
        results = []
        
        for el in elements:
            if attr:
                results.append(el.get(attr, ''))
            else:
                results.append(el.get_text(strip=True))
        
        return results
    except Exception as e:
        return {'error': str(e)}


def extract_links(html, base_url=None, pattern=None):
    """提取页面中的所有链接"""
    soup = BeautifulSoup(html, 'lxml')
    links = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if base_url:
            href = urljoin(base_url, href)
        text = a.get_text(strip=True)
        if pattern:
            if re.search(pattern, href):
                links.append({'url': href, 'text': text})
        else:
            links.append({'url': href, 'text': text})
    
    return links


def extract_images(html, base_url=None):
    """提取页面中的所有图片"""
    soup = BeautifulSoup(html, 'lxml')
    images = []
    
    for img in soup.find_all('img', src=True):
        src = img['src']
        if base_url:
            src = urljoin(base_url, src)
        images.append({
            'url': src,
            'alt': img.get('alt', ''),
        })
    
    return images


def fetch_json_api(url, params=None, headers=None):
    """获取 JSON API 数据"""
    try:
        req_headers = HEADERS.copy()
        if headers:
            req_headers.update(headers)
        
        resp = session.get(url, params=params, headers=req_headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def extract_article(html):
    """提取文章内容（智能提取正文）"""
    soup = BeautifulSoup(html, 'lxml')
    
    # 移除干扰元素
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
        tag.decompose()
    
    # 尝试常见的文章容器
    article_selectors = [
        'article',
        '.article-content',
        '.post-content',
        '.entry-content',
        '.content',
        '#content',
        '.main-content',
    ]
    
    for selector in article_selectors:
        article = soup.select_one(selector)
        if article:
            # 提取标题
            title = soup.select_one('h1')
            title_text = title.get_text(strip=True) if title else ''
            
            # 提取正文
            content = article.get_text(separator='\n', strip=True)
            
            return {
                'title': title_text,
                'content': content,
            }
    
    # 如果没找到，返回整个页面文本
    return {
        'title': '',
        'content': soup.get_text(separator='\n', strip=True)[:5000],
    }


# ============ Tushare 财经数据 ============

def get_stock_a(code, days=30):
    """获取 A 股行情"""
    if not pro:
        return {'error': 'Tushare 未配置'}
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    try:
        df = pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
        if df.empty:
            return {'error': '未找到数据'}
        return df.sort_values('trade_date', ascending=False).to_dict('records')
    except Exception as e:
        return {'error': str(e)}


def get_stock_hk(code, days=30):
    """获取港股行情"""
    if not pro:
        return {'error': 'Tushare 未配置'}
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    try:
        df = pro.hk_daily(ts_code=code, start_date=start_date, end_date=end_date)
        if df.empty:
            return {'error': '未找到数据'}
        return df.sort_values('trade_date', ascending=False).to_dict('records')
    except Exception as e:
        return {'error': str(e)}


def get_stock_us(code, days=30):
    """获取美股行情"""
    if not pro:
        return {'error': 'Tushare 未配置'}
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    try:
        df = pro.us_daily(ts_code=code, start_date=start_date, end_date=end_date)
        if df.empty:
            return {'error': '未找到数据'}
        return df.sort_values('trade_date', ascending=False).to_dict('records')
    except Exception as e:
        return {'error': str(e)}


def get_index_global(code='IXIC', days=30):
    """获取国际指数"""
    if not pro:
        return {'error': 'Tushare 未配置'}
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    try:
        df = pro.index_global(ts_code=code, start_date=start_date, end_date=end_date)
        if df.empty:
            return {'error': '未找到数据'}
        return df.sort_values('trade_date', ascending=False).to_dict('records')
    except Exception as e:
        return {'error': str(e)}


def get_limit_down(days=5):
    """获取近期跌停股票"""
    if not pro:
        return {'error': 'Tushare 未配置'}
    
    try:
        # 获取最近的交易日
        cal = pro.trade_cal(exchange='SSE', is_open=1, 
                           start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'),
                           end_date=datetime.now().strftime('%Y%m%d'))
        if cal.empty:
            return {'error': '无交易数据'}
        
        trade_date = cal['cal_date'].iloc[-1]
        
        # 获取涨跌停数据
        df = pro.limit_list_d(trade_date=trade_date, limit_type='D')
        if df.empty:
            return {'error': '当日无跌停股票', 'trade_date': trade_date}
        
        return df.to_dict('records')
    except Exception as e:
        return {'error': str(e)}


def get_limit_up(days=5):
    """获取近期涨停股票"""
    if not pro:
        return {'error': 'Tushare 未配置'}
    
    try:
        cal = pro.trade_cal(exchange='SSE', is_open=1,
                           start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'),
                           end_date=datetime.now().strftime('%Y%m%d'))
        if cal.empty:
            return {'error': '无交易数据'}
        
        trade_date = cal['cal_date'].iloc[-1]
        
        df = pro.limit_list_d(trade_date=trade_date, limit_type='U')
        if df.empty:
            return {'error': '当日无涨停股票', 'trade_date': trade_date}
        
        return df.to_dict('records')
    except Exception as e:
        return {'error': str(e)}


# ============ 命令行接口 ============

def print_json(data):
    """格式化输出 JSON"""
    if isinstance(data, list) and len(data) > 10:
        print(json.dumps(data[:10], ensure_ascii=False, indent=2))
        print(f"\n... 共 {len(data)} 条数据")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("""
通用网页爬虫工具 v2.0
====================

用法: python web_crawler.py <命令> [参数]

【通用爬取】
  page <url>                    获取网页内容
  links <url> [pattern]         提取页面链接
  images <url>                  提取页面图片
  article <url>                 智能提取文章内容
  json <url>                    获取 JSON API

【财经数据 (Tushare)】
  stock_a <代码> [天数]         A股行情 (如 000001.SZ)
  stock_hk <代码> [天数]        港股行情 (如 01810.HK)
  stock_us <代码> [天数]        美股行情 (如 AAPL)
  index <代码> [天数]           国际指数 (IXIC/SPX/DJI/HSI)
  limit_down                    跌停板
  limit_up                      涨停板

【指数代码】
  IXIC  - 纳斯达克
  SPX   - 标普500
  DJI   - 道琼斯
  HSI   - 恒生指数
  N225  - 日经225

示例:
  python web_crawler.py page https://example.com
  python web_crawler.py article https://news.sina.com.cn/xxx
  python web_crawler.py stock_a 000001.SZ 30
  python web_crawler.py stock_hk 01810.HK
  python web_crawler.py stock_us AAPL
  python web_crawler.py index IXIC 60
  python web_crawler.py limit_down
""")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    try:
        if cmd == 'page':
            url = sys.argv[2]
            result = fetch_page(url)
            if result['success']:
                text = parse_html(result['html'])
                print(text[:3000])
            else:
                print(f"错误: {result['error']}")
        
        elif cmd == 'links':
            url = sys.argv[2]
            pattern = sys.argv[3] if len(sys.argv) > 3 else None
            result = fetch_page(url)
            if result['success']:
                links = extract_links(result['html'], url, pattern)
                print_json(links[:50])
            else:
                print(f"错误: {result['error']}")
        
        elif cmd == 'images':
            url = sys.argv[2]
            result = fetch_page(url)
            if result['success']:
                images = extract_images(result['html'], url)
                print_json(images)
            else:
                print(f"错误: {result['error']}")
        
        elif cmd == 'article':
            url = sys.argv[2]
            result = fetch_page(url)
            if result['success']:
                article = extract_article(result['html'])
                print(f"标题: {article['title']}\n")
                print(article['content'][:3000])
            else:
                print(f"错误: {result['error']}")
        
        elif cmd == 'json':
            url = sys.argv[2]
            data = fetch_json_api(url)
            print_json(data)
        
        elif cmd == 'stock_a':
            code = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            data = get_stock_a(code, days)
            print_json(data)
        
        elif cmd == 'stock_hk':
            code = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            data = get_stock_hk(code, days)
            print_json(data)
        
        elif cmd == 'stock_us':
            code = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            data = get_stock_us(code, days)
            print_json(data)
        
        elif cmd == 'index':
            code = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            data = get_index_global(code, days)
            print_json(data)
        
        elif cmd == 'limit_down':
            data = get_limit_down()
            print_json(data)
        
        elif cmd == 'limit_up':
            data = get_limit_up()
            print_json(data)
        
        else:
            print(f"未知命令: {cmd}")
    
    except Exception as e:
        print(f"执行错误: {str(e)}")
