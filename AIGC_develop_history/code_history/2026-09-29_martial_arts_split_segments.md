# 武术指导 · 分段拼接方案落地（8+8 拍 × 15 秒 → 30 秒）+ 45s 实测

日期：2026-09-29
状态：**分段拼接 30s 端到端验证通过（第五次提交成功）**；45s 实测已交付

## 用户决策

"转换方向，先测试45/60 秒，不理想的话使用两个15秒(各8镜头)拼接成一个30秒长视频，但要注意保证视频连贯性，避免画面崩坏。"
"切到分段拼接验证一次 30s 成片"

## 分段拼接实现（新代码已生效）

### 核心思路
16 拍拆 **8+8**，两段各 **15 秒**（H3 官方训练舒适区 5-15s）→ 第二段首帧 = **第一段真实尾帧**（保证时空连贯）→ ffmpeg 拼接成 30 秒。

### 后端（martial_arts.py）
- `GenerateVideoRequest` 新增 `split_segments: bool`
- 新函数：
  - `_assemble_segment_h3(beats, persona, duration=15)`：拍子集 → H3 官方模板（15s）
  - `_extract_video_last_frame(video_url, out_path)`：ffmpeg `-sseof -0.2` 抽第一段尾帧
  - `_concat_two_videos(path1, path2, out_path)`：ffmpeg concat（等参数逐帧拼接，libx264）
- generate-video 新增分支：`split_segments && mode==ref2va && duration>=24` 时：
  1. `_extract_video_beats` 拆拍 → 均分两段（各 8 拍）
  2. 段 1：分镜第 1 格作首帧，H3 15s 生成
  3. 段 2：**段 1 视频真实尾帧**（ffmpeg 抽帧 + 上传 ComfyUI input）作首帧，H3 15s 生成
  4. ffmpeg concat → 写入 ComfyUI output → 返回 `/view` URL
  5. 每段独立 gpu_serial 锁 + 视频前 /free 卸载
  6. 失败降级：拼接失败退回段 2 成片（不阻断）；h3_prompt 存两段模板（==SEG2== 分隔）

### 前端（MartialArts/index.tsx）
- `splitSegments` state
- 时长 ≥ 24 秒时显示勾选框「分段拼接 8+8（15s×2，更稳）」
- generateVideo 传 `split_segments: splitSegments && videoDuration >= 24`
- tsc 通过

## 45s 实测（已完成并交付）

- 45s = 1093 帧（24fps），H3 节点帧数上限 3600 内
- 16 拍时间戳正确分布：Shot1 @0.000 → Shot16 @42.188（每拍 2.8 秒）
- **15:16 出片 `MiniMax_H3_00056_.mp4`（45.54s / 864×480 / 24fps）**，抽帧目检：动作有层次（起手→跃起→交击→对峙，中后段非重复）、女性主角/男性对手全程稳定、吊桥场景一致 → 已补录 DB（martial_arts_history 92879fc4 video_url ← 00056）
- 结论：45s 质量达标，H3 支持 45s 长视频

## 分段拼接 30s 端到端验证（五次提交修复史）

### 第 1 次失败（卡"启动"15+ 分钟）
- 根因：旧分段分支插在 `workflow = wf_info["workflow"]` 之前，引用 `mapping`/`_tid` 未定义；且位于整体英文化之后，节拍已非中文
- 修复：英文化块前加 `_is_split_mode` 判断（split_segments+ref2va+duration≥24 时跳过英文化）；删除旧分支，在 `wf_info` 校验后、`workflow = wf_info["workflow"]` 处插入**自包含**新分支（seg_workflow/seg_mapping/seg_builder/seg_save_node 自行定义、自行 `_martial_start` 起 _tid）

### 第 2 次失败（HTTP 400: prompt_outputs_failed_validation）
- 根因：分段分支漏设段 1 参考图（LoadImage 节点 image 为空 → 工作流校验失败）
- 修复：分支内 `seg_workflow[ref_node].setdefault("inputs", {})["image"] = first_filename`

### 第 3 次失败（name 'tempfile' is not defined）
- 根因：分段分支用 `tempfile.mkdtemp` 但文件头部未导入
- 修复：分支内 `import tempfile as _tempfile`（第 4 次提交段 1 出片 00057 后暴露）

### 第 4 次失败（name 'asyncio' is not defined）
- 根因：`asyncio.get_event_loop()` 用于 ffmpeg 下载/抽尾帧，但文件头部从未导入 asyncio
- 修复：文件头部 `import asyncio`（补在 `import json` 前）；py_compile + import OK 验证通过

### 第 5 次提交（成功）✅
- **16:12 提交 → 16:25 出片**，全程 13.2 分钟
- 段 1：16:18 出片 `MiniMax_H3_00059_.mp4`（15s）
- 段 1 真实尾帧抽取（ffmpeg -sseof）→ 上传 ComfyUI input → 段 2 参考图替换，**全部自动衔接成功**
- 段 2 生成完成 → ffmpeg concat → **`F:\Develop\ComfyUI\output\martial_arts_concat_1790670321.mp4`（30.17s / 7.6MB）**
- DB 回写：martial_arts_history 92879fc4 video_url ← concat URL；h3_prompt ← 段1 H3 + `==SEG2==` + 段2 H3（16 拍完整保留）
- 返回 `{"success": true, "mode": "split_segments", "duration_seconds": 30}`

### 成片目检（30s 抽 8 帧网格 + 段间边界放大）
- 8 帧（0/5/10/14.5/15.5/20/25/29.5s）：白衣女 vs 深衣男、吊桥、云雾、黄昏全程稳定；动作有层次（对峙→挥剑→近身缠斗→收势）
- **段间边界 14.5s（段1尾）→ 15.5s（段2首）**：人物位置一致（女左男右）、场景/服装/光影完全一致、动作自然连续（男跃起→落地应对），**无跳变、无崩坏**
- 时长 30.166s ✓

## 结论

- 分段拼接 8+8×15s → 30s **方案验证通过**：段间用真实尾帧衔接，连贯性达标
- 两个候选方向对比：45s（单段长视频）与 30s（分段拼接）**均已出片且质量达标**
- 下一步可选：前端页面实测勾选「分段拼接」按钮走 UI 链路；60s 单段测试；或继续换模型评估（Wan2.2-5B / HunyuanVideo 1.5）——待用户决策

## 待办
1. ~~45s 完成 → 验证时长/抽帧目检动作~~ ✅
2. ~~分段拼接 30s 端到端跑通~~ ✅
3. 前端 UI 链路实测分段拼接按钮（代码已上线，待页面操作验证）
4. 60s 单段测试（可选）
5. 换模型评估（Wan2.2-5B / HunyuanVideo 1.5 或云端）——待用户决策
