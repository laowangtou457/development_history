# 代码/配置变更记录

## 2026-09-24 · 修复"系统默认-人设生成"映射配置不完整报错

**报错**：生成角色时提示"工作流 '系统默认-人设生成' 的映射配置不完整，缺少：提示词输入节点, 图片保存节点"

### 根因
1. 上轮 4B 切换将 character 激活为 `e5be752e`（系统默认-人设生成，Flux2-4B 双模型人设），但其 `node_mapping` 字段为 NULL（旧 SDXL 工作流 3d110fe7 有映射，新工作流没配）。
2. 校验函数：`backend/app/services/character_service.py` `_validate_workflow_node_mapping`（约 602-647 行）要求 character 类型必须含 `prompt_node_id`/`save_image_node_id`；scene_service.py(392-401)/prop_image_service.py(406-415)/task_service.py(100-137) 同类。

### 修复动作
| 项 | 内容 |
|---|---|
| node_mapping | e5be752e 设为 `{"prompt_node_id": "117", "save_image_node_id": "9"}` |
| 117 CR Text 文本 | `生成这张角色三视图，包括正面，侧面，背面, ##STYLE##` → `{CHARACTER_PROMPT}, 生成这张角色三视图，包括正面，侧面，背面, ##STYLE##`（占位符共存，inject_prompt 会替换角色描述） |
| 模板同步 | `backend/workflows/character_default.json` 同步 117 文本 |
| 全表检查 | 16 条 active 工作流 node_mapping 完整性全部 OK |

### 关键发现：e5be752e 依赖缺失模型（重要）
e5be752e 是"两阶段人设工作流"：
- 阶段1（参考图生成）：Z-image-turbo（129 KSampler + 128 `z_image_turbo_bf16.safetensors` + 122 `ae.safetensors`）用 {CHARACTER_PROMPT} 生成角色参考图 → 125 VAEDecode → 107/115 → ReferenceLatent(114/116)
- 阶段2（三视图）：Flux2-4B 主分支以参考图 + 三视图模板(117→110) 生成最终三视图 → 100/101 → SaveImage(9)

**`z_image_turbo_bf16.safetensors` 与 `ae.safetensors` 未下载**（ComfyUI 模型库仅有 flux-2-klein-4b/9b）→ 即使映射修好，工作流执行也会因模型缺失失败。

### 决策：character 回退 SDXL
- active：`3d110fe7` SDXL-AnimagineXL-角色三视图（映射 2/7 齐全、模型在位、加五官/性别约束后质量已认可）
- inactive：`e5be752e`（node_mapping 已修复、占位符已加，保留为候选——将来下载 z_image_turbo_bf16 + ae 后可启用）

### 影响范围
- 角色生成：立即恢复可用（SDXL 三视图）
- 场景/道具/分镜/关键帧/视频：不受影响（Flux2-4B）
