#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""资金面评估（四面评估之二，全池股运行，tushare免费接口+东财datacenter，零搜索配额）

用法: python3.11 fetch_capital.py 603338.SH [002192.SZ ...]
输出: JSON到stdout（每股一个对象：主力资金/两融/筹码/大宗/解禁/龙虎榜 + 0-10评分 + 警示标记）

评分规则（详见 references/scoring_rules.md 第五节）:
  主力资金(4分): 近10日主力(超大+大单)净流入>0 +1.5 | 近5日vs前5日改善 +1 | 量价配合无背离 +1 | 净流入>流通市值0.3% +0.5
  杠杆(1.5分): 融资余额20日变化 -5%~+15%均衡 +1.5 | +15~25%偏热 +0.5 | 其他 +0
  筹码(1.5分): 最新一期股东户数环比下降 +1.5 | 上升 +0
  事件(3分): 基础3分；大宗折价>5% -1 | 未来6个月解禁>流通盘5% -1 | 近60日龙虎榜上榜且卖方机构席位 -1
警示(不扣分单独标): 流入价跌=吸筹嫌疑 | 流出价涨=出货嫌疑
"""
import os
import sys
import json
import time
import datetime
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
    if os.path.exists(tok_file):
        try:
            t = open(tok_file).read().strip()
            if t:
                token = t
        except Exception:
            pass
    ts.set_token(token)
    return ts.pro_api()


def safe_div(a, b):
    try:
        if a is None or b is None or b == 0:
            return None
        return round(a / b, 4)
    except Exception:
        return None


def pct(a, b):
    try:
        if a is None or b is None or b == 0:
            return None
        return round((a / b - 1) * 100, 2)
    except Exception:
        return None


def em_float_mkv(pro, ts_code):
    """流通市值(亿元) via 东财行情API，失败返回None"""
    try:
        import requests
        market = "1" if ts_code.endswith(".SH") else "0"
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        r = requests.get(url, params={"secid": "%s.%s" % (market, ts_code[:6]),
                                      "fields": "f43,f84,f85,f116,f117"},
                         timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        d = r.json().get("data") or {}
        f117 = d.get("f117")  # 流通市值
        if f117:
            return float(f117) / 1e8
    except Exception:
        pass
    return None


def em_lhb(code6):
    """近60日东财龙虎榜上榜次数，失败返回None"""
    try:
        import requests
        end = datetime.date.today().strftime("%Y-%m-%d")
        start = (datetime.date.today() - datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        params = {"reportName": "R_DAILYBILLBOARD_DETAILSNEW", "columns": "ALL",
                  "filter": '(SECURITY_CODE="%s")(TRADE_DATE>=\'%s\')(TRADE_DATE<=\'%s\')' % (code6, start, end),
                  "pageSize": 50, "pageNumber": 1}
        r = requests.get(url, params=params, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        rows = (r.json().get("result") or {}).get("data") or []
        return rows
    except Exception:
        return None


def evaluate(ts_code):
    pro = get_pro()
    out = {"ts_code": ts_code, "flags": [], "warnings": [], "score_details": []}
    today = datetime.date.today()
    d0 = today.strftime("%Y%m%d")
    d_start_60 = (today - datetime.timedelta(days=90)).strftime("%Y%m%d")
    d_start_20 = (today - datetime.timedelta(days=40)).strftime("%Y%m%d")
    score = 0.0

    # ---- 1. 主力资金 (moneyflow) ----
    try:
        mf = pro.moneyflow(ts_code=ts_code, start_date=d_start_20, end_date=d0)
        if mf is not None and len(mf) >= 10:
            mf = mf.sort_values("trade_date").reset_index(drop=True)
            for col in ["buy_elg_amount", "sell_elg_amount", "buy_lg_amount", "sell_lg_amount"]:
                mf[col] = pd.to_numeric(mf[col], errors="coerce")
            mf["main_net"] = (mf["buy_elg_amount"] - mf["sell_elg_amount"]) + (mf["buy_lg_amount"] - mf["sell_lg_amount"])
            mf["main_net"] = mf["main_net"] * 1000  # 千元→元
            net10 = float(mf["main_net"].tail(10).sum())
            net5 = float(mf["main_net"].tail(5).sum())
            prev5 = float(mf["main_net"].iloc[-10:-5].sum())
            out["main_net_inflow_10d_yi"] = round(net10 / 1e8, 3)
            out["main_net_5d_yi"] = round(net5 / 1e8, 3)
            out["main_net_prev5d_yi"] = round(prev5 / 1e8, 3)
            if net10 > 0:
                score += 1.5; out["score_details"].append("10日主力净流入+1.5")
            if net5 > prev5:
                score += 1; out["score_details"].append("近5日环比改善+1")
            # 与价格交叉验证
            px = pro.daily(ts_code=ts_code, start_date=d_start_20, end_date=d0)
            if px is not None and len(px) >= 10:
                px = px.sort_values("trade_date").reset_index(drop=True)
                chg10 = float(px["close"].iloc[-1] / px["close"].iloc[-11] - 1) * 100
                out["price_chg_10d_pct"] = round(chg10, 2)
                if net10 > 0 and chg10 < -3:
                    out["warnings"].append("资金流入但价跌10日%.1f%%：吸筹嫌疑或接飞刀" % chg10)
                elif net10 < 0 and chg10 > 3:
                    out["warnings"].append("资金流出但价涨10日%.1f%%：出货嫌疑" % chg10)
                else:
                    score += 1; out["score_details"].append("量价(资金)配合+1")
            fmkb = em_float_mkv(pro, ts_code)
            if fmkb and net10 > 0:
                ratio = net10 / (fmkb * 1e8) * 100
                out["main_net_10d_over_floatmk_pct"] = round(ratio, 3)
                if ratio > 0.3:
                    score += 0.5; out["score_details"].append("净流入>流通市值0.3%+0.5")
        else:
            out["main_flow"] = "数据不足"
    except Exception as e:
        out["main_flow"] = "获取失败: %s" % str(e)[:80]

    # ---- 2. 两融 ----
    try:
        mg = pro.margin_detail(ts_code=ts_code, start_date=(today - datetime.timedelta(days=60)).strftime("%Y%m%d"), end_date=d0)
        if mg is not None and len(mg) >= 10:
            mg = mg.sort_values("trade_date").reset_index(drop=True)
            mg["rzye"] = pd.to_numeric(mg["rzye"], errors="coerce")
            n = min(len(mg) - 1, 20)
            chg = pct(float(mg["rzye"].iloc[-1]), float(mg["rzye"].iloc[-1 - n]))
            out["rzye_yi"] = round(float(mg["rzye"].iloc[-1]) / 1e8, 2)
            out["rzye_20d_chg_pct"] = chg
            if chg is not None:
                if -5 <= chg <= 15:
                    score += 1.5; out["score_details"].append("两融均衡+1.5")
                elif 15 < chg <= 25:
                    score += 0.5; out["score_details"].append("两融偏热+0.5")
                elif chg > 25:
                    out["warnings"].append("融资余额20日+%.1f%%过热" % chg)
                else:
                    out["warnings"].append("融资余额20日%.1f%%退潮" % chg)
    except Exception as e:
        out["margin"] = "获取失败: %s" % str(e)[:80]

    # ---- 3. 筹码：股东户数（多期趋势，老板要求优选下降趋势 2026-08-20）----
    try:
        hn = pro.stk_holdernumber(ts_code=ts_code, start_date=(today - datetime.timedelta(days=420)).strftime("%Y%m%d"), end_date=d0)
        if hn is not None and len(hn) >= 2:
            hn = hn.copy()
            hn["holder_num"] = pd.to_numeric(hn["holder_num"], errors="coerce")
            hn = hn.dropna(subset=["holder_num"]).sort_values(["end_date", "ann_date"]).drop_duplicates("end_date", keep="last").reset_index(drop=True)
            if len(hn) >= 2:
                recent = hn.tail(5).reset_index(drop=True)  # 最近5期（月度披露，约5个月）
                qoq = [pct(float(recent["holder_num"].iloc[i]), float(recent["holder_num"].iloc[i - 1]))
                       for i in range(1, len(recent))]
                consec_down = 0
                for q in reversed(qoq):
                    if q is not None and q < 0:
                        consec_down += 1
                    else:
                        break
                trend_4p = pct(float(recent["holder_num"].iloc[-1]), float(recent["holder_num"].iloc[0])) if len(recent) >= 2 else None
                out["holder_num"] = {
                    "end_date": str(recent["end_date"].iloc[-1]), "num": int(recent["holder_num"].iloc[-1]),
                    "qoq_pct": qoq[-1] if qoq else None,
                    "trend": {"periods": [str(x) for x in recent["end_date"]], "nums": [int(x) for x in recent["holder_num"]],
                              "qoq_pct_list": qoq, "consecutive_down_periods": consec_down,
                              "chg_over_periods_pct": trend_4p},
                }
                # 评分：连续≥2期下降=强集中 +1.5 | 仅最新一期下降 +1 | 上升 +0
                if consec_down >= 2:
                    score += 1.5; out["score_details"].append("股东户数连续%d期下降(筹码集中)+1.5" % consec_down)
                elif qoq and qoq[-1] is not None and qoq[-1] < 0:
                    score += 1; out["score_details"].append("股东户数最新一期环比%.1f%%下降 +1" % qoq[-1])
                else:
                    out["score_details"].append("股东户数未现下降趋势 +0")
                # 警示：5期累计升幅过大
                if trend_4p is not None and trend_4p > 20:
                    out["warnings"].append("股东户数%d期累计+%.1f%%明显分散(散户进场)" % (len(recent) - 1, trend_4p))
    except Exception as e:
        out["holders"] = "获取失败: %s" % str(e)[:80]

    # ---- 4. 大宗交易 ----
    try:
        bt = pro.block_trade(ts_code=ts_code, start_date=d_start_60, end_date=d0)
        n_bt = 0 if bt is None else len(bt)
        out["block_trade_90d"] = n_bt
        if n_bt:
            bt = bt.copy()
            bt["premium"] = pd.to_numeric(bt.get("premium"), errors="coerce")
            bt["price"] = pd.to_numeric(bt.get("price"), errors="coerce")
            worst = float(np.nanmin(bt["premium"].values)) if "premium" in bt else None
            out["block_trade_worst_premium_pct"] = worst
            if worst is not None and worst < -5:
                out["flags"].append("大宗折价%.1f%%超5%%" % worst)
    except Exception as e:
        out["block_trade"] = "获取失败: %s" % str(e)[:80]

    # ---- 5. 解禁 ----
    try:
        sf_ = pro.share_float(ts_code=ts_code, start_date=d0, end_date=(today + datetime.timedelta(days=365)).strftime("%Y%m%d"))
        n_sf = 0 if sf_ is None else len(sf_)
        out["float_events_12m"] = n_sf
        if n_sf:
            sf_ = sf_.sort_values("float_date")
            ratios = pd.to_numeric(sf_.get("float_ratio"), errors="coerce").dropna()
            mx = float(ratios.max()) if len(ratios) else None
            out["float_max_ratio_pct"] = mx
            if mx is not None and mx > 5:
                out["flags"].append("未来12个月最大解禁占比%.1f%%" % mx)
    except Exception as e:
        out["share_float"] = "获取失败: %s" % str(e)[:80]

    # ---- 6. 龙虎榜 ----
    try:
        rows = em_lhb(ts_code[:6])
        if rows is None:
            out["lhb_60d"] = None
        else:
            out["lhb_60d"] = len(rows)
            if rows:
                out["flags"].append("近60日龙虎榜上榜%d次(需人工看席位)" % len(rows))
    except Exception:
        out["lhb_60d"] = None

    # ---- 事件分 ----
    event = 3.0 - 1.0 * len(out["flags"])
    out["score_details"].append("事件分(基础3-警示%d)=%.1f" % (len(out["flags"]), event))
    score += event

    out["score"] = round(max(0.0, min(score, 10)), 1)
    # 清理NaN（跨语言JSON兼容）
    def clean(o):
        if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list): return [clean(v) for v in o]
        if isinstance(o, float) and (np.isnan(o) or np.isinf(o)): return None
        return o
    out = clean(out)
    return out


if __name__ == "__main__":
    codes = sys.argv[1:]
    if not codes:
        print("用法: fetch_capital.py 603338.SH [002192.SZ ...]", file=sys.stderr)
        sys.exit(1)
    for code in codes:
        o = evaluate(code)
        print(json.dumps(o, ensure_ascii=False))
        time.sleep(0.8)
