#!/bin/bash
# 批量查询默认ETF基本面
# 串行执行，每只间隔5秒，单只失败不中断

set -u

SKILL_DIR="/home/admin/.openclaw/workspace-hunter/skills/etf-index-fundamentals"
FETCH_SCRIPT="$SKILL_DIR/scripts/fetch_constituents.py"
PUSH_SCRIPT="/home/admin/Hualin/OnDemand_Index_PE_Push.py"
LOG_FILE="/tmp/batch_etf_$(date +%Y%m%d_%H%M%S).log"
TMP_DIR="/tmp/batch_etf_stocks"
mkdir -p "$TMP_DIR"

# ETF列表: ts_code|simple_code|name
ETS=(
"512890.SH|512890|红利低波ETF华泰柏瑞"
"159992.SZ|159992|创新药ETF银华"
"512480.SH|512480|半导体ETF国联安"
"512880.SH|512880|证券ETF国泰"
"512800.SH|512800|银行ETF华宝"
"512170.SH|512170|医疗ETF华宝"
"512710.SH|512710|军工龙头ETF富国"
"515220.SH|515220|煤炭ETF国泰"
"512400.SH|512400|有色金属ETF南方"
"515880.SH|515880|通信ETF国泰"
"159530.SZ|159530|机器人ETF易方达"
"159819.SZ|159819|人工智能ETF易方达"
"159869.SZ|159869|游戏ETF华夏"
"159611.SZ|159611|电力ETF广发"
"513180.SH|513180|恒生科技ETF华夏"
"515790.SH|515790|光伏ETF华泰柏瑞"
"515030.SH|515030|新能源车ETF华夏"
"512200.SH|512200|房地产ETF南方"
"515210.SH|515210|钢铁ETF国泰"
"159870.SZ|159870|化工ETF鹏华"
"159206.SZ|159206|卫星ETF永赢"
)

TOTAL=${#ETS[@]}
SUCCESS=0
FAIL=0
FAILED_LIST=""

echo "========================================" | tee "$LOG_FILE"
echo "批量ETF基本面查询 - $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "共 $TOTAL 只ETF" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

for i in "${!ETS[@]}"; do
    IFS='|' read -r ts_code simple_code etf_name <<< "${ETS[$i]}"
    idx=$((i+1))
    echo "" | tee -a "$LOG_FILE"
    echo "[$idx/$TOTAL] $etf_name ($simple_code) - $(date '+%H:%M:%S')" | tee -a "$LOG_FILE"
    
    # 步骤1: 获取成分股
    STOCKS_FILE="$TMP_DIR/stocks_${simple_code}.json"
    echo "  获取成分股..." | tee -a "$LOG_FILE"
    python3.11 "$FETCH_SCRIPT" --etf "$simple_code" --output "$STOCKS_FILE" 2>&1 | tee -a "$LOG_FILE"
    
    if [ ! -f "$STOCKS_FILE" ]; then
        echo "  ❌ 成分股获取失败，跳过" | tee -a "$LOG_FILE"
        FAIL=$((FAIL+1))
        FAILED_LIST="$FAILED_LIST\n  ❌ $etf_name ($simple_code) - 成分股获取失败"
        sleep 5
        continue
    fi
    
    # 步骤2: 运行基本面计算并推送
    echo "  计算基本面并推送..." | tee -a "$LOG_FILE"
    python3.11 "$PUSH_SCRIPT" \
        --name "$etf_name" \
        --code "$ts_code" \
        --stocks "$STOCKS_FILE" \
        --is-etf 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "  ✅ 完成" | tee -a "$LOG_FILE"
        SUCCESS=$((SUCCESS+1))
    else
        echo "  ❌ 失败 (exit code: $EXIT_CODE)" | tee -a "$LOG_FILE"
        FAIL=$((FAIL+1))
        FAILED_LIST="$FAILED_LIST\n  ❌ $etf_name ($simple_code) - exit code $EXIT_CODE"
    fi
    
    # 间隔5秒（最后一只不用等）
    if [ $idx -lt $TOTAL ]; then
        echo "  等待5秒..." | tee -a "$LOG_FILE"
        sleep 5
    fi
done

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "批量查询完成 - $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "总计: $TOTAL 只 | ✅ 成功: $SUCCESS | ❌ 失败: $FAIL" | tee -a "$LOG_FILE"
if [ -n "$FAILED_LIST" ]; then
    echo -e "失败列表:$FAILED_LIST" | tee -a "$LOG_FILE"
fi
echo "========================================" | tee -a "$LOG_FILE"
echo ""
echo "BATCH_DONE"
