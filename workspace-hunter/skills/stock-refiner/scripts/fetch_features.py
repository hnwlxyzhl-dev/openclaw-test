#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""获取个股多年量化特征（成长/周期/价值判定用，Layer-1证据）

用法: python3.11 fetch_features.py 002192.SZ [600519.SH ...]
输出: JSON到stdout（每股一个对象，含年营收/净利序列与计算特征）

特征清单:
  - rev_cagr_3y / rev_cagr_5y       营收复合增速
  - netprofit_cv_5y                 净利润波动系数(标准差/均值, >0.8周期嫌疑)
  - boom_bust_signature             繁荣-萧条签名(某年yoy>+50%且某年yoy<-30%)
  - gross_margin_range_5y           毛利率5年极差(pct, >15周期嫌疑)
  - latest_np_yoy_over_rev_yoy      最新年报净利增速/营收增速(>2.5价格驱动嫌疑)
  - neg_rev_years_5y                近5年营收负增长年数
  - roe_dt_series                   扣非ROE年度序列(看斜率: 价值股平稳/成长股上行)
"""
import os
import sys
import json
import time
import numpy as np
import tushare as ts

TOKEN = os.environ.get("TUSHARE_TOKEN", "dde651506e87c13c30474693d2c4091345f987a2b8bfffad4989530c")
pro = ts.pro_api(TOKEN)


def sf(x):
    try:
        x = float(x)
        if np.isnan(x) or np.isinf(x):
            return None
        return round(x, 4)
    except (TypeError, ValueError):
        return None


def growth(curr, base):
    if curr is None or base is None or base == 0:
        return None
    return (curr - base) / abs(base) * 100.0


def cagr(latest, earliest, years):
    if latest is None or earliest is None or years <= 0 or earliest <= 0:
        return None
    ratio = latest / earliest
    if ratio <= 0:
        return None
    return (ratio ** (1.0 / years) - 1.0) * 100.0


def get_features(ts_code):
    out = {"ts_code": ts_code, "errors": []}
    this_year = int(time.strftime("%Y"))
    start = "%d0101" % (this_year - 9)

    # 基本信息+行业
    try:
        basic = pro.stock_basic(ts_code=ts_code, fields="ts_code,name,industry,list_date")
        if not basic.empty:
            out["name"] = basic.iloc[0]["name"]
            out["industry"] = basic.iloc[0]["industry"]
            out["list_date"] = basic.iloc[0]["list_date"]
    except Exception as e:
        out["errors"].append("basic: %s" % e)

    # 年度利润表（近9个年报）
    try:
        inc = pro.income(ts_code=ts_code, start_date=start,
                         fields="ts_code,end_date,report_type,total_revenue,n_income_attr_p")
        inc = inc[inc["report_type"] == "1"]
        inc = inc[inc["end_date"].str.endswith("1231")].drop_duplicates(subset=["end_date"])
        inc = inc.sort_values("end_date", ascending=True).tail(9)
    except Exception as e:
        out["errors"].append("income: %s" % e)
        inc = None

    rev_y = np_y = None
    if inc is not None and not inc.empty:
        rev_y = [sf(v) for v in inc["total_revenue"].tolist()]
        np_y = [sf(v) for v in inc["n_income_attr_p"].tolist()]
        years = inc["end_date"].tolist()
        out["annual_report_dates"] = years
        out["annual_revenue"] = rev_y
        out["annual_net_profit"] = np_y

        rev_yoy = [growth(rev_y[i], rev_y[i - 1]) for i in range(1, len(rev_y))]
        np_yoy = [growth(np_y[i], np_y[i - 1]) for i in range(1, len(np_y))]
        out["rev_yoy_pct"] = rev_yoy
        out["np_yoy_pct"] = np_yoy

        # CAGR（用最近可用年份）
        if len(rev_y) >= 4 and rev_y[-4]:
            out["rev_cagr_3y"] = cagr(rev_y[-1], rev_y[-4], 3)
        if len(rev_y) >= 6 and rev_y[-6]:
            out["rev_cagr_5y"] = cagr(rev_y[-1], rev_y[-6], 5)

        # 净利润CV（近5年，均值需>0）
        if len(np_y) >= 5:
            seg = [v for v in np_y[-5:] if v is not None]
            if len(seg) >= 4 and np.mean(seg) > 0:
                out["netprofit_cv_5y"] = round(float(np.std(seg) / np.mean(seg)), 4)
            elif len(seg) >= 4:
                out["netprofit_cv_5y"] = None
                out["netprofit_cv_note"] = "5年均值为负(曾深度亏损), 本身即周期/困境信号"

        # 繁荣-萧条签名（全样本yoy）
        valid = [v for v in np_yoy if v is not None]
        if valid:
            out["boom_bust_signature"] = bool(max(valid) > 50 and min(valid) < -30)
            out["np_yoy_max"] = round(max(valid), 2)
            out["np_yoy_min"] = round(min(valid), 2)

        # 负增长年（近5年营收）
        if len(rev_yoy) >= 4:
            out["neg_rev_years_5y"] = int(sum(1 for v in rev_yoy[-5:] if v is not None and v < 0))

        # 增速比（最新年报）
        if rev_yoy and np_yoy and rev_yoy[-1] is not None and np_yoy[-1] is not None and rev_yoy[-1] > 0:
            out["latest_np_yoy_over_rev_yoy"] = round(np_yoy[-1] / rev_yoy[-1], 3)
    else:
        out["errors"].append("no annual income data")

    # 年度财务指标（毛利率/扣非ROE）
    try:
        fin = pro.fina_indicator(ts_code=ts_code, start_date=start,
                                 fields="ts_code,end_date,grossprofit_margin,roe_dt")
        fin = fin[fin["end_date"].str.endswith("1231")].drop_duplicates(subset=["end_date"])
        fin = fin.sort_values("end_date", ascending=True).tail(6)
        if not fin.empty:
            gm = [sf(v) for v in fin["grossprofit_margin"].tolist()]
            roe = [sf(v) for v in fin["roe_dt"].tolist()]
            out["gross_margin_series"] = gm
            out["roe_dt_series"] = roe
            seg = [v for v in gm[-5:] if v is not None]
            if len(seg) >= 3:
                out["gross_margin_range_5y"] = round(max(seg) - min(seg), 2)
    except Exception as e:
        out["errors"].append("fina_indicator: %s" % e)

    return out


if __name__ == "__main__":
    codes = [c for c in sys.argv[1:] if not c.startswith("-")]
    if not codes:
        print(json.dumps({"error": "usage: fetch_features.py TS_CODE [TS_CODE ...]"}, ensure_ascii=False))
        sys.exit(1)
    results = []
    for code in codes:
        results.append(get_features(code))
        time.sleep(0.35)  # tushare限速
    print(json.dumps(results, ensure_ascii=False, indent=1, allow_nan=False))
