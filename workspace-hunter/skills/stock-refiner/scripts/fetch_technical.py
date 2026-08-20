#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""技术面评估（四面评估之一，全池股运行，纯tushare免费接口，零搜索配额）

用法: python3.11 fetch_technical.py 603338.SH [002192.SZ ...]
输出: JSON到stdout（每股一个对象：趋势/动量/位置/量价/关键位 + 0-10评分 + 择时参考）

评分规则（详见 references/scoring_rules.md 第五节）:
  趋势(4分): 站上MA60且MA60上行+2 | 站上MA250 +1 | MA5>MA10>MA20多头排列 +1
  动量(2分): MACD DIF>DEA或绿柱连续收窄 +1 | RSI14在40~65 +0.5 | KDJ低位金叉/D<40 +0.5
  位置(2分): 52周分位30~70 +1 | 距52周高点回撤<15% +1
  量价(2分): 缩量回调或量价配合 +1.5 | 无顶背离(近60日新高但量能未同步萎缩) +0.5
用途: 不否决选股；输出左侧买点区间+右侧触发条件（择时建议由AI结合本数据生成）
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import tushare as ts

TOKEN = os.environ.get(
    "TUSHARE_TOKEN",
    os.environ.get("TS_TOKEN", "dde651506e87c13c30474693d2c4091345f987a2b8bfffad4989530c"),
)


def get_pro():
    token = TOKEN
    tok_file = os.path.expanduser("~/.tushare_token")
    if not token or token.startswith("dde651506e87c13c30474693d2c4091345f987a2b8bfffad4989530c") is False:
        pass
    if os.path.exists(tok_file):
        try:
            t = open(tok_file).read().strip()
            if t:
                token = t
        except Exception:
            pass
    ts.set_token(token)
    return ts.pro_api()


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def compute(df):
    """df: trade_date ascending, 含 close/high/low/vol/adj_close"""
    c = df["adj_close"]
    v = df["vol"].astype(float)
    out = {}

    # ---- 均线 ----
    for n in [5, 10, 20, 60, 120, 250]:
        df["ma%d" % n] = c.rolling(n).mean()
    last = df.iloc[-1]
    ma = {n: round(float(df["ma%d" % n].iloc[-1]), 2) if not np.isnan(df["ma%d" % n].iloc[-1]) else None
          for n in [5, 10, 20, 60, 120, 250]}
    out["ma"] = ma
    ma60_slope = None
    if len(df) > 65:
        ma60_slope = float(df["ma60"].iloc[-1] / df["ma60"].iloc[-21] - 1) * 100
    out["ma60_20d_slope_pct"] = round(ma60_slope, 2) if ma60_slope is not None else None

    # ---- MACD / RSI / KDJ ----
    ema12, ema26 = ema(c, 12), ema(c, 26)
    dif = ema12 - ema26
    dea = ema(dif, 9)  # type: ignore[arg-type]
    hist = (dif - dea) * 2
    out["macd"] = {"dif": round(float(dif.iloc[-1]), 3),
                   "dea": round(float(dea.iloc[-1]), 3),
                   "hist": round(float(hist.iloc[-1]), 3),
                   "hist_prev": round(float(hist.iloc[-2]), 3),
                   "hist_shrinking_2d": bool(hist.iloc[-1] > hist.iloc[-2] > hist.iloc[-3]) if len(hist) > 3 else None}
    delta = c.diff()
    up = delta.clip(lower=0)
    dn = (-delta).clip(lower=0)
    rs = up.ewm(alpha=1 / 14, adjust=False).mean() / dn.ewm(alpha=1 / 14, adjust=False).mean()
    rsi = 100 - 100 / (1 + rs)
    out["rsi14"] = round(float(rsi.iloc[-1]), 1)

    low9 = df["adj_low"].rolling(9).min() if "adj_low" in df else df["low"].rolling(9).min()
    high9 = df["adj_high"].rolling(9).max() if "adj_high" in df else df["high"].rolling(9).max()
    rsv = (c - low9) / (high9 - low9).replace(0, np.nan) * 100
    k = rsv.ewm(com=2, adjust=False).mean()
    d = k.ewm(com=2, adjust=False).mean()
    j = 3 * k - 2 * d
    out["kdj"] = {"k": round(float(k.iloc[-1]), 1), "d": round(float(d.iloc[-1]), 1), "j": round(float(j.iloc[-1]), 1)}

    # ---- 布林 ----
    mid = c.rolling(20).mean()
    std = c.rolling(20).std()
    out["boll"] = {"upper": round(float((mid + 2 * std).iloc[-1]), 2),
                   "mid": round(float(mid.iloc[-1]), 2),
                   "lower": round(float((mid - 2 * std).iloc[-1]), 2)}

    # ---- 位置 ----
    y252 = df.tail(252)
    hi52, lo52 = float(y252["adj_high"].max()), float(y252["adj_low"].min())
    px = float(c.iloc[-1])
    out["pct_52w"] = round((px - lo52) / (hi52 - lo52) * 100, 1)
    out["pct_5y"] = round((px - float(df["adj_low"].min())) / (float(df["adj_high"].max()) - float(df["adj_low"].min())) * 100, 1) if len(df) > 400 else None
    out["drawdown_52w_high_pct"] = round((px / hi52 - 1) * 100, 1)
    out["high_52w"] = round(hi52, 2)
    out["low_52w"] = round(lo52, 2)
    out["ret_20d_pct"] = round((px / float(c.iloc[-21]) - 1) * 100, 1) if len(df) > 21 else None
    out["ret_60d_pct"] = round((px / float(c.iloc[-61]) - 1) * 100, 1) if len(df) > 61 else None

    # ---- 量价 ----
    v5 = v.rolling(5).mean()
    out["vol_ratio_vs_5d"] = round(float(v.iloc[-1] / v5.iloc[-2]), 2) if len(v) > 6 else None
    vol_20d_trend = None
    if len(df) > 40:
        vol_20d_trend = float(v.tail(20).mean() / v.iloc[-40:-20].mean() - 1) * 100
    out["vol_20d_trend_pct"] = round(vol_20d_trend, 1) if vol_20d_trend is not None else None
    ret20 = out.get("ret_20d_pct")
    out["pattern"] = None
    if ret20 is not None and vol_20d_trend is not None:
        if ret20 < 0 and vol_20d_trend < -10:
            out["pattern"] = "缩量回调"
        elif ret20 > 0 and vol_20d_trend > 10:
            out["pattern"] = "放量上行"
        elif ret20 > 0 and vol_20d_trend < -15:
            out["pattern"] = "缩量上涨(警惕)"
        elif ret20 < 0 and vol_20d_trend > 15:
            out["pattern"] = "放量下跌(警惕)"

    # ---- 关键位 ----
    supports, resistances = [], []
    ma_cluster = [ma[n] for n in [60, 120, 250] if ma[n]]
    if ma_cluster:
        cmin, cmax = min(ma_cluster), max(ma_cluster)
        if cmax / cmin - 1 < 0.05 and px > cmin:  # 粘合带且在上方
            supports.append({"level": round((cmin + cmax) / 2, 2), "type": "中长期均线粘合带(60/120/250)"})
        else:
            below = [m for m in ma_cluster if m < px]
            if below:
                supports.append({"level": max(below), "type": "MA%d" % [n for n in [60, 120, 250] if ma[n] == max(below)][0]})
    if out["boll"]["lower"] < px:
        supports.append({"level": out["boll"]["lower"], "type": "布林下轨"})
    supports.append({"level": round(float(y252["adj_low"].min()), 2), "type": "52周低点"})
    if ma[20] and ma[20] > px:
        resistances.append({"level": ma[20], "type": "MA20"})
    if out["boll"]["upper"] > px:
        resistances.append({"level": out["boll"]["upper"], "type": "布林上轨"})
    resistances.append({"level": out["high_52w"], "type": "52周高点"})
    supports = sorted([s for s in supports if s["level"] < px], key=lambda x: -x["level"])[:2]
    resistances = sorted([r for r in resistances if r["level"] > px], key=lambda x: x["level"])[:2]
    out["supports"] = supports
    out["resistances"] = resistances

    # ---- 评分 ----
    score = 0.0
    details = []
    if ma[60] and px > ma[60] and (ma60_slope or 0) > 0:
        score += 2; details.append("站上MA60且上行+2")
    if ma[250] and px > ma[250]:
        score += 1; details.append("站上MA250+1")
    if ma[5] and ma[10] and ma[20] and ma[5] > ma[10] > ma[20]:
        score += 1; details.append("短均线多头排列+1")
    m = out["macd"]
    if m["dif"] > m["dea"] or m["hist_shrinking_2d"]:
        score += 1; details.append("MACD友好+1")
    if 40 <= out["rsi14"] <= 65:
        score += 0.5; details.append("RSI中性区+0.5")
    if out["kdj"]["d"] < 40 or (out["kdj"]["k"] > out["kdj"]["d"] and out["kdj"]["k"] < 50):
        score += 0.5; details.append("KDJ低位友好+0.5")
    if 30 <= out["pct_52w"] <= 70:
        score += 1; details.append("52周分位中性+1")
    if out["drawdown_52w_high_pct"] > -15:
        score += 1; details.append("距高点回撤<15%+1")
    if out["pattern"] in ("缩量回调", "放量上行"):
        score += 1.5; details.append("量价配合(%s)+1.5" % out["pattern"])
    elif out["pattern"] not in ("缩量上涨(警惕)", "放量下跌(警惕)"):
        score += 0.5; details.append("无量价背离+0.5")
    out["score"] = round(min(score, 10), 1)
    out["score_details"] = details
    return out


def evaluate(ts_code):
    result = {"ts_code": ts_code, "error": None}
    try:
        pro = get_pro()
        import datetime
        start = (datetime.date.today() - datetime.timedelta(days=5 * 365 + 30)).strftime("%Y%m%d")
        end = datetime.date.today().strftime("%Y%m%d")
        daily = pro.daily(ts_code=ts_code, start_date=start, end_date=end)
        af = pro.adj_factor(ts_code=ts_code, start_date=start, end_date=end)
        if daily is None or len(daily) < 30:
            result["error"] = "kline不足"
            return result
        daily = daily.sort_values("trade_date").reset_index(drop=True)
        af = af.sort_values("trade_date").reset_index(drop=True)
        df = daily.merge(af[["trade_date", "adj_factor"]], on="trade_date", how="left")
        df["adj_factor"] = df["adj_factor"].ffill().bfill()
        last_af = df["adj_factor"].iloc[-1]
        df["adj_close"] = df["close"] * df["adj_factor"] / last_af
        df["adj_high"] = df["high"] * df["adj_factor"] / last_af
        df["adj_low"] = df["low"] * df["adj_factor"] / last_af
        result.update(compute(df))
        result["as_of"] = str(df["trade_date"].iloc[-1])
        result["close"] = float(df["close"].iloc[-1])
    except Exception as e:
        result["error"] = str(e)[:200]
    return result


if __name__ == "__main__":
    import time  # noqa
    codes = sys.argv[1:]
    if not codes:
        print("用法: fetch_technical.py 603338.SH [002192.SZ ...]", file=sys.stderr)
        sys.exit(1)
    outs = []
    for code in codes:
        o = evaluate(code)
        outs.append(o)
        print(json.dumps(o, ensure_ascii=False))
        time.sleep(0.6)
