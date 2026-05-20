# 📖 OpenYouTubeClaw 文档导航

OpenYouTubeClaw 是 YouTube 专用的本地 AI 推荐 Agent。公开产品名、CLI、浏览器插件、配置样例和文档都以 YouTube 为主路径；内部 Python 包名第一阶段仍保留 `openbiliclaw`，用于降低迁移风险。

## 快速入口

- [中文 README](../README.md)：安装、初始化、插件加载、双语界面、日常命令和故障排查。
- [English README](../README_EN.md)：English quick start and usage guide.
- [配置参考](modules/config.md)：YouTube-only `config.toml` 字段说明。
- [CLI 命令参考](modules/cli.md)：`openyoutubeclaw` 命令一览。
- [YouTube 模块](modules/youtube.md)：Takeout、YouTube client、discovery 策略与任务流。
- [架构说明](architecture.md)：当前 YouTube-only 数据流。
- [系统规格](spec.md)：更完整的模块边界与设计约束。
- [变更日志](changelog.md)：版本交付记录。

## 模块文档

| 模块 | 文档 | 代码位置 | 状态 |
| --- | --- | --- | --- |
| CLI | [modules/cli.md](modules/cli.md) | `src/openbiliclaw/cli.py` | ✅ 主入口为 `openyoutubeclaw` |
| 配置 | [modules/config.md](modules/config.md) | `src/openbiliclaw/config.py` / `config.example.toml` | ✅ YouTube 默认启用，legacy 源默认关闭 |
| YouTube 接入 | [modules/youtube.md](modules/youtube.md) | `src/openbiliclaw/youtube/` / `sources/yt_tasks.py` | ✅ Takeout、插件任务、discovery |
| 发现链路 | [modules/discovery.md](modules/discovery.md) | `src/openbiliclaw/discovery/` | ✅ 运行时只注册 YouTube 策略 |
| 推荐引擎 | [modules/recommendation.md](modules/recommendation.md) | `src/openbiliclaw/recommendation/` | ✅ source-agnostic |
| 画像与记忆 | [modules/memory.md](modules/memory.md) | `src/openbiliclaw/memory/` / `soul/` | ✅ 使用 YouTube 行为事件重建 |
| API / Runtime | [modules/api.md](modules/api.md) | `src/openbiliclaw/api/` / `runtime/` | ✅ 本地 FastAPI + 调度器 |
| 浏览器插件 | [modules/extension.md](modules/extension.md) | `extension/` | ✅ YouTube + localhost 权限，支持中英双语界面 |

## 推荐阅读顺序

1. 先读 [README](../README.md) 完成安装和首轮初始化。
2. 需要调配置时读 [配置参考](modules/config.md)。
3. 需要脚本化或排查命令时读 [CLI 参考](modules/cli.md)。
4. 修改数据流或模块边界前，先同步 [架构说明](architecture.md) 与 [系统规格](spec.md)。

## 贡献提醒

根据仓库 `AGENTS.md`：任何改动 CLI、配置、数据流、模块边界、浏览器插件权限或对外文案，都必须同步更新相关模块文档、架构说明与 changelog。
