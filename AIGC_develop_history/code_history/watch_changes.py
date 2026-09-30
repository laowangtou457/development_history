# -*- coding: utf-8 -*-
"""
代码变更监控（后台常驻）

功能：轮询扫描监控目录中的代码文件，对比快照，
      每次发现变更（新增/修改/删除）即追加记录到 F:/Develop/code_history/变更记录/YYYY-MM-DD.md。

启动：pythonw watch_changes.py（无窗口后台运行）
停止：读取 .watch.pid 后 kill
"""
import json
import os
import time
import datetime
import hashlib
import sys

# ── 配置 ──────────────────────────────────────────────
CODE_HISTORY = r"F:\Develop\code_history"
SNAPSHOT_FILE = os.path.join(CODE_HISTORY, ".snapshot.json")
LOG_DIR = os.path.join(CODE_HISTORY, "变更记录")
PID_FILE = os.path.join(CODE_HISTORY, ".watch.pid")
SCAN_INTERVAL = 5          # 扫描间隔（秒）
MAX_BATCH_RECORDS = 200    # 单次扫描最多记录条数（防止刷屏）

# 监控的代码根目录（递归扫描）
MONITOR_ROOTS = [
    r"F:\Develop\NewAIProductionWorkflow\AI-NovelFlow\backend\app",
    r"F:\Develop\NewAIProductionWorkflow\AI-NovelFlow\frontend\my-app\src",
    r"F:\Develop\NewAIProductionWorkflow\ComfyUI-H3-Prompt-Builder\comfyui-h3-prompt-builder",
    r"F:\Develop\NewAIProductionWorkflow\ManjuToSplitFrameAndProperty",
]

# 排除的目录名 / 文件后缀（大小写不敏感）
EXCLUDE_DIRS = {
    "node_modules", "venv", ".venv", ".git", "__pycache__", "dist", "build",
    "output", "outputs", ".output", "target", "bin", "obj", ".next", "cache",
    "logs", "tmp", "temp", ".idea", ".vscode", ".pytest_cache", "assets_tmp",
}
EXCLUDE_SUFFIXES = {
    ".pyc", ".pyo", ".db", ".sqlite", ".log", ".tmp", ".bak", ".swp", ".swo",
    ".lock", ".class", ".o", ".so", ".dll", ".exe", ".png", ".jpg", ".jpeg",
    ".gif", ".mp4", ".webp", ".zip", ".7z", ".rar", ".tar", ".gz",
    ".wav", ".mp3", ".flac",
}
EXCLUDE_PREFIXES = ("~$", ".~", "#", "._")

# 关键文件：即使是 .md / .txt 也纳入（如规则文件、文档）
EXTRA_TRACK_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}


def should_ignore(rel_path: str) -> bool:
    """判断相对路径是否应忽略。"""
    parts = rel_path.replace("\\", "/").split("/")
    for p in parts:
        if p.lower() in EXCLUDE_DIRS:
            return True
    name = os.path.basename(rel_path)
    if name.lower().endswith(tuple(EXCLUDE_SUFFIXES)):
        return True
    if name.startswith(EXCLUDE_PREFIXES):
        return True
    return False


def file_sig(path: str):
    """文件签名：(mtime_ns, size)"""
    st = os.stat(path)
    return (st.st_mtime_ns, st.st_size)


def scan_files():
    """扫描所有监控根目录，返回 {abs_path: (mtime_ns, size)}（仅跟踪代码文件）。"""
    result = {}
    code_suffixes = {".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".css", ".scss",
                     ".html", ".sh", ".bat", ".ps1", ".sql"} | EXTRA_TRACK_SUFFIXES
    for root in MONITOR_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # 原地过滤排除目录
            dirnames[:] = [d for d in dirnames if d.lower() not in EXCLUDE_DIRS]
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, root)
                if should_ignore(rel):
                    continue
                ext = os.path.splitext(fn)[1].lower()
                if ext not in code_suffixes:
                    continue
                try:
                    result[full] = file_sig(full)
                except OSError:
                    pass
    return result


def load_snapshot():
    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            snap = json.load(f)
        # json 读回的是 list，转回 tuple 以便与 file_sig 比较
        return {k: tuple(v) if isinstance(v, list) else v for k, v in snap.items()}
    except Exception:
        return {}


def save_snapshot(snap):
    tmp = SNAPSHOT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False)
    os.replace(tmp, SNAPSHOT_FILE)


def today_log_path():
    return os.path.join(LOG_DIR, datetime.date.today().strftime("%Y-%m-%d") + ".md")


def append_record(lines):
    path = today_log_path()
    with open(path, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def rel_of(path):
    """取相对最短的展示路径（去掉监控根前缀）。"""
    for root in MONITOR_ROOTS:
        if path.startswith(root):
            return os.path.relpath(path, root)
    return path


def main():
    # 单实例保护
    if os.path.exists(PID_FILE):
        try:
            old_pid = int(open(PID_FILE).read().strip())
            if old_pid > 0:
                try:
                    os.kill(old_pid, 0)
                    print(f"已有监控实例运行中 (PID {old_pid})，退出")
                    return
                except OSError:
                    pass  # 旧进程已死
        except Exception:
            pass
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    print(f"[CodeWatch] 启动，PID={os.getpid()}，扫描间隔 {SCAN_INTERVAL}s")
    print(f"[CodeWatch] 监控目录:")
    for root in MONITOR_ROOTS:
        print(f"  - {root}")

    prev = load_snapshot()
    first_run = not prev
    if first_run:
        print("[CodeWatch] 首次运行，建立基线快照（不记录历史存量变更）")
    try:
        while True:
            time.sleep(SCAN_INTERVAL)
            try:
                now = scan_files()
            except Exception as e:
                print(f"[CodeWatch] 扫描异常: {e}")
                continue

            records = []
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 新增 / 修改
            for path, sig in now.items():
                if path not in prev:
                    records.append((path, "新增", sig))
                elif prev[path] != sig:
                    records.append((path, "修改", sig))

            # 删除
            for path in prev:
                if path not in now:
                    records.append((path, "删除", None))

            if records and not first_run:
                records.sort(key=lambda x: x[0])
                lines = [f"### {ts} 检测到 {len(records)} 处变更"]
                for path, kind, sig in records[:MAX_BATCH_RECORDS]:
                    size = sig[1] if sig else 0
                    kb = f"{size/1024:.1f}KB" if size >= 0 else "-"
                    lines.append(f"- [{kind}] `{rel_of(path)}` ({kb})")
                if len(records) > MAX_BATCH_RECORDS:
                    lines.append(f"- ... 另有 {len(records) - MAX_BATCH_RECORDS} 处变更（超出单次上限）")
                lines.append("")
                append_record(lines)
                print(f"[CodeWatch] {ts} 记录 {len(records)} 处变更")

            # 更新快照（无论是否有变更，保持最新基线）
            prev = now
            save_snapshot(prev)
            first_run = False
    except KeyboardInterrupt:
        print("[CodeWatch] 已停止")
    finally:
        try:
            os.remove(PID_FILE)
        except OSError:
            pass


if __name__ == "__main__":
    main()
