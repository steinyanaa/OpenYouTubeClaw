# 浏览器插件模块

## 概述

`extension/` 是 OpenYouTubeClaw 的浏览器插件子项目，面向 Chrome / Edge / Brave 与 Firefox。当前公开形态是 **YouTube-only**：插件只注入 YouTube 页面，只连接本机后端，并在侧边栏提供推荐、画像、聊天、消息和设置入口。

## 已实现功能

| 功能 | 状态 | 说明 |
| --- | --- | --- |
| YouTube content script | ✅ | `manifest.json` / `manifest.firefox.json` 只匹配 `*://*.youtube.com/*`。 |
| 本地后端连接 | ✅ | host permissions 只包含 `http://127.0.0.1/*` 与 `http://localhost/*`。 |
| YouTube 任务桥 | ✅ | 后端可派发 YouTube bootstrap / fetch 类任务，插件在已登录 YouTube 会话内执行并回传结果。 |
| 推荐侧边栏 | ✅ | popup/side panel 展示推荐、画像、聊天与运行时消息。 |
| 双语界面 | ✅ | `popup/i18n.js` 提供中文 / English 语言切换，语言选择保存在 `localStorage`。 |
| Legacy 平台 UI | Disabled | Bilibili / 小红书 / 抖音 / 通用网页源卡片在 YouTube fork 中隐藏，不作为公开主路径。 |

## 公开 API / 文件入口

```text
extension/
├── manifest.json              # Chromium manifest，YouTube-only 权限
├── manifest.firefox.json      # Firefox manifest，构建时注入版本
├── popup/
│   ├── popup.html             # 侧边栏页面
│   ├── i18n.js                # 中英双语静态文案切换
│   ├── popup.js               # 推荐 / 画像 / 聊天 / 设置交互
│   ├── popup-api.js           # 后端 API client
│   └── popup-helpers.js       # UI 字段规范化与渲染 helper
├── src/
│   ├── background/service-worker.ts
│   └── content/youtube.ts
└── tests/
```

### 插件权限

```json
{
  "host_permissions": [
    "*://*.youtube.com/*",
    "http://127.0.0.1/*",
    "http://localhost/*"
  ]
}
```

## 配置项

插件侧主要读取后端地址配置：

- 后端地址：默认 `127.0.0.1`
- 后端端口：默认 `8420`
- UI 语言：`localStorage.openyoutubeclaw.uiLanguage`，可取 `zh-CN` 或 `en-US`

后端数据源与 discovery 配置仍以 `config.toml` 为准，详见 [配置参考](config.md)。

## 本地开发

```bash
cd extension
npm install
npm test
npm run typecheck
npm run build
```

手动联调：

1. 在项目根目录启动后端：`openyoutubeclaw start`。
2. 在 `extension/` 下执行 `npm run build`。
3. 在浏览器扩展管理页加载 `extension/` 目录。
4. 打开 YouTube 页面并登录。
5. 打开插件侧边栏，确认只出现 YouTube / localhost 权限，语言切换可在中文和 English 间切换。

## 设计决策

- **YouTube-only 权限最小化**：公开插件不再请求 Bilibili / 小红书 / 抖音域名权限，降低安装时的认知负担。
- **双语不阻塞主逻辑**：`popup/i18n.js` 只处理静态 UI 文案；动态推荐内容、画像摘要和 LLM 回复保持后端返回的语言。
- **保留内部兼容代码**：部分旧字段和 helper 仍存在，避免第一阶段硬分叉引入大规模迁移风险；公开 UI 会隐藏 legacy 平台入口。


> 2026-05-20: Chromium `manifest.json` no longer requests the `cookies` permission in the YouTube-only public path. Popup inbox hydration was split into `popup/popup-inbox.js` and covered by characterization tests.
