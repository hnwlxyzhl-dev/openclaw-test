#!/usr/bin/env python3.11
"""
Test script to check tushare data structure
"""
import tushare as ts
from pathlib import Path

# Get tushare token
TUSHARE_TOKEN_FILE = Path.home() / ".tushare_token"
token = TUSHARE_TOKEN_FILE.read_text().strip() if TUSHARE_TOKEN_FILE.exists() else None

if not token:
    print("No tushare token found")
    exit(1)

try:
    ts.set_token(token)
    pro = ts.pro_api()
    
    # Get A-share spot data
    df = pro.daily(trade_date='20260427')
    
    print("Data columns:")
    print(df.columns.tolist())
    print("=" * 50)
    
    print("Sample data:")
    print(df.head())
    
except Exception as e:
    print(f"Error: {e}")