# 2026-10-08 视频资源替换工作流三：补齐「生成新视频」最后一环

> 触发：用户要求"视频资源替换功能还没完成，原本设计的链路是【视频导入生成提示词-->拆分资产（人物，场景）-->替换资产-->生成新视频】，目前生成新视频还没完成。把提示词生成视频功能加进去，主动点击生成视频"
> 目标：为平台工作流三（视频资源替换）补齐最后一环——替换资产后，用逐镜 H3 提示词 + 替换后的资产参考图，经 ComfyUI H3 视频工作流逐镜生成视频，ffmpeg 合并成片，在平台内查看/下载。

## 变更清单（后端 4 文件 + 前端 2 文件，新增约 580 行 / 修改约 130 行）

### 后端（backend/）
| 文件 | 变更 |
|---|---|
| `migrations/add_video_asset_video_fields.py`（新增） | 为 `video_asset_history` 增加 `video_status` / `video_stage` / `video_error` / `video_summary_json` 四字段（迁移已执行） |
| `app/services/video_asset_video_service.py`（新增，约 460 行） | 核心生成服务：`build_shot_plans`（逐镜计划：关键帧首帧=主图 + payload 资产参考图=附加帧，1/2/3/4 张自动匹配 video/first_last/three/four_frame 工作流，时长 clamp 4–15s）；`run_generate_new_video`（逐镜串行调 ComfyUI、单镜失败继续、进度落库、ffmpeg concat 合并、每镜后 POST /free 释放显存）；`_prompts_md_fallback`（payload 缺失时用 prompts.md 兜底） |
| `app/api/video_asset.py`（修改） | 新增 `POST /jobs/{job_id}/generate-video`（校验 success、防重复提交、重置状态、挂 `worker_manager.worker("video_asset_video")` 串行执行）与 `GET /jobs/{job_id}/video`（状态+逐镜进度+new_video 文件树）；`/jobs` 列表与 `/jobs/{id}` 详情增加 `video_status` / `video` 字段 |
| `app/models/video_asset_history.py`（修改） | 增加四字段（SQLAlchemy Column） |

### 前端（frontend/my-app/）
| 文件 | 变更 |
|---|---|
| `src/api/videoAsset.ts`（修改） | 新增 `VideoGenSummary` / `VideoShotProgress` / `VideoGenStatus` 类型与 `generateVideo` / `getVideoStatus` API；Job 增加 `video_status` |
| `src/pages/VideoAssetSwap/index.tsx`（修改） | 新增 `SHOT_STATUS_META` / `VIDEO_STATUS_META`、`handleGenerateVideo`、头部「生成新视频」按钮（success+has_prompts 可点、running 禁用）、Tabs 第 5 页签「新视频」（流程说明+进度条+逐镜网格+最终成片播放/下载+idle 引导+错误展示）、轮询 5s→3s（分析或视频 running 时刷新） |

## 关键技术点 / 踩坑记录
1. **H3 单段时长 4–15s 约束**：`_clamp_duration` 强制 clamp，超长镜头需分段（后续可按需扩展多段拼接）。
2. **参考图数量→工作流映射**：主图（关键帧首帧，保留构图/动作起点）+ 附加资产图（最多 3 张）→ 1/2/3/4 张对应 video / first_last / three / four_frame；payload 缺失时按镜头归属从 assets.json 取场景/角色图兜底。
3. **DetachedInstanceError 两次踩坑**（重要教训）：
   - 第一次：`lambda: run_generate_new_video(job_id, job.video_path, job.output_dir)` 闭包延迟访问 detached ORM 实例属性 → worker 启动即失败。
   - 第二次：重置状态块 `db.commit()` 后（SQLAlchemy 默认 expire_on_commit）实例属性全部过期，`db.close()` 后再访问 `job.video_path` 同样抛 DetachedInstanceError。
   - 修复：所有需要的属性在 commit 之前取为普通字符串，闭包只捕获字符串。
4. **GPU 防死锁复用**：worker 经 `background_workers.AsyncWorker` + 全局 `gpu_lock` 串行；每镜结束 `POST /free` 释放 ComfyUI 模型显存（复用平台防卡死三件套）。
5. **合并回退**：`ffmpeg -f concat -c copy` 失败自动回退 `libx264 + aac` 重编码，保证产物可播放。

## 验证记录（sample_12s 端到端）
- 后端重启加载新代码；`/api/video-asset/jobs` 返回 `video_status=idle`（3 个历史任务）；`GET /jobs/{id}/video` 正常。
- 前端 tsc --noEmit 通过；浏览器实测：列表页正常 → 详情页出现「生成新视频」按钮 + 第 5 页签「新视频」→ idle 引导界面正常。
- POST generate-video（sample_12s f1bcf48b…）→ `video_status=running` → 计划构建成功（3 镜，首尾帧工作流，4s/镜）→ ComfyUI 队列 running=1 → 逐镜生成中。
- 产物路径：`ManjuToSplitFrameAndProperty/output/sample_12s/new_video/shot_001.mp4 … final_video.mp4`。

## 待办 / 后续
- 端到端完整跑通（3 镜 + 合并）确认成片可播放后，前端「新视频」页签展示最终视频（本记录撰写时第 1 镜生成中）。
- 验证截图：`AI-NovelFlow/_verify_vas_1..4*.png`（临时产物，确认后可清理）。
