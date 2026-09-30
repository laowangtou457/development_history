# 武术指导 · 历史任务时间修复（晚 8 小时）

日期：2026-09-29
状态：已验证

## 用户反馈

历史任务记录的时间不对，和系统时间不一致。

## 根因

`martial_arts_history.created_at` 使用 SQLite `CURRENT_TIMESTAMP` 默认值——**存的是 UTC 时间**。后端返回 `h.created_at.isoformat()`（无时区字符串如 `2026-09-28T10:02:08`），前端 `new Date(...)` 按浏览器本地时区（UTC+8）解析 → 所有记录显示比真实时间**晚 8 小时**。

（示例：真实生成于 09-28 18:02，库里存 10:02:08 UTC，前端显示 10:02）

## 修复（backend/app/api/martial_arts.py）

1. **创建时显式写本地时间**：`from datetime import datetime` + 两处 `MartialArtsHistory(...)` 创建（generate 接口、create 接口）均传 `created_at=datetime.now()`，替代 CURRENT_TIMESTAMP 的 UTC 存储。
2. **存量数据修正**：`UPDATE martial_arts_history SET created_at = datetime(created_at, '+8 hours')`（9 条，UTC → 本地）。

## 验证

| 项 | 结果 |
|---|---|
| 系统时间 | 2026-09-29 09:02 |
| 新 generate 记录 createdAt | 2026-09-29T09:03:01 ✅ 与系统一致 |
| 存量记录 | 09-28 17:12 / 18:02 / 18:08 / 18:10（原 09:12 / 10:02 / 10:08 / 10:10）✅ |
| py_compile / 后端重启 | ✅ PID 56300 |

## 说明

- 前端无需改动：后端现在返回本地时间字符串，`new Date()` 无时区按本地解析即正确显示。
- 主流程其他表（shots/novels 等）若同样用 CURRENT_TIMESTAMP 也存在此问题，本次仅按用户反馈修复武打历史表，未扩大影响面。
