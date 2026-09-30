# 武术指导 · 逐分镜独立英文镜头块（H3 官方格式，机位逐镜变化）

日期：2026-09-29
状态：已验证（16 个独立镜头块真实生成，py_compile 通过，后端重启）

## 用户反馈

1. 镜头没有跟随视频提示词变化（提示词写机位变了，视频镜头没变）。
2. 后半段变成重复动作，与视频提示词不符。
3. 判断提示词没有完全生效；要求：每一个分镜都是独立的镜头，把十六个分镜按 H3 分镜提示词格式分别写出来，要素齐全，重新生成。

## 根因

上一版是"中文节拍 + The camera cuts to 一句话连写"（16 拍共用一条长句链）：
- H3/qwen3vl 对一句话链里的机位变化不敏感 → 镜头不跟随；
- 提示词长（2040 字符）且后半段与前半段句式雷同 → 模型注意力衰减，后半段自行循环前半段动作 → 重复动作。

## 修复：逐分镜独立英文镜头块

1. **新增 `H3_BEAT_TRANSLATE_SYSTEM`**：16 个中文节拍 → 8b 一次性翻译为严格 JSON 数组（每拍一个对象）：
   - `camera`：机位景别（wide/medium/close-up/extreme close-up/low-angle/high-angle/tracking/push-in...，**必须逐拍变化，禁止连续两拍相同**）
   - `subject_action`：主体动作（谁+性别+兵器+具体招式+轨迹，如 "The white-clad female swordsman flicks her wrist, thrusting the Tang saber straight out from her waist"）
   - `opponent_reaction`：对手反应
   - `camera_motion`：相机运动（自然英文句 "The camera tracks the blade at high speed"）
   - 每拍 45-60 词
2. **新增 `_translate_beats_to_blocks(beats)`**：调 8b → 解析 JSON → 逐项校验（camera/action 非空、数量=16），失败返回 None 走兜底
3. **新增 `_assemble_h3_blocks(blocks, persona, duration)`**：确定性组装，**每个分镜独立成块**：
   - `[Shot N] At 00:SS.mmm, the camera cuts to {camera} as {subject_action}, while {opponent_reaction}. {camera_motion}.`
   - 每镜以句号结束、独立段落，时间戳 15 秒均分递增（00:00.938 → 00:14.062）
4. `_to_h3_video_prompt`：优先走"逐拍翻译→组装"；翻译失败回退中文节拍模板（再失败回退 8b 旧转换）

## 验证

- 真实历史 16 拍转换：16 个独立镜头块生成，机位逐镜变化（wide → medium → close-up → low-angle → slow-motion close-up → tracking → overlapping medium → split-second close-up → low-angle → fast wide → low-angle → ...），全英文、性别明确（female swordsman/male pursuer）、动作具体
- 长度 4997 字符（每拍 ~50 词，H3/qwen3vl 上下文内）
- py_compile 通过；后端重启 health ok

## 使用

重新生成「武打分镜提示词」→「生成视频」即可。每个分镜现在是独立英文镜头块：机位、动作、对手反应、相机运动各自成句，H3 逐镜执行。
