# 武术指导 · 历史任务持久化（刷新不丢，可回看/恢复）

日期：2026-09-28
状态：端到端验证通过

## 一、需求

武术指导页面保留历史任务、可查看历史人物，刷新页面不丢失记录。

## 二、实现

### 1. 数据模型（新增）

`backend\app\models\martial_arts_history.py` → 表 `martial_arts_history`：
- 需求 + 高级选项（options_json）
- 提示词三件套：character_card / image_prompt / video_prompt / raw
- 产物三 URL：character_image_url / storyboard_image_url / video_url
- created_at / updated_at

注册到 `main.py` 模型导入区（create_all 自动建表）。

### 2. 后端接口（martial_arts.py 新增 CRUD + 自动保存）

| 接口 | 说明 |
|---|---|
| `GET /api/martial-arts/history` | 历史列表（倒序，最多 100 条，含三产物 URL 用于缩略） |
| `GET /api/martial-arts/history/{id}` | 单条详情（点击回看/恢复） |
| `POST /api/martial-arts/history` | 手动创建（一般由 /generate 自动创建） |
| `PUT /api/martial-arts/history/{id}` | 部分更新（仅更新非 None 字段） |
| `DELETE /api/martial-arts/history/{id}` | 删除 |

**自动保存链路**（无需前端额外操作）：
- `POST /generate` 成功后 → 自动创建历史记录，返回 `data.historyId`
- `POST /generate-image`（带 history_id）→ 成功后自动回写 `character_image_url`
- `POST /edit-image`（带 history_id）→ 成功后自动回写 `storyboard_image_url`
- `POST /generate-video`（带 history_id）→ 成功后自动回写 `video_url`
- 三个生成请求模型新增可选 `history_id`；回写失败静默（不阻断主流程）

### 3. 前端

`api\martialArts.ts`：新增 `MartialArtsHistoryItem` 类型 + 5 个 API 方法（list/get/create/update/delete）；三个生成请求类型加 `history_id`。

`pages\MartialArts\index.tsx`：
- 页面加载自动拉历史列表（useEffect）
- 顶部「历史任务」面板：每条显示角色图缩略图 + 需求 + 时间 + 产物标记（锚定卡/角色图/分镜图/视频）+ 删除按钮
- 点击条目 → 恢复全部状态（锚定卡/提示词/三产物 URL/currentHistoryId），可继续接着生成
- 「新建任务」按钮清空工作区（历史保留）；「刷新」按钮重拉列表
- 当前选中任务高亮；生成成功后自动刷新列表
- 三个生成调用自动携带 currentHistoryId

## 三、验证（真实端到端）

| 验证项 | 结果 |
|---|---|
| 历史 CRUD（建/列/改/查/删） | ✅ 全部通过（测试记录已清理） |
| `generate` 自动建历史 | ✅ 35s，返回 historyId=2be1c2ae… |
| `generate-image` 带 history_id 回写 | ✅ 20s，`characterImageUrl` 自动写入该记录 |
| 前端 `npx tsc --noEmit` | ✅ 通过 |
| 后端 `py_compile` + 重启 | ✅ 通过（PID 5992） |

真实历史记录（太极宗师需求 + 锚定卡 + 提示词 + 角色图）已存在于数据库，刷新前端页面即可在历史面板看到并点开。

## 四、说明

- 产物 URL 指向 ComfyUI output 目录文件（`martial_arts_00004_.png` 等），展示时前端 `toMediaUrl` 转同源代理；只要不手动清理 output 目录即可长期回看。
- 删除历史仅删除记录行，不删除 output 里的图片文件。
