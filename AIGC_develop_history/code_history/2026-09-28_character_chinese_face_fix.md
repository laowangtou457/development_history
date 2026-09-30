# 代码/配置变更记录

## 2026-09-28 · 角色生成"欧美脸"修复：全链路加中国风硬约束

### 问题
小说《蛊》是中国古代背景，但除方源外角色全部生成为欧美脸（金发碧眼、西方服饰/发型）。排查发现：**角色外貌描述生成（LLM）和写实人设模板中均无任何"中国风/东亚脸"约束**，Flux 默认按欧美形象生成。

### 改动
| 位置 | 改动 |
| --- | --- |
| backend/app/constants/llm.py `get_character_appearance_prompt` | 增加硬约束第 6 条：角色必须是中国古代背景华人/东亚人形象——东方脸型（East Asian facial features，黑/深棕发、深色眼）、中国古代传统服饰（traditional Chinese hanfu / ancient Chinese costume，明确款式主色）、古代中国发型（发髻/束发/盘发）；**严禁欧美脸（caucasian features）、金发碧眼、西方服饰、现代服饰** |
| prompt_templates 表（DB）"写实人设"模板（8c1b3507-46f5-4c45-a628-2758ac3646ee） | 模板插入 `East Asian Chinese facial features, traditional Chinese ancient costume and hairstyle`，使最终拼接提示词带中国风 |

### 验证（真实运行时链路：ollama qwen3:8b + 写实风格，实测生成"白凝冰"）
```
Young male character, pale smooth skin with a refined East Asian facial structure,
long straight black hair tied in a high topknot with silver thread accents,
sharp and cold grey eyes with pale pupils, wearing a traditional Chinese hanfu
in deep blue and silver color scheme with a high collar and flowing sleeves,
jade hair ornament, subtle expression with a faintly cold smile, ...
photorealistic, realistic rendering, highly detailed, professional photography, studio lighting, 8k
```
- ✅ East Asian facial structure（东方脸型）、黑发高束发髻（古代中国发型）、Chinese hanfu（中国古代服饰）
- ✅ 英文输出、写实风格、性别准确（young male）、无中文残留
- ✅ 后端已重启生效（健康检查 200）；LLM 日志确认 parse_characters / generate_character_appearance / translate_appearance 均走 ollama qwen3:8b

### 生效范围与操作
- **已生成的角色**：需在角色页点【AI 生成外貌描述】重新生成英文外貌描述（带上中国风），再重新生成角色图
- 后续新角色自动生效

### 备注
- 约束同时适用于所有画风分支（写实/动漫/Q版/水墨），默认中国风；若未来做西方题材需放开，可把约束改为可配置
- 运行中 LLM 配置：ollama / qwen3:8b / 127.0.0.1:11434/v1（system_configs）
