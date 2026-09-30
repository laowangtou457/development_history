# 代码/配置变更记录

## 2026-09-24 · 春秋蝉道具生成失败修复（prop 工作流 112 节点漏修）

### 现象
春秋蝉生成失败，任务报错：
```
ComfyUI 错误 (HTTP 400): Node '#112 #-1 Concat Text' not found
class_type: 'ConcatTextOfUtils'（旧节点名，当前 ComfyUI 已移除）
```

### 根因
此前修复场景工作流（85e0e9d3）时，把节点 112 `ConcatTextOfUtils` 改成了 `StringConcatenate`，但**prop 工作流（e9dde35c）的 112 节点当时未修复**（只修了场景）。DB 与模板 `prop_flux2_klein_20260831_api.json` 中 112 仍是坏节点。

### 修复
- **DB**：prop 工作流 e9dde35c 节点 112：`ConcatTextOfUtils{text1,text2,separator,text3}` → `StringConcatenate{string_a:[110,0], string_b:[111,0], delimiter:","}`（commit）
- **模板**：`backend/workflows/prop_flux2_klein_20260831_api.json` 同样替换

### 验证
- 重跑 `POST /api/props/ae47292c.../generate-image` → 任务 6f590fde completed
- 新图：`user_story/story_cbcb6f7c/images/春秋蝉_20260924_165038.png`（1088×704）
  - 蝉体深黑褐、纹理清晰、双翅展开、翅面翡翠绿渐变+红棕斑、半透明质感、浅灰背景——符合描述
- prop.generating_status 已更新为 completed

### 备注
道具/场景工作流均为"112=110+111 拼接"结构，修复时两处都要改（已全量核对：scene、prop 现均为 StringConcatenate）。
