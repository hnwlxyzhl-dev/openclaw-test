#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
方案⑤ 三趋势寻优 v3 — 防过拟合版 (2026-10-13)

相对v2(约束版)的改进:
1. K折交叉验证: 训练期2010-2020轮次按首买日等分4折, 目标=各折收益均值-λ×标准差(不稳定罚分)
2. 边界排除: b1距网格两端≥3格(允许-1.25~-12.25), sell距两端≥3格(允许-0.5~+4.5), 杜绝贴边针尖解
3. 平台选择: 每趋势网格评分做5×5邻域均值平滑, 取平滑峰值(选高原不选尖峰)
4. 轻度收缩: 最终参数向固定方案⑤先验收缩10% (b1→neg80, sell→0)
5. 样本外铁律: 寻优只用≤2020数据; 2021~2026仅在参数定稿后评估一次

其余口径同v2: 趋势划分MA60的20日斜率±1%; 补仓1.5/2/3×首买联动; 份结构1:2:3:4; 训练2010-2020/样本外2021-2026
输出: data/backtest_out/opt_v3/
"""
import os
import sys
import json
import time
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection

plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ma60_backtest_multi import INDICES, CACHE, push_image, push_text

WORKDIR = os.path.dirname(os.path.abspath(__file__)) + '/..'
OUT = os.path.join(WORKDIR, 'data', 'backtest_out', 'opt_v3')
V2_RESULTS = os.path.join(WORKDIR, 'data', 'backtest_out', 'opt', 'results.json')
UNITS = [1, 2, 3, 4]
SLOPE_WIN = 20
SLOPE_TH = 1.0
TRAIN_END = pd.Timestamp('2020-12-31')
MULTS = (1.0, 1.5, 2.0, 3.0)
# 防过拟合①: 网格两端各留3格余量(禁止贴边)
B1_GRID = [round(-0.5 - 0.25 * i, 2) for i in range(3, 48)]    # -1.25 ~ -12.25 步0.25
SELL_GRID = [round(0.5 * j, 1) for j in range(-1, 10)]       # -0.5 ~ +4.5 步0.5
MIN_ROUNDS = 3
REGIMES = [-1, 0, 1]
RNAME = {-1: '下降', 0: '震荡', 1: '上升'}
RCOLOR = {-1: '#d73027', 0: '#f39c12', 1: '#1a9850'}
N_FOLDS = 4
LAM = 1.0          # 防过拟合②: 跨折标准差罚分系数
SMOOTH_WIN = 5     # 防过拟合③: 平台平滑窗口(±2格)
SHRINK = 0.10      # 防过拟合④: 向基准⑤先验收缩比例
SWEEPS = 5


def prep(key, cache_file):
    df = pd.read_csv(os.path.join(CACHE, cache_file), parse_dates=['date'])
    close = df['close'].values.astype(float)
    ma60 = pd.Series(close).rolling(60).mean().values
    with np.errstate(invalid='ignore', divide='ignore'):
        dev = (close - ma60) / ma60 * 100.0
        prev = np.full_like(ma60, np.nan)
        prev[SLOPE_WIN:] = ma60[:-SLOPE_WIN]
        slope = (ma60 - prev) / prev * 100.0
    regime = np.zeros(len(close), dtype=np.int8)
    regime[slope > SLOPE_TH] = 1
    regime[slope < -SLOPE_TH] = -1
    valid = np.where(~np.isnan(dev))[0]
    start = int(valid[0])
    return (list(df['date']), close.tolist(), np.nan_to_num(dev, nan=1e9).tolist(),
            regime.tolist(), start, df['date'].iloc[start])


def run_machine(close, dev, regime, start, end, P):
    """P: {r: [b1,b2,b3,b4,sell]} → (rounds, open_lot_idx) 收盘判断收盘成交, 同日深破连买"""
    lots = []
    rounds = []
    for i in range(start, end):
        d = dev[i]
        p = P[regime[i]]
        if lots:
            if d >= p[4]:
                ret = 0.0
                ci = close[i]
                for k, bi in enumerate(lots):
                    ret += UNITS[k] * (ci / close[bi] - 1.0) * 100.0
                rounds.append(dict(buy=lots[0], adds=lots[1:], sell=i, ret=ret))
                lots = []
                continue
            k = len(lots)
            if k < 4 and d <= p[k]:
                lots.append(i)
        else:
            if d <= p[0]:
                lots.append(i)
                if d <= p[1]:
                    lots.append(i)
                if d <= p[2]:
                    lots.append(i)
                if d <= p[3]:
                    lots.append(i)
    return rounds, lots


def objective_cv(rounds, fold_edges, lam=LAM):
    """防过拟合②: 轮次按首买index分4折, 得分=均值-λ×std; 无轮次折记0"""
    if len(rounds) < MIN_ROUNDS:
        return -1e9
    sc = []
    for a, b in zip(fold_edges[:-1], fold_edges[1:]):
        sc.append(sum(r['ret'] for r in rounds if a <= r['buy'] < b))
    sc = np.array(sc, dtype=float)
    return sc.mean() - lam * sc.std()


def smooth2d(scores):
    """防过拟合③: 5×5邻域均值平滑(-1e9缺失格剔除), 取平滑峰值=平台中心"""
    h, w = scores.shape
    r = SMOOTH_WIN // 2
    out = np.full((h, w), -1e9)
    for i in range(h):
        for j in range(w):
            vals = []
            for ii in range(max(0, i - r), min(h, i + r + 1)):
                for jj in range(max(0, j - r), min(w, j + r + 1)):
                    v = scores[ii, jj]
                    if v > -1e8:
                        vals.append(v)
            if vals:
                out[i, j] = float(np.mean(vals))
    return out


def optimize_index_cv(close, dev, regime, start, train_end_i, neg80):
    """坐标下降×3趋势; 每趋势全网格评估CV得分→平滑→取平台峰值; 收敛后向基准收缩10%"""
    base = [neg80 * m for m in MULTS] + [0.0]
    P = {r: list(base) for r in REGIMES}
    fold_edges = np.linspace(start, train_end_i, N_FOLDS + 1).astype(int).tolist()
    t0 = time.time()
    evals = 0
    trace = []
    for sweep in range(SWEEPS):
        pre_best = None
        for r in REGIMES:
            nb, ns = len(B1_GRID), len(SELL_GRID)
            scores = np.full((nb, ns), -1e9)
            for ii, b1 in enumerate(B1_GRID):
                for jj, s in enumerate(SELL_GRID):
                    P[r] = [round(b1 * m, 2) for m in MULTS] + [s]
                    rounds, _ = run_machine(close, dev, regime, start, train_end_i, P)
                    scores[ii, jj] = objective_cv(rounds, fold_edges)
                    evals += 1
            sm = smooth2d(scores)
            ii, jj = np.unravel_index(np.argmax(sm), sm.shape)
            b1, s = B1_GRID[ii], SELL_GRID[jj]
            P[r] = [round(b1 * m, 2) for m in MULTS] + [s]
            rounds, _ = run_machine(close, dev, regime, start, train_end_i, P)
            cur = objective_cv(rounds, fold_edges)
            if pre_best is None or cur > pre_best:
                pre_best = cur
            trace.append((sweep, RNAME[r], b1, s, round(float(sm[ii, jj]), 2), round(cur, 2)))
        if sweep > 0 and pre_best <= trace_best + 1e-9:
            break
        trace_best = pre_best
    # 防过拟合④: 轻度收缩向固定⑤先验
    P_opt = {r: list(P[r]) for r in REGIMES}
    for r in REGIMES:
        b1s = round((1 - SHRINK) * P[r][0] + SHRINK * neg80, 2)
        ss = round((1 - SHRINK) * P[r][4], 2)
        P[r] = [round(b1s * m, 2) for m in MULTS] + [ss]
    rounds_f, _ = run_machine(close, dev, regime, start, train_end_i, P)
    final_cv = objective_cv(rounds_f, fold_edges)
    return P, P_opt, final_cv, evals, time.time() - t0, trace


def stat_rounds(rounds, dates):
    if not rounds:
        return dict(n=0, wins=0, losses=0, wr=None, tr=0.0, buys=0, l1=0, l2=0, l3=0, l4=0,
                    sells=0, worst=None)
    wins = [r for r in rounds if r['ret'] > 0]
    losses = [r for r in rounds if r['ret'] < 0]
    adds = [len(r['adds']) for r in rounds]
    w = min(rounds, key=lambda r: r['ret'])
    return dict(n=len(rounds), wins=len(wins), losses=len(losses),
                wr=round(len(wins) / len(rounds) * 100, 1),
                tr=round(sum(r['ret'] for r in rounds), 2),
                buys=len(rounds) + sum(adds), l1=len(rounds),
                l2=sum(1 for a in adds if a >= 1), l3=sum(1 for a in adds if a >= 2),
                l4=sum(1 for a in adds if a >= 3), sells=len(rounds),
                worst=dict(buy=str(dates[w['buy']].date()), sell=str(dates[w['sell']].date()),
                           ret=round(w['ret'], 2)))


def full_report(close, dev, regime, start, dates, P):
    rounds, open_lots = run_machine(close, dev, regime, start, len(close), P)
    tr_rounds = [r for r in rounds if dates[r['buy']] <= TRAIN_END]
    oos_rounds = [r for r in rounds if dates[r['buy']] > TRAIN_END]
    return rounds, open_lots, stat_rounds(tr_rounds, dates), stat_rounds(oos_rounds, dates)


def regime_trigger_stats(rounds, regime):
    res = {r: dict(entry=0, add=0) for r in REGIMES}
    for r_ in rounds:
        res[regime[r_['buy']]]['entry'] += 1
        for a in r_['adds']:
            res[regime[a]]['add'] += 1
    return res


def plot_one(idx, dates, close, dev, regime, start, P, rounds, s_tr, s_oos, png):
    n = len(close)
    x = dates[start:]
    fig, ax1 = plt.subplots(figsize=(16, 9), dpi=130)
    ax2 = ax1.twinx()
    i = start
    while i < n:
        j = i
        while j + 1 < n and regime[j + 1] == regime[i]:
            j += 1
        if regime[i] in (-1, 1):
            ax1.axvspan(dates[i], dates[j], color=RCOLOR[regime[i]], alpha=0.07, zorder=0)
        i = j + 1
    ax1.plot(x, close[start:], color='#333333', lw=0.9, label='指数收盘价', zorder=2)
    import matplotlib.colors as mcolors
    cmap = mcolors.ListedColormap([RCOLOR[-1], RCOLOR[0], RCOLOR[1]])
    norm = mcolors.BoundaryNorm([-1.5, -0.5, 0.5, 1.5], cmap.N)
    dv = np.array(dev[start:])
    rg = np.array(regime[start:])
    xn = mdates.date2num(x)
    pts = np.array([xn, dv]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    keep = (np.abs(dv) < 1e8)[:-1] & (np.abs(dv) < 1e8)[1:]
    segs = segs[keep]
    cols = ((rg[:-1] + rg[1:]) / 2)[keep]
    lc = LineCollection(segs, colors=[RCOLOR[int(round(c))] for c in cols], lw=1.4, alpha=0.85)
    ax2.add_collection(lc)
    dv_ok = dv[np.abs(dv) < 1e8]
    ax2.set_ylim(min(np.min(dv_ok) * 1.15, -1), max(np.max(dv_ok) * 1.2, 8))
    for r in REGIMES:
        p = P[r]
        ax2.axhline(p[0], color=RCOLOR[r], ls='--', lw=1.2, alpha=0.9)
        ax2.axhline(p[4], color=RCOLOR[r], ls=':', lw=1.2, alpha=0.9)
    for r_ in rounds:
        c = '#1a9850' if r_['ret'] > 0 else '#d73027'
        ax1.plot([mdates.date2num(dates[r_['buy']]), mdates.date2num(dates[r_['sell']])],
                 [close[r_['buy']], close[r_['sell']]], color=c, lw=1.8, alpha=0.8, zorder=4)
        for a in r_['adds']:
            ax1.scatter([dates[a]], [close[a]], marker='*', color='purple', s=90, zorder=6,
                        edgecolors='white', linewidths=0.5)
        ax1.scatter([dates[r_['buy']]], [close[r_['buy']]], marker='^', color='#1a9850', s=55, zorder=5,
                    edgecolors='white', linewidths=0.5)
        ax1.scatter([dates[r_['sell']]], [close[r_['sell']]], marker='v', color='#d73027', s=55, zorder=5,
                    edgecolors='white', linewidths=0.5)
    tbl = '趋势  首买   补1   补2   补3   卖出\n'
    for r in REGIMES:
        p = P[r]
        tbl += f'{RNAME[r]}  {p[0]:+.2f}  {p[1]:+.2f}  {p[2]:+.2f}  {p[3]:+.2f}  {p[4]:+.2f}\n'
    ax1.text(0.99, 0.01, tbl, transform=ax1.transAxes, fontsize=10,
             va='bottom', ha='right',
             bbox=dict(boxstyle='round,pad=0.4', fc='lightyellow', ec='#888888', alpha=0.92))
    ax1.set_title(f'{idx["name"]} · 方案⑤三趋势寻优v3防过拟合 (CV稳健得分+平台+收缩, 补仓1.5/2/3×联动)\n'
                  f'训练期(≤2020): {s_tr["n"]}轮 胜率{s_tr["wr"]}% 总{s_tr["tr"]:+.1f}%  |  '
                  f'样本外(2021~): {s_oos["n"]}轮 胜率{s_oos["wr"]}% 总{s_oos["tr"]:+.1f}%', fontsize=12)
    ax2.set_ylabel('MA60偏移率(%)·按趋势着色', fontsize=10)
    ax1.set_ylabel('指数点位', fontsize=11)
    ax1.grid(alpha=0.25, ls='--')
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    proxies = [Line2D([0], [0], color='#333333', lw=1.0, label='收盘价')]
    proxies += [Line2D([0], [0], color=RCOLOR[r], lw=3, alpha=0.5,
                       label=f'{RNAME[r]}趋势段·偏移率') for r in REGIMES]
    proxies += [Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=9, label='首买'),
                Line2D([0], [0], marker='*', color='w', markerfacecolor='purple', markersize=11, label='补仓'),
                Line2D([0], [0], marker='v', color='w', markerfacecolor='red', markersize=9, label='清仓'),
                Line2D([0], [0], color='#1a9850', lw=2, label='盈利轮'),
                Line2D([0], [0], color='#d73027', lw=2, label='亏损轮')]
    ax1.legend(handles=proxies, loc='upper left', fontsize=8.5, framealpha=0.85)
    fig.tight_layout()
    fig.savefig(png, bbox_inches='tight')
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--push', action='store_true')
    ap.add_argument('--only', default=None, help='只跑指定key(测试用)')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    params_path = os.path.join(OUT, 'params.json')
    results_path = os.path.join(OUT, 'results.json')
    indices = [i for i in INDICES if args.only is None or i['key'] == args.only]

    all_params, all_results = {}, {}
    # 基准校验: 全趋势同参=固定⑤, 须与v7逐位一致
    v7 = json.load(open(os.path.join(WORKDIR, 'data', 'backtest_out', 'multi', 'results.json')))
    for idx in indices:
        dates, close, dev, regime, start, dstart = prep(idx['key'], idx['cache'])
        train_end_i = int(np.searchsorted(dates, TRAIN_END))
        base = [idx['neg80'], idx['neg80'] * 1.5, idx['neg80'] * 2.0, idx['neg80'] * 3.0, 0.0]
        Pb = {r: list(base) for r in REGIMES}
        rounds_b, _ = run_machine(close, dev, regime, start, len(close), Pb)
        tr_b = round(sum(r['ret'] for r in rounds_b), 2)
        v7_tr = v7[idx['key']]['schemes']['s5']['tr']
        v7_n = v7[idx['key']]['schemes']['s5']['total']
        flag = '✓' if abs(tr_b - v7_tr) < 0.05 and len(rounds_b) == v7_n else f'✗(机{tr_b}/v7{v7_tr} 轮{len(rounds_b)}/{v7_n})'
        print(f'[基准] {idx["name"]}: {len(rounds_b)}轮 {tr_b:+.2f}% vs v7 {v7_tr:+.2f}% {flag}', flush=True)
        if '✗' in flag:
            raise SystemExit(f'基准校验失败: {idx["name"]}')
        # v3寻优(CV+平台+收缩)
        P, P_opt, final_cv, evals, secs, trace = optimize_index_cv(
            close, dev, regime, start, train_end_i, idx['neg80'])
        # 防过拟合⑤: 参数定稿后才碰样本外
        rounds, open_lots, s_tr, s_oos = full_report(close, dev, regime, start, dates, P)
        b_tr_r = [r for r in rounds_b if dates[r['buy']] <= TRAIN_END]
        b_oos_r = [r for r in rounds_b if dates[r['buy']] > TRAIN_END]
        s_tr_b = stat_rounds(b_tr_r, dates)
        s_oos_b = stat_rounds(b_oos_r, dates)
        trig = regime_trigger_stats(rounds, regime)
        all_params[idx['key']] = {str(r): [round(v, 2) for v in P[r]] for r in REGIMES}
        all_results[idx['key']] = dict(
            name=idx['name'], data=str(dstart.date()),
            train=s_tr, oos=s_oos, train_base=s_tr_b, oos_base=s_oos_b,
            cv_score=round(float(final_cv), 2),
            params_raw={str(r): [round(v, 2) for v in P_opt[r]] for r in REGIMES},
            trig={RNAME[r]: trig[r] for r in REGIMES},
            open_units=sum(UNITS[k] for k in range(len(open_lots))) if open_lots else 0)
        print(f'[v3寻优] {idx["name"]}: {evals}次评估 {secs:.0f}s CV分{final_cv:+.1f} '
              f'训练{s_tr["tr"]:+.1f}%(基{s_tr_b["tr"]:+.1f}%) 样本外{s_oos["tr"]:+.1f}%(基{s_oos_b["tr"]:+.1f}%)', flush=True)
        json.dump(all_params, open(params_path, 'w'), ensure_ascii=False, indent=1)
        json.dump(all_results, open(results_path, 'w'), ensure_ascii=False, indent=1, default=str)
    print('寻优完成', flush=True)

    # v2样本外对照(如有)
    v2 = json.load(open(V2_RESULTS)) if os.path.exists(V2_RESULTS) else {}

    # 出图
    for idx in indices:
        dates, close, dev, regime, start, dstart = prep(idx['key'], idx['cache'])
        P = {int(r): all_params[idx['key']][r] for r in all_params[idx['key']]}
        rounds, open_lots, s_tr, s_oos = full_report(close, dev, regime, start, dates, P)
        plot_one(idx, dates, close, dev, regime, start, P, rounds, s_tr, s_oos,
                 os.path.join(OUT, f'{idx["key"]}_opt.png'))
        print(f'[图] {idx["name"]} ✓', flush=True)

    # 汇总图: 样本外 v3 vs v2 vs 固定⑤
    keys = [i['key'] for i in indices]
    names = [i['name'] for i in indices]
    oos_v3 = [all_results[k]['oos']['tr'] for k in keys]
    oos_b = [all_results[k]['oos_base']['tr'] for k in keys]
    oos_v2 = [v2[k]['oos']['tr'] if k in v2 else 0 for k in keys]
    tr_v3 = [all_results[k]['train']['tr'] for k in keys]
    tr_b = [all_results[k]['train_base']['tr'] for k in keys]
    tr_v2 = [v2[k]['train']['tr'] if k in v2 else 0 for k in keys]
    order = np.argsort(oos_v3)
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(18, 9))
    for ax, a3, a2, ab, t in ((axA, tr_v3, tr_v2, tr_b, '训练期(2010~2020)'),
                              (axB, oos_v3, oos_v2, oos_b, '样本外(2021~2026)')):
        y = np.arange(len(order))
        ax.barh(y + 0.25, [a3[i] for i in order], height=0.25, color='#1a9850', label='v3防过拟合寻优')
        ax.barh(y, [a2[i] for i in order], height=0.25, color='#4393c3', label='v2约束寻优')
        ax.barh(y - 0.25, [ab[i] for i in order], height=0.25, color='#999999', label='固定方案⑤')
        ax.set_yticks(y)
        ax.set_yticklabels([names[i] for i in order], fontsize=9.5)
        for yi, i in zip(y, order):
            ax.text(a3[i] + (3 if a3[i] >= 0 else -3), yi + 0.25, f'{a3[i]:+.0f}%', va='center',
                    ha='left' if a3[i] >= 0 else 'right', fontsize=8, color='#1a9850', weight='bold')
        ax.axvline(0, color='#333333', lw=0.8)
        ax.set_title(t, fontsize=12)
        ax.grid(alpha=0.25, ls='--', axis='x')
        ax.legend(fontsize=9, loc='lower right')
    wins = sum(1 for k in keys if all_results[k]['oos']['tr'] > all_results[k]['oos_base']['tr'])
    fig.suptitle(f'方案⑤ 寻优 v3(防过拟合) vs v2 vs 固定⑤ — 样本外赢面 {wins}/{len(keys)}', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT, 'summary_opt.png'), bbox_inches='tight')
    plt.close(fig)
    print('[图] summary ✓', flush=True)

    if args.push:
        push_text('🎯 方案⑤ 三趋势寻优 v3 · 防过拟合版 (12指数)\n\n'
                  '【上一版问题】v2单段全样本寻优+纯收益最大化 → 训练期暴增但样本外6/12跑输, 过拟合实证\n'
                  '【v3改进】①4折交叉验证: 得分=各折收益均值-标准差(不稳定罚分)\n'
                  '②边界排除: 首买限-1.25~-12.25%, 卖出限-0.5~+4.5%, 杜绝贴边针尖解\n'
                  '③平台选择: 网格评分5×5邻域平滑后取峰值(选高原不选尖峰)\n'
                  '④轻度收缩: 参数向固定⑤先验收缩10%\n'
                  '⑤样本外铁律: 寻优全程不可见2021+数据, 定稿后仅评估一次\n'
                  '【口径】趋势划分/补仓联动/份结构同v2; 训练2010-2020, 样本外2021-2026\n'
                  '⚠️ 仅供参考, 不构成投资建议')
        for idx in indices:
            push_image(os.path.join(OUT, f'{idx["key"]}_opt.png'))
            r = all_results[idx['key']]
            L = [f'🎯 {idx["name"]} · 寻优v3(防过拟合)阈值']
            P = all_params[idx['key']]
            for rn in ('下降', '震荡', '上升'):
                p = P[rn] if rn in P else P[str({'下降': -1, '震荡': 0, '上升': 1}[rn])]
                L.append(f'【{rn}趋势】买 {p[0]:.2f}/{p[1]:.2f}/{p[2]:.2f}/{p[3]:.2f}% → 卖 {p[4]:+.2f}%')
            for tag, s, sb in (('训练期(2010~2020)', r['train'], r['train_base']),
                               ('样本外(2021~2026)', r['oos'], r['oos_base'])):
                if s['n']:
                    L.append(f'{tag}: {s["n"]}轮 盈{s["wins"]}/亏{s["losses"]} 胜率{s["wr"]}% '
                             f'买{s["buys"]}次 卖{s["sells"]}次 总{s["tr"]:+.2f}% (最差轮{s["worst"]["ret"]:+.1f}%)')
                else:
                    L.append(f'{tag}: 无完整轮')
                L.append(f'  对照固定⑤: {sb["n"]}轮 胜率{sb["wr"]}% 总{sb["tr"]:+.2f}%')
            if r['open_units']:
                L.append(f'⏳当前未平仓: {r["open_units"]}单位')
            L.append('⚠️ 仅供参考, 不构成投资建议')
            push_text('\n'.join(L))
        push_image(os.path.join(OUT, 'summary_opt.png'))
        L = ['🎯 寻优v3(防过拟合) 汇总: 样本外 vs 固定⑤ vs v2', '',
             '指数 | 样本外: v3 vs 固定⑤ vs v2 | 训练期: v3 vs 固定⑤']
        order = sorted(indices, key=lambda i: all_results[i['key']]['oos']['tr'], reverse=True)
        for idx in order:
            k = idx['key']
            r = all_results[k]
            v2s = f"{v2[k]['oos']['tr']:+.1f}%" if k in v2 else '—'
            L.append(f"{idx['name']}: 样本外 {r['oos']['tr']:+.1f}% vs {r['oos_base']['tr']:+.1f}% vs {v2s} | "
                     f"训练 {r['train']['tr']:+.1f}% vs {r['train_base']['tr']:+.1f}%")
        w3 = sum(1 for i in indices if all_results[i['key']]['oos']['tr'] > all_results[i['key']]['oos_base']['tr'])
        w2 = sum(1 for i in indices if i['key'] in v2 and v2[i['key']]['oos']['tr'] > all_results[i['key']]['oos_base']['tr'])
        L.append(f'\n样本外赢面: v3 {w3}/{len(indices)} (v2为{w2}/{len(indices)})')
        L.append('⚠️ 仅供参考, 不构成投资建议')
        push_text('\n'.join(L))
    else:
        print('\n(未推送, --push 启用)')


if __name__ == '__main__':
    main()
