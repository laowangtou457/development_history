# 代码/配置变更记录

## 2026-09-24 · 场景生成失败修复 + 角色卡通问题澄清（绿袍方源/青茅山血战）

### 问题1：青茅山血战场景生成失败
**报错**：`ComfyUI 错误 (HTTP 400): Node '#-1 Concat Text' not found (Node ID '#112')`
**根因**（两处，串联出现）：
1. 场景工作流（85e0e9d3）节点 112 是 `ConcatTextOfUtils`（ComfyUI_essentials 旧节点名），当前 ComfyUI 无该节点 → 改用 **StringConcatenate**（string_a/string_b/delimiter，schema 兼容）
2. 修好后又报节点 71 `PathchSageAttentionKJ` 缺 `sageattention` 库（非必需注意力加速补丁）→ **短路该节点**（下游 ModelPatchTorchSettings 的 model 直接接 UNETLoader）

**修复**：
- 场景 112：`ConcatTextOfUtils{text1,text2,separator,text3}` → `StringConcatenate{string_a:[110,0], string_b:[111,0], delimiter:","}`
- 场景+道具工作流：短路 PathchSageAttentionKJ（DB 2 行 + 模板 2 文件）
- DB commit 遗漏教训：UPDATE 后必须 conn.commit()（此前一次修复因 close 回滚未生效）

**验证**：场景工作流提交 ComfyUI success，1536×864 生成山谷古战场（尸体/血迹/兵器/旗帜/晨雾）——写实风格达标

### 问题2：绿袍方源人物过于卡通
**澄清**：该图为**今早 08:12 旧任务**（当时 character 工作流为 SDXL+AnimagineXL 动漫底模，提示词注入 anime style）——非当前链路产物。
**当前链路确认**：
- `get_style(db, 《蛊》, 'character')` 实测返回**写实风格模板**（photorealistic...no anime, no cartoon）✓
- 用绿袍方源真实外观描述（血发/碧玉冠/碧绿大袍/丹凤眼）+ 写实模板重新生成 → **写实三视角**（character__00004_.png：酒红长发、金瞳、绿冠、深绿古风长袍，非卡通）✓

### 附带确认
- 场景工作流 110 CR Prompt Text 中写死的"三国写实"描述会在注入时被整体覆盖为场景提示词（inject_prompt 无占位符即覆盖）——如需保留写实基底，应在场景描述提示词中自带风格或改模板加占位符

### 文件
- DB：novelflow.db（workflows 85e0e9d3 / e9dde35c）
- 模板：scene_flux2_klein_20260831_api.json、prop_flux2_klein_20260831_api.json
- 验证图：ComfyUI\output\ComfyUI_00002_.png（场景）、character__00004_.png（绿袍方源写实）
