# 武术指导 · 任务进程监控接入武打任务

日期：2026-09-28
状态：已验证

## 需求

「任务进程监控」页面没有监控武打（martial-arts）任务的生成过程——武打分镜/角色图/分镜图/武打视频在监控页看不到。

## 根因

主监控（`/api/health/system/monitor`）的任务数据来自 `tasks` 表 + `llm_logs` 表；武打工作流完全独立（martial_arts_history 表 + 内存调度），不写这两张表 → 主监控看不到武打任务。

## 实现

### 后端（backend/app/api/martial_arts.py）

**武打任务运行时监控注册表**（内存，进程重启清零）：
- `MARTIAL_TASKS`（dict）：运行中任务；`MARTIAL_RECENT`（deque maxlen=20）：最近完成/失败记录
- `_martial_start(task_type, detail)` / `_martial_update(tid, stage)` / `_martial_finish(tid, error)`

**四个接口全部埋点**：
| 接口 | 类型标签 | 阶段 |
|---|---|---|
| POST /generate | 武打分镜提示词 | 招式编排（qwen3:8b）→ 提示词组装（qwen3:8b） |
| POST /generate-image | 角色形象图（文生图） | ComfyUI 文生图（Flux2-4B） |
| POST /edit-image | 分镜图（图生图） | ComfyUI 图生图（4B） |
| POST /generate-video | 武打视频（图生视频） | ComfyUI 图生视频（H3） |

失败分支全部 `_martial_finish(tid, error=...)` 记录错误。

**新增接口**：`GET /api/martial-arts/monitor` → `{ running: [...], recent: [...] }`（运行中含经过分钟数，疑似卡死判定）。

### 前端

1. `src/api/martialArts.ts`：`MartialTaskRecord` / `MartialMonitorData` 类型 + `fetchMonitor()`
2. `src/pages/Monitor/index.tsx`：新增「武打任务」区块（LLM 调用状态下方）：
   - 运行中任务：名称+当前阶段+经过分钟（>10 分钟红标"疑似卡死"）
   - 最近完成/失败：名称+状态+耗时+错误信息
   - 随主监控 5 秒自动刷新联动

## 验证（真实端到端）

| 验证项 | 结果 |
|---|---|
| py_compile / tsc | ✅ |
| monitor 接口空态 | ✅ running=0 recent=0 |
| **真实 generate 运行中采样** | ✅ 采样1：运行中·招式编排（qwen3:8b）→ 采样2/3：提示词组装（qwen3:8b） |
| **真实 generate 完成后** | ✅ running=0，recent=[武打分镜提示词 completed 25.9s] |
| 后端重启 | ✅ PID 11380 |

## 说明

- 注册表是内存态：后端重启后清空（历史产物仍可查 martial_arts_history，监控仅反映进程内活动）
- 武打监控独立接口，前端拉取失败不影响主监控展示
