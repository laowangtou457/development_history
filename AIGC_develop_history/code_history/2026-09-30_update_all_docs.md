# 2026-09-30 更新全工程文档（三工作流 v2.0）

> 触发：用户要求"更新 F:\Develop\NewAIProductionWorkflow 目录下所有文档，包括子目录文档"
> 目标：把平台文档从早期 H3 集成版统一升级为当前三工作流状态，覆盖平台 docs/、管线 ManjuToSplitFrameAndProperty/docs/、根目录文档，并保留软著材料口径（三功能锁定：①小说生成视频 ②AI武术指导并生成视频 ③视频导入解析替换资产并生成视频）

## 变更清单（19 个文件，+1345 / -972 行）

### 平台 docs/（9 个）
| 文件 | 变更 |
|---|---|
| docs/00_软件开发文档.md | v2.0：头部/技术栈（Ollama 本地 LLM）/平台三工作流表/部署（一键启动全家桶）/验证 V11-V16/已知限制/新增第14章三工作流设计（武指+视频替换+显存治理） |
| docs/01_开发记录.md | 头部路径更新 + 追加第7章三功能演进记录（09-18~30 时间线 + ADR-7~10 + 三工作流定稿） |
| docs/02_代码变更清单.md | 头部更新 + 追加第10章 v2.0 变更清单（后端/前端/管线/显存治理模块级汇总） |
| docs/03_UML图集.md | 标题 v2.0 + 追加第8章三大工作流架构图（系统架构/组件/部署 mermaid） |
| docs/04_用户操作手册.md | 整体重写为三功能手册 v2.0（七节：三工作流分步操作+监控+FAQ） |
| docs/05_代码变更统计.md | 头部说明 + 追加 v2.0 三功能新增统计（核心新增 11 文件 4899 行） |
| docs/06_变更明细与前后对比.md | 追加更新说明（09-24 快照；之后变更指向 code_history/05/02） |
| docs/00_设计图集.html / UML图集.html / 用户操作手册.html | 由对应 md 重新生成（统一转换器，含 mermaid 渲染） |

### 管线 ManjuToSplitFrameAndProperty（7 个）
| 文件 | 变更 |
|---|---|
| README.md | 追加第7章平台集成说明（video-asset-swap 子进程调用/产物即接口/swap-asset） |
| docs/00_全生命周期开发文档.md | 版本 v1.1.0 + 追加第12章平台集成 |
| docs/01_用户操作手册.md | 追加"平台入口"附章 |
| docs/02_ComfyUI集成指南.md | 追加当前部署现状（ComfyUI 位于 F:\Develop\ComfyUI；平台子进程调用优先） |
| docs/04_变更记录.md | 追加 v1.1.0 条目（平台接入+路径迁移+验证） |
| 六段式提示词框架控制.md | 路径替换（D→F） |
| 移植方案.md | 路径替换 + 追加执行状态附章 |

### 根目录（2 个）
| 文件 | 变更 |
|---|---|
| 整体移植方案.md | 去除只读 + 追加执行状态表（部署完成/模型/三工作流/发布） |
| 部署报告.md | 追加后续部署与调试成果（模型定稿/三工作流验证/运维经验） |

## 路径与口径统一
- `D:\AIGC\develop\New_AI_Production_Workflow` → `F:\Develop\NewAIProductionWorkflow`
- `D:\AIGC\local_vlm` → `F:\Develop\VLM`；`D:\ComfyUI` → `F:\Develop\ComfyUI`
- 生态名 `New_AI_Production_Workflow` → `NewAIProductionWorkflow`
- 保留的历史引用（如"原始路径 D 盘"、"迁移记录"）未改动，作为历史事实

## 验证与发布
- 旧路径残留扫描：15 处全部为合理历史引用（已逐条确认）
- git commit `9e704f7`（19 files, +1345/-972），已 push 至 https://github.com/laowangtou457/AIGC_develop
