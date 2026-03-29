# MEMORY.md - Long-Term Memory

## Preferences

- **⚠️ 回复准则（最高优先级）**：
  - 被问的问题必须客观回复，绝对不能撒谎
  - 没有明确的信息不能随意回复，必须说"不知道"
  - 宁可承认不知道，也不能编造或猜测信息
  - 杜绝错误信息、假信息！
  - **在说"不知道"之前，先尽力获取信息（查日志、查进程、查系统状态等），尽全力后仍不知道才说不知道，不要轻易放弃**
- **⚠️ 金融数据准确性原则（最高优先级）**：
  - 提供金融数据和信息，一定要非常可靠！
  - **第一步永远是验证日期**：用代码确认星期几、是否交易日，绝不凭直觉说日期
  - **先挑战自己**：这个数据有没有可能是错的？计算逻辑对不对？来源可靠吗？
  - 然后再去确认：交叉验证、检查计算过程、确认数据口径
  - 金融数据一定要准确、可靠！错误数据可能导致错误的投资决策
  - 常见陷阱：累计值 vs 单季度、同比 vs 环比、数据口径差异、单位换算、**日期/星期错误**
- **⚠️ 执行指令原则**：
  - 如果接收到明确的操作指令，不能私自改变执行方式
  - 有不同意见可以先提出来询问，但未经用户同意不能私自改变策略
  - 例如：用户说"运行完"，就不能擅自设置超时中断程序
- **联网搜索优先使用 searxng skill** —— 只要涉及联网搜索任务，优先调用 searxng 技能而非直接使用 web_search 工具。
- **⚠️ 数据获取执行顺序（最高优先级）**：
  - **必须按以下顺序获取数据，不能跳过任何一步**：
    1. **先用工具**：
       - `scripts/finance_data.py` - 统一金融数据（行情/指数/公告/新闻）
       - `scripts/realtime_quote.py` - A股实时行情（盘中可用）
       - tushare skill / akshare skill
    2. **工具没有的，用搜索**：searxng skill > web_search
    3. **搜索没有的，用爬虫**：
       - `scripts/scrapling_demo.py` - 高性能网页抓取（绑过反爬）
       - crawl4ai-skill > browser > web_fetch
    4. **都没有的，诚实说"不知道"**，不要编造
  - **禁止**：工具报错就直接放弃说"无法获取"
  - **禁止**：不尝试搜索/爬虫就说"数据缺失"
  - **每条数据必须注明**：来源、时间、可靠性
  - **示例**：
    ```
    ❌ 错误：工具没有历史分位数据 → 直接说"无法获取"
    ✅ 正确：工具没有 → 搜索"铜价历史分位" → scrapling爬取专业网站 → 都没有才说"不知道"
    ```
- **⚠️ 金融数据获取原则（最高优先级）**：
  - **必须优先使用统一金融数据工具**：`scripts/finance_data.py`
  - 这个工具会自动按优先级尝试多个数据源，直到成功
  - **公告数据源优先级**：东方财富（最新，7天内） > 巨潮资讯网（历史）
- **股票新闻监控列表**：`/home/admin/.openclaw/workspace/data/stock_watchlist.json`
  - 增删股票：直接编辑该 JSON 文件
  - 当前监控：长江电力(600900)、国创高新(002377)、绿城水务(601368)、健盛集团(603558)、铁龙物流(600125)、金隅冀东(000401)、新北洋(002376)
  - 每个交易日 21:00 自动检索新闻和公告
    - A股行情：akshare > tushare > eastmoney_api（爬虫）
    - 美股行情：yahoo_finance > eastmoney_api（爬虫）
    - 跌停股：akshare > tushare
    - 金融新闻：searxng > eastmoney_api
    - **指数行情：tushare (A股) > akshare (A股) > eastmoney_api**
  - **使用方式**：
    ```bash
    # A股行情
    python3.11 scripts/finance_data.py quote 002637
    
    # 美股行情
    python3.11 scripts/finance_data.py quote AAPL --us
    
    # 指数行情（所有）
    python3.11 scripts/finance_data.py index
    
    # 指数行情（单个）
    python3.11 scripts/finance_data.py index nasdaq
    python3.11 scripts/finance_data.py index sh
    
    # 公司公告
    python3.11 scripts/finance_data.py announcement 002637
    
    # 今日跌停股
    python3.11 scripts/finance_data.py limit-down
    
    # 搜索新闻
    python3.11 scripts/finance_data.py news 赞宇科技
    ```
  - **Python 调用**：
    ```python
    import sys
    sys.path.insert(0, 'scripts')
    from finance_data import get_quote, get_limit_down, search_news, get_index, get_announcement
    
    # 获取行情
    quote = get_quote("002637")  # A股
    quote = get_quote("AAPL", is_us=True)  # 美股
    
    # 获取指数
    indexes = get_index()  # 所有指数
    nasdaq = get_index("nasdaq")  # 单个指数
    
    # 获取公告
    announcements = get_announcement("002637")
    
    # 获取跌停股
    limit_down = get_limit_down()
    
    # 搜索新闻
    news = search_news("赞宇科技")
    ```
  - **支持的指数代码**：
    - A股：sh(上证), sz(深证), cyb(创业板), hs300(沪深300), sz50(上证50), kc50(科创50), zz500(中证500)
    - 美股：sp500(标普500), nasdaq(纳斯达克)
    - 港股：hsi(恒生指数)
  - **不要**直接调用 akshare/tushare/yahoo-finance，走统一工具
  - 这个工具会持续演进，新增数据源和功能
- **⚠️ 金融分析原则（最高优先级）**：
  - **必须优先使用统一金融分析工具**：`scripts/finance_analysis.py`
  - 这个工具会根据需求自动选择合适的分析工具
  - **工具优先级**：
    - A股价值分析/筛选/估值：china-stock-analysis
    - A股实时行情/技术面/板块：akshare-stock
    - 美股分析（8维度/情绪/时机）：stock-analysis
    - 投资组合管理：stock-analysis
    - 加密货币分析：stock-analysis
  - **使用方式**：
    ```bash
    # A股个股分析
    python3.11 scripts/finance_analysis.py stock 002637
    python3.11 scripts/finance_analysis.py stock 002637 --level deep
    
    # 美股分析
    python3.11 scripts/finance_analysis.py stock AAPL --us
    python3.11 scripts/finance_analysis.py stock TSLA --us --json
    
    # 股票筛选
    python3.11 scripts/finance_analysis.py screen --pe-max 15 --roe-min 15
    python3.11 scripts/finance_analysis.py screen --scope hs300 --dividend-min 3
    
    # 行业分析
    python3.11 scripts/finance_analysis.py sector "白酒"
    
    # 股票对比
    python3.11 scripts/finance_analysis.py compare 002637,600519
    
    # 投资组合分析
    python3.11 scripts/finance_analysis.py portfolio
    python3.11 scripts/finance_analysis.py portfolio --period weekly
    
    # 加密货币分析
    python3.11 scripts/finance_analysis.py crypto BTC-USD
    
    # 智能分析（自然语言）
    python3.11 scripts/finance_analysis.py smart "分析贵州茅台"
    python3.11 scripts/finance_analysis.py smart "筛选PE小于15且ROE大于15的股票"
    ```
  - **Python 调用**：
    ```python
    import sys
    sys.path.insert(0, 'scripts')
    from finance_analysis import (
        analyze_a_stock, analyze_us_stock, screen_a_stocks,
        analyze_sector, compare_stocks, analyze_portfolio, analyze_crypto,
        smart_analyze
    )
    
    # A股分析
    result = analyze_a_stock("002637", level="standard")
    
    # 美股分析
    result = analyze_us_stock("AAPL")
    
    # 股票筛选
    result = screen_a_stocks({"pe_max": 15, "roe_min": 15})
    
    # 行业分析
    result = analyze_sector("白酒")
    
    # 股票对比
    result = compare_stocks(["002637", "600519"])
    
    # 投资组合
    result = analyze_portfolio(period="weekly")
    
    # 加密货币
    result = analyze_crypto("BTC-USD")
    
    # 智能分析
    result = smart_analyze("分析贵州茅台的估值")
    ```
  - **分析能力对照表**：
    | 需求 | 工具 | 功能 |
    |------|------|------|
    | A股价值分析 | china-stock-analysis | 杜邦分析、财务健康、估值计算、风险检测 |
    | A股筛选 | china-stock-analysis | PE/PB/ROE/股息率/负债率筛选 |
    | A股技术面 | akshare-stock | K线、分时、涨跌停、资金流 |
    | A股板块 | akshare-stock | 行业板块、概念轮动、资金流 |
    | 美股分析 | stock-analysis | 8维度、情绪、时机、地缘风险 |
    | 组合管理 | stock-analysis | 创建组合、追踪收益、周期报告 |
    | 加密货币 | stock-analysis | 市值分类、BTC相关性、动量 |
  - **不要**直接调用各个 skills 的脚本，走统一工具
  - 这个工具会持续演进，新增分析能力和优化路由逻辑
- **多模型配置**：
  - 文本内容处理 → 优先使用 GLM-5
  - 视觉/图片内容 → 自动使用 GLM-4V
- **Skill选择原则**：
  - 优先选择评价高、评分高的技能（匹配度 > 1.1 为佳）
  - 低质量、评分低的技能尽量避免使用
  - 安装前先用 skill-vetter 审查安全性
- **问题分析原则**：
  - 错误信息不一定反映根本原因，要深入分析
  - 遇到问题时，按以下顺序排查：认证状态 → 权限/配额 → 网络连接 → 服务端问题
  - 部分功能可用、部分不可用，通常是认证/权限问题
  - 不要被表面错误信息误导，要找到问题本质
- **⚠️ 反馈闭环原则（最高优先级）**：
  - **用户提出的任何需求，都必须有反馈，绝不允许"说着说着就没下文了"**
  - 无论结果如何，都要给出明确反馈：
    - 找到解决方案 → 告诉用户结果
    - 没找到解决方案 → 明确告诉用户"没找到"
    - 遇到错误/失败 → 告诉用户失败原因
    - 任务还在进行中 → 告诉用户进度
  - 禁止：说了"我去查/去找/去试"，然后就消失了
  - 每个承诺的动作，都必须有对应的反馈
- **⚠️ 备份规范（最高优先级）**：
  - 备份 `openclaw.json` 文件时，文件名必须带上日期时间戳，格式：`openclaw.json.bak.YYYYMMDD_HHMMSS`
  - 示例：`cp openclaw.json openclaw.json.bak.20260328_122901`
  - 禁止使用不带日期的通用备份名
- **子代理共享记忆**：
  - 共享配置文件：`~/.openclaw/workspace/shared/memory.md`
  - 所有子代理启动时自动读取该文件
  - 包含用户偏好、关注列表、通用规则

## Notes

- Created: 2026-03-05

## Skills 仓库

搜索和下载 skills 的渠道：

| 仓库 | 地址 | 安装命令 | 说明 |
|------|------|----------|------|
| **ClawHub** | https://clawhub.com | `clawhub install <skill>` | 需要登录认证 |
| **skills.sh** | https://skills.sh/ | `npx skills add <owner/repo@skill>` | Vercel Labs，无需登录 |

**ClawHub Token:** `clh_HFznCaeYn_jRaRsGe3yA4R3VCeeONDgO-9E09vJVwx0`
- 登录命令：`clawhub login --token clh_HFznCaeYn_jRaRsGe3yA4R3VCeeONDgO-9E09vJVwx0`

**使用建议：**
- ClawHub 需要先 `clawhub login --token <token>` 登录
- skills.sh 可以直接使用，有安全审计（Socket/Snyk）
- 安装前检查安全评估结果
