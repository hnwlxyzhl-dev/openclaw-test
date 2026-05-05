# TOOLS.md - 工具操作手册

_详细的使用方法、参数、代码示例。行为规则见 MEMORY.md。_

---

## 🤝 Agent 协调

作为大管家，你通过以下工具与其他 Agent 协同工作。

### 分派任务

```python
# 一次性任务（执行完自动结束）
sessions_spawn(task="分析XX行业", agentId="hunter", runtime="subagent", mode="run")

# 持久会话（可多轮交互）
sessions_spawn(task="你是PPT专家...", agentId="weaver", runtime="subagent", mode="session", thread=True)
```

### 跨 Agent 通信

```python
# 向某个 session 发消息
sessions_send(sessionKey="agent:weaver:feishu:weaver:direct:xxx", message="请完成XX任务")

# 向指定 agent 的最新 session 发消息
sessions_send(label="weaver", message="请确认任务完成")
```

### 管理子代理

```python
# 查看当前活跃的子代理
subagents(action="list")

# 向子代理发送新指令
subagents(action="steer", target="子代理ID", message="调整方向...")

# 终止子代理
subagents(action="kill", target="子代理ID")
```

### 查询 Agent 能力

分派任务前，先读取目标 Agent 的配置文件了解其能力：
```bash
# 读取 Agent 的身份和灵魂文件
read /home/admin/.openclaw/workspace-{agent_id}/SOUL.md
read /home/admin/.openclaw/workspace-{agent_id}/IDENTITY.md
```

**已知 Agent workspace 路径：**

| Agent | Workspace |
|-------|-----------|
| hunter | `/home/admin/.openclaw/workspace-hunter` |
| weaver | `/home/admin/.openclaw/workspace-weaver` |
| coordinate | `/home/admin/.openclaw/workspace-coordinate` |
| visionary | `/home/admin/.openclaw/workspace-visionary` |
| forger | `/home/admin/.openclaw/workspace-forger` |
| sentinel | `/home/admin/.openclaw/workspace-sentinel` |
| evolver | `/home/admin/.openclaw/workspace-evolver` |
| companion | `/home/admin/.openclaw/workspace-companion` |
| guardian | `/home/admin/.openclaw/workspace-guardian` |
| dictator | `/home/admin/.openclaw/workspace-dictator` |

---

## 🔍 信息获取

### 搜索工具

| 优先级 | 工具 | 用法 |
|--------|------|------|
| 1 | Tavily | `tavily_search` 工具，支持搜索/提取/爬取/地图/深度研究 |
| 2 | Multi Search Engine | `web_fetch({"url": "https://duckduckgo.com/html/?q=keyword"})` |
| 3 | SearXNG | 本地隐私搜索实例 |
| 4 | web_search | Brave API |

### 网页抓取

| 工具 | 用途 | 用法 |
|------|------|------|
| `web_fetch` | 轻量抓取（HTML→文本） | `web_fetch({"url": "https://...", "extractMode": "markdown"})` |
| `tavily_extract` | 批量提取多个 URL | `tavily_extract({"urls": ["url1", "url2"]})` |
| `tavily_crawl` | 站点爬取（多页面） | `tavily_crawl({"url": "https://...", "max_depth": 2})` |
| `crawl4ai-skill` | 动态页面抓取（反爬） | 读取 skill 文件后按指引使用 |

---

## 📄 飞书操作

### 文档读写
- `feishu_doc`：读取/写入/创建飞书文档
- `feishu_wiki`：知识库导航和搜索
- `feishu_drive`：云空间文件管理
- `feishu_bitable_*`：多维表格操作

### 消息发送
```python
# 发送消息
message(action="send", channel="feishu", message="内容", target="user:open_id")

# 群聊发送
message(action="send", channel="feishu", message="内容", target="chat:chat_id")
```

### 权限管理
- `feishu_perm`：文档分享和权限管理
- `feishu_chat`：群聊成员和群信息查询

---

## 🔧 开发工具

### GitHub 配置

- 用户名：`hnwlxyzhl-dev`
- 邮箱：`18817350793@163.com`
- SSH：`~/.ssh/id_ed25519`
- Token：`~/.config/github-token`

```bash
git clone git@github.com:hnwlxyzhl-dev/仓库名.git
git add . && git commit -m "message" && git push
```

### Skills 仓库

| 仓库 | 地址 | 安装命令 |
|------|------|----------|
| ClawHub | https://clawhub.com | `clawhub install <skill>` |
| skills.sh | https://skills.sh/ | `npx skills add <owner/repo@skill>` |

**ClawHub Token:** `clh_HFznCaeYn_jRaRsGe3yA4R3VCeeONDgO-9E09vJVwx0`
**登录：** `clawhub login --token clh_HFznCaeYn_jRaRsGe3yA4R3VCeeONDgO-9E09vJVwx0`

---

## ⚙️ 系统管理

### Cron 任务

查看当前任务：`cat ~/.openclaw/cron/jobs.json | jq '.jobs[] | {name, schedule}'`

任务列表是动态的，实时查询 jobs.json 才是最新状态，不要写死。

### 系统配置

- 主配置文件：`/home/admin/.openclaw/openclaw.json`
- Cron 配置：`~/.openclaw/cron/jobs.json`
- Gateway 状态：`openclaw gateway status`
