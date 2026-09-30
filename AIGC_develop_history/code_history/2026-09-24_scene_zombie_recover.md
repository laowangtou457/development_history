# 代码/配置变更记录

## 2026-09-24 · 场景批量生成"运行中但 ComfyUI 无队列"排查与恢复

### 现象
监控面板显示 1 个任务 running、118 个 pending，但 ComfyUI 队列 0/0、GPU 使用率 0%，疑似卡死。

### 根因
- 用户在 17:10 左右排队了场景批量生成（1 running + 118 pending）
- 17:25 重启后端（修复 ComfyUI 离线问题）时，**内存任务队列与 gpu_lock 全部重置，正在执行/排队的任务被中断**
- DB 里的任务状态未恢复 → 留下 1 running + 118 pending **僵尸记录**（无 worker 消费，ComfyUI 自然没有队列）

### 处理
1. DB 清理：该小说 119 个 running/pending 僵尸 scene_image 任务 → failed（记录"后端重启中断，已重置重新排队"）
2. 无图且状态 queued/running 的场景 generating_status → failed（保证能被批量接口重新选上）
3. 调用 `POST /api/scenes/generate-missing-images?novel_id=cbcb6f7c...` 重新排队 → 153 个任务入队
4. 观察验证：worker 正常消费，约 5–6 秒/张生成场景图

### 验证结果
- 清理后 30 秒：running=1、pending=147（队列已在消费）
- 恢复后 ~5 分钟：completed 41+，新图持续落盘
  - 新图路径：`backend/user_story/story_cbcb6f7c/scenes/*_20260924_17xxxx.png`（如 山体秘洞_20260924_173739.png）
- ComfyUI 日志 Prompt executed=0 属日志句柄问题（venv launcher 子进程输出未进日志文件），**不影响实际生成**——图文件已落盘验证

### 备注/防复发建议
- **重启后端会中断内存任务队列**（任务状态留在 DB 但不再被消费）——重启后如需继续，重新点"生成缺失图片"或调用 generate-missing-images 即可
- 若再出现"running/pending 但 ComfyUI 队列空"，先核对任务 created_at/updated_at 是否早于后端启动时间（僵尸判定），再清理重排
