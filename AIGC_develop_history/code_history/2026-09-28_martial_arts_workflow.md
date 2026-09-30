# 变更记录：武术指导独立工作流集成

- 日期：2026-09-28
- 上游参考：https://github.com/CY-CHENYUE/martial-arts-director-cy (Apache-2.0)
- 目标：将「武术指导」Skill（一句话需求 → N 宫格武打分镜海报提示词 + 视频提示词）作为**独立工作流**接入 AI-NovelFlow，初期在左侧主菜单添加入口。

## 集成形态（关键决策）

- **独立工作流**：不进入小说→分镜→视频主流程，不建 Task、不挂 novel/chapter/shot 数据，不碰任何队列。
- 独立路由 `/api/martial-arts/generate` + 独立前端页面 `/martial-arts`。
- **两步工作流（8b 全流程）**——实测 30b 长文输出带过程叙述草稿、占满 8192 token 预算导致正文截断/缺失（与平台 H3 分镜拆分的既有经验一致），最终：
  - Step 1 `qwen3:8b`：解析需求 → 人物锚定卡 + N 招招式列表（JSON）
  - Step 2 `qwen3:8b`：基于锚定卡+招式列表 → 图片提示词 + 视频提示词（两段）

## 后端改动

| 文件 | 改动 | 说明 |
|---|---|---|
| `backend/app/api/martial_arts.py` | **新增** | 独立 router；`POST /generate`；PLAN_SYSTEM（8b 编排，`response_format=json_object`）；BUILD_SYSTEM（8b 组装两段，`===` 分隔）；`gpu_serial` 包锁防并发 OOM；输出解析取"段内容最长"的完整组 |
| `backend/app/services/llm_service.py` | 修改 | `LIGHT_MODEL_TASKS` 新增 `martial_arts_plan`、`martial_arts_build`（均走 8b） |
| `backend/app/main.py` | 修改 | import + `include_router(martial_arts.router, prefix="/api/martial-arts")` |

## 前端改动

| 文件 | 改动 |
|---|---|
| `frontend/my-app/src/api/martialArts.ts` | 新增 API 封装（MartialArtsRequest / MartialArtsResult / generate） |
| `frontend/my-app/src/pages/MartialArts/index.tsx` | 新增独立页面：一句话需求 + 高级选项表单 + 三段结果展示（锚定卡/图片提示词/视频提示词，各带复制按钮） |
| `frontend/my-app/src/App.tsx` | lazy import `MartialArts` + `<Route path="martial-arts">` |
| `frontend/my-app/src/components/Sidebar.tsx` | navigation 新增 `{ name: t('nav.martialArts'), href: '/martial-arts', icon: Swords }`（位于任务监控之后） |
| `frontend/my-app/src/i18n/locales/{zh-CN,en-US,zh-TW,ja-JP,ko-KR}/nav.ts` | 新增 `martialArts` 键（武术指导 / Martial Arts / 武術指導 / 武術指導 / 무술 지도） |

## 验证

- `python -m py_compile`：3 个后端文件通过。
- `npx tsc --noEmit`：新增文件无类型错误（仅 1 个既有错误 `ChapterGenerateLayout.tsx:619`，与本次改动无关）。
- 后端重启（venv uvicorn :8000），`/api/health` OK。
- **真实端到端测试（两步 8b）**：输入"太极宗师对外家拳师，晨曦庭院，要有太极哲学"→ 返回 success=true：
  - 人物锚定卡 435 字符（markdown 表格：呈现风格/体型/武术体系/调性/装备/场景/宫格/兵器/影视参考）
  - 图片提示词 3101 字符（16 招全列，含镜头语言、对手虚化剪影、速度线、起势收势仪式感）
  - 视频提示词 3754 字符（参考图阅读协议 + 分镜执行清单 + 实时节奏 + 六阶段戏剧弧线 + 影视参考）
  - 无思考草稿污染、无截断。
- 前端 `http://localhost:5173/martial-arts` 可访问（vite 热更新已生效）。

## 已知问题与后续

1. **30b 长文输出缺陷（非本次引入）**：`qwen3:30b-a3b` 在 8000+ token 长文输出时会把过程叙述写进正文，占满预算后截断。武术指导暂用 8b 保证稳定；若后续要 30b 质量，需改为"单段输出 + 多次调用"（图片/视频提示词分两次生成）。
2. 图片提示词实测约 3000 字符，超出 SKILL.md 规范 700-1050 的推荐长度（8b 逐招写实所致），后续可在 BUILD_SYSTEM 加强字数压缩约束。
3. 可扩展方向：生成结果一键送入图片/视频生成（即梦/Kling/Seedance），需接生图链路。
