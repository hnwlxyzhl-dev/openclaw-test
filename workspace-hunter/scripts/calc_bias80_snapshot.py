#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""复刻 Bias warning 程序的80%分位值计算 (只算不推送)
pos_80 = 正偏移日(bias>0)的80%分位 (卖出警示线)
neg_80 = 负偏移日(bias<0)的20%分位 (买入提示线, 即"下跌到80%偏移率"的值)
基线: 长=20150101起, 短=20230101起; 均线: MA60 / MA10"""
import time
import pandas as pd
import tushare as ts

ts.set_token('dde651506e87c13c30474693d2c4091345f987a2b8bfffad4989530c')
pro = ts.pro_api()

CN = {  # Bias with turnover_warning_push.py
    "000001.SH": "上证指数", "000300.SH": "沪深300", "000905.SH": "中证500",
    "000852.SH": "中证1000", "000015.SH": "红利指数", "399006.SZ": "创业板指",
    "000680.SH": "科创综指"}
INTL = {"IXIC": "纳斯达克指数", "DJI": "道琼斯工业指数", "HSI": "恒生指数"}  # international_..._warning_push.py


def calc_80(df, col):
    b = df[col].dropna()
    pos, neg = b[b > 0], b[b < 0]
    return (pos.quantile(0.8) if len(pos) else None,
            neg.quantile(0.2) if len(neg) else None)


def report(tag, name, df):
    df = df.sort_values('trade_date').reset_index(drop=True)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    for c in ('close',):
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['ma60'] = df['close'].rolling(60).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['B60'] = (df['close'] - df['ma60']) / df['ma60']
    df['B10'] = (df['close'] - df['ma10']) / df['ma10']
    short = df[df['trade_date'] >= '2023-01-01']
    end = df['trade_date'].iloc[-1].date()
    out = []
    for baseline, sub in [('2015基线', df), ('2023基线', short)]:
        for ma, col in (('MA60', 'B60'), ('MA10', 'B10')):
            p, n = calc_80(sub, col)
            out.append((baseline, ma, p, n))
    print(f'[{tag}] {name}  数据截至{end}')
    for baseline, ma, p, n in out:
        ps = f'{p:+.2%}' if p is not None else 'N/A'
        ns = f'{n:+.2%}' if n is not None else 'N/A'
        print(f'  {baseline} {ma}: pos_80={ps}  neg_80={ns}')
    return out


print('=' * 60)
print('国内指数 (Bias with turnover_warning_push.py, idx_factor_pro)')
print('=' * 60)
for code, name in CN.items():
    try:
        df = pro.idx_factor_pro(ts_code=code, start_date=20150101,
                                fields=["ma_bfq_60", "ma_bfq_10", "ts_code", "trade_date", "close"])
        # 用接口自带MA保持口径一致; 若为空回退自算
        if df is not None and len(df):
            df = df.sort_values('trade_date').reset_index(drop=True)
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            for c in ('close', 'ma_bfq_60', 'ma_bfq_10'):
                df[c] = pd.to_numeric(df[c], errors='coerce')
            df['B60'] = (df['close'] - df['ma_bfq_60']) / df['ma_bfq_60']
            df['B10'] = (df['close'] - df['ma_bfq_10']) / df['ma_bfq_10']
            short = df[df['trade_date'] >= '2023-01-01']
            end = df['trade_date'].iloc[-1].date()
            print(f'[国内] {code} {name}  数据截至{end}')
            for baseline, sub in [('2015基线', df), ('2023基线', short)]:
                for ma, col in (('MA60', 'B60'), ('MA10', 'B10')):
                    p, n = calc_80(sub, col)
                    ps = f'{p:+.2%}' if p is not None else 'N/A'
                    ns = f'{n:+.2%}' if n is not None else 'N/A'
                    print(f'  {baseline} {ma}: pos_80={ps}  neg_80={ns}')
    except Exception as e:
        print(f'[国内] {code} {name} 失败: {e}')
    time.sleep(1.2)

print('=' * 60)
print('国际指数 (international_Bias_for_any_index_warning_push.py, index_global)')
print('=' * 60)
for code, name in INTL.items():
    try:
        df = pro.index_global(ts_code=code, start_date=20150101,
                              fields=["ts_code", "trade_date", "close"])
        if df is not None and len(df):
            report('国际', f'{code} {name}', df)
    except Exception as e:
        print(f'[国际] {code} {name} 失败: {e}')
    time.sleep(1.2)
