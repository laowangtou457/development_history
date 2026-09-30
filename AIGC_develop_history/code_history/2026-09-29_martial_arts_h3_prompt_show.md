# 武术指导 · H3 执行提示词前端展示（h3_prompt 入库 + 回显）

日期：2026-09-29
状态：已完成（后端 py_compile + 前端 tsc 通过，后端重启 health ok）

## 用户反馈

"6 个独立镜头块、机位逐镜变化、全英文、性别明确——前端不显示是吧？"

确认：生成视频时转换出的 H3 英文模板只用于提交 ComfyUI，**未存库、前端看不到**。

## 修复

### 后端
1. `martial_arts_history` 表新增 `h3_prompt` 列（幂等 ALTER）；model 增加对应字段
2. generate-video 成功后回写 `h3_prompt`（实际执行用的英文模板，非中文原始）
3. GET /history 与 /history/{id} 返回 `h3Prompt` 字段
4. generate-video 响应 data 直接带 `h3_prompt`，前端生成成功后立即回显

### 前端
1. `MartialArtsResult` / `MartialArtsHistoryItem` 类型增加 `h3Prompt?`
2. 结果区新增卡片「**H3 视频提示词（执行用，逐分镜独立镜头块）**」：
   - 展示生成视频时实际提交给本地 H3 的英文模板（每个 [Shot N] 独立镜头：机位/动作/对手反应/相机运动）
   - 复制按钮 + 说明（机位逐镜变化、性别外貌按锚定卡锁定）
3. 点击历史任务恢复时同步回显 h3Prompt；生成视频成功后自动填充

## 验证

- py_compile 通过；前端 tsc --noEmit 通过
- 后端重启 health ok
- 下次「生成武打视频」成功后，页面会立即出现 H3 英文模板卡片，可核对 16 个独立镜头块是否与预期一致

## 使用

重新生成视频 → 视频卡下方自动出现「H3 视频提示词（执行用）」卡片；历史任务点击回看也能看到该记录的执行模板。
