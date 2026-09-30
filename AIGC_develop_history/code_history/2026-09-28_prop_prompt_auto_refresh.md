# 代码/配置变更记录

## 2026-09-28 · 道具"保存外观描述后自动重新生成提示词"

### 需求
道具页编辑外观描述保存后，提示词仍固定为第一次生成的内容，未随外观更新。要求每次保存后自动重新生成提示词。

### 根因
- 提示词**后端本来就是动态构建**的（`GET /api/props/{id}/prompt` 每次用当前 appearance/description 实时拼接，无存储）
- 前端问题：`propPrompts` 状态只在**列表加载时**（fetchProps → fetchPropPrompt）拉取一次，编辑保存（handleUpdate）后没有重新拉取 → 卡片显示的还是旧提示词

### 改动（纯前端，2 处）
`frontend/my-app/src/pages/Props/index.tsx`
1. `handleUpdate`：保存成功后调用 `fetchPropPrompt(data.data!.id)` —— 用最新 appearance 重新拉取提示词，PropCard 立即显示新提示词
2. `handleCreate`：创建成功后同样调用 `fetchPropPrompt` 拉取初始提示词

### 验证
- 月刃（id d52e2d1a）prompt 接口实测：`GET /api/props/d52e2d1a.../prompt` 正常返回，提示词包含最新外观"弯月形刀刃，无柄，刃身泛着淡蓝色能量波动" + 写实风格标签（photorealistic...）
- 生效方式：vite 热更新，刷新道具页即可

### 备注
- 当前提示词中外观描述以**中文原文拼接**（如"弯月形刀刃，无柄，刃身泛着淡蓝色能量波动"直接出现在英文提示词里），Flux 对中文理解较弱——如需更优效果，可后续把外观描述英文化（同角色外观描述的处理方式）
