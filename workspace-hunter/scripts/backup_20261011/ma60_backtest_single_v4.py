#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
MA60偏移率阈值回测 v1.0 (2026-10-10)

策略: 空仓时 MA60偏移率 <= 买入阈值 → 收盘价买入(一次)
      持仓时 偏移率 >= 0% → 收盘价卖出(一次)
      未平仓轮次排除, 不计入统计
口径: 每轮固定本金(1万元), 总收益% = 各轮收益率简单加总

数据源: HSI/DJI/IXIC/HKTECH = tushare index_global (分年段)
        创业板指 = 腾讯行情接口 (分年段)
输出:   图表PNG + 统计JSON, 可选推送企业微信
"""
import os
import sys
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
CACHE_DIR = os.path.join(WORKDIR, 'data', 'backtest_cache')
OUT_DIR = os.path.join(WORKDIR, 'data', 'backtest_out')
WEBHOOK = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=bc5c29fd-9a4a-4dc1-b1d7-f1cc75916a43'
PUSH_INTERVAL = 4  # 秒, 防企业微信限流

INDICES = [
    dict(key='HSI',     name='恒生指数',    source='tushare', code='HSI',     buy_th=-5.23),
    dict(key='DJI',     name='道琼斯指数',  source='tushare', code='DJI',     buy_th=-3.78),
    dict(key='IXIC',    name='纳斯达克指数', source='tushare', code='IXIC',    buy_th=-5.75),
    dict(key='CYB',     name='创业板指数',  source='tencent', code='sz399006', buy_th=-7.88),
    dict(key='HSTECH',  name='恒生科技指数', source='tushare', code='HKTECH',  buy_th=-8.0),
]

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


# ---------------------------------------------------------------- 数据获取
def fetch_tushare_global(code):
    """tushare 国际指数, 分年段绕过单次4000行上限"""
    import tushare as ts
    pro = ts.pro_api()
    frames = []
    for s, e in [('20100101', '20141231'), ('20150101', '20191231'), ('20200101', '20261231')]:
        for attempt in range(4):  # 应对 10次/分钟 频率限制
            try:
                df = pro.index_global(ts_code=code, start_date=s, end_date=e)
                if df is not None and len(df):
                    frames.append(df[['trade_date', 'close']])
                break
            except Exception as ex:
                if '频率超限' in str(ex) and attempt < 3:
                    print(f'    [tushare] {code} {s}~{e} 频率超限, 等65秒...')
                    time.sleep(65)
                else:
                    raise
        time.sleep(0.6)
    if not frames:
        raise RuntimeError(f'tushare {code} 无数据')
    out = pd.concat(frames).drop_duplicates('trade_date').sort_values('trade_date')
    out.columns = ['date', 'close']
    out['date'] = pd.to_datetime(out['date'])
    out['close'] = out['close'].astype(float)
    return out.reset_index(drop=True)


def fetch_tencent_index(code):
    """腾讯行情, 分年段(count<=2000)"""
    frames = []
    for s, e in [('2010-01-01', '2015-12-31'), ('2016-01-01', '2020-12-31'), ('2021-01-01', '2026-12-31')]:
        url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,{s},{e},2000,qfq'
        r = requests.get(url, headers=UA, timeout=20)
        d = r.json().get('data')
        if not (isinstance(d, dict) and code in d):
            raise RuntimeError(f'tencent {code} 段 {s}~{e} 返回异常: {str(d)[:80]}')
        days = d[code].get('day') or d[code].get('qfqday')
        frames.extend((row[0], float(row[2])) for row in days)
        time.sleep(1.2)
    out = pd.DataFrame(frames, columns=['date', 'close']).drop_duplicates('date').sort_values('date')
    out['date'] = pd.to_datetime(out['date'])
    return out.reset_index(drop=True)


def load_data(idx, refresh=False):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = os.path.join(CACHE_DIR, f'{idx["key"]}.csv')
    if os.path.exists(cache) and not refresh:
        df = pd.read_csv(cache, parse_dates=['date'])
        # 缓存最新日期距今超过7天才重拉
        latest = df['date'].max()
        age_days = (pd.Timestamp.now() - latest).days
        if age_days <= 7:
            print(f'  [cache] {idx["name"]}: {len(df)} bars, {df["date"].iloc[0].date()} ~ {latest.date()}')
            return df
        print(f'  [stale ] {idx["name"]}: 缓存截至 {latest.date()}, 重拉')
    print(f'  [fetch ] {idx["name"]} ({idx["source"]}:{idx["code"]}) ...')
    df = fetch_tushare_global(idx['code']) if idx['source'] == 'tushare' else fetch_tencent_index(idx['code'])
    df.to_csv(cache, index=False)
    print(f'  [done  ] {idx["name"]}: {len(df)} bars, {df["date"].iloc[0].date()} ~ {df["date"].iloc[-1].date()}')
    return df


# ---------------------------------------------------------------- 回测
def backtest(df, buy_th):
    """金字塔加仓1:2: 无仓时 dev<=buy_th 买1单位; 持仓时 dev<=buy_th*1.5 加仓2单位
    (buy_th为负, 1.5倍即更深阈值; 首日即深破两阈值则同日双买)
    持仓时 dev>=0 全部卖出. 单位本金1万, 轮收益=Σ(各份收益率×金额权重), 权重1:2"""
    th2 = buy_th * 1.5
    d = df.copy().sort_values('date').reset_index(drop=True)
    d['ma60'] = d['close'].rolling(60).mean()
    d['dev'] = (d['close'] - d['ma60']) / d['ma60'] * 100.0

    rounds = []
    lots = []  # 每份 (date, price, units): 首买units=1, 加仓units=2
    for row in d.itertuples():
        if pd.isna(row.dev):
            continue
        if lots and row.dev >= 0.0:  # 全部平仓
            ret = sum(u * (row.close - bp) / bp * 100.0 for _, bp, u in lots)
            rounds.append(dict(
                buy_date=lots[0][0], buy_price=lots[0][1],
                add_date=lots[1][0] if len(lots) > 1 else None,
                add_price=lots[1][1] if len(lots) > 1 else None,
                units=sum(u for _, _, u in lots), sell_date=row.date, sell_price=float(row.close), ret=ret))
            lots = []
            continue
        if not lots:
            if row.dev <= buy_th:
                lots.append((row.date, float(row.close), 1))
                if row.dev <= th2:  # 首日即深破, 同日双买
                    lots.append((row.date, float(row.close), 2))
        elif len(lots) == 1 and row.dev <= th2:
            lots.append((row.date, float(row.close), 2))
    return d, rounds, lots  # lots非空即未平仓轮(排除)


def summarize(idx, d, rounds, open_lots):
    wins = [r for r in rounds if r['ret'] > 0]
    losses = [r for r in rounds if r['ret'] < 0]
    flat = [r for r in rounds if r['ret'] == 0]
    total_ret = sum(r['ret'] for r in rounds)
    first_signal_date = d['date'].iloc[59] if len(d) > 59 else None
    if open_lots:
        last_close = d['close'].iloc[-1]
        float_ret = sum(u * (last_close - bp) / bp * 100.0 for _, bp, u in open_lots)
        op = dict(buy_date=str(open_lots[0][0].date()),
                  add_date=str(open_lots[1][0].date()) if len(open_lots) > 1 else None,
                  units=sum(u for _, _, u in open_lots), float_ret=round(float_ret, 2))
    else:
        op = None
    stats = dict(
        name=idx['name'], buy_th=idx['buy_th'], add_th=round(idx['buy_th'] * 1.5, 3),
        data_start=str(d['date'].iloc[0].date()), data_end=str(d['date'].iloc[-1].date()),
        signal_start=str(first_signal_date.date()) if first_signal_date is not None else '',
        total_rounds=len(rounds), win_rounds=len(wins), loss_cnt=len(losses), flat_cnt=len(flat),
        added_rounds=sum(1 for r in rounds if r['units'] > 1),
        win_rate=round(len(wins) / len(rounds) * 100, 1) if rounds else None,
        total_ret_pct=round(total_ret, 2),
        total_profit_cny=round(total_ret / 100 * 10000, 0),  # 每1% = 100元/单位本金
        open_position=op,
        loss_rounds=[dict(no=i, buy=str(r['buy_date'].date()),
                          add=str(r['add_date'].date()) if r['add_date'] else None,
                          sell=str(r['sell_date'].date()),
                          ret=round(r['ret'], 2)) for i, r in enumerate(rounds, 1) if r['ret'] < 0],
        all_rounds=[dict(no=i, buy=str(r['buy_date'].date()),
                         add=str(r['add_date'].date()) if r['add_date'] else None,
                         sell=str(r['sell_date'].date()), units=r['units'],
                         ret=round(r['ret'], 2)) for i, r in enumerate(rounds, 1)],
    )
    return stats


# ---------------------------------------------------------------- 绘图
def plot_index(idx, d, rounds, out_png):
    fig, ax1 = plt.subplots(figsize=(16, 9), dpi=130)
    ax2 = ax1.twinx()
    th2 = idx['buy_th'] * 1.5

    # 指数收盘价 (左轴)
    ax1.plot(d['date'], d['close'], color='#333333', lw=0.9, label='指数收盘价', zorder=2)

    # MA60偏移率 (右轴)
    ax2.plot(d['date'], d['dev'], color='#4a90d9', lw=0.7, alpha=0.5, label='MA60偏移率(%)', zorder=1)
    ax2.axhline(0, color='#4a90d9', ls=':', lw=0.9, alpha=0.6)
    ax2.axhline(idx['buy_th'], color='orange', ls='--', lw=1.1, alpha=0.8,
                label=f'首买阈值 {idx["buy_th"]}%')
    ax2.axhline(th2, color='purple', ls='--', lw=1.1, alpha=0.8,
                label=f'加仓阈值 {round(th2, 3)}%')
    ax2.set_ylabel('MA60偏移率 (%)', color='#4a90d9', fontsize=11)
    ax2.tick_params(axis='y', labelcolor='#4a90d9')

    # 交易轮次: 买→卖连线 绿=盈利 红=亏损, ★=加仓点
    nw = nl = na = 0
    for i, r in enumerate(rounds, 1):
        win = r['ret'] > 0
        color = '#1a9850' if win else '#d73027'
        if win:
            nw += 1
        else:
            nl += 1
        added = r['units'] > 1
        if added:
            na += 1
        # 每份独立连线
        ax1.plot([r['buy_date'], r['sell_date']], [r['buy_price'], r['sell_price']],
                 color=color, lw=2.2, alpha=0.85, zorder=5)
        if added:
            ax1.plot([r['add_date'], r['sell_date']], [r['add_price'], r['sell_price']],
                     color=color, lw=1.6, alpha=0.65, ls='-', zorder=4)
            ax1.scatter([r['add_date']], [r['add_price']], marker='*', color='purple', s=150,
                        zorder=7, edgecolors='white', linewidths=0.5)
        ax1.scatter([r['buy_date']], [r['buy_price']], marker='^', color='#1a9850', s=75, zorder=6, edgecolors='white', linewidths=0.5)
        ax1.scatter([r['sell_date']], [r['sell_price']], marker='v', color='#d73027', s=75, zorder=6, edgecolors='white', linewidths=0.5)
        mid = r['buy_date'] + (r['sell_date'] - r['buy_date']) / 2
        tag = f'#{i}' + ('*' if added else '')
        ax1.annotate(tag, (mid, (r['buy_price'] + r['sell_price']) / 2),
                     fontsize=7.5, ha='center', color=color, weight='bold', zorder=7)

    stats = dict(n=len(rounds), nw=nw, nl=nl, na=na, tr=sum(r['ret'] for r in rounds))
    ax1.set_title(
        f'{idx["name"]} · MA60偏移率金字塔加仓(1:2)回测 ({d["date"].iloc[0].date()} ~ {d["date"].iloc[-1].date()})  '
        f'规则: 偏移率≤{idx["buy_th"]}%首买1份 / ≤{round(th2, 3)}%加仓2份 / ≥0%清仓\n'
        f'共{stats["n"]}轮: 盈利{stats["nw"]}轮(绿▲) 亏损{stats["nl"]}轮(红▼) 加仓{stats["na"]}轮(紫★) '
        f'胜率{stats["nw"]/stats["n"]*100:.1f}%  总收益{stats["tr"]:+.2f}%(单位本金1万, 收益率加权加总)',
        fontsize=13)
    ax1.set_ylabel('指数点位', fontsize=11)
    ax1.grid(alpha=0.25, ls='--')
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=9, framealpha=0.85)

    fig.tight_layout()
    fig.savefig(out_png, bbox_inches='tight')
    plt.close(fig)
    return stats


# ---------------------------------------------------------------- 企业微信推送
def push_payload(payload, retries=3):
    for i in range(retries):
        try:
            r = requests.post(WEBHOOK, json=payload, timeout=15)
            resp = r.json()
            if resp.get('errcode') == 0:
                return True
            print(f'    [push] errcode={resp.get("errcode")} errmsg={resp.get("errmsg")}, 重试')
        except Exception as e:
            print(f'    [push] 异常: {e}, 重试')
        time.sleep(3)
    return False


def push_image(path):
    with open(path, 'rb') as f:
        b = f.read()
    print(f'    [push] 图片 {os.path.basename(path)} ({len(b)/1024:.0f}KB) ...', end=' ')
    ok = push_payload({'msgtype': 'image', 'image': {
        'base64': base64.b64encode(b).decode(), 'md5': hashlib.md5(b).hexdigest()}})
    print('✓' if ok else '✗')
    return ok


def push_text(content):
    # 企业微信text上限2048字节(UTF-8), 自适应压缩
    def try_push(c):
        print(f'    [push] 文本({len(c.encode("utf-8"))}B) ...', end=' ')
        ok = push_payload({'msgtype': 'text', 'text': {'content': c}})
        print('✓' if ok else '✗')
        return ok
    if len(content.encode('utf-8')) <= 2000:
        return try_push(content)
    # 超长: 去掉亏损轮次收益率
    lines = content.split('\n')
    slim = [ln if not (ln.strip().startswith(tuple('0123456789')) and '%)' in ln)
            else ln.split(' (')[0] + ')' for ln in lines]
    c2 = '\n'.join(slim)
    if len(c2.encode('utf-8')) <= 2000:
        return try_push(c2)
    # 仍超长: 亏损轮次只留编号+日期
    slim2 = [ln.split(' (')[0] if ('~' in ln and ln.strip()[0].isdigit()) else ln for ln in slim]
    c3 = '\n'.join(slim2)
    if len(c3.encode('utf-8')) <= 2000:
        return try_push(c3)
    # 最后兜底: 截断
    return try_push(content[:650] + '\n...(内容过长截断, 详见图表)')


def make_text(idx, d, stats):
    L = []
    L.append(f'📊 {idx["name"]} · MA60偏移率金字塔加仓(1:2)回测')
    L.append(f'数据区间: {stats["data_start"]} ~ {stats["data_end"]} (首个信号自 {stats["signal_start"]})')
    L.append(f'规则: 偏移率≤{idx["buy_th"]}%首买1份, 跌至≤{stats["add_th"]}%加仓2份(首买2倍金额), 回到≥0%清仓; 收盘价成交, 单位本金1万')
    L.append('')
    wr = f' (胜率{stats["win_rate"]}%)' if stats['win_rate'] is not None else ''
    L.append(f'一、共 {stats["total_rounds"]} 轮: 盈利 {stats["win_rounds"]} 轮, 亏损 {stats["loss_cnt"]} 轮{wr}')
    L.append(f'    其中触发加仓 {stats["added_rounds"]} 轮')
    sign = '盈利' if stats['total_ret_pct'] >= 0 else '亏损'
    L.append(f'二、总体{sign}: {stats["total_ret_pct"]:+.2f}% (单位本金1万, 轮收益=各份收益率×金额权重(1:2)加总, 累计{sign}{abs(stats["total_profit_cny"]):,.0f}元)')
    L.append('三、亏损轮次时间段:')
    if not stats['loss_rounds']:
        L.append('  无亏损轮次 ✅')
    else:
        for r in stats['loss_rounds']:
            add_s = f', {r["add"]}加仓' if r['add'] else ''
            L.append(f'  第{r["no"]}轮 {r["buy"]} ~ {r["sell"]} ({r["ret"]:+.1f}%{add_s})')
    if stats.get('open_position'):
        op = stats['open_position']
        add_s = f', {op["add_date"]}加仓' if op.get('add_date') else ''
        L.append(f'注: 有一轮未平仓({op["buy_date"]}买入{add_s}, 已投{op["units"]}单位, 浮动{op["float_ret"]:+.1f}%), 按规则不计入统计')
    L.append('')
    L.append('⚠️ 回测基于历史数据, 仅供参考, 不构成投资建议')
    return '\n'.join(L)


def make_summary_text(all_stats):
    L = ['📈 五大指数 MA60偏移率金字塔加仓(1:2)回测汇总', '',
         '规则: 偏移率≤T1%首买1份, 跌至≤T1×1.5加仓2份(首买2倍), 回到≥0%清仓', '']
    L.append(f'{"指数":<8}{"首买":>6} {"加仓":>7}  {"总轮数":>4} {"盈利":>3} {"亏损":>3} {"加仓轮":>4} {"胜率":>7} {"总收益":>9}')
    for s in all_stats:
        wr = f'{s["win_rate"]}%' if s['win_rate'] is not None else '-'
        L.append(f'{s["name"]:<8}{s["buy_th"]:>6}% {s["add_th"]:>7}%  {s["total_rounds"]:>4} {s["win_rounds"]:>3} {s["loss_cnt"]:>3} {s["added_rounds"]:>4} {wr:>7} {s["total_ret_pct"]:>+9.2f}%')
    L.append('')
    L.append('口径: 收盘判断收盘成交, 未平仓轮排除, 单位本金1万, 轮收益=各份收益率×金额权重(1:2)加总')
    L.append('⚠️ 回测仅供参考, 不构成投资建议')
    return '\n'.join(L)


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--push', action='store_true', help='推送到企业微信')
    ap.add_argument('--refresh', action='store_true', help='强制重拉数据')
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    all_stats = []
    for idx in INDICES:
        print(f'=== {idx["name"]} (阈值 {idx["buy_th"]}%) ===')
        df = load_data(idx, refresh=args.refresh)
        d, rounds, open_lots = backtest(df, idx['buy_th'])
        stats = summarize(idx, d, rounds, open_lots)
        png = os.path.join(OUT_DIR, f'{idx["key"]}_backtest.png')
        plot_index(idx, d, rounds, png)
        all_stats.append(stats)
        print(f'  回测: {stats["total_rounds"]}轮 盈{stats["win_rounds"]} 亏{stats["loss_cnt"]} '
              f'加仓{stats["added_rounds"]}轮 胜率{stats["win_rate"]}% 总收益{stats["total_ret_pct"]:+.2f}% '
              f'未平仓: {"是" if stats["open_position"] else "无"}')

    with open(os.path.join(OUT_DIR, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)
    print(f'\n结果已保存: {OUT_DIR}/results.json')

    if args.push:
        print('\n=== 推送企业微信 ===')
        for idx, stats in zip(INDICES, all_stats):
            png = os.path.join(OUT_DIR, f'{idx["key"]}_backtest.png')
            push_image(png)
            time.sleep(PUSH_INTERVAL)
            push_text(make_text(idx, None, stats))
            time.sleep(PUSH_INTERVAL)
        push_text(make_summary_text(all_stats))
    else:
        print('\n(未推送, --push 启用)')


if __name__ == '__main__':
    main()
