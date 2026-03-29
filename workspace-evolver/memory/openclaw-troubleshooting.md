# OpenClaw 故障排除指南

> Evolver 整理的 OpenClaw 故障排除知识

---

## 1. 诊断工具

### 1.1 openclaw doctor

最常用的诊断命令：

```bash
# 基础诊断
openclaw doctor

# 深度诊断
openclaw doctor --deep

# 自动修复
openclaw doctor --fix

# 检查所有
openclaw doctor --all
```

### 1.2 检查项目

| 项目 | 说明 |
|-----|------|
| 配置验证 | 检查 openclaw.json 格式 |
| 模型状态 | 检查 API Key 和模型可用性 |
| 渠道状态 | 检查渠道连接 |
| 插件状态 | 检查插件加载 |
| 沙箱配置 | 检查 Docker 配置 |
| 权限 | 检查文件和目录权限 |

### 1.3 状态命令

```bash
# Gateway 状态
openclaw gateway status

# 模型状态
openclaw models status

# 插件状态
openclaw plugins doctor

# 查看日志
openclaw logs
openclaw logs --follow
```

---

## 2. Gateway 启动失败

### 2.1 常见原因

| 原因 | 解决方案 |
|-----|---------|
| 端口被占用 | 更改端口或释放端口 |
| 配置错误 | 运行 `openclaw doctor --fix` |
| 权限问题 | 检查文件权限 |
| 依赖缺失 | 重新安装依赖 |
| Docker 问题 | 检查 Docker 服务 |

### 2.2 详细排查

**1. 检查端口占用**：
```bash
# Linux/macOS
lsof -i :443
netstat -tlnp | grep 443

# 更改端口
openclaw config set gateway.port 8443
```

**2. 检查配置**：
```bash
# 验证配置
openclaw doctor --deep

# 查看配置
openclaw config get
```

**3. 检查日志**：
```bash
# 查看最新日志
openclaw logs --tail 100

# 日志文件位置
/tmp/openclaw/openclaw-*.log
```

**4. 检查依赖**：
```bash
# 重新安装
npm install -g openclaw

# 或使用 npx
npx openclaw doctor
```

### 2.3 Docker 问题

```bash
# 检查 Docker 服务
docker info

# 重启 Docker
sudo systemctl restart docker

# 检查镜像
docker images | grep openclaw

# 拉取最新镜像
docker pull openclaw/openclaw:latest
```

### 2.4 环境变量问题

```bash
# 检查环境变量
env | grep OPENCLAW
env | grep ANTHROPIC
env | grep OPENAI

# 设置缺失的环境变量
export ANTHROPIC_API_KEY=xxx
export OPENAI_API_KEY=xxx
```

---

## 3. 模型问题

### 3.1 认证失败

```bash
# 检查 API Key
openclaw models status

# 重新认证
openclaw models auth login --provider anthropic
openclaw models auth login --provider openai
```

### 3.2 模型不可用

```bash
# 查看可用模型
openclaw models list

# 设置默认模型
openclaw models set anthropic/claude-sonnet-4-5

# 扫描免费模型
openclaw models scan
```

### 3.3 Fallback 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-opus-4-6",
        fallbacks: [
          "anthropic/claude-sonnet-4-5",
          "openai/gpt-5.2"
        ]
      }
    }
  }
}
```

---

## 4. 渠道问题

### 4.1 WhatsApp

**问题：无法连接**
```bash
# 检查会话文件
ls ~/.openclaw/credentials/whatsapp/

# 重新登录
openclaw channels logout --channel whatsapp
openclaw channels login --channel whatsapp
```

**问题：消息不发送**
```bash
# 检查配对状态
openclaw doctor --channel whatsapp

# 检查 allowFrom
openclaw config get channels.whatsapp.allowFrom
```

### 4.2 Telegram

**问题：Bot 不响应**
```bash
# 检查 Bot Token
openclaw config get channels.telegram.botToken

# 检查 webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# 删除 webhook（使用 long polling）
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

### 4.3 Discord

**问题：Bot 不在线**
```bash
# 检查 Token
openclaw config get channels.discord.token

# 检查 Bot 权限
# 在 Discord Developer Portal 检查 Bot 权限
```

---

## 5. 插件问题

### 5.1 插件加载失败

```bash
# 检查插件状态
openclaw plugins list
openclaw plugins doctor

# 重新安装
openclaw plugins uninstall <plugin-id>
openclaw plugins install <plugin-id>
```

### 5.2 兼容性问题

```bash
# 检查兼容性
openclaw plugins inspect <plugin-id>

# 查看警告
openclaw doctor --all | grep plugin
```

---

## 6. 沙箱问题

### 6.1 Docker 连接失败

```bash
# 检查 Docker 服务
docker info

# 检查权限
sudo usermod -aG docker $USER

# 重启 Docker
sudo systemctl restart docker
```

### 6.2 沙箱超时

```json5
{
  agents: {
    defaults: {
      sandbox: {
        docker: {
          timeout: 60000  // 60秒
        }
      }
    }
  }
}
```

### 6.3 网络问题

```json5
{
  agents: {
    defaults: {
      sandbox: {
        docker: {
          network: "bridge",  // 允许网络
          dns: ["8.8.8.8", "1.1.1.1"]
        }
      }
    }
  }
}
```

---

## 7. Token 问题

### 7.1 上下文过长

```bash
# 启用 context pruning
openclaw config set agents.defaults.contextPruning.mode adaptive
```

### 7.2 成本过高

```bash
# 启用 prompt caching
openclaw config set agents.defaults.models.anthropic/claude-opus-4-6.params.cacheRetention long

# 限制历史
openclaw config set channels.whatsapp.historyLimit 30
```

---

## 8. 性能问题

### 8.1 响应慢

**可能原因**：
- 模型延迟高
- 上下文过长
- 网络问题

**解决方案**：
```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-sonnet-4-5"  // 使用更快的模型
      },
      contextPruning: {
        mode: "aggressive"
      }
    }
  }
}
```

### 8.2 内存占用高

```bash
# 检查内存
top -p $(pgrep -f openclaw)

# 重启 Gateway
openclaw gateway restart
```

---

## 9. 日志分析

### 9.1 日志位置

```
/tmp/openclaw/openclaw-YYYY-MM-DD.log
```

### 9.2 常用过滤

```bash
# 错误日志
openclaw logs | grep -i error

# 特定渠道
openclaw logs | grep "whatsapp"

// 特定会话
openclaw logs | grep "session-id"
```

### 9.3 调试模式

```bash
# 启用调试
DEBUG=openclaw:* openclaw gateway start

# 更详细的日志
LOG_LEVEL=debug openclaw gateway start
```

---

## 10. 重置和恢复

### 10.1 重置配置

```bash
# 备份配置
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak

# 重置为默认
openclaw configure --reset
```

### 10.2 清理会话

```bash
# 清理所有会话
rm -rf ~/.openclaw/agents/*/sessions/*

# 清理特定 Agent
openclaw session clear --agent-id main
```

### 10.3 完全重装

```bash
# 卸载
npm uninstall -g openclaw

# 清理
rm -rf ~/.openclaw

# 重新安装
npm install -g openclaw

# 重新配置
openclaw onboard
```

---

## 11. 预防措施

### 11.1 定期维护

```bash
# 每周运行
openclaw doctor --deep
openclaw models status
openclaw plugins doctor
```

### 11.2 监控

```bash
# 设置 cron 定期检查
openclaw cron add --name "health-check" \
  --schedule "0 3 * * *" \
  --prompt "Run openclaw doctor and report issues"
```

### 11.3 备份

```bash
# 备份配置
cp ~/.openclaw/openclaw.json ~/.openclaw/backups/

# 备份工作区
tar -czf workspace-backup.tar.gz ~/.openclaw/workspace-*
```

---

_持续更新中..._
