# 代码/配置变更记录

## 2026-09-24 · 118 个 pending 场景未进队列修复（场景状态表未同步）

### 现象
场景列表 118 个场景一直 pending（待生成），但任务表无 pending/running、ComfyUI 队列空，无新任务进队列。

### 根因
- 这 118 个场景**已有图**（9-23 生成的旧图），generating_status='pending' 是上午批量"重新生成"排队时标记的
- 上午那批任务在 09:33 被清理为 failed（见 scene_zombie_recover 记录）时，**只清了任务表，未同步场景表的 generating_status**
- 批量接口 `generate-missing-images` 只选「无图 或 failed」的场景 → 这 118 个"有图 + pending"永远选不中 → 无任务进队列

### 处理
1. `UPDATE scenes SET generating_status='failed' WHERE novel_id=... AND generating_status='pending'`（118 个，保留旧图兜底）
2. 调用 `POST /api/scenes/generate-missing-images` → 119 个任务入队
3. 验证：15 秒后 running=1、pending=116，队列正常消费

### 教训
清理僵尸任务时必须**同步重置场景/角色/道具表的 generating_status**，否则"有图+pending"状态会成为批量接口的死角。
