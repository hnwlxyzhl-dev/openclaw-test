#!/bin/bash
# watchdog-1024-evening: 10-24 晚间决胜段看门狗 (18:40-23:00)
# 输出事件行: [BASE]/[ALERT]/[RENEW]/[RECOVER]/[END]，由上层 agent 读取并转发飞书
export XDG_RUNTIME_DIR=/run/user/1000
BASE_PID=3638114
END_TS=$(date -d "today 23:00" +%s)
ANY=0

gw_stat() { # 网关进程 anon MB (smaps_rollup, fallback RSS)
  local p
  p=$(systemctl --user show openclaw-gateway -p MainPID --value 2>/dev/null)
  [ -z "$p" ] && p=$(pgrep -f openclaw-gateway | head -1)
  if [ -n "$p" ] && [ -r "/proc/$p/smaps_rollup" ]; then
    awk '/^Anonymous:/{printf "%d", $2/1024}' "/proc/$p/smaps_rollup"
  elif [ -n "$p" ]; then
    awk -v p="$p" '{printf "%d", $1/1024}' "/proc/$p/statm" 2>/dev/null || ps -o rss= -p "$p" | awk '{printf "%d", $1/1024}'
  else
    printf "NA"
  fi
}

batch_stat() { # batch 类进程 RSS 合计 MB
  ps -eo rss,args | awk '!/awk/ && $2 ~ /[Bb]atch/ {s+=$1} END {if (s>0) printf "%d", s/1024; else print "NA"}'
}

LAST_OOM=$(dmesg 2>/dev/null | grep -c -iE "oom-kill|Out of memory")
echo "[BASE] $(date '+%H:%M:%S') oom_base=$LAST_OOM avail=$(free -m | awk '/^Mem:/{print $7}') gateway_pid=$BASE_PID"

avail_alert=0; oom_alert=0; pid_reported=0
avail_last=0; oom_last=0

while true; do
  sleep 60
  NOW=$(date +%s)
  if [ $NOW -ge $END_TS ]; then
    echo "[END] $(date '+%H:%M:%S') watchdog_exit any_alert=$ANY avail_alert_final=$avail_alert oom_alert_final=$oom_alert"
    exit 0
  fi

  AVAIL=$(free -m | awk '/^Mem:/{print $7}')
  OOM=$(dmesg 2>/dev/null | grep -c -iE "oom-kill|Out of memory")
  PID=$(systemctl --user show openclaw-gateway -p MainPID --value 2>/dev/null)
  [ -z "$PID" ] && PID=$(pgrep -f openclaw-gateway | head -1)

  # --- 1) 网关重启（只报一次） ---
  if [ -n "$PID" ] && [ "$PID" != "$BASE_PID" ] && [ $pid_reported -eq 0 ]; then
    pid_reported=1; ANY=1
    echo "[ALERT] type=pid_restart|newpid=$PID|avail=$AVAIL|gw=$(gw_stat)MB|batch=$(batch_stat)MB|time=$(date '+%H:%M:%S')"
  fi

  # --- 2) avail < 250 ---
  if [ "$AVAIL" -lt 250 ] 2>/dev/null; then
    if [ $avail_alert -eq 0 ]; then
      avail_alert=1; avail_last=$NOW; ANY=1
      echo "[ALERT] type=avail_low|avail=${AVAIL}MB|gw=$(gw_stat)MB|batch=$(batch_stat)MB|time=$(date '+%H:%M:%S')"
    elif [ $((NOW - avail_last)) -ge 300 ]; then
      avail_last=$NOW
      echo "[RENEW] type=avail_low|avail=${AVAIL}MB|gw=$(gw_stat)MB|batch=$(batch_stat)MB|time=$(date '+%H:%M:%S')"
    fi
  elif [ $avail_alert -eq 1 ]; then
    avail_alert=0
    echo "[RECOVER] type=avail_low|avail=${AVAIL}MB|time=$(date '+%H:%M:%S')"
  fi

  # --- 3) OOM 增量 ---
  if [ "$OOM" -gt "$LAST_OOM" ] 2>/dev/null; then
    if [ $oom_alert -eq 0 ]; then
      oom_alert=1; oom_last=$NOW; ANY=1
      echo "[ALERT] type=oom|new_oom=$((OOM-LAST_OOM))|oom_total=$OOM|avail=${AVAIL}MB|gw=$(gw_stat)MB|batch=$(batch_stat)MB|time=$(date '+%H:%M:%S')"
    elif [ $((NOW - oom_last)) -ge 300 ]; then
      oom_last=$NOW
      echo "[RENEW] type=oom|new_oom=$((OOM-LAST_OOM))|oom_total=$OOM|avail=${AVAIL}MB|gw=$(gw_stat)MB|batch=$(batch_stat)MB|time=$(date '+%H:%M:%S')"
    fi
    LAST_OOM=$OOM
  elif [ $oom_alert -eq 1 ] && [ $((NOW - oom_last)) -ge 300 ]; then
    oom_alert=0
    echo "[RECOVER] type=oom|time=$(date '+%H:%M:%S')"
  fi
done
