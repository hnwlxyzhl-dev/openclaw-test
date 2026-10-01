#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""参数敏感性分析: 不同分位阈值/条件组合下能捞回多少稳定段"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(BASE, 'data', 'sh000001_daily_2011_2026.csv'), parse_dates=['date'])
lr = np.log(df['close'] / df['close'].shift(1))
df['lr'] = lr
df['vol'] = lr.rolling(60).std() * np.sqrt(252)
df['rng'] = df['high'].rolling(60).max() / df['low'].rolling(60).min() - 1

MIN_LEN, BUFFER, CUT = 60, 5, -0.10

def segments(mask):
    idx = np.where(mask)[0]
    if len(idx) == 0: return []
    segs, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i == p + 1: p = i
        else: segs.append((s, p)); s = i; p = i
    segs.append((s, p))
    out = []
    for a, b in segs:
        if b - a + 1 < MIN_LEN: continue
        sub = df.iloc[a + BUFFER: b - BUFFER + 1]
        logc = np.log(sub['close'].values)
        slope = np.polyfit(np.arange(len(logc)), logc, 1)[0] * 252
        if slope >= CUT:  # 剔除阴跌
            out.append((sub['date'].iloc[0].date(), sub['date'].iloc[-1].date(), len(sub)))
    return out

# HMM 部分与主脚本一致
from hmmlearn.hmm import GaussianHMM
X = df['lr'].dropna()
valid = df['lr'].notna().values
Xa = ((X - X.mean()) / X.std()).values.reshape(-1, 1)
best = None
for seed in range(10):
    try:
        m = GaussianHMM(n_components=2, covariance_type='full', n_iter=500, random_state=seed)
        m.fit(Xa)
        ll = m.score(Xa)
        if best is None or ll > best[0]: best = (ll, m)
    except Exception: pass
probs = best[1].predict_proba(Xa)
low_state = int(np.argmin([float(best[1].covars_[i][0][0]) for i in range(2)]))
mask_b = np.zeros(len(df), dtype=bool)
mask_b[valid] = probs[:, low_state] > 0.80

print(f"HMM低波态占比: {mask_b.sum()/len(df):.1%}\n")
print("| 组合 | 段数 | 稳态天数 | 占比 | 覆盖年份 |")
print("|---|---|---|---|---|")
for pctl in [0.25, 0.30, 0.35, 0.40]:
    for mode, label in [('both', '波+幅'), ('vol', '仅波动')]:
        vq, rq = df['vol'].quantile(pctl), df['rng'].quantile(pctl)
        mask_a = df['vol'] <= vq
        if mode == 'both':
            mask_a = mask_a & (df['rng'] <= rq)
        segs = segments((mask_a & pd.Series(mask_b, index=df.index)).values)
        if not segs:
            print(f"| {pctl:.0%} {label} | 0 | 0 | 0% | - |"); continue
        days = sum(s[2] for s in segs)
        yrs = sorted({s[0].year for s in segs})
        yr_str = ','.join(str(y) for y in yrs)
        print(f"| {pctl:.0%} {label} | {len(segs)} | {days} | {days/len(df):.1%} | {yr_str} |")

# 明细: 35%仅波动 和 40%双条件
print("\n----- 明细: 30% 仅波动 -----")
vq = df['vol'].quantile(0.30)
segs = segments(((df['vol'] <= vq).values & mask_b))
for s in segs: print(s)
print("\n----- 明细: 35% 仅波动 -----")
vq = df['vol'].quantile(0.35)
segs = segments(((df['vol'] <= vq).values & mask_b))
for s in segs: print(s)
