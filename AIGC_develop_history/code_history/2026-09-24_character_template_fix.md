# 代码/配置变更记录

## 2026-09-24 · 修复角色"动漫人设"写死问题（绿袍方源卡通根因）

### 根因（用户判断正确）
角色生成提示词由**角色提示词模板**决定，与风格模板是两套独立链路：
- **角色提示词模板**（novels.prompt_template_id → prompt_templates type='character'）：《蛊》关联的是 **c530b38c「标准动漫人设」**：`character portrait, anime style, high quality, detailed, {appearance}, single character, centered, clean background, professional artwork, 8k` —— **anime style 写死在模板里**
- **风格模板**（novels.style_prompt_template_id → 写实风格 573d46a5）：只注入工作流 ##STYLE## 占位符

`build_character_prompt()`：template.replace("{appearance}", appearance) → 生成的 prompt 自带 "anime style" → 注入 117 的 {CHARACTER_PROMPT} → 与 ##STYLE## 的 photorealistic 冲突 → 模型倾向动漫。

**场景/道具正常的原因**：scene 模板（bdaaf02f）、prop 模板（7eb4e3e9）含 `##STYLE##` 占位符，写实风格能注入；character 模板无 ##STYLE##，风格无法进入。

### 修复
- **novels.cbcb6f7c（蛊）.prompt_template_id**：`c530b38c（标准动漫人设）` → **`8c1b3507（写实人设）`**
  `character portrait, realistic style, photorealistic, highly detailed, {appearance}, single character, centered, professional photography, studio lighting, 8k`

### 验证（全链路模拟）
| 步骤 | 结果 |
|---|---|
| build_character_prompt | "character portrait, **realistic style, photorealistic**, highly detailed, Male character, blood-red long hair..."（无 anime）✓ |
| 117 注入 | 写实 prompt + character design sheet + ##STYLE##(写实) 无冲突 ✓ |
| ComfyUI 推理 | character__00005_.png：三视角写实建模（酒红长发/碧玉冠/绿袍刺绣/金瞳/灰背景）✓ |

### 用户可在界面自行更改的位置
1. **小说编辑**（novel 详情/设置）→ 提示词模板选择 → 选「写实人设」（8c1b3507）
2. **系统配置 → 提示词模板** → type='character' 的模板管理（可新建/编辑"写实人设"模板）
3. 全局默认：get_default_system_template("character") 取创建最早的 system 模板——如需全局写实，把「写实人设」创建时间提前或改默认

### 模板层级总结（三层互不影响）
| 层级 | 存储 | 作用 |
|---|---|---|
| 角色提示词模板 | novels.prompt_template_id | 决定人设基底（anime/写实/Q版/水墨） |
| 风格模板 | novels.style_prompt_template_id | 注入 ##STYLE## 占位符（角色模板无占位符时无效） |
| 工作流 | workflows.node_mapping + 117 模板 | 三视图结构 + {CHARACTER_PROMPT} 注入 |
