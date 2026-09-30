# AIGC_develop_history — 开发文档归档索引

> 归档时间：2026-09-30 ｜ 来源工程：`F:\Develop\NewAIProductionWorkflow`（含 AI-NovelFlow / ManjuToSplitFrameAndProperty / ComfyUI-H3-Prompt-Builder）
> 归档目的：全部开发文档分门别类留存，独立于工程目录，便于查阅、备份与随 git 仓库（https://github.com/laowangtou457/AIGC_develop）对照。

## 目录结构

```
AIGC_develop_history/
├── README.md                      # 本索引
├── code_history/                  # 逐次代码变更记录（2026-09-24 ~ 09-30，62 份）
├── 01_平台开发文档/               # AI-NovelFlow 平台 docs（软件开发文档/开发记录/变更清单/UML图集/操作手册/统计/明细 + 3 个 HTML 图集）
├── 02_管线开发文档/               # ManjuToSplitFrameAndProperty（README + docs/：全生命周期/用户手册/ComfyUI集成/H3导出规范/变更记录/六段式提示词框架控制）
├── 03_部署与移植/                 # 整体移植方案、部署报告、管线移植方案、一键启动全家桶.bat、compare_llm.py
└── 04_根目录说明/                 # 根 README、MiniMaxH3模型下载清单、H3漫剧工作流集成说明
```

## 文档地图（三工作流）

| 工作流 | 入口页面 | 核心文档 |
|---|---|---|
| ① 小说生成视频 | 章节生成页 | 01_平台开发文档/00_软件开发文档.md（第14章）、04_用户操作手册.md（第三节） |
| ② AI 武术指导并生成视频 | /martial-arts | 01_平台开发文档/00_软件开发文档.md（14.1）、04_用户操作手册.md（第四节） |
| ③ 视频导入解析替换资产并生成视频 | /video-asset-swap | 02_管线开发文档/（README、00_全生命周期、01_用户操作手册）、00_软件开发文档.md（14.2） |

## 模型与显存口径（2026-09-30 定稿）

- LLM：Ollama 本地 qwen3:8b（解析）/ qwen3:30b-a3b（规划）/ qwen2.5vl:3b（VLM）
- 生图：Flux2-Klein-4B（默认）＋ SDXL 动漫/写实底模
- 生视频：ComfyUI + MiniMax H3（15s 单段上限，分段拼接 30/45/60s）
- 显存治理：GPU 串行调度 + Ollama keep_alive:0 + 视频前 /free

## 说明

- 本归档为快照副本；工程内文档持续更新时，归档需手动刷新（重新复制覆盖）。
- 软著申报三件套（申请表/源代码文档 7730 行版与 4000 行版/操作手册 30 页）位于 `F:\备案\备案(软件著作权)`，未纳入本目录。
- code_history 含监控脚本运行时文件（.snapshot.json / .watch.pid），属自动生成，可忽略。
