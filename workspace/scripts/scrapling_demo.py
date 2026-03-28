#!/usr/bin/env python3.11
"""
Scrapling 网页抓取工具

用法：
    python3.11 scrapling_demo.py <URL>
    python3.11 scrapling_demo.py https://example.com

特点：
    - 反检测能力强，可绑过 Cloudflare
    - 语义化查找元素
    - 支持 JavaScript 渲染的页面
"""

import sys
from scrapling import StealthyFetcher


def fetch_page(url: str):
    """抓取网页并返回结构化数据"""
    fetcher = StealthyFetcher()
    page = fetcher.fetch(url)
    
    return {
        'url': page.url,
        'status': page.status,
        'title': page.css("title")[0].text if page.css("title") else None,
        'body_text': page.css("body")[0].get_all_text()[:500] if page.css("body") else None,
        'html': page.html_content[:2000] if hasattr(page, 'html_content') else None,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"正在抓取: {url}\n")
    
    result = fetch_page(url)
    
    print(f"状态码: {result['status']}")
    print(f"标题: {result['title']}")
    print(f"\n内容预览:\n{result['body_text'][:300]}...")


if __name__ == "__main__":
    main()
