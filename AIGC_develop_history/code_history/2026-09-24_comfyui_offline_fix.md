# 代码/配置变更记录

## 2026-09-24 · ComfyUI "动不动离线"修复（双实例残留 + 健康探测超时过短）

### 现象
ComfyUI 频繁显示离线，需反复重启；重启后有时又"离线"。

### 根因（两个）
1. **重复启动残留 + 端口冲突**：venv 的 `Scripts\python.exe` 在 Windows 上是 launcher，会再拉起系统 Python 作为真实解释器（所以"两个进程"其实是同一实例的父子链，属正常）。但反复启动/重启时旧实例未清理，出现**两条链抢 8188**：绑定成功的一条在服务，另一条绑定失败变成孤儿；前端探测落空即判"离线"。本次排查发现 8188 曾被系统 Python 实例占用、venv 实例成孤儿。
2. **健康探测超时过短**：后端探测 ComfyUI 的 `system_stats`/`queue` 超时仅 4–5 秒。生图高峰期（Flux2-4B 模型加载 7GB、单次推理 30–50s）时 ComfyUI 偶发响应变慢，探测超时即误报 offline。

### 改动
1. **`F:\Develop\NewAIProductionWorkflow\一键启动全家桶.bat`**（原文件已备份为 `.bat.bak_20260924`）
   - 启动 ComfyUI 前新增：精确清理所有残留 `main.py` 进程（只匹配 main.py，不影响后端 uvicorn/Ollama/前端 vite）→ 杜绝端口冲突
2. **`backend/app/api/health.py`**
   - `/system/monitor` 探测：probe 默认 4s→10s；queue 4s→10s；Ollama 4s→8s
   - `get_comfyui_system_stats`（/comfyui、/system-status）：system_stats 5s→10s
3. **`backend/app/services/comfyui_monitor.py`**
   - `_update_system_stats`：system_stats 5s→10s、queue 5s→10s

### 验证
- ComfyUI 已统一为 venv 规范启动（PID 8772→真实解释器 31344 服务 8188），单链健康
- 后端重启（venv PID 31536），`GET /api/health/system/monitor` → comfyui=ok、ollama=ok
- 一键启动.bat 下次启动时会先清残留再拉起，不再出现孤儿/抢端口

### 备注
- 以后手动重启 ComfyUI：先杀干净再启动，或直接用一键启动.bat
- 如再遇"离线"，先看监控面板 ComfyUI 状态与 comfyui_4b.log 尾部，别盲目反复重启
