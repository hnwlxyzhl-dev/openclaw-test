# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

---

## 📈 实时股价查询

**脚本位置：** `scripts/realtime_quote.py`

**用途：** 获取A股实时行情（盘中可用，非盘后数据）

**使用方法：**
```bash
# 单只股票
python3 scripts/realtime_quote.py 002637

# 多只股票
python3 scripts/realtime_quote.py 002637,600519,000001

# JSON 输出（便于程序处理）
python3 scripts/realtime_quote.py 002637 --json
```

**输出字段：**
- `price` - 现价
- `pct_chg` - 涨跌幅(%)
- `is_limit_down` - 是否跌停
- `is_limit_up` - 是否涨停
- `open/high/low/pre_close` - 开高低昨收
- `volume/amount` - 成交量/成交额
- `date/time` - 行情时间

**Python 调用示例：**
```python
import sys
sys.path.insert(0, 'scripts')
from realtime_quote import get_realtime_quote

quotes = get_realtime_quote("002637")
for q in quotes:
    print(f"{q['name']}: {q['price']} ({q['pct_chg']:+.2f}%)")
    if q['is_limit_down']:
        print("跌停中!")
```

**注意：**
- 使用 `ts.get_realtime_quotes()` 获取实时数据
- 不要用 `pro.daily()` —— 那是盘后数据，盘中查不到当天

---

## 🦂 Scrapling 网页抓取

**脚本位置：** `scripts/scrapling_demo.py`

**用途：** 高性能网页抓取，可绑过 Cloudflare 等反爬机制

**特点：**
- 反检测能力强，模拟真人浏览器行为
- 语义化查找元素，不依赖 CSS 选择器
- 支持 JavaScript 渲染的动态页面
- 相比 BeautifulSoup 快 774 倍

**使用方法：**
```bash
# 抓取网页
python3.11 scripts/scrapling_demo.py https://example.com
```

**Python 调用示例：**
```python
from scrapling import StealthyFetcher

fetcher = StealthyFetcher()
page = fetcher.fetch("https://example.com")

# CSS 选择器
titles = page.css("title")
print(titles[0].text)

# 获取文本
body = page.css("body")[0]
print(body.get_all_text())

# 语义查找（不依赖标签名）
elements = page.find_all("价格")  # 自动找包含"价格"的元素
```

**注意：**
- 必须用 `python3.11` 运行（系统默认 python3.6 不支持）
- 方法名是 `fetch()` 不是 `get()`
- 查找元素用 `page.css("selector")` 返回列表

---

---

## 🔧 GitHub 配置

**Git 身份：**
- 用户名：`hnwlxyzhl-dev`
- 邮箱：`18817350793@163.com`

**认证方式：**
- SSH：已配置（`~/.ssh/id_ed25519`）
- Token：已保存（`~/.config/github-token`）

**创建仓库脚本：**
```bash
# 创建新仓库
curl -X POST https://api.github.com/user/repos \
  -H "Authorization: token $(cat ~/.config/github-token | cut -d= -f2)" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"name":"仓库名","private":false}'
```

**常用操作：**
```bash
# 克隆仓库（SSH）
git clone git@github.com:hnwlxyzhl-dev/仓库名.git

# 提交并推送
git add . && git commit -m "message" && git push
```

---

## 📋 Cron 任务

**查看当前任务**：`cat ~/.openclaw/cron/jobs.json | jq '.jobs[] | {name, schedule}'`

**注意**：任务列表是动态的，不要写死在文档里，实时查询 jobs.json 才是最新状态。
