#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""检查 quant_hits_detail.json 新鲜度，必要时调起 stock_push.py 重新生成

用法:
  python3.11 ensure_json.py           # 仅检查：输出状态+JSON摘要，exit 0=新鲜可直接用
  python3.11 ensure_json.py --run     # 检查；不新鲜(>48h或缺失)则调起主程序重新生成（阻塞约45分钟）
                                      #        主程序照常推送企业微信（已确认接受的副作用）
输出: JSON到stdout
"""
import os
import sys
import json
import time
import subprocess
import datetime

JSON_PATH = "/home/admin/Hualin/quant_hits_detail.json"
MAIN_PY = "/home/admin/Hualin/stock_push.py"
VENV_PY = "/home/admin/financial/bin/python"
WORKDIR = "/home/admin/Hualin"
RUN_LOG = "/tmp/stock_refiner_run.log"
MAX_AGE_HOURS = 48  # 老板定的：2天内有效
RUN_TIMEOUT_SEC = 5400  # 主程序全市场扫描约45~60分钟


def load_status():
    if not os.path.exists(JSON_PATH):
        return {"status": "missing", "path": JSON_PATH}
    age_hours = (time.time() - os.path.getmtime(JSON_PATH)) / 3600.0
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        return {"status": "corrupt", "error": str(e), "path": JSON_PATH}

    hits_brief = [
        {
            "ts_code": h.get("ts_code"),
            "name": h.get("name"),
            "is_new": h.get("is_new"),
            "data_source": h.get("data_source"),
            "peg": (h.get("metrics") or {}).get("valuation", {}).get("peg"),
            "pe_ttm": (h.get("metrics") or {}).get("valuation", {}).get("pe_ttm"),
        }
        for h in d.get("hits", [])
    ]
    return {
        "status": "fresh" if age_hours <= MAX_AGE_HOURS else "stale",
        "path": JSON_PATH,
        "age_hours": round(age_hours, 1),
        "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(JSON_PATH)).strftime("%Y-%m-%d %H:%M:%S"),
        "max_age_hours": MAX_AGE_HOURS,
        "run_info": d.get("run_info", {}),
        "hits_brief": hits_brief,
        "removed_today": d.get("removed_today", []),
    }


def run_main_program():
    """调起 stock_push.py 重新生成JSON（阻塞至完成）"""
    with open(RUN_LOG, "ab") as logf:
        proc = subprocess.run(
            [VENV_PY, MAIN_PY],
            cwd=WORKDIR,
            stdout=logf,
            stderr=subprocess.STDOUT,
            timeout=RUN_TIMEOUT_SEC,
        )
    return proc.returncode


if __name__ == "__main__":
    do_run = "--run" in sys.argv
    st = load_status()
    if st["status"] in ("missing", "stale", "corrupt") and do_run:
        print(json.dumps({"action": "rerun_started", "log": RUN_LOG, "prev_status": st}, ensure_ascii=False))
        sys.stdout.flush()
        try:
            rc = run_main_program()
        except subprocess.TimeoutExpired:
            print(json.dumps({"action": "rerun_timeout", "hint": "查看日志确认是否已写出JSON"}, ensure_ascii=False))
            sys.exit(2)
        st = load_status()
        st["rerun_returncode"] = rc
    print(json.dumps(st, ensure_ascii=False, indent=1))
