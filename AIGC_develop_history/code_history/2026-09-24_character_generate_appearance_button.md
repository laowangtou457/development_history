# 代码/配置变更记录

## 2026-09-24 · 角色【AI生成外貌描述】按钮全量保留 + 写实风格化 + 英文输出

### 需求
每个角色（无论是否已有外貌描述）都保留【AI生成外貌描述】按钮，编辑后可重新生成**英文**外貌描述提示词，避免模型不认（flux 对英文理解更好）。

### 改动清单

#### 后端
1. **`backend/app/constants/llm.py` — `get_character_appearance_prompt(style)`**
   - 原实现 style 参数**完全未使用**，示例固定 `anime style`（写死动漫）
   - 新增按风格分支：realistic→写实摄影标签（photorealistic/realistic rendering…）、chibi→Q版、ink→水墨、默认 anime
   - 强化约束：只输出英文正文、画风标签严格匹配风格、性别/年龄必须准确体现（young girl/young man/woman/man）

2. **`backend/app/api/characters.py` — `generate_appearance`**
   - 原 `style="anime"` 写死 → 改为**跟随所属小说的风格模板**推断（novels.style_prompt_template_id → 模板名含"写实"→realistic / "Q版"→chibi / "水墨"→ink / 默认 anime）
   - 新增依赖注入 novel_repo、prompt_template_repo
   - 生成时传入 novel_id/character_id（供 LLM 日志与分流追踪）

#### 前端
3. **`Characters/components/CharacterCard.tsx`** — 外貌特征区改造
   - 原逻辑：appearance 为空才显示按钮；有内容则只显示文字
   - 新逻辑：**始终显示【AI生成外貌描述】按钮**（内容在上、按钮在下），可随时重新生成

4. **`Characters/index.tsx`**
   - `generateAppearance()`：成功后同步 `setEditingCharacter`（若正在编辑该角色，弹窗内表单值立即更新，不再只更新卡片列表）
   - 编辑弹窗 appearance 下方新增【AI生成外貌描述】按钮（loading 态 + 无 description 时禁用并提示）
   - import 补充 `Sparkles` 图标

### 验证
- 后端 py_compile 通过
- 后端重启（8000 现由 venv 单实例 PID 23304 提供；清理了重复的双 uvicorn 进程）
- 接口实测：`POST /api/characters/{id}/generate-appearance`（绿袍方源 92ab876d）→ 返回英文写实描述：
  `Young male character, blood-red hair in a high topknot with a jade束髻冠, emerald green robe with intricate traditional Chinese patterns, ... realistic skin texture, detailed fabric texture, photorealistic, realistic rendering, highly detailed, professional photography`（末尾写实标签，不再 anime）
- 前端 tsc --noEmit：本次改动文件无错误；仅一个既有无关错误（ChapterGenerateLayout.tsx:619），不影响 vite dev

### 备注
- LLM 偶发把个别词汇残留中文（如"jade束髻冠"），可在编辑框手动修正后保存
- 创建弹窗未加该按钮（新建角色无 id 无法调用接口；创建后卡片上即可生成）
