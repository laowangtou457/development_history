# 变更记录

## 2026-09-28 · 场景「AI 重新生成提示词」功能（对齐道具）

### 需求
每个场景都要有"AI 重新生成提示词"按钮；修改场景描述后能重新生成环境设定（setting），避免生图还是旧样子。

### 现状问题
1. 前端 `SceneCard.tsx`：生成设定按钮**只在 setting 为空时显示**，已有设定的场景按钮消失 → 无法重新生成
2. 后端 `generate-setting` 接口：风格**写死 "anime"**，不跟随小说模板（写实/动漫），与提示词接口 get_style(db,novel,"scene") 不一致
3. `PUT /scenes/{id}` 保存时**无中译英**（Flux/SDXL 对中文理解弱，中文 setting 生图效果差）
4. 前端 `generateSetting` 成功后**不刷新拼接提示词**（scenePrompt 仍显示旧设定构建的 prompt）

### 修复
**后端 `api/scenes.py`：**
1. `PUT /{scene_id}`：加 `llm_service` 依赖，setting 含中文时自动 `translate_scene_setting_to_en`（与道具 update_prop 一致，翻译失败不阻断保存）
2. `POST /{scene_id}/generate-setting`：风格改为 `get_style(db, novel, "scene")` 自适应（跟随小说写实/动漫模板）；生成结果含中文再中译英兜底

**前端：**
3. `SceneCard.tsx`：环境设定常显 + "AI 重新生成提示词"按钮**始终显示**（有 setting 显示"AI 重新生成提示词"，无则"AI生成环境设定"）
4. `index.tsx`：generateSetting 成功后 `fetchScenePrompt(scene.id)` 刷新拼接提示词
5. i18n：5 语言（zh-CN/en-US/zh-TW/ja-JP/ko-KR）新增 `regenerateSetting`

### 验证
- 后端语法校验通过；重启 :8000 health 200
- 实测：场景"三楼窗口" generate-setting **4 秒成功**，新 setting 纯英文（无中文残留），风格跟随写实模板
- 前端 vite 热更新自动生效，刷新场景页即可看到按钮

### 使用
场景卡片 → 点击「AI 重新生成提示词」→ 用当前描述重新生成环境设定 → 提示词自动刷新 → 再生成图片即用新设定
