"""
手动验证创业板 Q4 2025 净利润同比增长率
严格遵循 Index_PE_Push.py 的逻辑
"""
import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime
import time

TS_TOKEN = 'dde651506e87c13c30474693d2c4091345f987a2b8bfffad4989530c'
pro = ts.pro_api(TS_TOKEN)
INDEX_CODE = '399006.SZ'
END_DATE = datetime.now().strftime('%Y%m%d')

def fetch_with_retry(api_func, **kwargs):
    max_retries = 10
    for attempt in range(max_retries):
        try:
            df = api_func(**kwargs)
            return df
        except Exception as e:
            if "每分钟最多访问" in str(e):
                print(f"  Rate limited, sleeping 180s (attempt {attempt+1})...")
                time.sleep(180)
            else:
                print(f"  Error: {e}, sleeping 10s (attempt {attempt+1})...")
                time.sleep(10)
    return pd.DataFrame()

# ============================================================
# STEP 1: 获取创业板成分股及权重
# ============================================================
print("=" * 70)
print("STEP 1: 获取创业板成分股及权重")
print("=" * 70)

index_weight = fetch_with_retry(pro.index_weight, index_code=INDEX_CODE,
                                start_date=END_DATE, end_date=END_DATE)
if index_weight.empty:
    m_ago = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y%m%d')
    index_weight = fetch_with_retry(pro.index_weight, index_code=INDEX_CODE,
                                    start_date=m_ago, end_date=END_DATE)
    if not index_weight.empty:
        index_weight = index_weight[index_weight['trade_date'] == index_weight['trade_date'].max()]

N_total = len(index_weight)
print(f"成分股数量: {N_total}")
print(f"权重总和: {index_weight['weight'].sum():.4f}")

# Normalize
weight_map = dict(zip(index_weight['con_code'], index_weight['weight']))
total_w = sum(weight_map.values())
weight_map = {k: v / total_w for k, v in weight_map.items()}
print(f"归一化权重总和: {sum(weight_map.values()):.4f}")

# Stock names
print("\n预取股票名称...")
df_basic = fetch_with_retry(pro.stock_basic, fields='ts_code,name')
name_map = dict(zip(df_basic['ts_code'], df_basic['name']))

con_codes = index_weight['con_code'].tolist()
print(f"前10只: {[(c, name_map.get(c,'?'), f'{weight_map[c]*100:.2f}%') for c in con_codes[:10]]}")

# ============================================================
# STEP 2: 逐股获取财报数据（income + fina_indicator）
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: 获取成分股财报数据 (income + fina_indicator)")
print("=" * 70)

fina_list = []
for i, code in enumerate(con_codes):
    time.sleep(0.4)
    df_inc = fetch_with_retry(pro.income, ts_code=code,
                              start_date='20130101', end_date=END_DATE,
                              fields='end_date,revenue')
    df_fin = fetch_with_retry(pro.fina_indicator, ts_code=code,
                              start_date='20130101', end_date=END_DATE,
                              fields='end_date,ann_date,profit_dedt,bps')
    if not df_inc.empty and not df_fin.empty:
        m = pd.merge(df_inc.drop_duplicates('end_date'),
                     df_fin.drop_duplicates('end_date'),
                     on='end_date', how='outer')
        m['ts_code'] = code
        fina_list.append(m)
    if (i + 1) % 200 == 0:
        print(f"  进度: {i+1}/{N_total}")

print(f"成功获取财报的股票数: {len(fina_list)}/{N_total}")

# ============================================================
# STEP 3: 数据处理 - 季度对齐 + 单季度利润还原
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: 季度对齐 + 单季度利润还原 (q_p)")
print("=" * 70)

all_f = pd.concat(fina_list, ignore_index=True)
del fina_list
all_f['end_date'] = pd.to_datetime(all_f['end_date'], errors='coerce')

# Align end_date to quarter end
valid = all_f['end_date'].notna()
all_f.loc[valid, 'year_temp'] = all_f.loc[valid, 'end_date'].dt.year
all_f.loc[valid, 'quarter_temp'] = all_f.loc[valid, 'end_date'].dt.quarter
all_f.loc[valid, 'end_date'] = pd.to_datetime(
    all_f.loc[valid, 'year_temp'].astype(int).astype(str) + '-' +
    (all_f.loc[valid, 'quarter_temp'].astype(int) * 3).astype(str) + '-01'
) + pd.offsets.MonthEnd(0)
all_f = all_f.drop(columns=['year_temp', 'quarter_temp'], errors='ignore')
all_f = all_f.drop_duplicates(subset=['ts_code', 'end_date'], keep='last')
all_f['ann_date'] = pd.to_datetime(all_f['ann_date'], format='%Y%m%d', errors='coerce')
all_f['year'] = all_f['end_date'].dt.year
all_f['quarter'] = all_f['end_date'].dt.quarter
all_f = all_f.sort_values(['ts_code', 'end_date']).reset_index(drop=True)

# 单季度利润 = 累计值差分
all_f['q_s'] = np.where(
    all_f['quarter'] == 1, all_f['revenue'],
    all_f.groupby(['ts_code', 'year'])['revenue'].diff())
all_f['q_p'] = np.where(
    all_f['quarter'] == 1, all_f['profit_dedt'],
    all_f.groupby(['ts_code', 'year'])['profit_dedt'].diff())
all_f['q_p_abs'] = all_f['q_p']

# 特殊处理：只有H1+Annual的情况
for code in all_f['ts_code'].unique():
    mask = all_f['ts_code'] == code
    for yr in all_f.loc[mask, 'year'].unique():
        fy_mask = mask & (all_f['year'] == yr)
        fy_rows = all_f.loc[fy_mask].sort_values('quarter')
        if fy_rows.empty:
            continue
        qp = set(fy_rows['quarter'].tolist())
        if 2 in qp and 4 in qp and 1 not in qp and 3 not in qp:
            q2_idx = fy_rows[fy_rows['quarter'] == 2].index
            q4_idx = fy_rows[fy_rows['quarter'] == 4].index
            h1_p = fy_rows.loc[fy_rows['quarter'] == 2, 'profit_dedt'].iloc[0]
            ann_p = fy_rows.loc[fy_rows['quarter'] == 4, 'profit_dedt'].iloc[0]
            all_f.loc[q2_idx, 'q_p'] = h1_p / 2
            all_f.loc[q2_idx, 'q_p_abs'] = h1_p / 2
            all_f.loc[q4_idx, 'q_p'] = (ann_p - h1_p) / 2
            all_f.loc[q4_idx, 'q_p_abs'] = (ann_p - h1_p) / 2
        elif 1 in qp and 2 in qp and 3 not in qp and 4 in qp:
            q4_idx = fy_rows[fy_rows['quarter'] == 4].index
            h1_p = fy_rows.loc[fy_rows['quarter'] == 2, 'profit_dedt'].iloc[0]
            ann_p = fy_rows.loc[fy_rows['quarter'] == 4, 'profit_dedt'].iloc[0]
            all_f.loc[q4_idx, 'q_p'] = (ann_p - h1_p) / 2
            all_f.loc[q4_idx, 'q_p_abs'] = (ann_p - h1_p) / 2

print(f"总数据行数: {len(all_f)}")
print(f"涉及股票数: {all_f['ts_code'].nunique()}")
print(f"季度范围: {all_f['end_date'].min()} ~ {all_f['end_date'].max()}")

# ============================================================
# STEP 4: 筛选 Q4 2025 和 Q4 2024 数据
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: 筛选 Q4 2025 和 Q4 2024 的单季度利润")
print("=" * 70)

q4_2025 = all_f[(all_f['year'] == 2025) & (all_f['quarter'] == 4)].copy()
q4_2024 = all_f[(all_f['year'] == 2024) & (all_f['quarter'] == 4)].copy()

print(f"Q4 2025 有数据的股票数: {len(q4_2025)} (q_p非NaN: {q4_2025['q_p'].notna().sum()})")
print(f"Q4 2024 有数据的股票数: {len(q4_2024)} (q_p非NaN: {q4_2024['q_p'].notna().sum()})")

# 展示 Q4 2025 有 q_p 数据的股票（前20只权重股）
print(f"\n--- Q4 2025 前20只权重股的 q_p ---")
sorted_codes = sorted(con_codes, key=lambda c: weight_map.get(c, 0), reverse=True)
for c in sorted_codes[:20]:
    row_25 = q4_2025[q4_2025['ts_code'] == c]
    row_24 = q4_2024[q4_2024['ts_code'] == c]
    qp_25 = row_25['q_p'].iloc[0] if not row_25.empty and pd.notna(row_25['q_p'].iloc[0]) else None
    qp_24 = row_24['q_p'].iloc[0] if not row_24.empty and pd.notna(row_24['q_p'].iloc[0]) else None
    w = weight_map.get(c, 0) * 100
    name = name_map.get(c, c)
    print(f"  {name}({c}) 权重{w:.2f}% | Q4'25 q_p={qp_25} | Q4'24 q_p={qp_24}")

# ============================================================
# STEP 5: 构建 strict_report 匹配集
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: strict_report 匹配 (两只季度都有真实数据的股票)")
print("=" * 70)

# 只取 q_p 非NaN的（即有真实报告的）
q4_2025_valid = q4_2025[q4_2025['q_p'].notna()][['ts_code', 'q_p']].rename(columns={'q_p': 'q_p_2025'})
q4_2024_valid = q4_2024[q4_2024['q_p'].notna()][['ts_code', 'q_p']].rename(columns={'q_p': 'q_p_2024'})

matched = pd.merge(q4_2025_valid, q4_2024_valid, on='ts_code', how='inner')
matched = matched[matched['q_p_2024'] != 0]  # 代码逻辑: prev != 0

print(f"Q4'25 有 q_p 的股票: {len(q4_2025_valid)}")
print(f"Q4'24 有 q_p 的股票: {len(q4_2024_valid)}")
print(f"两期都有数据且 Q4'24 != 0: {len(matched)}")

# ============================================================
# STEP 6: 汇总计算同比增长率
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: 汇总计算 Profit YoY")
print("=" * 70)

sum_q4_2025 = matched['q_p_2025'].sum()
sum_q4_2024 = matched['q_p_2024'].sum()

print(f"参与计算的股票数: {len(matched)}/{N_total}")
print(f"Q4 2025 利润总和 (sum q_p): {sum_q4_2025:,.2f}")
print(f"Q4 2024 利润总和 (sum q_p): {sum_q4_2024:,.2f}")
print(f"差值 (2025 - 2024): {sum_q4_2025 - sum_q4_2024:,.2f}")

profit_yoy = (sum_q4_2025 - sum_q4_2024) / abs(sum_q4_2024) * 100
print(f"\n{'='*50}")
print(f"  创业板 Q4 2025 净利润同比增长率: {profit_yoy:+.2f}%")
print(f"{'='*50}")

# 展示贡献最大的前20只股票
print("\n--- 利润变动贡献 Top 20 ---")
matched['delta'] = matched['q_p_2025'] - matched['q_p_2024']
matched['name'] = matched['ts_code'].map(name_map)
matched['weight'] = matched['ts_code'].map(weight_map)
matched['contrib_pct'] = matched['delta'] / abs(sum_q4_2024) * 100
top_contrib = matched.nlargest(20, 'delta')
for _, r in top_contrib.iterrows():
    print(f"  {r['name']}({r['ts_code']}) | Q4'25={r['q_p_2025']:,.0f} Q4'24={r['q_p_2024']:,.0f} | 变动={r['delta']:+,.0f} | 贡献={r['contrib_pct']:+.2f}pp")

print("\n--- 利润拖累最大 Top 20 ---")
bottom_contrib = matched.nsmallest(20, 'delta')
for _, r in bottom_contrib.iterrows():
    print(f"  {r['name']}({r['ts_code']}) | Q4'25={r['q_p_2025']:,.0f} Q4'24={r['q_p_2024']:,.0f} | 变动={r['delta']:+,.0f} | 贡献={r['contrib_pct']:+.2f}pp")

# 额外：统计正增长/负增长/扭亏/转亏
positive = matched[matched['delta'] > 0]
negative = matched[matched['delta'] < 0]
print(f"\n--- 分布统计 ---")
print(f"利润增长: {len(positive)} 家")
print(f"利润下降: {len(negative)} 家")
print(f"增长占比: {len(positive)/len(matched)*100:.1f}%")
