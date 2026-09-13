#!/usr/bin/env python3.11
"""业绩好的个股筛选：基于2026年中报（20260630）财务指标 + 最新估值"""
import tushare as ts
import pandas as pd
import time, sys

pro = ts.pro_api()
PERIOD = '20260630'   # 2026中报
TRADE_DATE = '20260911'  # 最近交易日

# ---- 1. 全市场中报财务指标（VIP接口分页）----
fields = ('ts_code,ann_date,eps,roe_waa,roe_dt,netprofit_yoy,or_yoy,q_netprofit_yoy,'
          'netprofit_margin,grossprofit_margin')
rows, offset = [], 0
while True:
    df = pro.fina_indicator_vip(period=PERIOD, fields=fields, limit=1000, offset=offset)
    if df is None or len(df) == 0:
        break
    rows.append(df)
    offset += len(df)
    if len(df) < 1000:
        break
    time.sleep(0.35)
fina = pd.concat(rows, ignore_index=True).drop_duplicates(subset='ts_code')
print(f"中报财务指标: {len(fina)} 只", file=sys.stderr)

# ---- 2. 股票列表（名称/行业，剔除ST退市）----
basic = pro.stock_basic(list_status='L', fields='ts_code,name,industry')
basic = basic[~basic['name'].str.contains('ST|退', na=False)]

# ---- 3. 最新每日指标（估值/市值）----
db = pro.daily_basic(trade_date=TRADE_DATE,
                     fields='ts_code,close,pe_ttm,pb,total_mv')
print(f"每日指标: {len(db)} 只", file=sys.stderr)

# ---- 4. 合并筛选 ----
m = fina.merge(basic, on='ts_code').merge(db, on='ts_code')
m = m.dropna(subset=['roe_waa', 'netprofit_yoy', 'or_yoy'])

cond = (
    (m['roe_waa'] >= 10) &          # 半年加权ROE >= 10%（年化约20%+）
    (m['netprofit_yoy'] >= 30) &    # 净利润同比 >= 30%
    (m['or_yoy'] >= 15) &           # 营收同比 >= 15%
    (m['pe_ttm'] > 0) & (m['pe_ttm'] <= 60) &  # 估值合理
    (m['total_mv'] >= 50)           # 市值 >= 50亿
)
sel = m[cond].copy()
print(f"筛选通过: {len(sel)} 只", file=sys.stderr)

# 综合得分: ROE与增速各占一半（增速做对数压缩防极端）
import numpy as np
sel['score'] = (sel['roe_waa'].rank(pct=True) * 0.5 +
                np.log1p(sel['netprofit_yoy'].clip(0, 500)).rank(pct=True) * 0.3 +
                np.log1p(sel['or_yoy'].clip(0, 300)).rank(pct=True) * 0.2)
sel = sel.sort_values('score', ascending=False).head(20)

out = sel[['ts_code','name','industry','close','pe_ttm','pb','total_mv',
           'roe_waa','netprofit_yoy','or_yoy','q_netprofit_yoy','grossprofit_margin','ann_date']].copy()
out['total_mv'] = (out['total_mv'] / 10000).round(1)  # 亿
out.columns = ['代码','名称','行业','现价','PE_TTM','PB','市值(亿)',
               'ROE_加权%','净利同比%','营收同比%','Q2单季净利同比%','毛利率%','中报披露日']
for c in ['现价','PE_TTM','PB','ROE_加权%','净利同比%','营收同比%','Q2单季净利同比%','毛利率%']:
    out[c] = out[c].round(1)
print(out.to_string(index=False))
