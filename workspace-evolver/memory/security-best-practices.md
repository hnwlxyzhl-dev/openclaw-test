# AI 安全最佳实践

> Evolver 整理的 AI 应用安全知识

---

## 1. 威胁模型 (MITRE ATLAS)

AI 系统面临的主要威胁类别：

### 1.1 输入攻击

| 攻击类型 | 描述 | 防护措施 |
|---------|------|---------|
| **Prompt Injection** | 恶意输入操控 AI 行为 | 输入验证、指令隔离 |
| **Jailbreak** | 绕过安全限制 | 系统提示加固 |
| **Data Poisoning** | 污染训练数据 | 数据验证、来源控制 |

### 1.2 信息泄露

| 攻击类型 | 描述 | 防护措施 |
|---------|------|---------|
| **Training Data Extraction** | 提取训练数据 | 差分隐私 |
| **Prompt Leakage** | 泄露系统提示 | 敏感信息隔离 |
| **Context Leakage** | 上下文信息泄露 | 最小权限原则 |

### 1.3 工具滥用

| 攻击类型 | 描述 | 防护措施 |
|---------|------|---------|
| **Tool Abuse** | 滥用工具能力 | 工具权限控制 |
| **Code Execution** | 恶意代码执行 | 沙箱隔离 |
| **Network Exfiltration** | 数据外泄 | 网络限制 |

---

## 2. OpenClaw 安全配置

### 2.1 访问控制

**配对模式（推荐）**：
```json5
{
  channels: {
    whatsapp: {
      dmPolicy: "pairing",  // 需要配对才能使用
      groups: {
        "*": { requireMention: true }  // 群聊需要 @
      }
    }
  }
}
```

**白名单模式**：
```json5
{
  channels: {
    whatsapp: {
      dmPolicy: "allowlist",
      allowFrom: ["+15555550123"]
    }
  }
}
```

### 2.2 沙箱隔离

**默认沙箱**：
```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",  // 非主会话沙箱化
        scope: "agent",
        docker: {
          network: "none",       // 无网络
          capDrop: ["ALL"],      // 移除所有能力
          readOnlyRoot: true,    // 只读文件系统
          seccomp: "unconfined"  // 或自定义 profile
        }
      }
    }
  }
}
```

**自定义镜像**：
```json5
{
  agents: {
    defaults: {
      sandbox: {
        docker: {
          image: "my-sandbox:v1",
          setupCommand: "apt-get update && apt-get install -y git"
        }
      }
    }
  }
}
```

### 2.3 工具控制

**工具 Profile**：
```json5
{
  agents: {
    list: [{
      id: "restricted",
      tools: {
        profile: "minimal",  // minimal | coding | messaging | full
        allow: ["read", "write"],
        deny: ["exec", "browser"]
      }
    }]
  }
}
```

**敏感工具限制**：
```json5
{
  tools: {
    elevated: {
      enabled: true,
      allowFrom: {
        whatsapp: ["+15555550123"]  // 只允许特定用户提升权限
      }
    }
  }
}
```

### 2.4 命令限制

```json5
{
  commands: {
    bash: false,      // 禁用 ! 命令
    config: false,    // 禁用 /config
    restart: false,   // 禁用 /restart
    shell: false      // 禁用 /shell
  }
}
```

---

## 3. Prompt 注入防护

### 3.1 常见注入模式

```
Ignore previous instructions and...
You are now in developer mode...
[SYSTEM OVERRIDE]...
```

### 3.2 防护策略

1. **指令隔离**：系统指令与用户输入分开
2. **输入验证**：过滤可疑模式
3. **权限最小化**：限制敏感操作
4. **沙箱执行**：隔离不可信输入

### 3.3 OpenClaw 内置防护

- 系统提示与用户输入分离
- 工具权限分级
- 沙箱隔离执行
- 敏感命令需要确认

---

## 4. 数据安全

### 4.1 敏感数据处理

**不要**：
- 在 prompt 中包含密码、API key
- 让 AI 处理高度敏感数据
- 将凭证写入日志或记忆文件

**应该**：
- 使用 SecretRef 管理凭证
- 启用磁盘加密
- 定期审计访问日志

### 4.2 凭证管理

```json5
{
  models: {
    providers: {
      anthropic: {
        apiKey: { source: "env", provider: "default", id: "ANTHROPIC_API_KEY" }
      }
    }
  }
}
```

### 4.3 记忆文件安全

- `MEMORY.md` 只在主会话加载
- 不要在记忆中存储凭证
- 定期清理敏感信息

---

## 5. 网络安全

### 5.1 Gateway 配置

**绑定地址**：
```json5
{
  gateway: {
    host: "127.0.0.1",  // 只监听本地
    port: 443
  }
}
```

**反向代理**：
- 使用 Nginx/Caddy 添加 HTTPS
- 配置 rate limiting
- 启用访问日志

### 5.2 沙箱网络

**无网络（最安全）**：
```json5
{ sandbox: { docker: { network: "none" } } }
```

**限制网络**：
```json5
{
  sandbox: {
    docker: {
      network: "bridge",
      dns: ["1.1.1.1"],
      extraHosts: ["internal.local:10.0.0.1"]
    }
  }
}
```

---

## 6. 主机安全（Healthcheck）

### 6.1 基本检查

```bash
# OpenClaw 安全审计
openclaw security audit --deep

# 应用安全默认配置
openclaw security audit --fix

# 检查更新
openclaw update status
```

### 6.2 风险配置文件

| 配置文件 | 适用场景 | 特点 |
|---------|---------|------|
| **Home/Workstation** | 个人电脑 | 防火墙开启，远程访问受限 |
| **VPS Hardened** | 公网服务器 | 拒绝默认，最小端口，仅密钥 SSH |
| **Developer** | 开发环境 | 更多本地服务，明确警告 |

### 6.3 关键安全措施

- [ ] 防火墙启用
- [ ] SSH 仅密钥认证
- [ ] 禁用 root 登录
- [ ] 自动安全更新
- [ ] 磁盘加密 (FileVault/LUKS/BitLocker)
- [ ] 定期备份
- [ ] 定期安全审计

---

## 7. 监控与审计

### 7.1 日志配置

```json5
{
  logging: {
    level: "info",
    file: "/var/log/openclaw/openclaw.log",
    redactSecrets: true
  }
}
```

### 7.2 定期审计

使用 OpenClaw cron 定时审计：
```bash
openclaw cron add --name "security-audit" \
  --schedule "0 3 * * *" \
  --prompt "Run security audit" \
  --target "log"
```

---

## 8. 最佳实践清单

### 8.1 基础安全

- [ ] 使用配对模式或白名单
- [ ] 启用沙箱（至少 non-main）
- [ ] 限制敏感工具
- [ ] 禁用不必要的命令

### 8.2 数据安全

- [ ] 不在 prompt 中存储凭证
- [ ] 启用磁盘加密
- [ ] 定期清理记忆文件
- [ ] 备份重要数据

### 8.3 网络安全

- [ ] Gateway 只监听本地或 VPN
- [ ] 使用 HTTPS
- [ ] 沙箱无网络或限制网络
- [ ] 配置防火墙

### 8.4 持续监控

- [ ] 启用日志
- [ ] 定期安全审计
- [ ] 关注更新通知
- [ ] 监控异常活动

---

_持续更新中..._
