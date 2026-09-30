# 武术指导 · 产物同源展示/下载修复（ComfyUI /view 跨源 403）

日期：2026-09-28
状态：已修复并验证

## 一、问题

武指页面的角色形象图 / 分镜图 / 武打视频全部显示为"坏"（图片裂开、视频无法播放）。

## 二、根因

前端 `<img>` / `<video>` 标签加载跨源资源时，浏览器会自动携带 `Referer: http://localhost:5173/...`。
ComfyUI `/view` 接口（0.37.0）对跨源 Referer 请求返回 **403**。
武指接口直接把 ComfyUI 产物 URL（`http://127.0.0.1:8188/view?...`）返回给前端，
浏览器请求被 403 拒绝 → 裂图/视频加载失败。

复现证据：后端 WebClient 无 Referer 下载 8188 成功（873KB）；带 `Referer`/`Origin` 头后返回 403。

> 主流程（小说分镜图等）不受影响，是因为其产物走后端静态服务（同源 8000），从未直连 8188。

## 三、修复方案（同源媒体代理）

**后端** `backend\app\api\martial_arts.py`：
- 新增 `GET /api/martial-arts/media-proxy?filename=...&subfolder=...&type=...`
- 由后端（无 Referer）用 httpx 转发 `http://127.0.0.1:8188/view`，返回文件流 + 正确的 content-type
- 安全：`filename` 白名单校验（`[\w.\-]+`），路径穿越请求返回 400

**前端**：
- `api\martialArts.ts`：新增 `toMediaUrl(url)` —— 把 ComfyUI `/view` URL 解析为
  `/api/martial-arts/media-proxy?filename=...&subfolder=...&type=...` 同源地址（已代理过的直接返回）
- `pages\MartialArts\index.tsx`：三个产物 `<img>` / `<video>` 全部改用 `toMediaUrl(...)`；
  每个产物下方新增「下载」链接（`<a download>`，png/mp4 同源直下）

## 四、验证

| 验证项 | 结果 |
|---|---|
| 代理 png（带 Referer 模拟浏览器） | ✅ HTTP 200，image/png，1071837 bytes |
| 代理 mp4（带 Referer 模拟浏览器） | ✅ HTTP 200，video/mp4，507776 bytes |
| 路径穿越 `../` 非法 filename | ✅ HTTP 400 |
| 前端 `npx tsc --noEmit` | ✅ 通过 |
| 后端 `py_compile` | ✅ 通过 |
| 后端重启 | ✅ PID 27720，health ok |

## 五、效果

用户刷新 / HMR 后，三个产物自动走同源代理地址，可正常展示、播放，并可通过「下载」按钮保存
（角色形象图.png / 分镜图.png / 武打视频.mp4）。
