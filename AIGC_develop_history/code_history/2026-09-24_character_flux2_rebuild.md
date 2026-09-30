# 代码/配置变更记录

## 2026-09-24 · 改造 e5be752e：双模型人设 -> 纯 Flux2-4B 单模型三视图（角色生图全面切 4B）

**目标**：角色/场景/道具全部使用 Flux2-4B 生成（场景、道具上轮已切，本轮完成角色）。

### 背景
e5be752e 原为"两阶段人设工作流"：Z-image-turbo（z_image_turbo_bf16 + ae）先按 {CHARACTER_PROMPT} 生成角色参考图 → ReferenceLatent 喂给 Flux2-4B 主分支 → 三视图。
Z-image-turbo 模型未下载（bf16 需 14-16GB 显存），且两模型同时驻留显存超 30GB > 22.5GB 上限，无法启用。

### 改造内容（DB workflows.e5be752e + 模板 character_default.json 同步）
**删除 14 个节点**：Z-turbo 分支（121 CLIPLoader lumina2、122 VAELoader ae、124 ConditioningZeroOut、125 VAEDecode、126 ModelSamplingAuraFlow、128 UNETLoader z_image、129 KSampler、132 EmptySD3LatentImage、133 CLIPTextEncode）+ 参考图尺寸链（107 ImageScaleToTotalPixels、112 GetImageSize、114/115/116 ReferenceLatent/VAEEncode）

**修改 3 个节点**：
| 节点 | 修改 |
|---|---|
| 108 CFGGuider | positive: 116(ReferenceLatent) → **110(CLIPTextEncode 主提示词)**；negative: 114 → **111(ConditioningZeroOut)** |
| 106 EmptyFlux2LatentImage | 尺寸链(width=[112,1]) → **固定 768×1344**（后端按 aspect_ratio 覆盖） |
| 109 Flux2Scheduler | 同上 → **固定 768×1344** |

**保留 14 节点**：9 SaveImage、99/100/101/102（采样链）、103 UNETLoader(flux-2-klein-4b)、104 CLIPLoader(qwen_3_4b, flux2)、105 VAELoader(flux2-vae)、110 CLIPTextEncode(←117)、111 ConditioningZeroOut、117 CR Text

**node_mapping**：`{"prompt_node_id": "117", "save_image_node_id": "9"}`（不变，117 含 {CHARACTER_PROMPT} 占位符 + ##STYLE##）

### 激活状态（角色生图）
- active：`e5be752e` 系统默认-人设生成（纯 Flux2-4B 三视图）
- inactive：`3d110fe7` SDXL-AnimagineXL-角色三视图（保留可回退）

### 验证
- 悬空引用检查：无
- ComfyUI 真实推理：768×1344 提交 success，生成 `character__00001_.png`（浅蓝和服少女三视图，正面/侧面/背面四视角，白底设定图，完全符合模板提示词）
- 显存：与场景/道具同一水平（4B 全套 ~17GB），不再需要 Z-image-turbo

### 注意
- 原双模型版已备份：`F:\Develop\code_history\backup_e5be752e_dual_model_20260924.json`（回退可还原）
- 参考图（ReferenceLatent）能力已移除；将来需要"上传参考图驱动人设"可再扩展为可选参考图输入
