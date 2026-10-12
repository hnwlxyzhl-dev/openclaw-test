#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
方案⑤ 大盘下行阶段专项分析 (2026-10-12)

下行段识别(AI波段识别): ZigZag法 — 从峰回撤≥20%确认下行段开始,
  从谷反弹≥20%确认谷底、下行段结束(峰日→谷日, 技术性熊市标准).
轮次归类: 按方案⑤每轮首次买入日是否落在下行段内.
统计: 下行段内胜率/盈利比例(盈利贡献占比/盈亏比)/买入次数(分层)/卖出次数,
  并与非下行段对比. 未平仓轮排除胜率统计(单列). 单位本金1万.
数据: data/backtest_cache/*.csv (截至2026-10-09, 与v7回测同源).
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ma60_backtest_multi import backtest_layers, INDICES, CACHE, push_image, push_text

WORKDIR = os.path.dirname(os.path.abspath(__file__)) + '/..'
OUT = os.path.join(WORKDIR, 'data', 'backtest_out', 'downtrend')
S5 = [(1.0, 1), (1.5, 2), (2.0, 3), (3.0, 4)]  # 方案⑤ 四层金字塔1:2:3:4
PCT = 20.0  # ZigZag 回撤/反弹确认阈值(%)


def zigzag_segments(close, pct=PCT):
    """ZigZag交替波峰波谷识别. 返回下行段列表 [{h,l,dd,ongoing,h_date,l_date}]
    h=峰索引 l=谷索引 dd=峰→谷跌幅% ongoing=尾部未确认谷(进行中)"""
    close = np.asarray(close, dtype=float)
    n = len(close)
    pivots = []
    direction = 0  # 0未定 1上行(跟踪候选峰) -1下行(跟踪候选谷)
    cand = 0
    lo_i = hi_i = 0
    for i in range(1, n):
        c = close[i]
        if c < close[lo_i]:
            lo_i = i
        if c > close[hi_i]:
            hi_i = i
        if direction == 0:
            if hi_i != lo_i and close[hi_i] * (1 - pct / 100.0) >= close[lo_i]:
                if lo_i < hi_i:      # 低点在前 → 上行确立(从谷反弹≥pct)
                    pivots.append((lo_i, 'L'))
                    direction = 1
                    cand = hi_i
                else:                 # 高点在前 → 下行确立(从峰回撤≥pct)
                    pivots.append((hi_i, 'H'))
                    direction = -1
                    cand = lo_i
        elif direction == 1:
            if c > close[cand]:
                cand = i
            elif close[cand] * (1 - pct / 100.0) >= c:  # 从峰回撤≥pct确认峰
                pivots.append((cand, 'H'))
                direction = -1
                cand = i
        else:
            if c < close[cand]:
                cand = i
            elif c >= close[cand] * (1 + pct / 100.0):
                pivots.append((cand, 'L'))
                direction = 1
                cand = i
    segs = []
    last_h = None
    for idx, kind in pivots:
        if kind == 'H':
            last_h = idx
        elif kind == 'L' and last_h is not None:
            segs.append(dict(h=last_h, l=idx, ongoing=False))
            last_h = None
    if direction == -1 and last_h is not None:
        segs.append(dict(h=last_h, l=cand, ongoing=True))  # 尾部下行进行中
    for s in segs:
        s['dd'] = (close[s['l']] / close[s['h']] - 1) * 100.0
    return segs


def classify(d, rounds, open_lots, segs):
    """按首买日归类轮次到下行段/非下行段"""
    for s in segs:
        s['h_date'] = pd.Timestamp(d['date'].iloc[s['h']])
        s['l_date'] = pd.Timestamp(d['date'].iloc[s['l']])

    def in_seg(dt):
        return any(s['h_date'] <= dt <= s['l_date'] for s in segs)

    dn = [r for r in rounds if in_seg(r['buy_date'])]
    up = [r for r in rounds if not in_seg(r['buy_date'])]
    op_dn = None
    if open_lots and in_seg(open_lots[0][0]):
        lc = float(d['close'].iloc[-1])
        op_dn = dict(
            buy=str(open_lots[0][0].date()),
            units=sum(u for _, _, u in open_lots),
            layers=len(open_lots),
            float_ret=round(sum(u * (lc - bp) / bp * 100.0 for _, bp, u in open_lots), 2))
    return dn, up, op_dn


def phase_stats(rs):
    """一组轮次的统计"""
    if not rs:
        return dict(n=0, wins=0, losses=0, wr=None, tr=0.0, tw=0.0, tl=0.0,
                    ratio=None, share=None, avg_w=None, avg_l=None, worst=None,
                    buys=0, b1=0, b2=0, b3=0, b4=0, sells=0)
    wins = [r for r in rs if r['ret'] > 0]
    losses = [r for r in rs if r['ret'] < 0]
    tw = sum(r['ret'] for r in wins)
    tl = sum(r['ret'] for r in losses)
    tr = tw + tl
    adds_cnt = [len(r['adds']) for r in rs]
    worst = min(rs, key=lambda r: r['ret'])
    return dict(
        n=len(rs), wins=len(wins), losses=len(losses),
        wr=round(len(wins) / len(rs) * 100, 1) if rs else None,
        tr=round(tr, 2), tw=round(tw, 2), tl=round(tl, 2),
        ratio=round(abs(tw / tl), 2) if tl < 0 else None,
        share=round(tw / (tw - tl) * 100, 1) if (tw - tl) > 0 and tl < 0 else (100.0 if tl == 0 and tw > 0 else None),
        avg_w=round(tw / len(wins), 2) if wins else None,
        avg_l=round(tl / len(losses), 2) if losses else None,
        worst=dict(buy=str(worst['buy_date'].date()), sell=str(worst['sell_date'].date()),
                   ret=round(worst['ret'], 2)),
        buys=len(rs) + sum(adds_cnt), b1=len(rs),
        b2=sum(1 for a in adds_cnt if a >= 1),
        b3=sum(1 for a in adds_cnt if a >= 2),
        b4=sum(1 for a in adds_cnt if a >= 3),
        sells=len(rs))


def plot_one(idx, neg80, d, segs, dn, up, op_dn, st, png):
    ths = [neg80 * f for f, _ in S5]
    fig, ax1 = plt.subplots(figsize=(16, 9), dpi=130)
    ax2 = ax1.twinx()
    ax1.plot(d['date'], d['close'], color='#333333', lw=0.9, label='指数收盘价', zorder=2)
    ax2.plot(d['date'], d['dev'], color='#4a90d9', lw=0.6, alpha=0.45, label='MA60偏移率(%)', zorder=1)
    ax2.axhline(0, color='#4a90d9', ls=':', lw=0.9, alpha=0.6)
    ax2.axhline(ths[0], color='orange', ls='--', lw=1.0, alpha=0.8, label=f'首买阈值 {ths[0]:.2f}%')
    for k, c in zip(range(1, 4), ['purple', 'darkviolet', 'indigo']):
        ax2.axhline(ths[k], color=c, ls='--', lw=0.9, alpha=0.7, label=f'{k+1}层阈值 {ths[k]:.2f}%')
    ax2.set_ylabel('MA60偏移率 (%)', color='#4a90d9', fontsize=11)
    ax2.tick_params(axis='y', labelcolor='#4a90d9')
    # 下行段阴影
    first = True
    for s in segs:
        ax1.axvspan(s['h_date'], s['l_date'], color='#d73027', alpha=0.10, zorder=0,
                    label='下行段(回撤≥20%)' if first else '_')
        first = False
        dd_txt = f"{s['dd']:.0f}%" + ('…' if s['ongoing'] else '')
        ax1.annotate(dd_txt, (s['h_date'], d['close'].iloc[s['h']] * 1.03),
                     fontsize=8.5, color='#d73027', weight='bold')
    # 非下行段轮次(淡)
    for r in up:
        ax1.plot([r['buy_date'], r['sell_date']], [r['buy_price'], r['sell_price']],
                 color='#999999', lw=1.0, alpha=0.28, zorder=3)
    # 下行段轮次(粗, 红绿标盈亏)
    for i, r in enumerate(dn, 1):
        c = '#1a9850' if r['ret'] > 0 else '#d73027'
        ax1.plot([r['buy_date'], r['sell_date']], [r['buy_price'], r['sell_price']],
                 color=c, lw=2.2, alpha=0.9, zorder=5)
        for j, (ad, ap, au) in enumerate(r['adds']):
            ax1.plot([ad, r['sell_date']], [ap, r['sell_price']], color=c, lw=1.4, alpha=0.5, zorder=4)
            ax1.scatter([ad], [ap], marker='*', color='purple', s=110 + 70 * j, zorder=7,
                        edgecolors='white', linewidths=0.5)
        ax1.scatter([r['buy_date']], [r['buy_price']], marker='^', color='#1a9850', s=75, zorder=6,
                    edgecolors='white', linewidths=0.5)
        ax1.scatter([r['sell_date']], [r['sell_price']], marker='v', color='#d73027', s=75, zorder=6,
                    edgecolors='white', linewidths=0.5)
        mid = r['buy_date'] + (r['sell_date'] - r['buy_date']) / 2
        ax1.annotate(f'#{i}', (mid, (r['buy_price'] + r['sell_price']) / 2),
                     fontsize=7.5, ha='center', color=c, weight='bold', zorder=7)
    if st['wr'] is not None:
        t2 = (f"下行段内: {st['n']}轮 盈{st['wins']}/亏{st['losses']} 胜率{st['wr']}% "
              f"总收益{st['tr']:+.2f}% 买入{st['buys']}次(4层补仓{st['b2']}/{st['b3']}/{st['b4']}轮) "
              f"卖出{st['sells']}次")
    else:
        t2 = '下行段内: 无完整轮次'
    ax1.set_title(f'{idx["name"]} · 方案⑤四层金字塔 · 下行阶段专项 (ZigZag≥20%)\n'
                  f'灰色线=非下行段轮次 彩色线=下行段轮次(绿盈/红亏, 紫★=分层补仓)\n{t2}', fontsize=12.5)
    ax1.set_ylabel('指数点位', fontsize=11)
    ax1.grid(alpha=0.25, ls='--')
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=9, framealpha=0.85)
    fig.tight_layout()
    fig.savefig(png, bbox_inches='tight')
    plt.close(fig)


def plot_summary(stats, png):
    rows = [s for s in stats if s['dn']['n'] > 0]
    rows.sort(key=lambda s: (s['dn']['wr'] or 0))
    names = [f"{s['name']}\n轮{s['dn']['n']} 买{s['dn']['buys']} 卖{s['dn']['sells']}" for s in rows]
    y = np.arange(len(rows))
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(17, 9))
    wrs = [s['dn']['wr'] for s in rows]
    bars = axA.barh(y, wrs, color=['#1a9850' if w >= 60 else ('#f39c12' if w >= 40 else '#d73027') for w in wrs])
    axA.set_yticks(y)
    axA.set_yticklabels(names, fontsize=9)
    for yi, s in zip(y, rows):
        d_ = s['dn']
        axA.text(d_['wr'] + 1.5, yi, f"{d_['wr']}%", va='center', fontsize=10, weight='bold')
    axA.set_xlim(0, 108)
    axA.set_xlabel('下行段内胜率 (%)', fontsize=11)
    axA.set_title('下行段内胜率', fontsize=12)
    axA.grid(alpha=0.25, ls='--', axis='x')
    trs = [s['dn']['tr'] for s in rows]
    axB.barh(y, trs, color=['#1a9850' if t > 0 else '#d73027' for t in trs])
    for yi, s in zip(y, rows):
        d_ = s['dn']
        txt = f"{d_['tr']:+.1f}%"
        axB.text(d_['tr'] + (3 if d_['tr'] >= 0 else -3), yi, txt, va='center',
                 ha='left' if d_['tr'] >= 0 else 'right', fontsize=9, weight='bold')
    axB.axvline(0, color='#333333', lw=0.8)
    axB.set_yticks(y)
    axB.set_yticklabels([])
    axB.set_xlabel('下行段内总收益 (%)', fontsize=11)
    axB.set_title('下行段内总收益(单位本金1万)', fontsize=12)
    axB.grid(alpha=0.25, ls='--', axis='x')
    lo = min(min(trs, default=0) * 1.25, -5)
    hi = max(max(trs, default=0) * 1.25, 5)
    axB.set_xlim(lo, hi)
    fig.suptitle('方案⑤(四层金字塔1:2:3:4) 各指数下行阶段(ZigZag≥20%)表现汇总', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(png, bbox_inches='tight')
    plt.close(fig)


def fmt_seg(segs):
    if not segs:
        return '无(该指数历史上无≥20%回撤段)'
    return '、'.join(f"{s['h_date'].date()}→{s['l_date'].date()}({s['dd']:.0f}%{'进行中' if s['ongoing'] else ''})"
                     for s in segs)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--push', action='store_true')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    all_stats = []
    for idx in INDICES:
        df = pd.read_csv(os.path.join(CACHE, idx['cache']), parse_dates=['date'])
        d, rounds, open_lots = backtest_layers(df, idx['neg80'], S5)
        segs = zigzag_segments(d['close'].values)
        dn, up, op_dn = classify(d, rounds, open_lots, segs)
        st_dn, st_up = phase_stats(dn), phase_stats(up)
        # 交叉校验: 下行+非下行 = 总轮数
        assert st_dn['n'] + st_up['n'] == len(rounds), f"{idx['key']} 轮数拆分不一致"
        png = os.path.join(OUT, f"{idx['key']}_dn.png")
        plot_one(idx, idx['neg80'], d, segs, dn, up, op_dn, st_dn, png)
        all_stats.append(dict(key=idx['key'], name=idx['name'], segs=segs,
                              dn=st_dn, up=st_up, open=op_dn))
        print(f'=== {idx["name"]} ===')
        print(f'  下行段{len(segs)}段: {fmt_seg(segs)}')
        print(f'  下行段内: {st_dn["n"]}轮 盈{st_dn["wins"]}/亏{st_dn["losses"]} 胜率{st_dn["wr"]}% '
              f'总{st_dn["tr"]:+.2f}% 买{st_dn["buys"]}(1/2/3/4层: {st_dn["b1"]}/{st_dn["b2"]}/{st_dn["b3"]}/{st_dn["b4"]}) '
              f'卖{st_dn["sells"]} 最差轮{st_dn["worst"]["ret"] if st_dn["worst"] else "-"}')
        if op_dn:
            print(f'  未平仓(下行段买): {op_dn["buy"]} {op_dn["layers"]}层{op_dn["units"]}单位 浮{op_dn["float_ret"]:+.1f}%')
        print(f'  非下行段: {st_up["n"]}轮 胜率{st_up["wr"]}% 总{st_up["tr"]:+.2f}%')
    with open(os.path.join(OUT, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump([{k: v for k, v in s.items()} for s in all_stats], f,
                  ensure_ascii=False, indent=1, default=str)
    plot_summary(all_stats, os.path.join(OUT, 'summary_dn.png'))
    print(f'\n图与结果: {OUT}/')

    if args.push:
        push_text('📉 方案⑤(四层金字塔1:2:3:4) 大盘下行阶段专项分析\n\n'
                  '【下行段识别口径】AI波段识别(ZigZag法): 指数从峰值回撤≥20%确认进入下行段,\n'
                  '从谷底反弹≥20%确认谷底、下行段结束(即"技术性熊市"标准, 峰日→谷日)\n'
                  '【轮次归类】按每轮首次买入日是否落在下行段内划分; 加仓跟随首买轮\n'
                  '【统计】胜率=盈利轮/总轮; 盈利比例=盈利轮收益/(盈利+|亏损|);\n'
                  '买入次数含4层补仓; 卖出次数=清仓次数; 未平仓排除胜率(单列)\n'
                  f'【数据】2010-01~2026-10-09收盘(与v7回测同源), 单位本金1万\n'
                  '⚠️ 仅供参考, 不构成投资建议')
        time_sleep_note = True
        for s in all_stats:
            push_image(os.path.join(OUT, f"{s['key']}_dn.png"))
            d_, u_ = s['dn'], s['up']
            L = [f'📉 {s["name"]} · 方案⑤下行阶段表现 (neg80阈值)']
            L.append(f'识别下行段{len(s["segs"])}段: {fmt_seg(s["segs"])}')
            if d_['n']:
                L.append(f'【下行段内】{d_["n"]}轮: 盈{d_["wins"]}/亏{d_["losses"]} 胜率{d_["wr"]}%')
                L.append(f'  总收益{d_["tr"]:+.2f}% (盈利轮{d_["tw"]:+.2f}%/亏损轮{d_["tl"]:+.2f}%)')
                share = f'{d_["share"]:.0f}%' if d_['share'] is not None else '—'
                ratio = f'{d_["ratio"]:.2f}:1' if d_['ratio'] is not None else '—(无亏损)'
                L.append(f'  盈利比例{share} 盈亏比{ratio} 平均盈{d_["avg_w"]}%/亏{d_["avg_l"]}%')
                L.append(f'  买入{d_["buys"]}次(首买{d_["b1"]},2层补{d_["b2"]},3层补{d_["b3"]},4层补{d_["b4"]}) '
                         f'卖出{d_["sells"]}次')
                L.append(f'  最差轮: {d_["worst"]["buy"]}~{d_["worst"]["sell"]} {d_["worst"]["ret"]:+.2f}%')
            else:
                L.append('【下行段内】无完整轮次')
            if s['open']:
                o = s['open']
                L.append(f'  ⏳未平仓(下行段买): {o["buy"]} {o["layers"]}层{o["units"]}单位 浮{o["float_ret"]:+.1f}%')
            if u_['n']:
                L.append(f'【非下行段】{u_["n"]}轮 胜率{u_["wr"]}% 总{u_["tr"]:+.2f}% (对照)')
            L.append('⚠️ 仅供参考, 不构成投资建议')
            push_text('\n'.join(L))
        push_image(os.path.join(OUT, 'summary_dn.png'))
        L = ['📉 方案⑤ 12指数下行阶段汇总', '',
             '指数 | 下行段内: 轮数 胜率 总收益 买/卖 | 非下行段: 轮数 胜率 总收益']
        for s in sorted(all_stats, key=lambda x: -(x['dn']['wr'] or 0)):
            d_, u_ = s['dn'], s['up']
            if d_['n']:
                L.append(f'{s["name"]}: {d_["n"]}轮 {d_["wr"]}% {d_["tr"]:+.1f}% 买{d_["buys"]}/卖{d_["sells"]}'
                         f' | {u_["n"]}轮 {u_["wr"]}% {u_["tr"]:+.1f}%')
            else:
                L.append(f'{s["name"]}: 下行段内无完整轮 | {u_["n"]}轮 {u_["wr"]}% {u_["tr"]:+.1f}%')
        tot_dn = sum(s['dn']['tr'] for s in all_stats)
        L.append(f'\n12指数下行段收益合计: {tot_dn:+.2f}%')
        L.append('⚠️ 仅供参考, 不构成投资建议')
        push_text('\n'.join(L))
    else:
        print('\n(未推送, --push 启用)')


if __name__ == '__main__':
    main()
