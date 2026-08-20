#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""获取最新定期报告元数据（tushare）+ 东方财富官方PDF（下载/取链接）

用法:
  python3.11 fetch_latest_report.py 002192.SZ                # 元数据+PDF链接
  python3.11 fetch_latest_report.py 002192.SZ --download     # 下载PDF到 skill data/report_pdfs/
输出: JSON到stdout

要点:
  - tushare 取正式财报最新 f_ann_date/end_date（report_type=1），校验距今<=5个月(153天)
  - 东方财富公告API(np-anotice-stock.eastmoney.com)按股票查"财务报告"类公告(f_node=1)，
    标题过滤：含 年度报告/半年度报告/季度报告 且排除 摘要/英文/取消/更正/补充/退市
  - PDF: https://pdf.dfcfw.com/pdf/H2_{art_code}_1.pdf
  - 标题自带"公司名:"前缀，脚本自动校验与tushare股票名一致（防串号，20260819实测巨潮
    纯代码查询会返回无关公司公告，已弃用巨潮改东财）
"""
import os
import sys
import json
import time
import datetime
import requests
import tushare as ts

TOKEN = os.environ.get("TUSHARE_TOKEN", "dde651506e87c13c30474693d2c4091345f987a2b8bfffad4989530c")
pro = ts.pro_api(TOKEN)

PDF_DIR = os.path.expanduser("~/.openclaw/workspace-hunter/skills/stock-refiner/data/report_pdfs")
EM_ANN_URL = "https://np-anotice-stock.eastmoney.com/api/security/ann"
EM_PDF_URL = "https://pdf.dfcfw.com/pdf/H2_{art}_1.pdf"

EXCLUDE_KEYS = ["摘要", "英文", "取消", "更正", "补充", "退市", "说明会", "已回复", "全文文本", "公告板"]
REPORT_KEYS = ["年度报告", "半年度报告", "第一季度报告", "第三季度报告", "季度报告"]


def get_stock_name(ts_code):
    try:
        df = pro.stock_basic(ts_code=ts_code, fields="ts_code,name")
        return df.iloc[0]["name"] if not df.empty else None
    except Exception:
        return None


def get_latest_from_tushare(ts_code):
    start = (datetime.datetime.now() - datetime.timedelta(days=550)).strftime("%Y%m%d")
    df = pro.income(ts_code=ts_code, start_date=start,
                    fields="ts_code,end_date,f_ann_date,report_type")
    df = df[df["report_type"] == "1"].drop_duplicates(subset=["end_date"])
    if df.empty:
        return None
    df = df.sort_values("end_date", ascending=False)
    row = df.iloc[0]
    f_ann = str(row.get("f_ann_date", ""))
    end_date = str(row["end_date"])
    age_days = None
    if f_ann and f_ann != "nan":
        age_days = (datetime.datetime.now() - datetime.datetime.strptime(f_ann, "%Y%m%d")).days
    return {
        "latest_report_end_date": end_date,
        "latest_report_ann_date": f_ann if f_ann != "nan" else None,
        "ann_age_days": age_days,
        "fresh_within_5months": bool(age_days is not None and age_days <= 153),
    }


def search_eastmoney(ts_code, stock_name=None):
    """东财按股票查财务报告类公告，返回过滤后的定期报告（新→旧）"""
    code6 = ts_code.split(".")[0]
    params = {
        "sr": "-1", "page_size": "50", "page_index": "1",
        "ann_type": "A", "client_source": "web",
        "stock_list": code6, "f_node": "1", "s_node": "0",
    }
    try:
        r = requests.get(EM_ANN_URL, params=params,
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        items = r.json().get("data", {}).get("list", []) or []
    except Exception as e:
        return [{"error": str(e)}]

    found = []
    for it in items:
        title = (it.get("title") or "").strip()
        if not any(k in title for k in REPORT_KEYS):
            continue
        if any(k in title for k in EXCLUDE_KEYS):
            continue
        # 防串号校验：标题应含公司简称（东财标题格式"公司名:2026年半年度报告"）
        if stock_name and title.find(stock_name) < 0:
            continue
        art = it.get("art_code", "")
        found.append({
            "title": title,
            "notice_date": (it.get("notice_date") or "")[:10],
            "art_code": art,
            "pdf_url": EM_PDF_URL.format(art=art) if art else None,
        })
    found.sort(key=lambda x: x.get("notice_date") or "", reverse=True)
    return found


def download_pdf(pdf_url, ts_code):
    if not pdf_url:
        return None
    os.makedirs(PDF_DIR, exist_ok=True)
    fname = "%s_%s.pdf" % (ts_code.replace(".", "_"), time.strftime("%Y%m%d_%H%M"))
    path = os.path.join(PDF_DIR, fname)
    try:
        r = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=90, stream=True)
        r.raise_for_status()
        if not r.content[:5].startswith(b"%PDF"):
            return {"error": "not a PDF (got %r)" % r.content[:20]}
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return path
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    do_download = "--download" in sys.argv
    if not args:
        print(json.dumps({"error": "usage: fetch_latest_report.py TS_CODE [TS_CODE ...] [--download]"}, ensure_ascii=False))
        sys.exit(1)

    results = []
    for ts_code in args:
        item = {"ts_code": ts_code}
        stock_name = get_stock_name(ts_code)
        item["name"] = stock_name
        try:
            item["tushare_latest"] = get_latest_from_tushare(ts_code)
        except Exception as e:
            item["tushare_latest"] = {"error": str(e)}
        try:
            anns = search_eastmoney(ts_code, stock_name)
            item["em_reports"] = anns[:5]  # 最近5份定期报告(新→旧)
            if do_download and anns and anns[0].get("pdf_url"):
                item["downloaded_pdf"] = download_pdf(anns[0]["pdf_url"], ts_code)
        except Exception as e:
            item["em_reports"] = [{"error": str(e)}]
        results.append(item)
        time.sleep(0.5)
    print(json.dumps(results, ensure_ascii=False, indent=1))
