# 更新 MiniMaxH3模型下载清单.md 为平台全模型清单

日期：2026-09-30
状态：已完成并推送 GitHub

## 需求

更新 `F:\Develop\NewAIProductionWorkflow\MiniMaxH3模型下载清单.md`。

## 变更内容

原文档仅含 H3 视频 5 模型（90GB+）；现扩展为**平台全部本地模型清单**，并依据实际部署状态标注 ✅/⬜：

| 分类 | 内容 |
|---|---|
| H3 视频模型（5 个） | minimax_h3_ref2va_bf16(63.2GB) / qwen3vl_32b(25.9GB) / video_vae(5GB) / audio_vae(577MB) / turbo LoRA(1.9GB) —— 全部 ✅ 已部署 |
| 生图模型 | flux-2-klein-4b(默认,7.4GB) / 9b(弃用,17.3GB) / flux2-vae / qwen_3_8b·4b 文本编码器 / SDXL 动漫底模 animagine-xl-3.1 / 写实底模 RealVisXL_V5.0 / sdxl_vae —— ✅ |
| Ollama LLM/VLM | qwen3:8b(5.2GB) / qwen3:30b-a3b(18GB) / qwen3:32b(20GB) / qwen2.5vl:3b(3.2GB) —— ✅；gpt-oss:120b-cloud 为云端引用无需下载 |
| ASR | faster-whisper-tiny ✅ 已缓存；base/small ⬜ 按需 |
| 任务分工速查 | 解析→8b；分镜/规划→30b-a3b；VLM→qwen2.5vl；生图→Flux2-4B；动漫/写实备选 SDXL；视频→H3 |
| 验证步骤/性能/备选 | 保留并扩充（新增各模型在 ComfyUI/Ollama 中的可见性验证） |

数据来源：实测 F:\Develop\ComfyUI\models（各目录文件+大小）、`ollama list`、Ollama 模型目录 F:\Develop\VLM\models、HuggingFace 缓存。

## Git 同步

- 本地 commit `3032e7f`（93 insertions, 20 deletions）
- 推送时遇 non-fast-forward（远端有用户网页端提交 a218efa「Update README.md」）→ `git pull --rebase` 成功 → push 成功（a218efa..3032e7f main）
- 最终历史：97aa703(initial) → a218efa(远端 README) → 3032e7f(模型清单)
