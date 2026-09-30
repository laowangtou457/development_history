# 代码/配置变更记录

## 2026-09-24 · Flux.2 klein 9B → 4B 模型切换部署

**背景**：Flux.2 klein 9B 显存峰值 ~19-22GB 贴近 4090 可用上限（23028 MiB），导致 OOM/卡死风险。切换为 Flux.2 klein 4B。

### 1. 模型下载（hf-mirror.com 镜像，官方 Comfy-Org 仓库）
| 文件 | 大小 | 落盘位置 |
|---|---|---|
| flux-2-klein-4b.safetensors（扩散模型 bf16 蒸馏版） | 7.22 GB | F:\Develop\ComfyUI\models\unet\ |
| qwen_3_4b.safetensors（配套文本编码器 bf16） | 7.49 GB | F:\Develop\ComfyUI\models\clip\ |
| flux2-vae.safetensors | 复用已有 | F:\Develop\ComfyUI\models\vae\ |

下载源：`https://hf-mirror.com/Comfy-Org/flux2-klein-4B/resolve/main/split_files/...`
（首次下载模型 4.23GB 处连接被重置，`curl -C -` 断点续传补齐，无数据损坏，实测推理通过）

### 2. 工作流模板替换（11 个文件，字符串级替换）
`F:\Develop\NewAIProductionWorkflow\AI-NovelFlow\backend\workflows\*.json`
- `flux-2-klein-9b.safetensors` → `flux-2-klein-4b.safetensors`
- `qwen_3_8b.safetensors` → `qwen_3_4b.safetensors`
- 涉及文件：character_default / keyframe_flux2_klein / prop_flux2_klein_20260831_api / scene_flux2_klein_20260831_api / shot_flux2_klein / shot_flux2_klein_dual_reference / shot_flux2_klein_three_ref_edit / shot_character_scene_flux2_klein_dual_ref_edit / shot_scene_flux2_klein_single_ref_edit / shot_scene_prop_flux2_klein_dual_ref_edit / single_image_edit_flux2_klein

### 3. 数据库 workflows 表（SQLite：novelflow.db）
- 全库 30 行 workflow_json：`flux-2-klein-9b` → `flux-2-klein-4b`
- 全库 30 行 workflow_json：`qwen_3_8b` → `qwen_3_4b`
- 残留复查：active 工作流 9b/8b 残留 = 0

### 4. 资产（角色/场景/道具）生图工作流切换（SDXL → Flux2-4B）
| type | 激活（Flux2-4B） | 停用（SDXL） |
|---|---|---|
| character | e5be752e 系统默认-人设生成（含三视图提示词，ReferenceLatent×2 参考图） | 3d110fe7 SDXL-AnimagineXL-角色三视图 |
| scene | 85e0e9d3 Flux2-Klein-4B-生成场景图（含 PurgeVRAM 显存清理） | 7e9e3b69 SDXL-AnimagineXL-场景图 |
| prop | e9dde35c Flux2-Klein-4B-生成道具图 | 5314d04f SDXL-AnimagineXL-道具图 |

### 5. ComfyUI 重启与验证
- 停止旧进程（9760 venv、3716 系统 python，均 `--reserve-vram 3`），重启单实例：
  `F:\Develop\ComfyUI\venv\Scripts\python.exe main.py --reserve-vram 3`（日志 F:\Develop\comfyui_4b.log）
- `/object_info` 确认：unet 含 flux-2-klein-4b.safetensors ✓、clip 含 qwen_3_4b.safetensors ✓
- 真实推理验证：768×768 文生图 `test_flux2_4b_00001_.png` 生成成功（4 步 euler，CLIPLoader type=flux2，Flux2Scheduler 仅需 steps/width/height 无 model 参数）

### 6. 显存实测
- 4B 全套 bf16（unet 7.2G + 编码器 7.5G + VAE）加载驻留约 **16.9GB**，推理峰值接近；free 余量 ~5.6GB
- 相比 9B（峰值 19-22GB）明显改善；比预期偏高（bf16 全量加载），如需进一步省显存可换 fp4 量化编码器（qwen_3_4b_fp4_flux2.safetensors，约省 5GB）

### 注意事项
- CLIPLoader 的 type 参数为 `flux2`（非 flux）
- 后端选工作流逻辑：`type + is_active`，同 type 仅取 first()
- 回退方案：资产工作流可随时将 3d110fe7/7e9e3b69/5314d04f（SDXL）置回 is_active=1 并停用 4B 行
