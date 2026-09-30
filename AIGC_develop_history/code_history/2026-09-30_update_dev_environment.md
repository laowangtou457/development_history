# 2026-09-30 重构 F:\DevelopmentEnvironment 开发环境目录

> 触发：用户要求"更新 F:\DevelopmentEnvironment 目录的内容，将本次开发所需的开发环境安装文件都放到该目录下，重新编写一键安装脚本"

## 变更内容

### 目录结构（新增 installers/ scripts/ models/ docs/）
```
F:\DevelopmentEnvironment\
├── installers\  ← 新增，集中本次开发所需安装包（5 个）
│   ├── python-3.12.10-amd64.exe   ← 从 F:\Develop\NewAIProductionWorkflow 复制（工程 venv 固定 3.12）
│   ├── node-v24.21.0-x64.msi      ← 原根目录移入
│   ├── Git-2.55.0.5-64-bit.exe    ← 原根目录移入
│   ├── OllamaSetup.exe            ← 从 F:\Develop\VLM 复制（本地 LLM/VLM）
│   └── VSCodeSetup-User-x64-1.138.0.exe ← 原根目录移入
├── scripts\  ← 新增，4 个脚本
│   ├── setup_all.ps1     ★ 新一键安装主脚本（5 阶段：基础软件→工程代码→依赖→模型→自检，幂等+管理员提权+日志）
│   ├── verify_env.ps1    环境自检（OK/FAIL 清单：命令/工程/venv/模型/Ollama）
│   ├── copy_models.bat   ComfyUI 模型增量拷贝（robocopy 只增不删，11 个类别，断点续传）
│   └── pull_ollama_models.bat   Ollama 模型在线拉取（qwen3:8b/30b-a3b/qwen2.5vl:3b）
├── models\模型清单.md    ← 新增，≈200GB 模型部署清单（ComfyUI 155GB + Ollama 44GB + ASR）
├── 安装开发环境.bat      ← 更新入口（调用 scripts\setup_all.ps1）
├── 安装操作手册.md        ← 重写为 AI 影视创作平台环境安装手册（六节：结构/一键安装/模型/启动/自检/排查）
├── setup.ps1             ← 保留（通用开发环境：Python3.14/Node/Git/VSCode/.NET，供非平台场景）
└── python-3.14.7-amd64.exe ← 保留（通用开发，平台不使用 3.14）
```

### 关键设计
- **Python 版本对齐**：平台后端/ComfyUI/管线全部固定 Python 3.12 → 安装包从工程复制 3.12.10；3.14 保留为通用开发
- **模型不落目录**：约 200GB 权重不适合随目录分发 → `copy_models.bat`（源机增量拷贝）+ `pull_ollama_models.bat`（在线）+ 模型清单文档
- **工程获取**：clone `laowangtou457/AIGC_develop`（含三工作流全量代码 + 一键启动全家桶.bat + docs）
- **幂等/分阶段**：-SkipBaseEnv / -SkipProject / -SkipModels 可分段执行；已存在自动跳过
- **自检闭环**：安装结束自动跑 verify_env.ps1，输出模型/venv/命令逐项 OK/FAIL

### 验证
- setup_all.ps1 / verify_env.ps1 PowerShell 语法解析 0 错误（UTF8 读取）
- 5 个安装包复制校验完成（python3.12 25.7MB / Ollama 50.2MB / node 31.7MB / git 62.3MB / vscode 225.1MB）
- 入口 bat（chcp 65001 + 调 scripts\setup_all.ps1）正常
