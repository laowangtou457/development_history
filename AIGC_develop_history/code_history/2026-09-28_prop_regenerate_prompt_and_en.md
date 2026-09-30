# 代码/配置变更记录

## 2026-09-28 · 道具页【AI 重新生成提示词】按钮 + 外观描述保存后自动中译英

### 需求
1. 道具卡片/编辑界面加【AI 重新生成提示词】按钮，可随时重新生成，不再"第一次生成后固定"
2. 外观描述每次保存后，中文自动转成英文（Flux/SDXL 对中文理解弱，中文残留影响生图）

### 根因
- 提示词后端本来就是**动态构建**（`GET /api/props/{id}/prompt` 实时拼接），"固定"是前端只在列表加载时拉一次、保存后未刷新（上轮已修）
- 提示词里的外观描述以**中文原文拼接**进英文提示词 → 需英文化
- 【生成外观】按钮只在外观描述**为空**时显示，有外观的道具（如月刃）看不到按钮 → 无法重新生成

### 改动清单
| 文件 | 改动 |
| --- | --- |
| backend/app/api/props.py | ①`update_prop`：appearance 更新且含中文时 → 自动调 `translate_prop_appearance_to_en` 英文化后保存（翻译失败保留原文，不阻断保存）；②`generate_prop_appearance`：风格跟随小说模板（`get_style(db, novel, "prop")`，写实/动漫自适应），生成结果若仍含中文再英文化一次 |
| backend/app/constants/llm.py | `get_prop_appearance_prompt` 加写实风格分支（写实摄影约束 + 英文示例尾巴）；风格判定改为宽松匹配（支持整段风格文字，如 "photorealistic, realistic rendering, ..."）；`get_character_appearance_prompt` 同款宽松判定（顺带改进，无副作用） |
| frontend .../pages/Props/index.tsx | `generateAppearance` 成功后调用 `fetchPropPrompt` 同步刷新提示词（上一轮已加 handleUpdate/handleCreate 保存后刷新） |
| frontend .../pages/Props/components/PropCard.tsx | 外观描述**有值时也显示按钮**，文案按状态切换：【AI 重新生成提示词】/【生成外观】 |
| frontend .../i18n/locales/zh-CN/props.ts | 新增 `regeneratePrompt: 'AI 重新生成提示词'` |

### 验证（实测，临时道具跑通后清理）
1. 创建测试道具（《蛊》cbcb6f7c）→ PUT 中文外观"弯月形刀刃，无柄，刃身泛着淡蓝色能量波动，刃脊有银色花纹" → 返回 appearance 为英文 "moon-shaped blade, no handle, blade surface with faint blue energy waves, silver patterns on the spine, metallic texture, sci-fi style"，含中文=False ✅
2. GET /prompt → 写实风格标签开头（photorealistic, realistic rendering, ...）✅；唯一中文残留为道具 name（数据本身，未英文化，属预期）
3. POST /generate-appearance → 英文输出且带写实词（photorealistic/realistic）✅，风格跟随小说《蛊》的"写实风格"模板
4. 后端已重启（venv uvicorn :8000，健康检查 200），前端 vite 热更新即生效

### 备注
- 提示词中**道具名保持中文**（如"月刃"）——道具名是数据标识，自动翻译有误译风险，未做英文化；若需要可后续加"道具名英文化"选项
- 翻译走 qwen3:8b 轻量分流（task_type=translate_appearance），不占用 30b 重任务
- 涉及文件均已 py_compile 校验通过
