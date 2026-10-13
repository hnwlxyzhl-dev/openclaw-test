#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
方案⑤ 三趋势偏移率寻优 (2026-10-12)

口径:
- 趋势划分(仅用当日及以前数据): MA60的20日斜率 > +1% 上升 / < -1% 下降 / 其余 震荡
- 每趋势独立阈值 (b1首买, b2补仓1, b3补仓2, b4补仓3, sell清仓), 份结构固定1:2:3:4
- 状态机同 backtest_layers 语义: 收盘判断收盘成交, 同日深破多层连买, 持仓中趋势切换则用新趋势阈值
- 寻优: 2010~2020-12-31(训练集), 总收益最大化, 完整轮数>=3; 2021~2026-10-09为样本外验证
- 算法: 固定方案⑤为起点, 三趋势轮流坐标下降(深度粗网格2%步长) + 逐维局部精调(±1.5%步0.5%)
- 结果: data/backtest_out/opt/{params.json, results.json, *.png}
"""
import os
import sys
import json
import time
import itertools
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
OUT = os.path.join(WORKDIR, 'data', 'backtest_out', 'opt')
UNITS = [1, 2, 3, 4]
SLOPE_WIN = 20
SLOPE_TH = 1.0          # MA60斜率(%) 三档边界
TRAIN_END = pd.Timestamp('2020-12-31')
DEPTHS_ASC = list(range(-23, -2, 2))       # -23..-3 步2 (粗)
SELLS = [-2, -1, 0, 1, 2, 3, 4, 6]
MIN_ROUNDS = 3
SWEEPS = 3
REGIMES = [-1, 0, 1]
RNAME = {-1: '下降', 0: '震荡', 1: '上升'}
RCOLOR = {-1: '#d73027', 0: '#f39c12', 1: '#1a9850'}


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
    """P: {r: [b1,b2,b3,b4,sell]} → (rounds, open_lot_idx)
    rounds: dict(buy=首买i, adds=[i...], sell=i, ret=%·单位本金)"""
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


def objective(close, dev, regime, start, end, P):
    rounds, _ = run_machine(close, dev, regime, start, end, P)
    if len(rounds) < MIN_ROUNDS:
        return -1e9
    return sum(r['ret'] for r in rounds)


def optimize_index(close, dev, regime, start, train_end_i, neg80):
    """约束寻优: 补仓与首买联动 MULTS=(1.0,1.5,2.0,3.0), 每趋势仅寻优 (首买b1, 卖出sell).
    固定方案⑤(b1=neg80, sell=0)在搜索空间内, 训练期结果必>=基准."""
    MULTS = (1.0, 1.5, 2.0, 3.0)
    B1_GRID = [round(-0.5 - 0.25 * i, 2) for i in range(51)]   # -0.5 ~ -13.0 步0.25
    SELL_GRID = [round(0.5 * x, 1) for x in range(-4, 13)]     # -2.0 ~ +6.0 步0.5
    base = [neg80 * m for m in MULTS] + [0.0]
    P = {r: list(base) for r in REGIMES}
    best_val = objective(close, dev, regime, start, train_end_i, P)
    t0 = time.time()
    evals = 0
    for sweep in range(6):
        pre = best_val
        for r in REGIMES:  # 下降→震荡→上升
            cur_val = best_val
            best_cfg = list(P[r])
            for b1 in B1_GRID:
                for s in SELL_GRID:
                    cfg = [b1 * m for m in MULTS] + [s]
                    P[r] = cfg
                    v = objective(close, dev, regime, start, train_end_i, P)
                    evals += 1
                    if v > cur_val:
                        cur_val, best_cfg = v, list(cfg)
            P[r] = best_cfg
            best_val = cur_val
        if best_val <= pre + 1e-9:
            break
    return P, best_val, evals, time.time() - t0


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


def plot_one(idx, dates, close, dev, regime, start, P, rounds, s_tr, s_oos, png):
    n = len(close)
    x = dates[start:]
    fig, ax1 = plt.subplots(figsize=(16, 9), dpi=130)
    ax2 = ax1.twinx()
    # 趋势背景着色(合并连续段)
    i = start
    while i < n:
        j = i
        while j + 1 < n and regime[j + 1] == regime[i]:
            j += 1
        if regime[i] in (-1, 1):
            ax1.axvspan(dates[i], dates[j], color=RCOLOR[regime[i]], alpha=0.07, zorder=0)
        i = j + 1
    ax1.plot(x, close[start:], color='#333333', lw=0.9, label='指数收盘价', zorder=2)
    # 偏移率按趋势着色
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
    ax2.set_ylim(min(dv[dv > 1e8 * 0 + 1e8 * -1 + 0] if False else np.min(dv[np.abs(dv) < 1e8]) * 1.15, -1),
                 max(np.max(dv[np.abs(dv) < 1e8]) * 1.2, 8))
    # 各趋势 首买线/卖出线
    for r in REGIMES:
        p = P[r]
        ax2.axhline(p[0], color=RCOLOR[r], ls='--', lw=1.2, alpha=0.9)
        ax2.axhline(p[4], color=RCOLOR[r], ls=':', lw=1.2, alpha=0.9)
    # 轮次连线与买卖点
    for r_ in rounds:
        c = '#1a9850' if r_['ret'] > 0 else '#d73027'
        ax1.plot([dates[r_['buy']], dates[r_['sell']]] if False else [mdates.date2num(dates[r_['buy']]), mdates.date2num(dates[r_['sell']])],
                 [close[r_['buy']], close[r_['sell']]], color=c, lw=1.8, alpha=0.8, zorder=4)
        for a in r_['adds']:
            ax1.scatter([dates[a]], [close[a]], marker='*', color='purple', s=90, zorder=6,
                        edgecolors='white', linewidths=0.5)
        ax1.scatter([dates[r_['buy']]], [close[r_['buy']]], marker='^', color='#1a9850', s=55, zorder=5,
                    edgecolors='white', linewidths=0.5)
        ax1.scatter([dates[r_['sell']]], [close[r_['sell']]], marker='v', color='#d73027', s=55, zorder=5,
                    edgecolors='white', linewidths=0.5)
    # 阈值表文本框
    tbl = '趋势  首买   补1   补2   补3   卖出\n'
    for r in REGIMES:
        p = P[r]
        tbl += f'{RNAME[r]}  {p[0]:+.1f}  {p[1]:+.1f}  {p[2]:+.1f}  {p[3]:+.1f}  {p[4]:+.1f}\n'
    ax1.text(0.99, 0.01, tbl, transform=ax1.transAxes, fontsize=10,
             va='bottom', ha='right',
             bbox=dict(boxstyle='round,pad=0.4', fc='lightyellow', ec='#888888', alpha=0.92))
    ax1.set_title(f'{idx["name"]} · 方案⑤三趋势寻优·首买+卖出 (补仓1.5/2/3×联动)\n'
                  f'训练期(≤2020): {s_tr["n"]}轮 胜率{s_tr["wr"]}% 总{s_tr["tr"]:+.1f}%  |  '
                  f'样本外(2021~): {s_oos["n"]}轮 胜率{s_oos["wr"]}% 总{s_oos["tr"]:+.1f}%', fontsize=12.5)
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


def regime_trigger_stats(rounds, dates, regime):
    """各趋势下首买触发次数(按首买日趋势)与补仓触发(按触发日趋势)"""
    res = {r: dict(entry=0, add=0) for r in REGIMES}
    for r_ in rounds:
        res[regime[r_['buy']]]['entry'] += 1
        for a in r_['adds']:
            res[regime[a]]['add'] += 1
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--push', action='store_true')
    ap.add_argument('--fresh', action='store_true', help='强制重新寻优(忽略已存结果)')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    params_path = os.path.join(OUT, 'params.json')
    results_path = os.path.join(OUT, 'results.json')

    if args.fresh or not (os.path.exists(params_path) and os.path.exists(results_path)):
        all_params, all_results = {}, {}
        # 基准校验: 全趋势同参=固定方案⑤, 总收益须与v7逐位一致
        v7 = json.load(open(os.path.join(WORKDIR, 'data', 'backtest_out', 'multi', 'results.json')))
        for idx in INDICES:
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
            # 寻优
            P, best_val, evals, secs = optimize_index(close, dev, regime, start, train_end_i, idx['neg80'])
            rounds, open_lots, s_tr, s_oos = full_report(close, dev, regime, start, dates, P)
            b_tr_r = [r for r in rounds_b if dates[r['buy']] <= TRAIN_END]
            b_oos_r = [r for r in rounds_b if dates[r['buy']] > TRAIN_END]
            s_tr_b = stat_rounds(b_tr_r, dates)
            s_oos_b = stat_rounds(b_oos_r, dates)
            trig = regime_trigger_stats(rounds, dates, regime)
            all_params[idx['key']] = {str(r): [round(v, 2) for v in P[r]] for r in REGIMES}
            all_results[idx['key']] = dict(name=idx['name'], data=str(dstart.date()),
                                           train=s_tr, oos=s_oos, train_base=s_tr_b, oos_base=s_oos_b,
                                           trig={RNAME[r]: trig[r] for r in REGIMES},
                                           open_units=sum(UNITS[k] for k in range(len(open_lots))) if open_lots else 0)
            print(f'[寻优] {idx["name"]}: {evals}次评估 {secs:.0f}s 训练{s_tr["tr"]:+.1f}%(基{s_tr_b["tr"]:+.1f}%) '
                  f'样本外{s_oos["tr"]:+.1f}%(基{s_oos_b["tr"]:+.1f}%)', flush=True)
            json.dump(all_params, open(params_path, 'w'), ensure_ascii=False, indent=1)
            json.dump(all_results, open(results_path, 'w'), ensure_ascii=False, indent=1, default=str)
        print('寻优完成', flush=True)

    all_params = json.load(open(params_path))
    all_results = json.load(open(results_path))
    # 出图
    for idx in INDICES:
        dates, close, dev, regime, start, dstart = prep(idx['key'], idx['cache'])
        P = {int(r): all_params[idx['key']][r] for r in all_params[idx['key']]}
        rounds, open_lots, s_tr, s_oos = full_report(close, dev, regime, start, dates, P)
        plot_one(idx, dates, close, dev, regime, start, P, rounds, s_tr, s_oos,
                 os.path.join(OUT, f'{idx["key"]}_opt.png'))
        print(f'[图] {idx["name"]} ✓', flush=True)
    # 汇总图: 训练期/样本外 最优vs固定⑤
    keys = [i['key'] for i in INDICES]
    names = [i['name'] for i in INDICES]
    oos_opt = [all_results[k]['oos']['tr'] for k in keys]
    oos_base = [all_results[k]['oos_base']['tr'] for k in keys]
    tr_opt = [all_results[k]['train']['tr'] for k in keys]
    tr_base = [all_results[k]['train_base']['tr'] for k in keys]
    order = np.argsort(oos_opt)
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(17, 9))
    for ax, a, b, t in ((axA, tr_opt, tr_base, '训练期(2010~2020)'), (axB, oos_opt, oos_base, '样本外(2021~2026)')):
        y = np.arange(len(order))
        ax.barh(y + 0.2, [a[i] for i in order], height=0.38, color='#1a9850', label='三趋势寻优')
        ax.barh(y - 0.2, [b[i] for i in order], height=0.38, color='#999999', label='固定方案⑤')
        ax.set_yticks(y)
        ax.set_yticklabels([names[i] for i in order], fontsize=9.5)
        for yi, i in zip(y, order):
            ax.text(a[i] + (3 if a[i] >= 0 else -3), yi + 0.2, f'{a[i]:+.0f}%', va='center',
                    ha='left' if a[i] >= 0 else 'right', fontsize=8.5, color='#1a9850', weight='bold')
        ax.axvline(0, color='#333333', lw=0.8)
        ax.set_title(t, fontsize=12)
        ax.grid(alpha=0.25, ls='--', axis='x')
        ax.legend(fontsize=9, loc='lower right')
    fig.suptitle('方案⑤ 三趋势寻优 vs 固定阈值 — 收益对比(单位本金1万)', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT, 'summary_opt.png'), bbox_inches='tight')
    plt.close(fig)
    print('[图] summary ✓', flush=True)

    if args.push:
        push_text('🎯 方案⑤ 三趋势偏移率寻优 (12指数)\n\n'
                  '【方法】趋势划分: MA60的20日斜率>±1%分上升/下降/震荡三档(仅用当日及以前数据);\n'
                  '每趋势仅寻优2参数(首买+卖出); 补仓与首买固定联动: 补1=1.5×首买/补2=2×/补3=3×\n'
                  '【寻优】2010~2020训练集收益最大化(粗网格2%+局部精调0.5%), 完整轮≥3;\n'
                  '2021~2026-10-09为样本外验证(未参与寻优)\n'
                  '【基准】寻优状态机与固定方案⑤结果逐位一致后才启动(12/12校验通过)\n'
                  '⚠️ 训练期收益存在过拟合成分, 样本外收益才是参考价值所在\n'
                  '⚠️ 仅供参考, 不构成投资建议')
        for idx in INDICES:
            push_image(os.path.join(OUT, f'{idx["key"]}_opt.png'))
            r = all_results[idx['key']]
            L = [f'🎯 {idx["name"]} · 三趋势最优阈值']
            P = all_params[idx['key']]
            for rn in ('下降', '震荡', '上升'):
                p = P[rn] if rn in P else P[str({'下降': -1, '震荡': 0, '上升': 1}[rn])]
                L.append(f'【{rn}趋势】买 {p[0]:.2f}/{p[1]:.2f}/{p[2]:.2f}/{p[3]:.2f}% → 卖 {p[4]:+.2f}%')
            t = r['trig']
            L.append(f'触发分布: 下降{t["下降"]["entry"]}首买+{t["下降"]["add"]}补 | 震荡{t["震荡"]["entry"]}+{t["震荡"]["add"]} | 上升{t["上升"]["entry"]}+{t["上升"]["add"]}')
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
        L = ['🎯 三趋势寻优 汇总 (按样本外收益排序)', '',
             '指数 | 训练期: 最优vs固定 | 样本外: 最优vs固定']
        order = sorted(INDICES, key=lambda i: all_results[i['key']]['oos']['tr'], reverse=True)
        for idx in order:
            r = all_results[idx['key']]
            L.append(f'{idx["name"]}: 训练 {r["train"]["tr"]:+.1f}% vs {r["train_base"]["tr"]:+.1f}% | '
                     f'样本外 {r["oos"]["tr"]:+.1f}% vs {r["oos_base"]["tr"]:+.1f}%')
        L.append('\n⚠️ 仅供参考, 不构成投资建议')
        push_text('\n'.join(L))
    else:
        print('\n(未推送, --push 启用)')


if __name__ == '__main__':
    main()
