#!/usr/bin/env python3
"""
Exa API 搜索工具 — 语义搜索 + 全文提取
免费版：20,000次/月，无需信用卡
文档：https://docs.exa.ai
"""

import requests
import json
import sys
import argparse

EXA_API_KEY = "4a7d2210-24ce-4ef0-9c02-0a46ba5d7a7b"
EXA_BASE_URL = "https://api.exa.ai"

HEADERS = {
    "x-api-key": EXA_API_KEY,
    "Content-Type": "application/json"
}


def search(query, num_results=5, category=None, start_date=None, end_date=None,
           include_text=False, include_summary=False, type="auto"):
    """
    语义搜索
    
    Args:
        query: 搜索关键词
        num_results: 返回结果数 (1-10)
        category: 专用索引类别，如 "financial report", "news", "research paper"
        start_date: 发布日期起始 (YYYY-MM-DD)
        end_date: 发布日期截止 (YYYY-MM-DD)
        include_text: 是否返回全文内容
        include_summary: 是否返回AI摘要
        type: "auto" (自动选择 neural/keyword) 或 "neural" 或 "keyword"
    
    Returns:
        list[dict]: 搜索结果
    """
    payload = {
        "query": query,
        "numResults": num_results,
        "type": type,
    }
    
    if category:
        payload["category"] = category
    if start_date:
        payload["startPublishedDate"] = f"{start_date}T00:00:00.000Z"
    if end_date:
        payload["endPublishedDate"] = f"{end_date}T23:59:59.999Z"
    if include_text:
        payload["contents"] = {
            "text": {"maxCharacters": 5000}
        }
    if include_summary:
        payload["contents"] = payload.get("contents", {})
        payload["contents"]["summary"] = True
    
    resp = requests.post(f"{EXA_BASE_URL}/search", json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    results = []
    for r in data.get("results", []):
        item = {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "id": r.get("id", ""),
        }
        if "text" in r:
            item["text"] = r["text"]
        if "summary" in r:
            item["summary"] = r["summary"]
        if "publishedDate" in r:
            item["published_date"] = r["publishedDate"]
        if "score" in r:
            item["score"] = r["score"]
        results.append(item)
    
    return results


def find_similar(url, num_results=5, include_text=False):
    """
    查找类似页面
    
    Args:
        url: 种子URL
        num_results: 返回结果数
        include_text: 是否返回全文
    """
    payload = {
        "url": url,
        "numResults": num_results,
    }
    if include_text:
        payload["contents"] = {"text": {"maxCharacters": 5000}}
    
    resp = requests.post(f"{EXA_BASE_URL}/findSimilar", json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def answer(query, num_results=5):
    """
    AI 问答（Exa Answer API）
    直接返回带引用的回答
    """
    payload = {
        "query": query,
        "numResults": num_results,
    }
    resp = requests.post(f"{EXA_BASE_URL}/answer", json=payload, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.json()


def format_results_md(results, query=""):
    """格式式化为 Markdown"""
    if not results:
        return "未找到结果。"
    
    lines = []
    if query:
        lines.append(f"## 搜索: {query}\n")
    
    for i, r in enumerate(results, 1):
        lines.append(f"### {i}. {r.get('title', '无标题')}")
        lines.append(f"**URL:** {r.get('url', '')}")
        if r.get("published_date"):
            lines.append(f"**日期:** {r['published_date'][:10]}")
        if r.get("summary"):
            lines.append(f"**摘要:** {r['summary']}")
        if r.get("text"):
            text = r["text"][:800]
            lines.append(f"**内容:** {text}...")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Exa API 搜索工具")
    sub = parser.add_subparsers(dest="command")
    
    # search
    s = sub.add_parser("search", help="语义搜索")
    s.add_argument("query", help="搜索关键词")
    s.add_argument("--num", type=int, default=5, help="结果数 (1-10)")
    s.add_argument("--category", help="专用索引 (financial report/news/research paper)")
    s.add_argument("--start-date", help="起始日期 YYYY-MM-DD")
    s.add_argument("--end-date", help="截止日期 YYYY-MM-DD")
    s.add_argument("--text", action="store_true", help="返回全文")
    s.add_argument("--summary", action="store_true", help="返回AI摘要")
    s.add_argument("--type", default="auto", help="搜索类型 auto/neural/keyword")
    s.add_argument("--json", action="store_true", help="输出JSON")
    
    # similar
    sim = sub.add_parser("similar", help="查找类似页面")
    sim.add_argument("url", help="种子URL")
    sim.add_argument("--num", type=int, default=5)
    sim.add_argument("--text", action="store_true")
    sim.add_argument("--json", action="store_true")
    
    # answer
    ans = sub.add_parser("answer", help="AI问答")
    ans.add_argument("query", help="问题")
    ans.add_argument("--num", type=int, default=5)
    ans.add_argument("--json", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "search":
        results = search(
            args.query, args.num, args.category,
            args.start_date, args.end_date,
            args.text, args.summary, args.type
        )
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(format_results_md(results, args.query))
    
    elif args.command == "similar":
        results = find_similar(args.url, args.num, args.text)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(format_results_md(results))
    
    elif args.command == "answer":
        result = answer(args.query, args.num)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result.get("answer", "无回答"))
            if result.get("citations"):
                print("\n## 引用来源")
                for i, c in enumerate(result["citations"], 1):
                    print(f"{i}. [{c.get('title', '')}]({c.get('url', '')})")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
