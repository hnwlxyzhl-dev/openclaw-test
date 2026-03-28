# Learnings Log

## [LRN-20260315-001] correction

**Logged**: 2026-03-15T14:48:00+08:00
**Priority**: high
**Status**: pending
**Area**: config

### Summary
错误诊断：将 ClawHub 认证问题误判为"限流"问题

### Details

**现象**：`clawhub install` 和 `clawhub search` 返回 "Rate limit exceeded"

**错误分析**：看到 "Rate limit exceeded" 就直接判断为服务器端限流

**根本原因**：未登录 ClawHub 账号
- `clawhub whoami` 返回 "Not logged in"
- `clawhub inspect` 可以用（不需要认证）
- `clawhub install/search` 需要认证，未登录被拒绝

**教训**：
1. 错误信息不一定反映根本原因
2. 看到 "rate limit" 应该先检查认证状态
3. 部分功能可用（inspect）、部分不可用（install）是认证问题的典型特征
4. 应该用 `whoami` 或类似命令验证认证状态

### Suggested Action
以后遇到 API 错误时，先检查：
1. 认证状态（`whoami` / `login`）
2. 权限/配额
3. 网络连接
4. 才考虑服务端限流

### Metadata
- Source: user_feedback
- Related Files: ~/.openclaw/workspace/MEMORY.md
- Tags: debugging, clawhub, authentication, error-diagnosis
- Pattern-Key: error_diagnosis.auth_vs_ratelimit

---
