# 全市场ETF/指数净利润同比扫描程序 - 修改任务

## 程序位置
`/home/admin/Hualin/Bianli_Index_PE_Push.py`

## 背景
这是一个全市场ETF/指数净利润同比扫描与推送程序，两阶段流程：
- Phase 1（轻量扫描）：遍历~538个去重后的ETF+指数，算净利润同比增速，筛>20%
- Phase 2（完整计算）：对合格目标跑完整逻辑，出PE/PB/PEG图+成分股表，推送企业微信

当前程序已从被改坏的版本回退到 `bak.20260614_143000`（用户确认同意的版本）。

## 已解决的问题
程序之前被擅自修改了两个函数（lightweight_profit_yoy_scan 和 load_stock_financials），导致计算逻辑错误。已回退到正确版本。

## 需要修改的内容

### 1. 内存管理：数据缓存到文件，释放内存
这是本次修改的核心需求。

**问题**：Step 4b 批量拉取~5500+只成分股财务数据时，如果 DataFrame 不及时释放，会导致内存溢出（OOM）。

**当前版本已有的措施**（保留不动）：
- `clear_stock_fin_cache()` 每次运行清空临时缓存
- Step 4b 每只股票拉完后 `del df_inc; del df_fin; del m` 释放 DataFrame
- 每10只 `gc.collect()`
- 财务数据每只股票单独存JSON文件（`temp_stock_financials/`）

**需要检查/增强的**：
- 检查 Phase 1 的 `lightweight_profit_yoy_scan` 函数，确保读取缓存后不会在内存中累积大量 DataFrame
- 检查 Phase 2 的 `process_index_full` 函数，确保大量 DataFrame 及时释放
- 如果有任何内存泄漏风险点，修复它

### 2. 指数去重优化（优先级较低，如果有时间再做）
当前 Step 2 对指数"全部保留"，但如果某个指数和某个ETF的benchmark一致，扫描结果会重复。
建议：如果指数代码出现在某个ETF的benchmark中，可以跳过该指数的Phase 1扫描（仅保留在Phase 2作为参考）。

### 3. 确认功能完整性
确保以下功能在修改后仍然正常：
- ✅ 每次运行清空临时缓存，全量重新拉取
- ✅ 成分股按月缓存（cache_constituents/）
- ✅ Phase 1 轻量扫描净利润同比 > 20%
- ✅ Phase 2 完整计算（PE/PB/PEG图、成分股表）
- ✅ 优中选优：非低基数 + 净利润同比加速
- ✅ 历史记录追踪（bianli_history.json）
- ✅ 企业微信推送

## 约束
1. **不改变计算逻辑**：Phase 1 和 Phase 2 的基本面计算逻辑保持不变
2. **不改变数据源**：继续使用 tushare
3. **修改前备份**：修改前先 `cp Bianli_Index_PE_Push.py Bianli_Index_PE_Push.py.bak.$(date +%Y%m%d_%H%M%S)`
4. **先调研后执行**：先读代码理解现状，再提出修改方案，获得确认后再改

## 测试要求
修改完成后，守望者会执行测试：
1. 运行程序，确保不OOM
2. 检查扫描结果是否合理（应该有若干个净利润同比>20%的目标）
3. 确认企业微信推送正常

## 参考文件
- 原始程序（OnDemand版）：`/home/admin/Hualin/Index_PE_Push.py`
- 当前版本备份（回退后的正确版本）：`/home/admin/Hualin/Bianli_Index_PE_Push.py.bak.20260614_143000`
- 被改坏的版本（参考，不要用）：`/home/admin/Hualin/Bianli_Index_PE_Push.py.bak.broken_dict_version.20260614_1825`
- 临时财务缓存目录：`/home/admin/Hualin/data/temp_stock_financials/`
- 成分股缓存目录：`/home/admin/Hualin/data/cache_constituents/`
- 历史记录：`/home/admin/Hualin/data/bianli_history.json`
