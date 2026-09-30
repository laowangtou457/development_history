# 运维记录

## 2026-09-28 · 角色生成任务卡死排查与恢复

### 现象
角色批量生成卡住：1 个任务 running + 39 个 pending，**全部停在 01:27 创建后无推进**；ComfyUI 显存 0（空闲）、队列空。

### 排查
- 任务卡在"提示词构建完成 → 提交 ComfyUI"之间（task.comfyui_prompt_id=None、无 error、current_step 停在提示词处）
- 事件循环存活（/api/health 200）、Ollama/ComfyUI 均正常——判定为**后端内存任务队列（asyncio worker + 全局 GPU 锁）内部卡死**，单个任务体在某 await 处挂起且无超时兜底
- 与历史"场景 118/119 僵尸队列"同模式：任务状态在 DB 持久化，但内存队列无消费者/消费者卡死

### 处理
1. 清僵尸任务：40 个 running/pending 任务 → failed（标注"恢复队列时重置(卡死任务)"）
2. 重置 40 个角色 generating_status → NULL（保留已有图）
3. 重启后端（venv uvicorn :8000，清内存队列与 GPU 锁）
4. 重新排队：40 个角色逐个调 `POST /api/characters/{id}/generate-portrait` 重新入队

### 恢复后观察（正常消费）
- 02:05 入队 → 02:06 完成 +12 → 02:07 完成 +10，ComfyUI running=1（任务已提交生成中）
- 运行中任务提示词已带**中国风约束**（East Asian facial features / long black hair / 写实人设）
- 恢复后 pending 17 + running 1，队列正常消费

### 说明
- 该卡死模式已多次出现（场景/角色/道具），根因是内存队列任务体 await 无超时兜底 + 全局 GPU 锁被挂起任务长期持有
- 后续建议（待做）：给任务体关键 await（LLM/ComfyUI）加全局看门狗超时；或任务恢复脚本通用化（character/scene/prop 三个类型共用）
