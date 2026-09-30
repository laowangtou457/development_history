# 武术指导 · 图生视频 500 修复（GenerateVideoRequest 缺 history_id）

日期：2026-09-28
状态：已验证

## 现象

前端点「生成武打视频」报：
`图生视频请求失败：SyntaxError: Unexpected token 'I', "Internal S"... is not valid JSON`

## 根因（后端日志定位）

```
File "backend/app/api/martial_arts.py", line 705, in generate_martial_arts_video
    _patch_history_url(db, data.history_id, video_url=video_url)
AttributeError: 'GenerateVideoRequest' object has no attribute 'history_id'
```

`GenerateVideoRequest` 模型缺少 `history_id` 字段（前端一直传了该字段，但 pydantic 模型未定义，
访问时抛 AttributeError → FastAPI 返回 500 纯文本 "Internal Server Error"）。
前端 api 封装 `res.json()` 直接解析该文本 → SyntaxError。

## 修复

1. **后端** `GenerateVideoRequest` 补 `history_id: Optional[str] = None`（与 generate-image/edit-image 对齐，视频成功后回写 video_url）
2. **前端** `src/api/index.ts`（全平台共用封装）：新增 `parseResponse()` 统一容错——
   - 空响应 → `{ success: false, message: 'HTTP xxx：服务返回空响应' }`
   - 非 JSON 文本（如 500）→ `{ success: false, message: 'HTTP xxx 服务异常：原文前200字' }`，不再抛 SyntaxError
   - get/post/put/delete/upload 全部走该解析

## 验证（真实端到端）

| 验证项 | 结果 |
|---|---|
| py_compile / tsc | ✅ |
| 后端重启 | ✅ PID 61616 |
| **真实 generate-video**（带 history_id，ref2va 4s，参考图 Flux2-Klein_00058_.png） | ✅ 生成成功 `MiniMax_H3_00049_.mp4`，history_id 正常回写，不再 500 |

## 影响面

- api/index.ts 为平台全局封装，容错对所有接口生效（小说主流程同样受益：任何接口 500 都会显示原文而非 SyntaxError）
- 前端 HMR 已生效，无需额外操作
