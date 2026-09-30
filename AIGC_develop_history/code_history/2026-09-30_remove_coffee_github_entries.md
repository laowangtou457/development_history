# 移除欢迎页/侧边栏底部【请我喝咖啡】与 GitHub 入口

日期：2026-09-30
状态：已完成并验证

## 需求

用户要求去掉平台主菜单（侧边栏）下方的【请我喝咖啡】按钮和 GitHub 链接及图标。

## 变更

| 文件 | 变更 |
|---|---|
| `frontend\my-app\src\components\Layout.tsx` | 删除 `import CoffeeButton` 与 `<CoffeeButton />` 渲染（原挂载点为侧边栏左下角） |
| `frontend\my-app\src\components\CoffeeButton.tsx` | 删除整个组件文件（内含 GitHub 圆形按钮 + 请我喝咖啡按钮 + 赞助弹窗二维码/联系方式） |

## 说明

- 两个入口（GitHub 链接 `https://github.com/qzw881130/AI-NovelFlow` 与咖啡赞助按钮）都在 `CoffeeButton.tsx` 内，随组件一并移除
- i18n 中 `coffee.*` 文案保留未删（不再被引用，无 UI 影响，便于日后恢复）

## 验证

- `npx tsc --noEmit` 通过（TSC_OK，无残留引用）
- 前端 dev server（5173）HMR 自动热更新，刷新欢迎页即可生效
