#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
上证指数近15年稳定时段识别
方案A: 滚动60日年化波动率 <= 全样本25%分位 AND 60日区间振幅 <= 全样本25%分位
方案B: 2状态高斯HMM, 低波状态后验概率 > 0.8
最终 = A ∩ B, 连续段 >= 60交易日, 边界砍5日, 年化斜率 < -10% 判阴跌剔除
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')
os.makedirs(DATA, exist_ok=True)

# ---------- 参数 ----------
START, END = '2011-10-01', '2026-09-30'
LOOKBACK = 60          # 滚动窗口(交易日)
VOL_PCTL = 0.25        # 波动率分位阈值
RANGE_PCTL = 0.25      # 振幅分位阈值
MIN_LEN = 60           # 最短时段长度
BUFFER = 5             # 边界缓冲(砍天数)
DOWNTREND_CUT = -0.10  # 年化斜率低于此值 -> 阴跌剔除
HMM_PROB = 0.80        # 低波状态后验概率阈值
SEEDS = 10             # HMM 随机种子数

# ---------- 数据 ----------
def fetch_index():
    """拉取上证指数日线, 新浪优先, 东财备选"""
    import akshare as ak
    df = None
    try:
        df = ak.stock_zh_index_daily(symbol='sh000001')
        df = df.rename(columns=lambda c: str(c).strip().lower())
        cols = {}
        for c in df.columns:
            lc = c.lower()
            if lc in ('date', '日期'): cols[c] = 'date'
            elif lc in ('open', '开盘'): cols[c] = 'open'
            elif lc in ('close', '收盘'): cols[c] = 'close'
            elif lc in ('high', '最高'): cols[c] = 'high'
            elif lc in ('low', '最低'): cols[c] = 'low'
        df = df.rename(columns=cols)
        df['date'] = pd.to_datetime(df['date'])
        df = df[['date', 'open', 'close', 'high', 'low']].astype(
            {c: float for c in ['open', 'close', 'high', 'low']})
        df = df.sort_values('date').reset_index(drop=True)
        print(f'[data] sina ok, rows={len(df)}, range={df.date.min().date()}~{df.date.max().date()}')
    except Exception as e:
        print(f'[data] sina failed: {e}')
        df = None
    if df is None:
        try:
            df = ak.index_zh_a_hist(symbol='000001', period='daily',
                                    start_date=START.replace('-', ''),
                                    end_date=END.replace('-', ''))
            ren = {}
            for c in df.columns:
                lc = str(c)
                if '日期' in lc: ren[c] = 'date'
                elif '开盘' in lc: ren[c] = 'open'
                elif '收盘' in lc: ren[c] = 'close'
                elif '最高' in lc: ren[c] = 'high'
                elif '最低' in lc: ren[c] = 'low'
            df = df.rename(columns=ren)[['date', 'open', 'close', 'high', 'low']]
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            print(f'[data] east ok, rows={len(df)}')
        except Exception as e:
            print(f'[data] east failed: {e}')
            raise SystemExit('no data source available')
    m = (df['date'] >= START) & (df['date'] <= END)
    df = df.loc[m].reset_index(drop=True)
    df.to_csv(os.path.join(DATA, 'sh000001_daily_2011_2026.csv'), index=False)
    return df


def main():
    print(f'run at: {pd.Timestamp.now()}')
    df = fetch_index()
    print(f'slice: rows={len(df)}, {df.date.iloc[0].date()} ~ {df.date.iloc[-1].date()}')
    assert len(df) > 2000, 'data rows too few'

    # ---------- 特征 ----------
    lr = np.log(df['close'] / df['close'].shift(1))
    df['lr'] = lr
    df['vol'] = lr.rolling(LOOKBACK).std() * np.sqrt(252)          # 年化波动率
    df['rng'] = df['high'].rolling(LOOKBACK).max() / df['low'].rolling(LOOKBACK).min() - 1
    vol_q = df['vol'].quantile(VOL_PCTL)
    rng_q = df['rng'].quantile(RANGE_PCTL)
    print(f'quantile({VOL_PCTL:.0%}): vol_q={vol_q:.2%}, rng_q={rng_q:.2%}')

    # 方案A
    mask_a = (df['vol'] <= vol_q) & (df['rng'] <= rng_q)

    # 方案B: HMM
    from hmmlearn.hmm import GaussianHMM
    X = df['lr'].dropna()
    valid = df['lr'].notna().values
    Xa = ((X - X.mean()) / X.std()).values.reshape(-1, 1)
    best = None
    for seed in range(SEEDS):
        try:
            m = GaussianHMM(n_components=2, covariance_type='full',
                            n_iter=500, random_state=seed)
            m.fit(Xa)
            ll = m.score(Xa)
            if best is None or ll > best[0]:
                best = (ll, m)
        except Exception:
            continue
    assert best is not None, 'hmm all seeds failed'
    _, model = best
    probs = model.predict_proba(Xa)
    covs = [float(model.covars_[i][0][0]) for i in range(2)]
    low_state = int(np.argmin(covs))
    print(f'hmm: ll={best[0]:.1f}, low_state={low_state}, '
          f'state_covs={[f"{c:.4f}" for c in covs]}, low_prob>={HMM_PROB} days={int((probs[:,low_state]>HMM_PROB).sum())}')
    mask_b = np.zeros(len(df), dtype=bool)
    mask_b[valid] = probs[:, low_state] > HMM_PROB

    mask = mask_a & mask_b
    print(f'A∩B days: {mask.sum()} / {len(df)} ({mask.sum()/len(df):.1%})')

    # ---------- 连续段提取 ----------
    idx = np.where(mask)[0]
    if len(idx) == 0:
        raise SystemExit('no stable candidates found')
    segs = []
    s = idx[0]; p = idx[0]
    for i in idx[1:]:
        if i == p + 1:
            p = i
        else:
            segs.append((s, p)); s = i; p = i
    segs.append((s, p))

    rows = []
    for (a, b) in segs:
        n = b - a + 1
        if n < MIN_LEN:
            continue
        a2, b2 = a + BUFFER, b - BUFFER     # 边界缓冲
        sub = df.iloc[a2:b2 + 1]
        logc = np.log(sub['close'].values)
        x = np.arange(len(logc))
        slope = np.polyfit(x, logc, 1)[0] * 252   # 年化斜率(对数)
        ann_vol = sub['lr'].std() * np.sqrt(252)
        rows.append({
            'start': sub['date'].iloc[0].date(),
            'end': sub['date'].iloc[-1].date(),
            'days': len(sub),
            'low': float(sub['low'].min()),
            'high': float(sub['high'].max()),
            'close_s': float(sub['close'].iloc[0]),
            'close_e': float(sub['close'].iloc[-1]),
            'net': float(sub['close'].iloc[-1] / sub['close'].iloc[0] - 1),
            'slope_ann': float(slope),
            'ann_vol': float(ann_vol),
        })
    res = pd.DataFrame(rows)
    res['阴跌'] = res['slope_ann'] < DOWNTREND_CUT
    res.to_csv(os.path.join(DATA, 'stable_periods_raw.csv'), index=False)

    keep = res[~res['阴跌']].reset_index(drop=True)
    drop = res[res['阴跌']].reset_index(drop=True)

    def fmt(d):
        if len(d) == 0: return '(无)'
        out = []
        for _, r in d.iterrows():
            out.append(f"| {r['start']} | {r['end']} | {r['days']} | "
                       f"{r['low']:.0f}~{r['high']:.0f} | {r['net']:+.1%} | "
                       f"{r['slope_ann']:+.1%} | {r['ann_vol']:.1%} |")
        return '\n'.join(out)

    print('\n===== 保留段(稳定) =====')
    print('| 开始 | 结束 | 交易日 | 点位区间 | 净涨跌 | 年化斜率 | 年化波动 |')
    print('|---|---|---|---|---|---|---|')
    print(fmt(keep))
    print('\n===== 剔除段(阴跌) =====')
    print('| 开始 | 结束 | 交易日 | 点位区间 | 净涨跌 | 年化斜率 | 年化波动 |')
    print('|---|---|---|---|---|---|---|')
    print(fmt(drop))

    total_keep = int(keep['days'].sum())
    print(f'\n稳态占比(保留段): {total_keep}/{len(df)} = {total_keep/len(df):.1%}')
    print(f'段数: 保留 {len(keep)}, 阴跌剔除 {len(drop)}')

    # ---------- 逐年统计 ----------
    df['stable'] = False
    for _, r in keep.iterrows():
        m = (df['date'] >= pd.Timestamp(r['start'])) & (df['date'] <= pd.Timestamp(r['end']))
        df.loc[m, 'stable'] = True
    df['year'] = df['date'].dt.year
    yearly = df.groupby('year')['stable'].agg(['sum', 'count'])
    yearly['pct'] = yearly['sum'] / yearly['count']
    print('\n===== 逐年稳态占比 =====')
    for y, r in yearly.iterrows():
        bar = '█' * int(r['pct'] * 20)
        print(f'{y}: {r["sum"]:3.0f}/{r["count"]:3.0f} {r["pct"]:5.0%} {bar}')

    # ---------- 图 ----------
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei']
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                             gridspec_kw={'height_ratios': [3, 1]})
    ax = axes[0]
    ax.plot(df['date'], df['close'], lw=0.8, color='#333', label='上证指数收盘价')
    for _, r in keep.iterrows():
        ax.axvspan(pd.Timestamp(r['start']), pd.Timestamp(r['end']),
                   color='#2e9e4f', alpha=0.28)
    for _, r in drop.iterrows():
        ax.axvspan(pd.Timestamp(r['start']), pd.Timestamp(r['end']),
                   color='#e07b2a', alpha=0.30)
    ax.set_title(f'上证指数稳定时段识别 ({START[:4]}-{END[:4]})  绿=稳定段  橙=阴跌剔除段', fontsize=13)
    ax.legend(loc='upper left'); ax.grid(alpha=0.3)
    ax2 = axes[1]
    ax2.plot(df['date'], df['vol'], lw=0.7, color='#1f6fb2', label='60日年化波动率')
    ax2.axhline(vol_q, color='#c0392b', ls='--', lw=1, label=f'{VOL_PCTL:.0%}分位={vol_q:.1%}')
    ax2.legend(loc='upper left'); ax2.grid(alpha=0.3)
    plt.tight_layout()
    png = os.path.join(DATA, 'stable_periods.png')
    plt.savefig(png, dpi=130)
    print(f'\nfigure saved: {png}')


if __name__ == '__main__':
    main()
