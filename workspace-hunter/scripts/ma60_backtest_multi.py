#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
MA60偏移率 12指数×4方案 批量回测 v6 (2026-10-11)

阈值来源(2023基线MA60 neg_80, 负偏移日20%分位=下跌80%分位线):
  国内7指数: Bias with turnover_warning_push.py 口径 (idx_factor_pro)
  国际3指数: international_Bias_for_any_index_warning_push.py 口径 (index_global)
  恒生科技/日经225: ETF_warning_push.py 口径 (513180.SH / 513880.SH fund_daily)

方案(层数结构 layers=[(阈值系数, 金额单位)]):
  ① neg80 单层            [(1.0,1)]
  ② neg80 等额加仓1:1     [(1.0,1),(1.5,1)]
  ③ neg80 金字塔1:2       [(1.0,1),(1.5,2)]
  ④ neg80 三层金字塔1:2:3  [(1.0,1),(1.5,2),(2.0,3)]
卖出: 偏移率≥0% 一次性清仓; 收盘判断收盘成交; 未平仓排除; 单位本金1万.
"""
import os
import json
import time
import base64
import hashlib
import argparse
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

WORKDIR = os.path.dirname(os.path.abspath(__file__)) + '/..'
CACHE = os.path.join(WORKDIR, 'data', 'backtest_cache')
OUT = os.path.join(WORKDIR, 'data', 'backtest_out', 'multi')
WEBHOOK = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=bc5c29fd-9a4a-4dc1-b1d7-f1cc75916a43'
PUSH_INTERVAL = 4

INDICES = [
    dict(key='SH000001', name='上证指数',   cache='SH000001.csv', neg80=-3.85),
    dict(key='SH000300', name='沪深300',   cache='SH000300.csv', neg80=-4.53),
    dict(key='SH000905', name='中证500',   cache='SH000905.csv', neg80=-5.93),
    dict(key='SH000852', name='中证1000',  cache='SH000852.csv', neg80=-6.75),
    dict(key='SH000015', name='红利指数',   cache='SH000015.csv', neg80=-4.29),
    dict(key='SZ399006', name='创业板指',   cache='CYB.csv',      neg80=-7.88),
    dict(key='SH000680', name='科创综指',   cache='SH000680.csv', neg80=-8.21),
    dict(key='IXIC',    name='纳斯达克指数', cache='IXIC.csv',    neg80=-5.75),
    dict(key='DJI',     name='道琼斯指数',  cache='DJI.csv',     neg80=-3.78),
    dict(key='HSI',     name='恒生指数',    cache='HSI.csv',     neg80=-5.23),
    dict(key='HSTECH',  name='恒生科技指数', cache='HSTECH.csv',  neg80=-8.01),
    dict(key='N225',    name='日经225指数', cache='N225.csv',    neg80=-3.99),
]
SCHEMES = [
    dict(no=1, tag='s1', name='方案① neg80 单层',          layers=[(1.0, 1)]),
    dict(no=2, tag='s2', name='方案② 等额加仓 1:1',        layers=[(1.0, 1), (1.5, 1)]),
    dict(no=3, tag='s3', name='方案③ 金字塔加仓 1:2',      layers=[(1.0, 1), (1.5, 2)]),
    dict(no=4, tag='s4', name='方案④ 三层金字塔 1:2:3',    layers=[(1.0, 1), (1.5, 2), (2.0, 3)]),
    dict(no=5, tag='s5', name='方案⑤ 四层金字塔 1:2:3:4',  layers=[(1.0, 1), (1.5, 2), (2.0, 3), (3.0, 4)]),
]


def backtest_layers(df, neg80, layers):
    """通用分层回测. layers=[(阈值系数,金额单位)], 阈值=neg80*系数(负值越深)
    逐层触发: 持k层时 dev<=第k+1层阈值则加仓; 同日深破多层则连买. dev>=0全清."""
    ths = [neg80 * f for f, _ in layers]
    us = [u for _, u in layers]
    n = len(layers)
    d = df.copy().sort_values('date').reset_index(drop=True)
    d['ma60'] = d['close'].rolling(60).mean()
    d['dev'] = (d['close'] - d['ma60']) / d['ma60'] * 100.0
    rounds, lots = [], []
    for row in d.itertuples():
        if pd.isna(row.dev):
            continue
        if lots and row.dev >= 0.0:
            ret = sum(u * (row.close - bp) / bp * 100.0 for _, bp, u in lots)
            rounds.append(dict(
                buy_date=lots[0][0], buy_price=lots[0][1],
                adds=[(dt, bp, u) for dt, bp, u in lots[1:]],
                units=sum(u for _, _, u in lots),
                sell_date=row.date, sell_price=float(row.close), ret=ret))
            lots = []
            continue
        if not lots:
            if row.dev <= ths[0]:
                lots.append((row.date, float(row.close), us[0]))
                for k in range(1, n):  # 同日深破多层连买
                    if row.dev <= ths[k]:
                        lots.append((row.date, float(row.close), us[k]))
                    else:
                        break
        else:
            k = len(lots)
            if k < n and row.dev <= ths[k]:
                lots.append((row.date, float(row.close), us[k]))
    return d, rounds, lots


def summarize(name, d, rounds, open_lots):
    wins = sum(1 for r in rounds if r['ret'] > 0)
    losses = [r for r in rounds if r['ret'] < 0]
    tr = sum(r['ret'] for r in rounds)
    op = None
    if open_lots:
        lc = d['close'].iloc[-1]
        op = dict(buy=str(open_lots[0][0].date()),
                  add=str(open_lots[1][0].date()) if len(open_lots) > 1 else None,
                  add2=str(open_lots[2][0].date()) if len(open_lots) > 2 else None,
                  add3=str(open_lots[3][0].date()) if len(open_lots) > 3 else None,
                  units=sum(u for _, _, u in open_lots),
                  float_ret=round(sum(u * (lc - bp) / bp * 100.0 for _, bp, u in open_lots), 2))
    return dict(total=len(rounds), wins=wins, losses=len(losses),
                wr=round(wins / len(rounds) * 100, 1) if rounds else None,
                tr=round(tr, 2), added=sum(1 for r in rounds if len(r['adds']) > 0),
                add_cnt=sum(len(r['adds']) for r in rounds), open=op,
                loss_rounds=[dict(no=i, buy=str(r['buy_date'].date()),
                                  sell=str(r['sell_date'].date()), ret=round(r['ret'], 2))
                             for i, r in enumerate(rounds, 1) if r['ret'] < 0])


def plot_one(idx, scheme, neg80, d, rounds, png):
    ths = [neg80 * f for f, _ in scheme['layers']]
    nl = len(scheme['layers'])
    colors = ['#1a9850', '#d73027']
    fig, ax1 = plt.subplots(figsize=(16, 9), dpi=130)
    ax2 = ax1.twinx()
    ax1.plot(d['date'], d['close'], color='#333333', lw=0.9, label='指数收盘价', zorder=2)
    ax2.plot(d['date'], d['dev'], color='#4a90d9', lw=0.7, alpha=0.5, label='MA60偏移率(%)', zorder=1)
    ax2.axhline(0, color='#4a90d9', ls=':', lw=0.9, alpha=0.6)
    ax2.axhline(ths[0], color='orange', ls='--', lw=1.1, alpha=0.8, label=f'首买阈值 {ths[0]:.2f}%')
    lc = ['purple', 'darkviolet', 'indigo']
    for k in range(1, nl):
        ax2.axhline(ths[k], color=lc[min(k - 1, 2)], ls='--', lw=1.0, alpha=0.8,
                    label=f'加仓{k}阈值 {ths[k]:.2f}%')
    ax2.set_ylabel('MA60偏移率 (%)', color='#4a90d9', fontsize=11)
    ax2.tick_params(axis='y', labelcolor='#4a90d9')
    nw = nl_ = na = 0
    for i, r in enumerate(rounds, 1):
        win = r['ret'] > 0
        c = colors[0] if win else colors[1]
        nw, nl_ = (nw + 1, nl_) if win else (nw, nl_ + 1)
        na += 1 if r['adds'] else 0
        ax1.plot([r['buy_date'], r['sell_date']], [r['buy_price'], r['sell_price']], color=c, lw=2.0, alpha=0.85, zorder=5)
        for j, (ad, ap, au) in enumerate(r['adds']):
            ax1.plot([ad, r['sell_date']], [ap, r['sell_price']], color=c, lw=1.4, alpha=0.55, zorder=4)
            ax1.scatter([ad], [ap], marker='*', color='purple', s=120 + 60 * j, zorder=7, edgecolors='white', linewidths=0.5)
        ax1.scatter([r['buy_date']], [r['buy_price']], marker='^', color='#1a9850', s=70, zorder=6, edgecolors='white', linewidths=0.5)
        ax1.scatter([r['sell_date']], [r['sell_price']], marker='v', color='#d73027', s=70, zorder=6, edgecolors='white', linewidths=0.5)
        mid = r['buy_date'] + (r['sell_date'] - r['buy_date']) / 2
        ax1.annotate(f'#{i}' + ('*' * len(r['adds'])), (mid, (r['buy_price'] + r['sell_price']) / 2),
                     fontsize=7, ha='center', color=c, weight='bold', zorder=7)
    n = len(rounds)
    wr = nw / n * 100 if n else 0
    tr = sum(r['ret'] for r in rounds)
    rat = ':'.join(str(u) for _, u in scheme['layers'])
    ax1.set_title(f'{idx["name"]} · {scheme["name"]} ({d["date"].iloc[0].date()} ~ {d["date"].iloc[-1].date()})\n'
                  f'规则: 首买≤{ths[0]:.2f}%' + ''.join(f' → 加仓≤{t:.2f}%' for t in ths[1:]) + ' / ≥0%清仓\n'
                  f'共{n}轮: 盈利{nw}轮(绿▲) 亏损{nl_}轮(红▼) 加仓{na}轮(紫★, 比例' + rat + ') '
                  f'胜率{wr:.1f}% 总收益{tr:+.2f}%(单位本金1万)', fontsize=12.5)
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


# ---------------- 推送 ----------------
def push_payload(payload, retries=3):
    for i in range(retries):
        try:
            r = requests.post(WEBHOOK, json=payload, timeout=15)
            resp = r.json()
            if resp.get('errcode') == 0:
                return True
            print(f'    [push] errcode={resp.get("errcode")}, 重试')
        except Exception as e:
            print(f'    [push] 异常: {e}')
        time.sleep(3)
    return False


def push_image(path):
    with open(path, 'rb') as f:
        b = f.read()
    print(f'    [img] {os.path.basename(path)} ({len(b)//1024}KB) ...', end=' ')
    ok = push_payload({'msgtype': 'image', 'image': {'base64': base64.b64encode(b).decode(), 'md5': hashlib.md5(b).hexdigest()}})
    print('✓' if ok else '✗')
    time.sleep(PUSH_INTERVAL)
    return ok


def push_text(content):
    parts, cur = [], ''
    for ln in content.split('\n'):
        if len((cur + ln + '\n').encode('utf-8')) > 1900:
            parts.append(cur)
            cur = ln + '\n'
        else:
            cur += ln + '\n'
    if cur.strip():
        parts.append(cur)
    for p in parts:
        print(f'    [txt] ({len(p.encode("utf-8"))}B) ...', end=' ')
        ok = push_payload({'msgtype': 'text', 'text': {'content': p.rstrip()}})
        print('✓' if ok else '✗')
        time.sleep(PUSH_INTERVAL)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--push', action='store_true')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    results = {}
    for idx in INDICES:
        df = pd.read_csv(os.path.join(CACHE, idx['cache']), parse_dates=['date'])
        print(f'=== {idx["name"]} (neg80={idx["neg80"]}%) {df["date"].iloc[0].date()}~{df["date"].iloc[-1].date()} ===')
        results[idx['key']] = dict(name=idx['name'], neg80=idx['neg80'],
                                   data=f'{df["date"].iloc[0].date()}~{df["date"].iloc[-1].date()}', schemes={})
        for sc in SCHEMES:
            d, rounds, open_lots = backtest_layers(df, idx['neg80'], sc['layers'])
            st = summarize(idx['name'], d, rounds, open_lots)
            results[idx['key']]['schemes'][sc['tag']] = st
            png = os.path.join(OUT, f'{idx["key"]}_{sc["tag"]}.png')
            plot_one(idx, sc, idx['neg80'], d, rounds, png)
            print(f'  {sc["name"]}: {st["total"]}轮 盈{st["wins"]} 亏{st["losses"]} 加仓{st["added"]}轮 胜率{st["wr"]}% 总{st["tr"]:+.2f}% 未平仓{"有" if st["open"] else "无"}')
    with open(os.path.join(OUT, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(f'\n结果: {OUT}/results.json')

    if args.push:
        push_text('📊 12指数×5方案 MA60偏移率回测 v3 (2010~2026-10-09)\n\n'
                  '阈值: 各指数MA60偏移率2023基线下跌80%分位线neg80\n'
                  '(国内7=Bias turnover程序; 国际3=international程序; 恒生科技513180=-8.01%, 日经225 513880=-3.99%为ETF口径)\n'
                  '方案①: neg80单层\n方案②: 等额加仓1:1 (1.5×neg80)\n'
                  '方案③: 金字塔1:2 (1.5×neg80加仓2份)\n方案④: 三层金字塔1:2:3 (2×neg80再补3份)\n'
                  '方案⑤: 四层金字塔1:2:3:4 (3×neg80再补4份)\n'
                  '卖出均≥0%; 收盘成交; 未平仓排除; 单位本金1万\n⚠️ 仅供参考, 不构成投资建议')
        for idx in INDICES:
            r = results[idx['key']]
            for sc in SCHEMES:
                push_image(os.path.join(OUT, f'{idx["key"]}_{sc["tag"]}.png'))
            L = [f'📊 {idx["name"]} (neg80={idx["neg80"]}%, 数据{r["data"]})']
            for sc in SCHEMES:
                st = r['schemes'][sc['tag']]
                buys = st['total'] + st['add_cnt']
                if st['open']:
                    buys += 1 + sum(1 for k in ('add', 'add2', 'add3') if st['open'].get(k))
                op = ''
                if st['open']:
                    adds = ''.join(f',{a}补仓' for a in (st['open'].get('add'), st['open'].get('add2'), st['open'].get('add3')) if a)
                    op = f', 未平仓({st["open"]["buy"]}买{adds}, {st["open"]["units"]}单位, 浮{st["open"]["float_ret"]:+.1f}%)'
                L.append(f'{sc["name"]}: 买入点{buys} 卖出点{st["total"]} 盈{st["wins"]}/亏{st["losses"]} 胜率{st["wr"]}% 总{st["tr"]:+.2f}%{op}')
                if st['loss_rounds']:
                    seg = '、'.join(f'{x["buy"]}~{x["sell"]}' for x in st['loss_rounds'])
                    L.append(f'  亏损轮: {seg}')
                else:
                    L.append('  亏损轮: 无 ✅')
            L.append('⚠️ 仅供参考, 不构成投资建议')
            push_text('\n'.join(L))
        for sc in SCHEMES:
            L = [f'📈 {sc["name"]} — 12指数汇总', '']
            for idx in INDICES:
                st = results[idx['key']]['schemes'][sc['tag']]
                L.append(f'{idx["name"]}: {st["total"]}轮 盈{st["wins"]}/亏{st["losses"]}, 胜率{st["wr"]}%, 总收益{st["tr"]:+.2f}%')
            tr_all = sum(results[i]['schemes'][sc['tag']]['tr'] for i in results)
            L.append(f'\n12指数合计收益: {tr_all:+.2f}%')
            L.append('⚠️ 仅供参考, 不构成投资建议')
            push_text('\n'.join(L))
    else:
        print('\n(未推送, --push 启用)')


if __name__ == '__main__':
    main()
