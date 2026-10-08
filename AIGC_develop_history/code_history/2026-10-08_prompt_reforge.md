# 2026-10-08 提示词提取与重构功能（PromptReforge）

> 监控脚本离线期间主动记录。功能：主菜单左侧新增【提示词提取与重构】，上传文件或直接输入提示词/剧本/小说，按"导演模型"提取剧本节拍 → 重构为 AI 工具可生成级的多平台逐镜提示词集（MiniMax H3 / Seedance / Kling / Veo / 即梦）。

## 一、需求背景

参考历史【AI 视频提示词导演技能安装】（武术指导 director skill 与 H3 六段式框架的提示词升级经验），抽象出 4 个「导演模型」，把"升级提示词"做成平台内可复用的独立工作流。产物要求【AI 工具可生成级】：模型拿到提示词无需二次理解即可生成。

## 二、变更清单

### 后端（新增 3 文件 + 修改 2 文件）

| 文件 | 变更 | 说明 |
|---|---|---|
| `backend/app/models/prompt_reforge_history.py` | 新增 | PromptReforgeHistory 模型，表 `prompt_reforge_history`：title/input_type/source_name/input_text/input_summary/director_model/target_platforms/status/stage/output_dir/output_md/report_json/error/时间戳 |
| `backend/app/services/prompt_reforge_service.py` | 新增（约 300 行） | 核心服务：① `DIRECTOR_MODELS` 导演模型抽象（h3_ref2va=官方 Ref2VA 六段式，规则读 `ManjuToSplitFrameAndProperty/docs/references/ref-en.txt`；h3_i2v=官方 I2VA 三字段，读 `base-en.txt`；martial_arts=武打导演 7 原则/姿态配额/场景尺度/武器约束；general_cinematic=通用六要素）② 提取 `_extract_beats`（8b JSON）③ 重构 `_reforge_prompts`（按平台分区 `### 平台名`）④ 组装 `_pack_outputs`（prompts.md + payloads/shot_NNN.json + report.json 落盘到 `backend/data/prompt_reforge/<task_id>/`）⑤ `_split_platform_parts` 按分区标题拆包 |
| `backend/app/api/prompt_reforge.py` | 新增 | `POST /api/prompt-reforge/tasks`（multipart：文件或文本 + director_model + target_platforms）、`GET /tasks`（列表）、`GET /tasks/{id}`（详情含 report/platform_parts/file_tree）、`GET /tasks/{id}/files/{path}`（产物下载，路径越界防护）、`GET /director-models`（4 导演模型） |
| `backend/app/main.py` | 修改 | import PromptReforgeHistory 模型（建表）+ 注册 `prefix=/api/prompt-reforge` |
| `backend/app/services/llm_service.py` | 修改 | `LIGHT_MODEL_TASKS` 新增 `prompt_reforge_extract`（节拍提取）与 `prompt_reforge_build`（逐镜重构），均走 qwen3:8b（轻量任务分流，避免 30b 长文截断） |

### 前端（新增 2 文件 + 修改 4 处）

| 文件 | 变更 | 说明 |
|---|---|---|
| `frontend/my-app/src/api/promptReforge.ts` | 新增 | list/get/create/listDirectorModels + reforgeFileUrl |
| `frontend/my-app/src/pages/PromptReforge/index.tsx` | 新增（约 430 行） | 左列任务列表 + 新建表单（标题/导演模型下拉/输入类型切换/文件上传/文本输入/目标平台多选）+ 详情 4 页签（原始输入/提取节拍/提示词集/产物文件）+ 平台分区切换 + 复制/下载 + 3s 轮询 |
| `frontend/my-app/src/App.tsx` | 修改 | lazy 引入 PromptReforge + 路由 `prompt-reforge`；**顺手修复历史残留脏字符**：monitor 行后曾混入字面 `` `r`n `` 文本 |
| `frontend/my-app/src/components/Sidebar.tsx` | 修改 | 新增导航项 `nav.promptReforge`（icon: Wand2，href: /prompt-reforge） |
| i18n 5 语言 `nav.ts`（zh-CN/zh-TW/en-US/ko-KR/ja-JP） | 修改 | 新增 `promptReforge` key；**修复了先前误操作**：曾把 videoAssetSwap 值改成了新功能名，已恢复原值并正确新增 promptReforge |

## 三、踩坑记录

1. **前端列表恒空（最坑）**：`api.get` 的 `parseResponse` 已把后端 `{success, data:[...]}` 解析为 `{success, data}`，`res.data` 本身就是数组。初版写成 `res.data?.data ?? []`（多取一层），数组上无 `.data` → 恒返回 `[]`，页面永远"历史任务（0）"，浏览器 fetch 却正常返回。**教训：以现有 api/videoAsset.ts 的 `api.get<T>` 用法为准，不要凭直觉多剥一层。**
2. **create 接口响应无 data 包裹**：后端 `POST /tasks` 初版返回 `{success, task_id, message}`，而 `parseResponse` 只保留 `{success, data, message}` 三字段 → task_id 丢失。改为返回 `{success, data:{task_id, message}}`。
3. **PowerShell 批量改 i18n 误伤**：正则替换把 4 个语言文件的 videoAssetSwap 值改成了新功能名且 promptReforge 未加上，需逐个 Read 后重写（Write 前必须 Read，否则拒绝）。
4. **8b 格式漂移**：重构输出偶发把角色名当平台标题（如 `### 黑衣刀客`）。`_split_platform_parts` 只认 `### 平台名` 白名单，未命中内容并入前一分区，前端回退显示整段 output_md，不阻塞使用；后续可在 prompt 中加示例强化。

## 四、验证记录

- 后端：`python -c` 语法/导演模型自检通过；`/api/prompt-reforge/director-models` 返回 4 模型。
- 端到端（真实 8b 推理）：提交"暴雨断桥刀客对峙"→ 提取 5 个剧本节拍（角色 2/场景 1 结构化正确）→ 重构 12 镜 × 5 平台 → **30 秒完成**。
- 产物：`backend/data/prompt_reforge/5bcfb0d7-.../` 下 prompts.md（约 9KB）+ report.json + 12 个 payload JSON；`platform_parts` 拆出 minimax_h3（3391 字符）/seedance（5557 字符）等 5 分区。
- 前端：tsc --noEmit 通过；浏览器实测——任务列表显示、详情页渲染、Seedance 分区切换、产物文件 tab 下载链接（prompts.md/report.json/payloads/*.json）全部正常；新建表单（导演模型下拉+输入类型切换+平台多选）完整。
- 服务状态：后端 8000 已重启生效，前端 5173 热更新，Ollama 11434 正常。

## 五、待迭代

- 8b 六段式格式遵循度一般（首镜结构完整、后续镜 detailed_description 内联），如需严格分段可换 30b 或加 few-shot 示例。
- 上传文件仅支持文本类；未来可接 docx/pdf 解析。
- 产物暂未接 ComfyUI 自动生图/生视频，可后续按 H3 payload 复用。
