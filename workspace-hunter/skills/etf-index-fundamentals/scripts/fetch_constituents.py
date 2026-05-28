#!/usr/bin/env python3.11
"""
Fetch the latest constituents and weights for an ETF or index.
Outputs a JSON file suitable for OnDemand_Index_PE_Push.py --stocks.

Data source: Tushare Pro API (fund_portfolio for ETF, index_weight for indices)

Usage:
    python3.11 fetch_constituents.py --etf 159206 --output /tmp/stocks.json
    python3.11 fetch_constituents.py --etf 515880 --output /tmp/stocks.json
    python3.11 fetch_constituents.py --index 000300.SH --output /tmp/stocks.json
    python3.11 fetch_constituents.py --index 931594.CSI --output /tmp/stocks.json
"""
import argparse
import json
import sys
import pandas as pd
from datetime import datetime

# Tushare Pro
TS_TOKEN = 'dde651506e87c13c30474693d2c4091345f987a2b8bfffad4989530c'
import tushare as ts
pro = ts.pro_api(TS_TOKEN)


def etf_code_to_tscode(etf_code: str) -> str:
    """Convert numeric ETF code to tushare ts_code format.
    
    Rules:
      - 51xxxx, 56xxxx, 58xxxx → .SH (上交所)
      - 15xxxx, 16xxxx → .SZ (深交所)
    """
    code = str(etf_code).zfill(6)
    if code.startswith(('51', '52', '56', '58', '59')):
        return f"{code}.SH"
    elif code.startswith(('15', '16')):
        return f"{code}.SZ"
    else:
        # fallback: try .SZ first
        return f"{code}.SZ"


def stock_code_to_tscode(code: str) -> str:
    """Convert 6-digit stock code to tushare ts_code format."""
    code = str(code).zfill(6)
    if code.startswith(('6', '9')):
        return f"{code}.SH"
    elif code.startswith(('0', '3')):
        return f"{code}.SZ"
    elif code.startswith(('4') or code.startswith('8')):
        return f"{code}.BJ"
    else:
        return f"{code}.SZ"


def fetch_etf_constituents(etf_code: str) -> dict:
    """
    Fetch ETF full holdings and weights via tushare fund_portfolio.
    
    Returns dict of {ts_code: weight_ratio} where weight_ratio sums to ~1.
    
    Notes:
      - fund_portfolio returns ALL holdings (not just top 10), with stk_mkv_ratio summing to ~100%
      - Data is from quarterly fund reports, may lag by 1-3 months
      - ts_code must use exchange suffix (.SZ for 15xxxx, .SH for 51xxxx/56xxxx)
    """
    ts_code = etf_code_to_tscode(etf_code)
    print(f"Fetching ETF holdings for {etf_code} (ts_code={ts_code}) via tushare fund_portfolio...")

    # Try recent quarters, newest first
    now = datetime.now()
    end_dates = []
    for year_offset in [0, -1]:
        y = now.year + year_offset
        for q_end in ['1231', '0930', '0630', '0331']:
            ed = f"{y}{q_end}"
            if ed <= now.strftime('%Y%m%d'):
                end_dates.append(ed)

    for end_date in end_dates:
        df = pro.fund_portfolio(ts_code=ts_code, end_date=end_date)
        if df.empty:
            continue

        # Get the latest reporting period
        latest_end = df['end_date'].max()
        latest = df[df['end_date'] == latest_end].copy()

        if latest.empty:
            continue

        # Sort by weight descending
        latest = latest.sort_values('stk_mkv_ratio', ascending=False)

        # Build result: symbol is already in ts_code format (e.g. '600118.SH')
        result = {}
        for _, row in latest.iterrows():
            symbol = row['symbol']
            weight = float(row['stk_mkv_ratio']) / 100.0  # percentage to ratio
            result[symbol] = weight

        total_pct = latest['stk_mkv_ratio'].sum()
        print(f"  Report period: {latest_end}, announced: {latest['ann_date'].iloc[0]}")
        print(f"  Holdings: {len(result)} stocks, weight sum: {total_pct:.2f}%")
        print(f"  Top 5: {', '.join([f'{k}={v*100:.1f}%' for k, v in list(result.items())[:5]])}")

        # Warn if weight sum is far from 100% (e.g. new ETF with incomplete data)
        if total_pct < 80:
            print(f"  ⚠️  Weight sum is only {total_pct:.1f}%, data may be incomplete!")

        return result

    raise ValueError(f"No fund_portfolio data found for ETF {etf_code} (ts_code={ts_code})")


def fetch_index_constituents(index_code: str) -> dict:
    """
    Fetch index weights via tushare index_weight.
    Returns dict of {ts_code: weight_ratio}.
    index_code: like '000300.SH', '931594.CSI'
    """
    print(f"Fetching index weights for {index_code} via tushare index_weight...")

    # Try current date, then expand range
    now_str = datetime.now().strftime('%Y%m%d')
    ranges = [
        (now_str, now_str),                              # today
        ('20260401', now_str),                            # this quarter
        ((datetime.now() - pd.Timedelta(days=90)).strftime('%Y%m%d'), now_str),  # 3 months
        ((datetime.now() - pd.Timedelta(days=180)).strftime('%Y%m%d'), now_str), # 6 months
    ]

    for start_date, end_date in ranges:
        df = pro.index_weight(index_code=index_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            # Get the latest trade_date
            latest_date = df['trade_date'].max()
            latest = df[df['trade_date'] == latest_date].copy()
            if not latest.empty:
                break
    else:
        raise ValueError(f"No index_weight data found for index {index_code}")

    # Build result: con_code is already in ts_code format, weight is percentage
    latest = latest.sort_values('weight', ascending=False)
    result = {}
    for _, row in latest.iterrows():
        con_code = row['con_code']
        weight = float(row['weight']) / 100.0  # percentage to ratio
        result[con_code] = weight

    total_pct = latest['weight'].sum()
    print(f"  Date: {latest_date}, constituents: {len(result)} stocks, weight sum: {total_pct:.2f}%")
    print(f"  Top 5: {', '.join([f'{k}={v*100:.1f}%' for k, v in list(result.items())[:5]])}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Fetch ETF/Index constituents via Tushare")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--etf', help='ETF code (numeric, e.g. 159206, 515880)')
    group.add_argument('--index', help='Tushare index code (e.g. 000300.SH, 931594.CSI)')

    parser.add_argument('--output', required=True, help='Output JSON file path')
    args = parser.parse_args()

    if args.etf:
        stocks = fetch_etf_constituents(args.etf)
    elif args.index:
        stocks = fetch_index_constituents(args.index)

    with open(args.output, 'w') as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Wrote {len(stocks)} constituents to {args.output}")


if __name__ == '__main__':
    main()
