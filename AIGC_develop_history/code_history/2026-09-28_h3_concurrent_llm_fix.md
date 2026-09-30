# 变更记录

## 2026-09-28 · H3 拆分与提示词并发调 LLM 修复（30b/8b 同时占显存）

### 现象
生成界面做 H3 分镜时：h3_split_storyboard（qwen3:30b-a3b）与 h3_prompt（qwen3:8b）**同时**被调用，
两个模型同时加载进显存（30b 激活+KV ≈ 20G+，8b ≈ 6G），4090 32G 逼近上限 → 拆分卡住/拆不出来。

### 根因
`backend/app/api/h3_workflow.py` 三个 H3 接口**未走全局 GPU 串行锁**（`gpu_scheduler.gpu_serial`）：
- `POST .../h3-split`（拆分，HEAVY_MODEL_TASKS→30b）直接 `await service.script_to_storyboard()`
- `POST .../h3-prompt`（逐镜/单镜提示词，LIGHT_MODEL_TASKS→8b）直接 `await service.storyboard_to_shot_prompt()`

模型分流本身正确（llm_service 三级分流：LIGHT→8b / HEAVY→30b / 其余→系统默认），
但**没有锁 → 用户连续触发两个按钮时两个 LLM 请求并发 → Ollama 同时加载两个模型**。
其它 API 直连 LLM 的端点（如关键帧规划 shots.py）早已用 gpu_serial 包锁，H3 属漏网。

### 修复（h3_workflow.py）
三个接口的 LLM 调用全部包 `gpu_serial`：
1. h3-split（30b 拆分）→ `gpu_serial("h3_split_storyboard", ...)`
2. h3_prompt_all_shots（8b 整批逐镜）→ 循环体抽为内部协程，整批 `gpu_serial("h3_prompt_all", ...)` 独占 GPU
3. h3_prompt_one_shot（8b 单镜）→ `gpu_serial("h3_prompt_one", ...)`

锁内无嵌套取锁（script_to_storyboard / storyboard_to_shot_prompt → chat_completion 不带锁），无死锁风险。

### 验证
- 语法校验通过；后端重启 :8000 health 200
- 效果：现在「H3 生成文字分镜」进行中，再点「生成分镜提示词（H3）」会**等待锁**而不是并发推理；
  拆分（30b）与提示词（8b）同一时刻只允许一个在 GPU 上运行

### 备注（可选后续）
- Ollama 默认 keep_alive=5min，拆分（30b）完成后模型仍驻留显存，紧接着加载 8b 时两者短暂共存；
  串行后同一时刻只推理一个，驻留共存一般可承受。若仍紧张可设环境变量
  `OLLAMA_MAX_LOADED_MODELS=1`（需重启 Ollama，代价是切模型时有冷启动延迟）。
