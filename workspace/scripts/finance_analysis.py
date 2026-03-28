#!/usr/bin/env python3.11
"""
统一金融分析工具

根据需求自动选择合适的分析工具，支持灵活组合。
优先级：china-stock-analysis > akshare-stock > stock-analysis > yahoo-finance

用法：
    python3.11 scripts/finance_analysis.py stock 002637              # A股个股分析
    python3.11 scripts/finance_analysis.py stock AAPL --us           # 美股个股分析
    python3.11 scripts/finance_analysis.py screen --pe 15 --roe 15   # 股票筛选
    python3.11 scripts/finance_analysis.py compare 002637,600519     # 股票对比
    python3.11 scripts/finance_analysis.py sector "白酒"             # 行业分析
    python3.11 scripts/finance_analysis.py portfolio                 # 投资组合分析
    python3.11 scripts/finance_analysis.py --help                    # 查看帮助
"""

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# ============================================================================
# 分析工具配置
# ============================================================================

ANALYSIS_TOOLS = {
    "china-stock-analysis": {
        "path": "~/.agents/skills/china-stock-analysis",
        "scripts": {
            "screener": "scripts/stock_screener.py",
            "analyzer": "scripts/financial_analyzer.py",
            "fetcher": "scripts/data_fetcher.py",
            "valuation": "scripts/valuation_calculator.py",
        },
        "market": "a_stock",
        "capabilities": ["screening", "fundamentals", "valuation", "risk_detection", "industry_compare"],
    },
    "akshare-stock": {
        "path": "~/.agents/skills/akshare-stock",
        "scripts": {
            "main": "main.py",
        },
        "market": "a_stock",
        "capabilities": ["realtime", "kline", "intraday", "limit_stats", "money_flow", "sector", "cross_market"],
    },
    "stock-analysis": {
        "path": "~/.agents/skills/stock-analysis",
        "scripts": {
            "analyze": "scripts/analyze_stock.py",
            "portfolio": "scripts/portfolio.py",
        },
        "market": "us_stock",
        "capabilities": ["8_dimension", "sentiment", "timing", "geopolitical", "portfolio", "crypto"],
    },
    "yahoo-finance": {
        "path": "~/.agents/skills/yahoo-finance",
        "scripts": {
            "quote": "scripts/quote.py",
        },
        "market": "global",
        "capabilities": ["quote", "fundamentals", "earnings", "options"],
    },
}


# ============================================================================
# 分析工具路由
# ============================================================================

def get_analysis_tool(market: str, analysis_type: str) -> str:
    """
    根据市场和分析类型选择最优工具
    
    Args:
        market: a_stock / us_stock / crypto
        analysis_type: screening / fundamentals / valuation / realtime / kline / sentiment
    
    Returns:
        工具名称
    """
    # A股分析优先级
    if market == "a_stock":
        if analysis_type in ["screening", "fundamentals", "valuation", "risk_detection"]:
            return "china-stock-analysis"
        elif analysis_type in ["realtime", "kline", "intraday", "limit_stats", "money_flow", "sector"]:
            return "akshare-stock"
        else:
            return "akshare-stock"  # 默认用 akshare 全能
    
    # 美股分析优先级
    elif market == "us_stock":
        return "stock-analysis"
    
    # 加密货币
    elif market == "crypto":
        return "stock-analysis"
    
    # 默认
    return "akshare-stock"


def run_tool(tool_name: str, script_name: str, args: list, cwd: str = None) -> dict:
    """
    运行分析工具脚本
    
    Args:
        tool_name: 工具名称
        script_name: 脚本名称
        args: 脚本参数
        cwd: 工作目录
    
    Returns:
        执行结果
    """
    tool_config = ANALYSIS_TOOLS.get(tool_name)
    if not tool_config:
        return {"error": f"工具 {tool_name} 不存在"}
    
    script_path = tool_config["scripts"].get(script_name)
    if not script_path:
        return {"error": f"脚本 {script_name} 不存在"}
    
    tool_path = Path(tool_config["path"]).expanduser()
    full_script_path = tool_path / script_path
    
    if not full_script_path.exists():
        return {"error": f"脚本路径不存在: {full_script_path}"}
    
    # 构建命令
    cmd = ["python3.11", str(full_script_path)] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=cwd or str(tool_path),
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "执行超时"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# A股分析（使用 china-stock-analysis / akshare-stock）
# ============================================================================

def analyze_a_stock(code: str, level: str = "standard") -> dict:
    """
    A股个股分析
    
    Args:
        code: 股票代码
        level: 分析深度 (summary/standard/deep)
    
    Returns:
        分析结果
    """
    # 优先使用 china-stock-analysis
    tool = "china-stock-analysis"
    
    # 1. 获取数据
    fetch_result = run_tool(tool, "fetcher", ["--code", code, "--data-type", "all", "--years", "5"])
    if "error" in fetch_result:
        # 回退到 akshare-stock
        tool = "akshare-stock"
        ak_result = run_tool(tool, "main", ["--query", f"{code}财务分析"])
        if "error" in ak_result:
            return {"error": "所有分析工具均失败"}
        
        return {
            "source": "akshare-stock",
            "code": code,
            "analysis": ak_result.get("stdout", ""),
        }
    
    # 2. 运行分析
    analyze_result = run_tool(tool, "analyzer", ["--level", level])
    if "error" in analyze_result:
        return {"error": analyze_result["error"]}
    
    # 3. 计算估值
    valuation_result = run_tool(tool, "valuation", ["--methods", "all"])
    
    return {
        "source": "china-stock-analysis",
        "code": code,
        "level": level,
        "financial_analysis": analyze_result.get("stdout", ""),
        "valuation": valuation_result.get("stdout", "") if "error" not in valuation_result else None,
    }


def screen_a_stocks(criteria: dict) -> dict:
    """
    A股股票筛选
    
    Args:
        criteria: 筛选条件 (pe_max, roe_min, debt_ratio_max, dividend_min, etc.)
    
    Returns:
        筛选结果
    """
    tool = "china-stock-analysis"
    
    args = ["--scope", criteria.get("scope", "all")]
    
    if criteria.get("pe_max"):
        args.extend(["--pe-max", str(criteria["pe_max"])])
    if criteria.get("roe_min"):
        args.extend(["--roe-min", str(criteria["roe_min"])])
    if criteria.get("debt_ratio_max"):
        args.extend(["--debt-ratio-max", str(criteria["debt_ratio_max"])])
    if criteria.get("dividend_min"):
        args.extend(["--dividend-min", str(criteria["dividend_min"])])
    if criteria.get("growth_min"):
        args.extend(["--growth-min", str(criteria["growth_min"])])
    
    result = run_tool(tool, "screener", args)
    
    if "error" in result:
        return {"error": result["error"]}
    
    return {
        "source": "china-stock-analysis",
        "criteria": criteria,
        "results": result.get("stdout", ""),
    }


def analyze_sector(sector_name: str) -> dict:
    """
    行业分析
    
    Args:
        sector_name: 行业名称
    
    Returns:
        分析结果
    """
    tool = "akshare-stock"
    
    result = run_tool(tool, "main", ["--query", f"{sector_name}行业板块分析"])
    
    if "error" in result:
        return {"error": result["error"]}
    
    return {
        "source": "akshare-stock",
        "sector": sector_name,
        "analysis": result.get("stdout", ""),
    }


# ============================================================================
# 美股分析（使用 stock-analysis）
# ============================================================================

def analyze_us_stock(code: str, output_format: str = "text") -> dict:
    """
    美股个股分析（8维度）
    
    Args:
        code: 股票代码
        output_format: text / json
    
    Returns:
        分析结果
    """
    tool = "stock-analysis"
    
    args = [code]
    if output_format == "json":
        args.append("--output")
        args.append("json")
    
    result = run_tool(tool, "analyze", args)
    
    if "error" in result:
        return {"error": result["error"]}
    
    return {
        "source": "stock-analysis",
        "code": code,
        "analysis": result.get("stdout", ""),
        "success": result.get("success", False),
    }


def analyze_crypto(code: str) -> dict:
    """
    加密货币分析
    
    Args:
        code: 加密货币代码 (BTC-USD, ETH-USD, etc.)
    
    Returns:
        分析结果
    """
    tool = "stock-analysis"
    
    result = run_tool(tool, "analyze", [code])
    
    if "error" in result:
        return {"error": result["error"]}
    
    return {
        "source": "stock-analysis",
        "code": code,
        "type": "crypto",
        "analysis": result.get("stdout", ""),
    }


def analyze_portfolio(portfolio_name: str = None, period: str = None) -> dict:
    """
    投资组合分析
    
    Args:
        portfolio_name: 组合名称
        period: 周期 (daily/weekly/monthly/quarterly/yearly)
    
    Returns:
        分析结果
    """
    tool = "stock-analysis"
    
    args = []
    if portfolio_name:
        args.extend(["--portfolio", portfolio_name])
    if period:
        args.extend(["--period", period])
    
    result = run_tool(tool, "analyze", args)
    
    if "error" in result:
        return {"error": result["error"]}
    
    return {
        "source": "stock-analysis",
        "portfolio": portfolio_name,
        "period": period,
        "analysis": result.get("stdout", ""),
    }


def manage_portfolio(action: str, **kwargs) -> dict:
    """
    投资组合管理
    
    Args:
        action: create / add / remove / update / show / list / delete
        **kwargs: 参数
    
    Returns:
        操作结果
    """
    tool = "stock-analysis"
    
    args = [action]
    
    if action == "create":
        args.append(kwargs.get("name", "My Portfolio"))
    elif action == "add":
        args.extend([kwargs["symbol"], "--quantity", str(kwargs.get("quantity", 1))])
        if kwargs.get("cost"):
            args.extend(["--cost", str(kwargs["cost"])])
    elif action == "remove":
        args.append(kwargs["symbol"])
    elif action == "update":
        args.extend([kwargs["symbol"], "--quantity", str(kwargs.get("quantity", 1))])
    
    result = run_tool(tool, "portfolio", args)
    
    if "error" in result:
        return {"error": result["error"]}
    
    return {
        "source": "stock-analysis",
        "action": action,
        "result": result.get("stdout", ""),
    }


# ============================================================================
# 比较分析
# ============================================================================

def compare_stocks(codes: list, market: str = "a_stock") -> dict:
    """
    股票对比
    
    Args:
        codes: 股票代码列表
        market: a_stock / us_stock
    
    Returns:
        对比结果
    """
    if market == "a_stock":
        tool = "china-stock-analysis"
        codes_str = ",".join(codes)
        result = run_tool(tool, "fetcher", ["--codes", codes_str, "--data-type", "comparison"])
        
        if "error" not in result:
            compare_result = run_tool(tool, "analyzer", ["--mode", "comparison"])
            return {
                "source": "china-stock-analysis",
                "codes": codes,
                "comparison": compare_result.get("stdout", ""),
            }
    
    # 美股或回退
    tool = "stock-analysis"
    result = run_tool(tool, "analyze", codes)
    
    return {
        "source": "stock-analysis",
        "codes": codes,
        "comparison": result.get("stdout", ""),
    }


# ============================================================================
# 智能分析（自动选择工具）
# ============================================================================

def smart_analyze(query: str) -> dict:
    """
    智能分析（自然语言输入）
    
    Args:
        query: 自然语言查询
    
    Returns:
        分析结果
    """
    # 判断市场
    is_us = any(k in query.upper() for k in ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD"])
    is_crypto = any(k in query.upper() for k in ["BTC", "ETH", "SOL", "XRP", "DOGE", "-USD"])
    
    # 判断分析类型
    is_screening = any(k in query for k in ["筛选", "找", "选", "符合条件"])
    is_sector = any(k in query for k in ["行业", "板块", "概念"])
    is_compare = any(k in query for k in ["对比", "比较", "vs"])
    is_portfolio = any(k in query for k in ["组合", "持仓", "我的股票"])
    
    # 提取股票代码
    import re
    code_matches = re.findall(r"\b(\d{6}|[A-Z]{1,5})\b", query)
    
    # 路由到对应功能
    if is_portfolio:
        return analyze_portfolio()
    
    if is_screening:
        # 解析筛选条件
        criteria = {}
        pe_match = re.search(r"PE[<≤]\s*(\d+)", query)
        if pe_match:
            criteria["pe_max"] = int(pe_match.group(1))
        roe_match = re.search(r"ROE[>≥]\s*(\d+)", query)
        if roe_match:
            criteria["roe_min"] = int(roe_match.group(1))
        
        return screen_a_stocks(criteria)
    
    if is_sector:
        sector_match = re.search(r"['\"「」『』]?(\w+)['\"「」『』]?[行业板块]", query)
        if sector_match:
            return analyze_sector(sector_match.group(1))
    
    if is_compare and code_matches:
        return compare_stocks(code_matches, "us_stock" if is_us else "a_stock")
    
    # 个股分析
    if code_matches:
        code = code_matches[0]
        if is_crypto:
            return analyze_crypto(code + "-USD" if "-USD" not in code else code)
        elif is_us:
            return analyze_us_stock(code)
        else:
            return analyze_a_stock(code)
    
    # 默认使用 akshare-stock 自然语言路由
    tool = "akshare-stock"
    result = run_tool(tool, "main", ["--query", query])
    
    return {
        "source": "akshare-stock",
        "query": query,
        "analysis": result.get("stdout", ""),
    }


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="统一金融分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # A股分析
  python3.11 scripts/finance_analysis.py stock 002637
  python3.11 scripts/finance_analysis.py stock 002637 --level deep

  # 美股分析
  python3.11 scripts/finance_analysis.py stock AAPL --us
  python3.11 scripts/finance_analysis.py stock TSLA --us --json

  # 股票筛选
  python3.11 scripts/finance_analysis.py screen --pe-max 15 --roe-min 15
  python3.11 scripts/finance_analysis.py screen --scope hs300 --dividend-min 3

  # 行业分析
  python3.11 scripts/finance_analysis.py sector "白酒"
  python3.11 scripts/finance_analysis.py sector "新能源"

  # 股票对比
  python3.11 scripts/finance_analysis.py compare 002637,600519
  python3.11 scripts/finance_analysis.py compare AAPL,MSFT --us

  # 投资组合
  python3.11 scripts/finance_analysis.py portfolio
  python3.11 scripts/finance_analysis.py portfolio --period weekly

  # 加密货币
  python3.11 scripts/finance_analysis.py crypto BTC-USD
  python3.11 scripts/finance_analysis.py crypto ETH-USD

  # 智能分析（自然语言）
  python3.11 scripts/finance_analysis.py smart "分析贵州茅台"
  python3.11 scripts/finance_analysis.py smart "筛选PE小于15且ROE大于15的股票"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # stock 命令
    stock_parser = subparsers.add_parser("stock", help="个股分析")
    stock_parser.add_argument("code", help="股票代码")
    stock_parser.add_argument("--us", action="store_true", help="美股")
    stock_parser.add_argument("--level", choices=["summary", "standard", "deep"], default="standard", help="分析深度")
    stock_parser.add_argument("--json", action="store_true", help="JSON输出")
    
    # screen 命令
    screen_parser = subparsers.add_parser("screen", help="股票筛选")
    screen_parser.add_argument("--scope", default="all", help="筛选范围 (all/hs300/zz500/cyb/kcb)")
    screen_parser.add_argument("--pe-max", type=float, help="最大PE")
    screen_parser.add_argument("--roe-min", type=float, help="最小ROE")
    screen_parser.add_argument("--debt-ratio-max", type=float, help="最大资产负债率")
    screen_parser.add_argument("--dividend-min", type=float, help="最小股息率")
    screen_parser.add_argument("--growth-min", type=float, help="最小增长率")
    
    # sector 命令
    sector_parser = subparsers.add_parser("sector", help="行业分析")
    sector_parser.add_argument("name", help="行业名称")
    
    # compare 命令
    compare_parser = subparsers.add_parser("compare", help="股票对比")
    compare_parser.add_argument("codes", help="股票代码，逗号分隔")
    compare_parser.add_argument("--us", action="store_true", help="美股")
    
    # portfolio 命令
    portfolio_parser = subparsers.add_parser("portfolio", help="投资组合分析")
    portfolio_parser.add_argument("--name", help="组合名称")
    portfolio_parser.add_argument("--period", choices=["daily", "weekly", "monthly", "quarterly", "yearly"], help="周期")
    
    # crypto 命令
    crypto_parser = subparsers.add_parser("crypto", help="加密货币分析")
    crypto_parser.add_argument("code", help="加密货币代码 (BTC-USD, ETH-USD)")
    
    # smart 命令
    smart_parser = subparsers.add_parser("smart", help="智能分析（自然语言）")
    smart_parser.add_argument("query", help="自然语言查询")
    
    args = parser.parse_args()
    
    if args.command == "stock":
        if args.us:
            result = analyze_us_stock(args.code, "json" if args.json else "text")
        else:
            result = analyze_a_stock(args.code, args.level)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(result.get("analysis", result.get("financial_analysis", "")))
            if result.get("valuation"):
                print("\n--- 估值分析 ---")
                print(result["valuation"])
    
    elif args.command == "screen":
        criteria = {
            "scope": args.scope,
            "pe_max": args.pe_max,
            "roe_min": args.roe_min,
            "debt_ratio_max": args.debt_ratio_max,
            "dividend_min": args.dividend_min,
            "growth_min": args.growth_min,
        }
        result = screen_a_stocks(criteria)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"📊 股票筛选结果 (数据源: {result['source']})\n")
            print(result["results"])
    
    elif args.command == "sector":
        result = analyze_sector(args.name)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"📊 {args.name}行业分析\n")
            print(result["analysis"])
    
    elif args.command == "compare":
        codes = args.codes.split(",")
        market = "us_stock" if args.us else "a_stock"
        result = compare_stocks(codes, market)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"📊 股票对比分析\n")
            print(result["comparison"])
    
    elif args.command == "portfolio":
        result = analyze_portfolio(args.name, args.period)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print("📊 投资组合分析\n")
            print(result["analysis"])
    
    elif args.command == "crypto":
        result = analyze_crypto(args.code)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"📊 {args.code} 分析\n")
            print(result["analysis"])
    
    elif args.command == "smart":
        result = smart_analyze(args.query)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"📊 智能分析结果 (数据源: {result['source']})\n")
            print(result.get("analysis", result.get("comparison", result.get("results", ""))))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
