# 武术指导工作流 · 本地生成接入（文生图 / 图生图 / 图生视频）

日期：2026-09-28
状态：端到端测试通过（文生图 16s / 图生图 12s / 图生视频 111s）

## 一、需求

在已完成的「武术指导」独立工作流（一句话需求 → 人物锚定卡 + 图片提示词 + 视频提示词，8b 两步）基础上，接入三个生成功能：
- **文生图**：人物锚定卡（角色信息）→ 角色形象图（Flux2-Klein-4B）
- **图生图**：角色形象图作参考 + 文字分镜提示词 → 分镜图（single_image_edit，4B）
- **图生视频**：分镜图 → H3 视频（ref2va 单参考 / first_last 首尾帧）

要求：使用平台现有 ComfyUI 工作流/模型，合理分配显存（4090 32G），不显存溢出。

## 二、变更文件

### 1. 后端 `AI-NovelFlow\backend\app\api\martial_arts.py`

新增 3 个接口 + 4 个辅助函数：

| 接口 | 说明 |
|---|---|
| `POST /api/martial-arts/generate-image` | 文生图：自建 Flux2-4B 纯文生图工作流（steps=8、cfg=1、负向 ConditioningZeroOut 防平台模板污染） |
| `POST /api/martial-arts/edit-image` | 图生图：复用激活的 single_image_edit（4B） |
| `POST /api/martial-arts/generate-video` | 图生视频：复用 video(ref2va) / first_last_video 两类 H3 工作流 |

辅助函数：
- `_build_flux2_4b_text2img_workflow(prompt, aspect_ratio)`：动态拼接 Flux2-Klein-4B 文生图节点链
- `_ensure_comfyui_input_filename(url)`：**关键修复**。ComfyUI LoadImage 只认 input 目录，不能直接引用 output 目录文件（直接引用报 400 `Invalid image file`）。此函数下载 output 图片 → 上传到 input 目录 → 返回文件名
- `_free_comfyui_cache()`：视频前调 ComfyUI `/free`（unload_models + free_memory），释放 flux 缓存
- `_queue_and_wait()` / `_get_active_workflow_json()` / `_comfyui_filename_from_url()`：排队等待、按类型取激活工作流、URL→文件名

显存治理三件套（均已在生成链路生效）：
1. `gpu_serial("martial_arts_*", coro)` 全局锁（app/services/gpu_scheduler.py）
2. `ComfyUIClient.queue_prompt` 内部自动 `keep_alive:0` 卸载 Ollama（qwen3:30b-a3b / 8b）
3. 视频前 `POST {comfyui}/free`

### 2. 前端 `frontend\my-app\src\api\martialArts.ts`

新增 4 个 API 方法（generate / generateImage / editImage / generateVideo）与请求/响应类型。本任务仅语义注释更新。

### 3. 前端 `frontend\my-app\src\pages\MartialArts\index.tsx`（整体重写语义）

本地生成区改为三步闭环（全部串行防显存溢出）：

| 步骤 | 输入 | 输出 | 模型 |
|---|---|---|---|
| ① 角色形象图（文生图） | 人物锚定卡（cardToText 提取） | 角色形象图（锁定人物） | Flux2-Klein-4B |
| ② 分镜图（图生图） | 角色形象图(参考) + 文字分镜提示词（留空默认用 imagePrompt） | 分镜图（多宫格海报） | single_image_edit 4B |
| ③ 武打视频（图生视频） | 分镜图（回退角色图）+ 视频提示词 | H3 视频 | MiniMax H3（ref2va / first_last） |

新增 `cardToText()`：人物锚定卡 markdown 表格 → 纯文本角色描述（"项目：内容；项目：内容"）。
状态重命名：posterUrl→characterUrl、posterRatio→characterRatio、editedUrl→storyboardUrl。
② ③ 区块在角色图生成后出现，避免空跑。

### 4. 前端 `frontend\my-app\src\pages\ChapterGenerate\components\FinalVideoPanel.tsx` + `ChapterGenerateLayout.tsx`

顺带修复 tsc 报错：`useParams` 返回的 id/cid 可能为 undefined，Props 类型放宽 + 传入处加 `|| ''`。

## 三、关键坑与根因

| 现象 | 根因 | 修复 |
|---|---|---|
| 图生图报 400 `prompt_outputs_failed_validation` / `Invalid image file` | ComfyUI LoadImage 只认 input 目录，output 目录文件不能直接引用 | `_ensure_comfyui_input_filename`：下载→上传 input→引用文件名 |
| 显存不足 OOM | 生图(flux) + LLM(ollama) + H3 视频同时驻留 | 串行锁 + 自动卸载 Ollama + 视频前 /free |

## 四、验证结果（真实端到端）

| 链路 | 耗时 | 结果 |
|---|---|---|
| ① 文生图（角色图） | 16s | ✅ `martial_arts_00001_.png` |
| ② 图生图（分镜图） | 12s | ✅ `Flux2-Klein_00058_.png`（1.07MB） |
| ③ 图生视频（ref2va 4s） | 111s | ✅ `MiniMax_H3_00045_.mp4`（0.51MB，subfolder=video） |

产物 URL 均已用 HTTP 下载验证可访问。
前端 `npx tsc --noEmit` 通过；后端 `py_compile` 通过；后端已重启（PID 56920）接口生效。

## 五、遗留 / 待确认

- 首尾帧（first_last）模式未实测，依赖同样的回传逻辑（已统一改造），建议后续用真实角色图+分镜图试跑一次。
- 文生图输入目前取人物锚定卡全表；若角色描述过长可考虑只取关键字段。
- 视频参考图默认取分镜图（②），未生成时回退角色图（①）——符合用户澄清语义。
