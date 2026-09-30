# 代码/配置变更记录

## 2026-09-24 · 角色三视图风格确认与模板优化（写实风格 + 三视图结构）

### 背景
用户反馈角色三视图"太卡通，要写实"。排查发现：
1. **系统真实链路已是写实风格**：小说《蛊》（cbcb6f7c）已关联写实风格模板（prompt_templates id=573d46a5，"photorealistic...no anime, no cartoon"），get_style() 会注入该模板到 ##STYLE##。
2. 之前交付的卡通验证图（character__00001_.png）是**测试脚本误用**——验证时把 ##STYLE## 写死成 "anime style"，不代表系统行为。

### 发现的问题与优化
- 用真实写实风格验证时：Flux2-4B 把"正面/侧面/背面"理解成**四个独立人物站场景**（character__00002_.png），三视图设定图结构被稀释。
- 优化：重写 117 节点模板，加入英文专业术语（Flux2-4B 英文理解远好于中文）：

**原 117 模板**：
`{CHARACTER_PROMPT}, 生成这张角色三视图，包括正面，侧面，背面, ##STYLE##`

**新 117 模板**：
`{CHARACTER_PROMPT}, character design sheet, turnaround, three views of the same character: front view, side view, back view, full body, standing pose, consistent face and outfit across all views, plain light gray background, centered, ##STYLE##`

### 变更位置
- DB `workflows.e5be752e` workflow_json 节点 117 文本
- 模板 `backend/workflows/character_default.json` 节点 117（同步）

### 验证（真实链路模拟）
| 版本 | 注入风格 | 结果 |
|---|---|---|
| character__00001_.png | anime（测试误用） | 动漫风三视图 |
| character__00002_.png | 写实模板（真实） | 写实但"四人物场景" |
| character__00003_.png | 写实模板 + 英文术语 | **写实标准三视图**（同一人物正面/侧面/背面，浅灰纯背景）✓ |

### 说明
- 场景/道具走同一 get_style 链路，同样注入《蛊》的写实模板
- 若其他小说未关联风格模板，会回落默认系统 style 模板（当前默认 22636cbe 动漫风格）——如要全局写实可改默认模板或给各小说关联写实模板
