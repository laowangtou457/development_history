# 视频资源替换功能接入（ManjuToSplitFrameAndProperty → AI-NovelFlow 平台）

日期：2026-09-29
状态：已上线并端到端验证通过

## 需求

将 `F:\Develop\NewAIProductionWorkflow\ManjuToSplitFrameAndProperty`（漫剧抽帧与属性管线：视频逆向 → 镜头切分/ASR/资产抽取/多平台提示词导出）接入 AI-NovelFlow 平台，在侧面主菜单新增【视频资源替换】入口，支持上传参考成片 → 浏览分镜/关键帧/台词/资产 → 替换为原创形象 → 重新导出 Seedance/Kling/Veo/即梦/MiniMax H3 提示词 → 打包下载。

## 架构决策

- **隔离调用**：后端以子进程调用管线工程自带 `.venv\Scripts\python.exe run_all.py <video> --asr-model tiny --platform minimax_h3`，依赖隔离，不污染后端 venv。
- **产物即接口**：管线产物（shots/storyboard/assets/minimax_h3）留在 `output/<视频名>/`，后端只读 JSON + 静态文件服务，零内存耦合、可中断续跑。
- **资产替换 = 覆盖参考图 + 重跑阶段4**：替换 assets.json 中资产第一张参考图（原图备份 .orig.bak）→ `run_all.py <video> --skip 1,2,3 --platform minimax_h3` 重新导出提示词/payload。
- **目录穿越防护**：文件服务 resolve 后校验前缀在 output_dir 内，越界 403。

## 后端变更

| 文件 | 变更 |
|---|---|
| `backend/app/models/video_asset_history.py` | 新增：VideoAssetHistory 模型（video_name/status/stage/video_path/output_dir/summary_json/error/时间戳） |
| `backend/app/api/video_asset.py` | 新增路由模块（prefix `/api/video-asset`） |
| `backend/app/main.py` | 注册 video_asset 路由 + 导入模型（自动建表） |

### 端点清单
- `POST /api/video-asset/analyze`：上传视频（mp4/mov/mkv/avi/webm/flv）→ 存 `ManjuToSplitFrameAndProperty/input/` → 后台 asyncio 任务跑管线 → 写 DB
- `GET /api/video-asset/jobs`：任务列表（状态/阶段/镜头/角色/场景摘要）
- `GET /api/video-asset/jobs/{id}`：详情（shots/storyboard/assets/video_info 全量 + 产物文件树）
- `GET /api/video-asset/jobs/{id}/files/{path}`：产物静态文件（jpg/png/webp/md/json/srt），防穿越
- `GET /api/video-asset/jobs/{id}/download`：打包 zip（排除 frames/audio 大目录）
- `POST /api/video-asset/jobs/{id}/swap-asset`：替换角色/场景资产图 → 自动重跑阶段4 → 重新导出 H3 提示词

## 前端变更

| 文件 | 变更 |
|---|---|
| `src/api/videoAsset.ts` | 新增 API 封装 + assetFileUrl/downloadUrl |
| `src/pages/VideoAssetSwap/index.tsx` | 新增页面：上传/任务列表/详情 Tabs（分镜镜头时间线+关键帧网格 / 分镜表 / 资产可替换 / H3提示词预览+payload+下载）；running 任务 5s 自动轮询 |
| `src/App.tsx` | 新增懒加载路由 `video-asset-swap` |
| `src/components/Sidebar.tsx` | 新增菜单【视频资源替换】（Clapperboard 图标） |
| `src/i18n/locales/{zh-CN,en-US,zh-TW,ja-JP,ko-KR}/nav.ts` | 新增 `nav.videoAssetSwap` |

## 验证记录

1. **前端**：`npx tsc --noEmit` 通过；vite `http://localhost:5173/video-asset-swap` 返回 200
2. **后端**：py_compile + import OK；`/api/video-asset/jobs` 200
3. **端到端（sample_12s.mp4）**：
   - analyze → success（3 镜头 / 12.0s / 3 场景；合成测试视频无人脸 → 0 角色属预期）
   - 详情：shots/storyboard/assets/video_info/file_tree（18 项）完整
   - 文件服务：关键帧图 GET 23KB；prompts.md GET 2488 字节（六段式提示词包）
   - zip 下载 74.6KB（18 条目，frames/audio 已排除）
   - 目录穿越 `../novelflow.db` → 403 ✓
4. **资产替换链路**：swap-asset s0（场景）→ success → prompts.md 重新导出 3185 字节；minimax_h3 全套（assets_manifest s0=图1 / mapping.txt / prompts.md / validation_report.json / 3 个 payload）均在

## 使用说明

侧边栏【视频资源替换】→ 上传视频 → 等待分析（约数分钟，自动刷新）→
- 分镜镜头：时间线条 + 关键帧网格
- 分镜表：镜号/时间/台词/画面描述（未开 VLM 时画面描述为"待补充"）
- 资产：角色/场景卡片，点【替换资产】上传原创形象图（无版权问题）→ 自动重导出提示词
- H3 提示词：prompts.md 全文预览 + 逐镜 payload + 产物 ZIP 下载（可直接粘贴 Seedance/Kling/Veo/即梦/海螺 H3）

## 备注

- 管线 VLM（qwen2.5vl:3b）走本地 Ollama（config.yaml 已配）；Ollama 未启时 VLM 降级留空，不阻断管线
- ASR 用 tiny（37集已下载模型），可改 config.yaml 或传参升级
- 替换资产前原图会备份为 `.orig.bak`，可手动恢复
- 合规自检清单在 prompts.md 末尾，发布前逐项确认（原创形象/非盈利/已授权素材）
