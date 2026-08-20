#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""消息面事件收集（四面评估之三的数据层，全池股运行，纯免费API，零搜索配额）

只负责收集结构化事实：近30天公告分类 + 未来事件日历(财报预约/解禁)。
舆情搜索(≤2次/股)与利空严重度判断由AI在Step 4b完成。

用法: python3.11 fetch_news_signals.py 603338.SH [002192.SZ ...]
输出: JSON到stdout（每股一个对象）

公告分类规则（关键词匹配，AI复核边界案例）:
  利好: 回购/增持/中标/预增/扭亏/分红/股权激励/员工持股/产能投产/战略合作
  利空: 减持/质押/诉讼/仲裁/立案/问询/警示/监管/处罚/预减/首亏/非标/退市/终止
  中性: 定期报告/大会/章程等
"""
import sys
import json
import time
import datetime
import requests

POS_KW = ["回购", "增持", "中标", "预增", "扭亏", "分红", "派息", "股权激励", "员工持股", "投产", "战略合作", "签订", "订单"]
NEG_KW = ["减持", "质押", "诉讼", "仲裁", "立案", "问询", "警示", "监管", "处罚", "预减", "首亏", "非标", "退市", "终止", "冻结", "违规"]
NEUTRAL_KW = ["季度报告", "年度报告", "半年度报告", "股东大会", "章程", "摘要", "提示性", "更正", "补充", "会计师事务所", "审计", "独立董事"]


def classify(title):
    t = title or ""
    for kw in NEG_KW:
        if kw in t:
            return "利空", kw
    for kw in POS_KW:
        if kw in t:
            return "利好", kw
    for kw in NEUTRAL_KW:
        if kw in t:
            return "中性", kw
    return "其他", None


def em_announcements(code6, days=30):
    """东财公告列表（np-anotise-stock，不带begin_time参数否则返回0条），本地过滤近N天"""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    out = []
    for page in range(1, 3):  # 最多2页100条，覆盖30天足够
        try:
            r = requests.get(
                "https://np-anotice-stock.eastmoney.com/api/security/ann",
                params={"sr": -1, "page_size": 50, "page_index": page,
                        "ann_type": "A", "client_source": "web", "stock_list": code6,
                        "f_node": "0", "s_node": "0"},
                timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            lst = (r.json() or {}).get("data", {}).get("list", [])
            if not lst:
                break
            stop = False
            for a in lst:
                title = (a.get("title") or "").strip()
                cd = (a.get("notice_date") or "")[:10]
                try:
                    if cd and datetime.date.fromisoformat(cd) < start:
                        stop = True
                        continue
                except ValueError:
                    continue
                out.append({"art_code": a.get("art_code"), "title": title, "date": cd})
            if stop or len(lst) < 50:
                break
        except Exception:
            break
        time.sleep(0.3)
    return out


def evaluate(ts_code, pro=None):
    out = {"ts_code": ts_code}
    code6 = ts_code[:6]

    # ---- 近30天公告分类 ----
    anns = em_announcements(code6)
    pos, neg, neutral = [], [], []
    for a in anns:
        cat, kw = classify(a["title"])
        a["cat"] = cat
        if cat == "利好":
            pos.append(a)
        elif cat == "利空":
            neg.append(a)
        elif cat == "中性":
            neutral.append(a)
    out["anns_30d"] = {"total": len(anns), "pos": pos, "neg": neg, "neutral": len(neutral)}

    # ---- 未来事件日历 ----
    cal = []
    # 财报预约（tushare disclosure_date）
    if pro is not None:
        today = datetime.date.today()
        # 最近一个未披露报告期: 计算当前应关注的报告期
        y, m = today.year, today.month
        candidates = []
        if m >= 10:
            candidates = ["%d0930" % y, "%d0630" % y, "%d0331" % y]
        elif m >= 7:
            candidates = ["%d0630" % y, "%d0331" % y, "%d1231" % (y - 1)]
        elif m >= 4:
            candidates = ["%d0331" % y, "%d1231" % (y - 1)]
        else:
            candidates = ["%d1231" % (y - 1), "%d0930" % (y - 1)]
        for ed in candidates[:2]:
            try:
                d = pro.disclosure_date(end_date=ed, ts_code=ts_code)
                if d is not None and len(d):
                    row = d.iloc[0]
                    actual = row.get("actual_date")
                    pre = row.get("pre_date")
                    if not actual:  # 未披露才放入日历
                        cal.append({"type": "财报披露", "report_period": ed,
                                    "scheduled": str(pre) if pre else None})
                        break
            except Exception:
                pass
        # 解禁
        try:
            sf_ = pro.share_float(ts_code=ts_code, start_date=today.strftime("%Y%m%d"),
                                  end_date=(today + datetime.timedelta(days=180)).strftime("%Y%m%d"))
            if sf_ is not None and len(sf_):
                sf_ = sf_.sort_values("float_date")
                for _, r in sf_.head(3).iterrows():
                    ratio = r.get("float_ratio")
                    cal.append({"type": "限售解禁", "date": str(r.get("float_date")),
                                "float_ratio_pct": float(ratio) if ratio is not None else None})
        except Exception:
            pass
    out["event_calendar"] = cal

    # ---- 消息新鲜度提示 ----
    if pos or neg:
        out["freshness_note"] = "所有公告均已带日期；距今>7天的市场多半已消化(财报催化剂教训)"
    return out


if __name__ == "__main__":
    codes = sys.argv[1:]
    if not codes:
        print("用法: fetch_news_signals.py 603338.SH [...]", file=sys.stderr)
        sys.exit(1)
    pro = None
    try:
        import os
        import tushare as ts
        token = os.environ.get("TUSHARE_TOKEN", "")
        tok_file = os.path.expanduser("~/.tushare_token")
        if os.path.exists(tok_file):
            t = open(tok_file).read().strip()
            if t:
                token = t
        if token:
            ts.set_token(token)
            pro = ts.pro_api()
    except Exception:
        pro = None
    for code in codes:
        print(json.dumps(evaluate(code, pro), ensure_ascii=False))
        time.sleep(0.8)
