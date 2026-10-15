#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
上证综指股债利差模型（FED Model / ERP）
利差 = 1/上证综指PE(TTM) - 10年期国债收益率
数据源：
  - 指数PE: Tushare index_dailybasic (000001.SH)
  - 10Y国债收益率: akshare bond_zh_us_rate (东方财富-中国国债收益率10年)
输出: 折线图 PNG，可推送企业微信webhook
用法:
  python3.11 scripts/sse_erp_spread.py                # 仅计算+出图
  python3.11 scripts/sse_erp_spread.py --push KEY     # 计算出图并推送
"""
import sys
import time
import json
import base64
import hashlib
import argparse
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 中文字体
for f in font_manager.fontManager.ttflist:
    pass
plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "SimHei", "Noto Sans CJK SC"]
plt.rcParams["axes.unicode_minus"] = False

import tushare as ts
import akshare as ak

START = "20111015"  # 15年前
END = datetime.now().strftime("%Y%m%d")
OUT_PNG = "/tmp/sse_erp_spread.png"


def fetch_sse_pe() -> pd.DataFrame:
    """分批拉取上证综指每日PE（Tushare index_dailybasic）"""
    pro = ts.pro_api()
    frames = []
    # 按年分批，避免单次行数限制
    start_year = int(START[:4])
    end_year = int(END[:4])
    for y in range(start_year, end_year + 1):
        s = f"{y}0101"
        e = f"{y}1231"
        if y == start_year:
            s = START
        if y == end_year:
            e = END
        for attempt in range(3):
            try:
                df = pro.index_dailybasic(
                    ts_code="000001.SH", start_date=s, end_date=e,
                    fields="ts_code,trade_date,pe,pb",
                )
                if df is not None and len(df) > 0:
                    frames.append(df)
                break
            except Exception as ex:
                print(f"  {y}年第{attempt+1}次尝试失败: {ex}", file=sys.stderr)
                time.sleep(3)
        else:
            raise RuntimeError(f"{y}年数据拉取失败")
        time.sleep(0.6)  # 频率控制
    all_df = pd.concat(frames, ignore_index=True)
    all_df["date"] = pd.to_datetime(all_df["trade_date"], format="%Y%m%d")
    all_df = all_df.sort_values("date").reset_index(drop=True)
    all_df["pe"] = pd.to_numeric(all_df["pe"], errors="coerce")
    cols = [c for c in ["date", "pe"] if c in all_df.columns]
    all_df = all_df[cols].dropna(subset=["pe"])
    return all_df


def fetch_cn10y() -> pd.DataFrame:
    """10年期中国国债收益率（东财，%）"""
    df = ak.bond_zh_us_rate()
    df["date"] = pd.to_datetime(df["日期"])
    df = df[["date", "中国国债收益率10年"]].dropna()
    df.columns = ["date", "cn10y"]
    df["cn10y"] = pd.to_numeric(df["cn10y"], errors="coerce")
    return df.sort_values("date").reset_index(drop=True)


def make_chart(spread_df: pd.DataFrame, out_path: str):
    d = spread_df
    ep = d["ep"]
    y10 = d["cn10y"]
    sp = d["spread"]
    sp_mean = sp.mean()
    sp_std = sp.std()
    latest = d.iloc[-1]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(13, 9), sharex=True,
        gridspec_kw={"height_ratios": [3, 2]}, dpi=120,
    )

    # ---- 主图: 股债利差 ----
    ax2.remove()
    ax1.remove()
    # 重新排: 主图在上
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 2], hspace=0.12)
    ax_main = fig.add_subplot(gs[0])
    ax_sub = fig.add_subplot(gs[1], sharex=ax_main)

    ax_main.plot(d["date"], sp, color="#C0392B", lw=1.4, label="股债利差 = 1/PE − 10Y国债")
    ax_main.axhline(sp_mean, color="#2C3E50", ls="--", lw=1.1,
                    label=f"15年均值 {sp_mean:.2f}%")
    ax_main.fill_between(d["date"], sp_mean - sp_std, sp_mean + sp_std,
                         color="#95A5A6", alpha=0.18, label="±1σ 区间")
    ax_main.fill_between(d["date"], sp_mean + sp_std, sp.max() * 1.02,
                         where=sp >= sp_mean + sp_std,
                         color="#27AE60", alpha=0.30, interpolate=True)
    # 当前值标注
    ax_main.annotate(
        f"最新 {latest['date'].strftime('%Y-%m-%d')}\n{sp.iloc[-1]:.2f}%",
        xy=(latest["date"], sp.iloc[-1]),
        xytext=(-95, -32), textcoords="offset points",
        fontsize=10, fontweight="bold", color="#C0392B",
        arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.2),
    )
    ax_main.set_ylabel("利差 (%)", fontsize=11)
    ax_main.set_title(
        "上证综指股债利差（盈利收益率 − 10年期国债收益率）\n"
        f"{d['date'].iloc[0].strftime('%Y-%m')} ~ {d['date'].iloc[-1].strftime('%Y-%m')}"
        "  |  盈利收益率 = 1 ÷ 指数PE，国债 = 中债10Y到期收益率",
        fontsize=13, fontweight="bold",
    )
    ax_main.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax_main.grid(alpha=0.3)
    plt.setp(ax_main.get_xticklabels(), visible=False)

    # ---- 副图: 两条原始序列 ----
    ax_sub.plot(d["date"], ep, color="#2E86C1", lw=1.2, label="上证盈利收益率 1/PE (%)")
    ax_sub.plot(d["date"], y10, color="#E67E22", lw=1.2, label="中国10Y国债收益率 (%)")
    ax_sub.set_ylabel("收益率 (%)", fontsize=11)
    ax_sub.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax_sub.grid(alpha=0.3)

    fig.text(0.99, 0.005,
             f"数据: Tushare指数估值 × 东财中债收益率 | 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             ha="right", fontsize=7.5, color="#7F8C8D")
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return sp_mean, sp_std, latest


def push_wecom(key: str, png_path: str, text: str):
    """推送企业微信群机器人: 图片 + markdown"""
    import requests
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"

    # 1) 图片消息 (base64 + md5, <2MB)
    with open(png_path, "rb") as f:
        raw = f.read()
    print(f"图片大小: {len(raw)/1024:.0f} KB")
    if len(raw) > 2 * 1024 * 1024:
        raise RuntimeError("图片超过2MB限制")
    b64 = base64.b64encode(raw).decode()
    md5 = hashlib.md5(raw).hexdigest()
    r = requests.post(url, json={"msgtype": "image", "image": {"base64": b64, "md5": md5}}, timeout=30)
    print("图片推送:", r.json())
    if r.json().get("errcode") != 0:
        raise RuntimeError(f"图片推送失败: {r.json()}")

    time.sleep(5)  # 防限流

    # 2) markdown 摘要
    r2 = requests.post(url, json={"msgtype": "markdown", "markdown": {"content": text}}, timeout=30)
    print("摘要推送:", r2.json())
    if r2.json().get("errcode") != 0:
        raise RuntimeError(f"摘要推送失败: {r2.json()}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--push", default=None, help="企业微信webhook key，不传则不推送")
    parser.add_argument("--years", type=int, default=15)
    args = parser.parse_args()

    global START
    START = (datetime.now() - timedelta(days=365 * args.years)).strftime("%Y%m%d")

    print(f"[1/4] 拉取上证综指PE {START}~{END} ...")
    pe_df = fetch_sse_pe()
    print(f"  共 {len(pe_df)} 个交易日, 范围 {pe_df['date'].min()} ~ {pe_df['date'].max()}")
    print(f"  最新PE: {pe_df.iloc[-1]['pe']}")

    print("[2/4] 拉取10年期国债收益率 ...")
    y10_df = fetch_cn10y()
    y10_df = y10_df[y10_df["date"] >= pe_df["date"].min() - pd.Timedelta(days=10)]
    print(f"  共 {len(y10_df)} 条, 最新 {y10_df.iloc[-1]['cn10y']}% @ {y10_df.iloc[-1]['date']}")

    print("[3/4] 合并计算 + 画图 ...")
    pe_df["date"] = pe_df["date"].astype("datetime64[ns]")
    y10_df["date"] = y10_df["date"].astype("datetime64[ns]")
    m = pd.merge_asof(pe_df, y10_df, on="date", direction="backward", tolerance=pd.Timedelta("7D"))
    m = m.dropna(subset=["cn10y"]).reset_index(drop=True)
    m["ep"] = 100.0 / m["pe"]          # 盈利收益率 %
    m["spread"] = m["ep"] - m["cn10y"]  # 利差 %
    sp_mean, sp_std, latest = make_chart(m, OUT_PNG)
    pct_rank = (m["spread"] < m["spread"].iloc[-1]).mean() * 100
    print(f"  图表已保存: {OUT_PNG}")
    print(f"  最新利差: {m['spread'].iloc[-1]:.2f}% | 均值 {sp_mean:.2f}% | σ {sp_std:.2f} | 历史分位 {pct_rank:.0f}%")

    if args.push:
        print("[4/4] 推送企业微信 ...")
        summary = (
            f"**上证综指股债利差（FED模型）**\n"
            f"最新（{latest['date'].strftime('%Y-%m-%d')}）：\n"
            f"> 指数PE：{latest['pe']:.2f}，盈利收益率 1/PE：{100/latest['pe']:.2f}%\n"
            f"> 10Y国债：{latest['cn10y']:.2f}%\n"
            f"> **利差：{m['spread'].iloc[-1]:.2f}%**（15年分位 {pct_rank:.0f}%，均值 {sp_mean:.2f}%，+1σ线 {sp_mean+sp_std:.2f}%）\n"
            f"利差处于高位 → 股票相对债券偏便宜；低位 → 债券相对占优。"
        )
        push_wecom(args.push, OUT_PNG, summary)
        print("推送完成 ✅")
    else:
        print("[4/4] 未指定 --push，跳过推送")
        print(summary if False else "")


if __name__ == "__main__":
    main()
