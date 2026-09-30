# 武术指导 · 角色形象图支持手动附加提示词约束

日期：2026-09-28
状态：已验证

## 需求

本地生成角色形象图（文生图）时，增加一个提示词输入框，允许手动增加文字约束——否则每次生成过于随机。

## 实现

### 后端（backend/app/api/martial_arts.py）

1. `GenerateImageRequest` 新增字段：`extra_prompt: Optional[str] = None`（手动附加提示词约束）
2. `POST /api/martial-arts/generate-image`：extra_prompt 非空时拼接到提示词末尾，格式 `f"{prompt}\n[手动附加约束]：{extra}"`——只追加约束、不干扰自动生成的锚定卡描述

### 前端

1. `src/api/martialArts.ts`：`GenerateImageRequest` 接口加 `extra_prompt?: string`
2. `src/pages/MartialArts/index.tsx`：
   - 新 state：`characterExtraPrompt`
   - `handleGenerateCharacter` 传 `extra_prompt: characterExtraPrompt.trim() || undefined`
   - ① 角色形象图区域新增 textarea 输入框，placeholder 示例："五官端正、中式古风服装、正面全身站姿、画面无文字无水印"

## 验证

| 验证项 | 结果 |
|---|---|
| py_compile | ✅ |
| npx tsc --noEmit | ✅ exit 0 |
| 后端重启 | ✅ PID 61900 |
| **真实端到端**：generate-image 带 extra_prompt="五官端正对称，中国男性脸，中式古风武术服，正面全身站姿，画面无文字无水印" | ✅ 生成成功 `martial_arts_00016_.png` |

## 使用说明

- 输入框在①角色形象图区域，选比例按钮下方
- 约束每次点击「生成角色形象图」时自动追加；跨角色复用（可自行清空）
- 约束同时作用于后续②图生图/③视频的参考图（因为角色图本身就带约束特征）
