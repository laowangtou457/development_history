# 2026-09-30 VS Code / .NET SDK 改为在线拉取安装

> 触发：用户要求"VSCodeSetup(225MB)、dotnet-sdk(286MB) 超 GitHub 100MB 限制无法上传，改为从线上拉取然后安装"

## 变更内容

### `scripts\setup_all.ps1`（阶段1 扩展 1.6 / 1.7）
- **1.6 VS Code 在线拉取安装**：
  - 官方最新版 User 安装器 URL `https://update.code.visualstudio.com/latest/win32-x64-user/stable` → 下载到 %TEMP% → `/VERYSILENT` 静默安装 → 装完删临时文件
  - 已安装检测（code 命令 或 %LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe）自动跳过
- **1.7 .NET SDK 10 在线拉取安装**：
  - 官方 `https://dot.net/v1/dotnet-install.ps1` 脚本 → `-Channel 10.0 -InstallDir F:\Software\dotnet` 用户级安装（免管理员，自动下载解压 zip）
  - Channel 10.0 失败自动回退 `-Channel LTS`
- **1.8 环境变量**：PATH 增加 `$InstallDir\dotnet\` 与 VS Code `bin\`；检测到 dotnet 时补设 `DOTNET_ROOT`（系统级）

### 文档同步
- README.md：超限组件改为在线拉取说明
- 安装操作手册.md：目录结构（installers 4 包 <100MB；dotnet zip 标"本地备份"）、阶段1 表格（VS Code/.NET 在线拉取）、故障排查新增该项

### 仓库文件策略
- `.gitignore` 继续排除 `dotnet-sdk-10.0.401-win-x64.zip`、`installers\VSCodeSetup-User-x64-1.138.0.exe`（不入库）
- 本地根目录的 dotnet zip 保留作备份，新机安装完全走在线拉取

## 验证
- setup_all.ps1 语法 0 错误（UTF8）；新段行号抽查 L122/L140/L160 就位
- 在线源为官方地址（VS Code update CDN / dot.net 官方脚本），VSCode 装完自动清理临时安装器
