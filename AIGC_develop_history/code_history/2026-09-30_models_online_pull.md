# 2026-09-30 模型部署改为在线拉取为主

> 触发：用户要求"模型选择在线拉取方式，打包体积过大，后期在别的机器部署也无法从旧机拷贝"

## 变更内容

### 新增 `scripts\download_comfyui_models.ps1`
- H3 视频模型自动在线下载（HuggingFace 官方仓库 `Comfy-Org/MiniMax-H3`，走 hf-mirror 国内镜像免梯子）
- 下载 H3 量化版 5 件 ~55GB：ref2va pruned_int8 主模型 20.97GB + int8 编码器 27.14GB（与平台模板同名）+ 视频/音频 VAE + turbo LoRA
- 断点续传（huggingface_hub，HF_HUB_ENABLE_HF_TRANSFER 多线程加速），中断重跑同命令继续
- **自动适配平台工作流模板**：unet_name（bf16→pruned_int8）、lora_name（夸克网盘名→HF 官方名）两处替换，原模板备份 .bak（-SkipFixTemplates 可关）
- 生图模型（Flux2-Klein-4B/CLIP/SDXL 共 ~29GB）打印 hf-mirror 直链清单，浏览器/IDM 下载更稳

### 修改 `scripts\setup_all.ps1`（阶段4）
- 模型部署默认改为**在线拉取**（H3 量化版 + Ollama pull）
- `-ModelSource` / `-OllamaModelSource` 降级为可选加速（旧机在身边时用 copy_models.bat 增量拷贝）

### 更新 `models\模型清单.md`
- 重写为在线拉取版：H3 量化版文件表（含平台模板引用与适配关系）、生图模型直链表、Ollama 清单、新机在线部署步骤

### 更新 `安装操作手册.md`
- 目录结构补 download_comfyui_models.ps1
- 第三节改为"在线拉取为主"（3.1 H3 自动下载 / 3.2 生图直链 / 3.3 Ollama / 3.4 旧机拷贝仅作可选加速）
- 阶段4表格改为在线拉取说明

### 依据（在线源核实）
- HuggingFace `Comfy-Org/MiniMax-H3` 官方仓库结构：diffusion_models（fl2va/ref2va pruned_int8_convrot 20.97GB）、text_encoders（qwen3vl_32b_minimax_h3_int8_convrot 27.14GB / nvfp4_awq 15.69GB）、vae（video fp16 5.21GB / audio fp32 0.61GB）、loras（ref2v_turbo_4step）
- 平台模板引用核实（Grep AI-NovelFlow\backend\workflows）：ref2va 工作流统一引用 `minimax_h3_ref2va_bf16.safetensors` + `qwen3vl_32b_minimax_h3_int8_convrot.safetensors`（HF 同名）+ 夸克网盘版 LoRA 名 → 需改 2 处
- 量化版选型：pruned int8 + int8 编码器（40 系原生加速，RTX 3060 级可跑），替代 bf16 63.2GB 版

## 验证
- setup_all.ps1 / download_comfyui_models.ps1 / verify_env.ps1 语法 0 错误（UTF8）
- H3 模板适配逻辑基于真实模板文件名的精确匹配（unet/lora 各 1 处）
- 旧机拷贝脚本 copy_models.bat 保留为可选加速路径（-ModelSource 触发）
