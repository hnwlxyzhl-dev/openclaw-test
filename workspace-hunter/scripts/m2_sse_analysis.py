#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
M2同比增速 vs 上证指数 点位关系分析（2010-01 至今）

数据源：
  - M2同比增长率: akshare macro_china_money_supply()（央行口径，月度）
  - 上证指数点位: akshare stock_zh_index_daily('sh000001')，取每月最后交易日收盘价

输出：
  - 双轴折线图 PNG（左轴: M2同比%，右轴: 上证指数点位）
  - 推送企业微信 Webhook（image 类型）
"""

import base64
import hashlib
import json
import sys
import urllib.request
from datetime import datetime

import akshare as ak
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

WEBHOOK_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    "?key=bc5c29fd-9a4a-4dc1-b1d7-f1cc75916a43"
)
OUTPUT_PNG = "/tmp/m2_sse_chart.png"
START_YEAR = 2010


def get_m2_yoy() -> pd.DataFrame:
    """获取M2同比增长率，返回 DataFrame[month: period, m2_yoy: float]"""
    df = ak.macro_china_money_supply()
    # 月份格式: "2026年08月份" → 统一为月初日期（与上证月度对齐用）
    parts = df["月份"].str.extract(r"(\d{4})年(\d{2})月")
    df["month"] = pd.to_datetime(parts[0] + "-" + parts[1], format="%Y-%m")
    df["m2_yoy"] = pd.to_numeric(df["货币和准货币(M2)-同比增长"], errors="coerce")
    df = df[["month", "m2_yoy"]].dropna().sort_values("month").reset_index(drop=True)
    return df


def get_sse_monthly() -> pd.DataFrame:
    """上证指数日线 → 月度收盘价（每月最后交易日）"""
    df = ak.stock_zh_index_daily(symbol="sh000001")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    monthly = (
        df.set_index("date")["close"]
        .resample("ME")
        .last()
        .dropna()
        .reset_index()
        .rename(columns={"date": "month", "close": "sse_close"})
    )
    # 月末日期 → 月初，与M2对齐
    monthly["month"] = monthly["month"] - pd.offsets.MonthBegin(1)
    return monthly


def build_chart(m2: pd.DataFrame, sse: pd.DataFrame) -> pd.DataFrame:
    """合并数据并画双轴折线图"""
    merged = pd.merge(m2, sse, on="month", how="inner")
    merged = merged[merged["month"].dt.year >= START_YEAR].reset_index(drop=True)

    plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax1 = plt.subplots(figsize=(14, 7), dpi=100)

    # 左轴: M2同比增速
    ax1.plot(
        merged["month"], merged["m2_yoy"],
        color="#d62728", linewidth=1.8, label="M2同比增长率(%)"
    )
    ax1.set_xlabel("时间", fontsize=12)
    ax1.set_ylabel("M2同比增长率(%)", color="#d62728", fontsize=12)
    ax1.tick_params(axis="y", labelcolor="#d62728")
    ax1.grid(True, alpha=0.3)

    # 右轴: 上证指数点位
    ax2 = ax1.twinx()
    ax2.plot(
        merged["month"], merged["sse_close"],
        color="#1f77b4", linewidth=1.8, label="上证指数收盘点位"
    )
    ax2.set_ylabel("上证指数点位", color="#1f77b4", fontsize=12)
    ax2.tick_params(axis="y", labelcolor="#1f77b4")

    # 图例合并
    l1, la1 = ax1.get_legend_handles_labels()
    l2, la2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, la1 + la2, loc="upper right", fontsize=11)

    title = (
        f"M2同比增长率 vs 上证指数（{START_YEAR}年至今）\n"
        f"数据截至 {merged['month'].max().strftime('%Y-%m')}"
        f" | M2: {merged['m2_yoy'].iloc[-1]:.1f}%"
        f" | 上证: {merged['sse_close'].iloc[-1]:.0f}点"
    )
    plt.title(title, fontsize=14)
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, bbox_inches="tight")
    plt.close()
    print(f"📊 图表已保存: {OUTPUT_PNG}，共 {len(merged)} 个月度数据点")
    return merged


def push_wecom(png_path: str) -> bool:
    """推送图片到企业微信webhook。注意: errcode=0才代表真正送达"""
    with open(png_path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    md5 = hashlib.md5(img_bytes).hexdigest()
    print(f"图片大小: {len(img_bytes)/1024:.0f} KB（企业微信限制2MB）")

    payload = {
        "msgtype": "image",
        "image": {"base64": b64, "md5": md5},
    }
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if result.get("errcode") == 0:
        print("✅ 企业微信推送成功")
        return True
    print(f"❌ 企业微信推送失败: {result}")
    return False


def main():
    print(f"⏰ 运行时间: {datetime.now()}")
    print("=" * 50)

    print("1️⃣ 获取M2同比增长率...")
    m2 = get_m2_yoy()
    print(f"   {len(m2)} 条, {m2['month'].min():%Y-%m} ~ {m2['month'].max():%Y-%m}")

    print("2️⃣ 获取上证指数月度收盘...")
    sse = get_sse_monthly()
    print(f"   {len(sse)} 条, {sse['month'].min():%Y-%m} ~ {sse['month'].max():%Y-%m}")

    print("3️⃣ 合并数据并绘制图表...")
    merged = build_chart(m2, sse)
    print(f"   合并后: {merged['month'].min():%Y-%m} ~ {merged['month'].max():%Y-%m}")

    print("4️⃣ 推送企业微信...")
    ok = push_wecom(OUTPUT_PNG)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
