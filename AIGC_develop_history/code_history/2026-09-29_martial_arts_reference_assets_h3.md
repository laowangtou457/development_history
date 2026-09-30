# 武术指导 · 参考图上传 + qwen2.5vl 视觉资产解析 + H3 官方模板重构

日期：2026-09-29
状态：已验证

## 用户需求

1. 一句话需求处加参考图上传
2. 用模型解析上传的参考图生成资产，再去生成提示词
3. 参考 MiniMax-H3 官方提示词模板（base-en.txt）重构任务锚定卡提示词
4. 加约束：人物性别、年龄、服装、武器长短、场景布置和构图、动作

## 实现（backend/app/api/martial_arts.py + 前端）

### 1. 参考图上传接口 POST /api/martial-arts/upload-reference
- 存 `user_story/martial_arts_references/`，返回 `/api/files/...` 平台 URL
- 支持 PNG/JPG/WEBP

### 2. 参考图解析接口 POST /api/martial-arts/analyze-reference
- **qwen2.5vl:3b**（Ollama，已有模型，2.98GB）视觉解析，直连 11434 `/api/chat`（base64 图）
- REFERENCE_ANALYZE_SYSTEM 输出 JSON：characters（name/gender/age/physique/clothing/weapon/weapon_length/martial）+ scene（place/layout/composition/scale/lighting/weather）+ action_style + camera
- `_reference_assets_markdown` 容错转 markdown 资产
- 走 gpu_serial 串行锁，keep_alive:0 自动卸载
- **关键坑**：Ollama /api/chat 必须传 `system` 消息，否则模型幻觉输出

### 3. generate 接入资产
- MartialArtsRequest 加 `reference_assets`；_build_user_message 增加【参考图解析资产】段（以参考图为准，冲突以需求为准）

### 4. PLAN_SYSTEM 重构（H3 模板对齐 + 新约束）
- card 新增字段：**gender（性别）/ age（年龄）/ weapon_length（武器长短）/ composition（场景布置与构图）**；characters[] 每行加 gender/age/weapon_length
- 规则新增：H3资产约束（参考图资产在场优先采用）、性别年龄强制（无反串歧义）、武器长短强制（长兵器大开大合/短兵器贴身近战，决定构图尺度）
- 原有：presentation_style/scene_weather/pose_reference/场景尺度/天气氛围/姿态参考

### 5. BUILD_SYSTEM 视频段按 H3 官方模板重构
输出严格按 base-en.txt 结构：
- 第一行首帧对齐指令：`For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.`
- `integrated_multimodal_description`（英文，风格+景别+主体锚点开头 → 6-8 关键节拍沿时间轴 + 镜头三要素 type+amplitude+speed）
- `overall_soundscape`（1-4 句英文环境音）
- `non_diegetic_music`（1-3 句英文配乐，禁抽象情绪词）
- 保留[动作连贯][忠于参考图][实时节奏]与六阶段戏剧弧线
- 图片提示词保持中文（Flux2-Klein-4B 生图不走 H3）

### 6. 前端（MartialArts/index.tsx + martialArts.ts）
- 需求输入区新增「参考图（可选）」卡片：选择图片 → 预览 →「解析参考图生成资产」（qwen2.5vl）→ 资产文本可编辑 → 随 generate 提交

## 验证（真实验证：上传吊桥海报图）

| 环节 | 结果 |
|---|---|
| 上传 | /api/files/martial_arts_references/ref_e670a6064a85.png ✅ |
| qwen2.5vl 解析 | 白衣女子（女/青年/苗条/白色武术服/单刀）、黑衣男子（男/青年/健壮）、吊桥横跨数百米峡谷、自然光雨天、腾跃翻滚、慢动作多角度 ✅ |
| generate 带资产 | 锚定卡含 性别/年龄/武器长短/场景布置与构图 ✅ |
| py_compile / tsc / 后端重启 | ✅ PID 55744 |

## 使用

武术指导页 → 一句话需求下「参考图（可选）」→ 选择图片 → 解析参考图生成资产（可编辑）→ 生成武打分镜提示词 → 后续链路不变。
视频提示词现已按 H3 官方模板输出（英文三字段），可直接粘贴 H3 类视频模型。
