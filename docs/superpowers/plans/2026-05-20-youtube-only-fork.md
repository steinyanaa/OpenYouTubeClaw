# YouTube-Only Fork Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn OpenBiliClaw into a YouTube-only recommendation agent where YouTube import, YouTube browser-extension bootstrap, YouTube discovery, and YouTube recommendations are the primary product path.

**Architecture:** Keep the existing local-first backend, SQLite memory, Soul profile, recommendation engine, FastAPI daemon, and browser extension. Remove or disable Bilibili/Xiaohongshu/Douyin entrypoints, make YouTube the only enabled source, and rely on existing `openbiliclaw.youtube`, `discovery.strategies.youtube`, `sources.yt_tasks`, and extension `yt-*` modules as the core.

**Tech Stack:** Python 3.11+, FastAPI, Typer, SQLite, Pydantic, yt-dlp, scrapetube, TypeScript Chrome MV3 extension, esbuild, node:test.

---

## Current Repo Facts

Inspected repository: `C:\Users\1\Documents\Codex\2026-05-15\codex-codex-mobile\OpenBiliClaw`
Current commit: `6d07072 feat: add bilibili discovery source toggle`

Existing YouTube assets to reuse:
- `src/openbiliclaw/youtube/client.py` — YouTube scraping/normalization via scrapetube, yt-dlp, InnerTube fallback.
- `src/openbiliclaw/youtube/takeout.py` — Google Takeout parser for watch history, subscriptions, likes.
- `src/openbiliclaw/discovery/strategies/youtube.py` — `yt_search`, `yt_trending`, `yt_channel` discovery strategies.
- `src/openbiliclaw/sources/yt_tasks.py` — YouTube task queue and event conversion.
- `extension/src/content/youtube.ts`, `extension/src/content/yt/task-executor.ts`, `extension/src/background/yt-task-dispatcher.ts` — browser-extension YouTube bootstrap path.
- `src/openbiliclaw/cli.py` already has `fetch-youtube` and `import-youtube` commands.

## Target File Structure

Recommended MVP: keep the internal Python package name `openbiliclaw` for the first pass to avoid a huge import rename. Rebrand public CLI/docs/extension first; package rename can be a separate final task.

Files to modify:
- `pyproject.toml` — project name, description, keywords, script alias, dependencies.
- `README.md`, `README_EN.md`, `config.example.toml`, `Dockerfile`, `docker-compose.yml`, `packaging/*` — public product/docs defaults.
- `src/openbiliclaw/config.py` — YouTube-only source defaults and generated config.
- `src/openbiliclaw/runtime/source_policy.py` — source order and pool shares.
- `src/openbiliclaw/api/models.py`, `src/openbiliclaw/api/app.py`, `src/openbiliclaw/api/runtime_context.py` — config API and runtime component cleanup.
- `src/openbiliclaw/cli.py` — YouTube-first init/discover/fetch/import UX.
- `src/openbiliclaw/runtime/account_sync.py` — remove from runtime or replace with a YouTube-specific no-background-sync policy.
- `src/openbiliclaw/runtime/refresh.py` — YouTube-only strategy plan and pool accounting.
- `src/openbiliclaw/discovery/engine.py`, `src/openbiliclaw/recommendation/engine.py`, `src/openbiliclaw/storage/database.py` — keep universal fields; only rename user-facing fallback labels.
- `extension/manifest.json`, `extension/manifest.firefox.json`, `extension/package.json`, `extension/src/background/service-worker.ts`, `extension/src/background/cookie-sync.ts`, `extension/popup/*` — remove non-YouTube hosts/scripts and rebrand.
- Tests under `tests/` and `extension/tests/` — update expectations to YouTube-only.

---

### Task 1: Establish a YouTube-only baseline configuration

**Files:**
- Modify: `src/openbiliclaw/config.py`
- Modify: `src/openbiliclaw/runtime/source_policy.py`
- Modify: `config.example.toml`
- Test: `tests/test_config.py`
- Test: `tests/test_source_policy.py`

- [ ] **Step 1: Change source defaults**

Set defaults so YouTube is the only enabled source:

```python
# src/openbiliclaw/config.py
_DEFAULT_POOL_SOURCE_SHARES = {
    "youtube": 1,
}
```

```python
# src/openbiliclaw/runtime/source_policy.py
SOURCE_ORDER = ("youtube",)
DEFAULT_SOURCE_ENABLED = {"youtube": True}
DEFAULT_POOL_SOURCE_SHARES = {"youtube": 1}
```

- [ ] **Step 2: Keep Bilibili/XHS/Douyin config dataclasses temporarily but default them off**

This avoids breaking tests and old config parsing during the first pass:

```python
@dataclass
class BilibiliSourceConfig:
    enabled: bool = False

@dataclass
class XiaohongshuSourceConfig:
    enabled: bool = False
    daily_search_budget: int = 0
    daily_creator_budget: int = 0
    task_interval_seconds: int = 45

@dataclass
class DouyinSourceConfig:
    enabled: bool = False
    mode: str = "direct"
    cookie_env: str = "OPENBILICLAW_DOUYIN_COOKIE"
    daily_search_budget: int = 0
    daily_hot_budget: int = 0
    daily_feed_budget: int = 0
    request_interval_seconds: int = 2

@dataclass
class YoutubeSourceConfig:
    enabled: bool = True
    daily_search_budget: int = 6
    daily_trending_budget: int = 50
    daily_channel_budget: int = 10
    request_interval_seconds: int = 2
```

- [ ] **Step 3: Update generated config output**

In `save_config()` generation, either remove non-YouTube sections from public output or keep them with `enabled = false`. For MVP, keep them disabled so legacy code keeps parsing.

- [ ] **Step 4: Update tests**

Run:

```bash
uv run pytest tests/test_config.py tests/test_source_policy.py -q
```

Expected: config defaults assert `sources.youtube.enabled is True`; effective pool shares return only `{"youtube": 1}`.

---

### Task 2: Make discovery YouTube-first in CLI and daemon

**Files:**
- Modify: `src/openbiliclaw/cli.py`
- Modify: `src/openbiliclaw/api/runtime_context.py`
- Modify: `src/openbiliclaw/runtime/refresh.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_refresh_runtime.py`
- Test: `tests/test_youtube_discovery_strategy.py`

- [ ] **Step 1: Replace CLI `_build_discovery_engine()` Bilibili registration with YouTube registration**

Use the existing helper from runtime context:

```python
from openbiliclaw.api.runtime_context import build_youtube_discovery_strategies
from openbiliclaw.youtube.client import YtScraperClient

yt_client = YtScraperClient()
for strategy in build_youtube_discovery_strategies(
    config=cfg,
    client=yt_client,
    llm_service=llm_service,
    memory=cast("Any", memory),
    concurrency=concurrency,
):
    engine.register_strategy(strategy)
```

Remove `SearchStrategy`, `TrendingStrategy`, `RelatedChainStrategy`, `ExploreStrategy`, and `_build_bilibili_client()` from this CLI build path.

- [ ] **Step 2: Change `discover` command default source**

Set:

```python
source: str = typer.Option(
    "youtube",
    "--source",
    "-s",
    help="触发发现的内容源：youtube。",
    case_sensitive=False,
)
```

Allow `youtube` only. Support `--strategy yt_search`, `--strategy yt_trending`, `--strategy yt_channel` or leave empty for all.

- [ ] **Step 3: Runtime context should register YouTube strategies only when YouTube is enabled**

Wrap registration with:

```python
yt_enabled = bool(getattr(getattr(new_config.sources, "youtube", None), "enabled", True))
if yt_enabled:
    ... register YouTube strategies ...
```

Do not instantiate Bilibili strategies/adapters in YouTube-only mode.

- [ ] **Step 4: Refresh source list**

In `src/openbiliclaw/runtime/refresh.py`, keep:

```python
_PLATFORM_SOURCE_ORDER = ("youtube",)
_DEFAULT_PLATFORM_SOURCE_SHARES = {"youtube": 1}
_BILIBILI_DISCOVERY_SOURCES = ()
_YOUTUBE_DISCOVERY_SOURCES = ("yt_search", "yt_trending", "yt_channel")
```

- [ ] **Step 5: Verify discovery strategy tests**

Run:

```bash
uv run pytest tests/test_youtube_discovery_strategy.py tests/test_refresh_runtime.py -q
```

Expected: YouTube strategies still normalize `source_platform="youtube"`; refresh calls YouTube discovery sources.

---

### Task 3: Turn init into a YouTube onboarding flow

**Files:**
- Modify: `src/openbiliclaw/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Remove Bilibili auth as a required init prerequisite**

Remove calls that force `_guide_bilibili_auth_before_init()` and `_build_bilibili_client()` for init. Init should accept one of these YouTube inputs:

```text
A. Browser extension bootstrap: openbiliclaw init --youtube-browser
B. Google Takeout import: openbiliclaw init --youtube-takeout PATH
C. Empty profile bootstrap: openbiliclaw init --empty-profile
```

- [ ] **Step 2: Promote existing YouTube commands**

Keep existing commands:

```bash
openbiliclaw fetch-youtube --wait-seconds 240
openbiliclaw import-youtube ./takeout.zip
```

Make `init` call the same internal functions based on user choice.

- [ ] **Step 3: Replace `--yes-youtube` / `--no-youtube` with YouTube-first flags**

Recommended flags:

```text
--youtube-browser       Use extension to collect watch/subscription/like signals.
--youtube-takeout PATH  Import Google Takeout signals.
--skip-youtube-import   Build an empty profile and let discovery start from prompts/default interests.
```

- [ ] **Step 4: Update CLI tests**

Run:

```bash
uv run pytest tests/test_cli.py -q
```

Expected: no Bilibili cookie is required for init; YouTube import path is the primary signal source.

---

### Task 4: Simplify the browser extension to YouTube + localhost

**Files:**
- Modify: `extension/manifest.json`
- Modify: `extension/manifest.firefox.json`
- Modify: `extension/src/background/service-worker.ts`
- Modify: `extension/src/background/cookie-sync.ts`
- Modify: `extension/src/background/yt-task-dispatcher.ts`
- Modify: `extension/src/content/youtube.ts`
- Modify: `extension/src/content/yt/task-executor.ts`
- Modify: `extension/popup/*`
- Test: `extension/tests/manifest-assets.test.ts`
- Test: add `extension/tests/yt-task-dispatcher.test.ts` if not already present.

- [ ] **Step 1: Reduce extension host permissions**

Manifest target:

```json
{
  "name": "OpenYouTubeClaw",
  "host_permissions": [
    "*://*.youtube.com/*",
    "http://127.0.0.1/*",
    "http://localhost/*"
  ],
  "content_scripts": [
    {
      "matches": ["*://*.youtube.com/*"],
      "js": ["dist/content/youtube.js"],
      "run_at": "document_idle"
    }
  ]
}
```

- [ ] **Step 2: Remove non-YouTube dispatcher wiring**

Keep runtime-stream handling for `yt_task_available`. Remove imports and listeners for Bilibili cookie sync, XHS task dispatch, Douyin task dispatch.

- [ ] **Step 3: Keep YouTube task executor unchanged first**

The executor already covers:

```text
yt_history        -> https://www.youtube.com/feed/history
yt_subscriptions -> https://www.youtube.com/feed/channels
yt_likes          -> https://www.youtube.com/playlist?list=LL
```

Only rebrand console logs and popup copy in the first pass.

- [ ] **Step 4: Verify extension build**

Run:

```bash
cd extension
npm test
npm run typecheck
npm run build
```

Expected: no manifest references to `bilibili.com`, `xiaohongshu.com`, or `douyin.com`; extension still builds YouTube content/background bundles.

---

### Task 5: Keep the database universal; do not rename columns in MVP

**Files:**
- Modify only if labels are user-facing: `src/openbiliclaw/storage/database.py`, `src/openbiliclaw/discovery/engine.py`, `src/openbiliclaw/recommendation/engine.py`
- Test: `tests/test_discovery_engine.py`

- [ ] **Step 1: Keep `bvid` as a legacy alias**

Do not perform a DB migration just to rename `bvid`. Existing code already has universal fields:

```python
content_id: str
content_url: str
source_platform: str
author_name: str
```

For YouTube, continue setting `bvid = video_id` for compatibility while rendering `content_id` / `content_url` in UI.

- [ ] **Step 2: Remove Bilibili fallback labels from user-facing paths only**

Replace visible fallback text from `bilibili` to `youtube` where it affects UI/API responses. Avoid deep schema churn.

- [ ] **Step 3: Verify recommendation path**

Run:

```bash
uv run pytest tests/test_discovery_engine.py -q
```

Expected: YouTube content remains cacheable, rankable, and recommendable.

---

### Task 6: Remove or neutralize Bilibili account sync

**Files:**
- Modify: `src/openbiliclaw/api/runtime_context.py`
- Modify: `src/openbiliclaw/runtime/account_sync.py` or stop importing it
- Test: `tests/test_refresh_runtime.py`, `tests/test_api_app.py`

- [ ] **Step 1: Stop creating `AccountSyncService` for YouTube-only runtime**

Because the existing service is explicitly Bilibili-only (`history`, `favorites`, `following` via `BilibiliAPIClient`), do not run it in YouTube-only mode.

- [ ] **Step 2: Do not silently run browser automation in background**

YouTube watch history bootstrap needs a focused browser tab, so periodic account sync should not unexpectedly steal focus. Keep this as explicit commands:

```bash
openbiliclaw fetch-youtube
openbiliclaw import-youtube ./takeout.zip
```

- [ ] **Step 3: Optional later enhancement**

Add a manual scheduler button/API that enqueues a YouTube bootstrap only after user confirmation.

---

### Task 7: Rebrand package, CLI, docs, and release artifacts

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`, `README_EN.md`
- Modify: `extension/package.json`
- Modify: `Dockerfile`, `docker-compose.yml`, `packaging/*`

- [ ] **Step 1: Public rename**

Recommended MVP public identifiers:

```toml
# pyproject.toml
name = "openyoutubeclaw"
description = "Your local AI friend for YouTube — understands your watch signals and finds videos you'll love."
keywords = ["youtube", "ai", "agent", "recommendation", "llm"]

[project.scripts]
openyoutubeclaw = "openbiliclaw.cli:app"
```

Keep the old script temporarily as an alias if desired:

```toml
openbiliclaw = "openbiliclaw.cli:app"
```

- [ ] **Step 2: Dependencies**

Remove `bilibili-api-python` only after all imports are gone. Keep:

```toml
"scrapetube>=2.1",
"yt-dlp>=2024.1.0",
"fastapi>=0.115",
"typer>=0.12",
"pydantic>=2.0"
```

- [ ] **Step 3: Docs**

README quickstart should be:

```bash
git clone <your-fork>
cd OpenYouTubeClaw
uv sync
cp config.example.toml config.toml
openyoutubeclaw start
openyoutubeclaw import-youtube ./takeout.zip
openyoutubeclaw discover --source youtube
openyoutubeclaw recommend
```

---

### Task 8: Final validation matrix

**Files:**
- No new production files unless failures require fixes.

- [ ] **Step 1: Python tests**

```bash
uv run pytest tests/test_config.py tests/test_source_policy.py tests/test_youtube_discovery_strategy.py tests/youtube/test_takeout.py tests/test_discovery_engine.py -q
```

Expected: PASS.

- [ ] **Step 2: Extension tests and build**

```bash
cd extension
npm test
npm run typecheck
npm run build
```

Expected: PASS and generated manifest/bundles contain only YouTube + localhost host permissions.

- [ ] **Step 3: Manual smoke**

```bash
openyoutubeclaw import-youtube ./sample-takeout.zip --dry-run
openyoutubeclaw import-youtube ./sample-takeout.zip
openyoutubeclaw rebuild-profile --source youtube
openyoutubeclaw discover --source youtube --limit 10
openyoutubeclaw recommend
```

Expected: profile events are `source_platform=youtube`; discovered candidates use `yt_search`, `yt_trending`, or `yt_channel`; recommendation URLs are `https://www.youtube.com/watch?v=...`.

---

## Recommended Execution Order

1. MVP configuration defaults: YouTube enabled, all other sources disabled.
2. CLI discovery path: `discover --source youtube` works without Bilibili client.
3. Init/onboarding path: `import-youtube` and `fetch-youtube` become first-class.
4. Runtime daemon: remove Bilibili account sync and register YouTube strategies only.
5. Extension: trim to YouTube-only permissions and task dispatcher.
6. Docs/rebrand: public name, README, package metadata.
7. Cleanup: remove dead Bilibili/XHS/Douyin modules only after tests are green.

## Key Risks

- YouTube DOM and private InnerTube structures can drift; keep `yt-dlp` fallback and tests around normalization.
- Extension YouTube bootstrap needs a logged-in active browser tab; do not run it as invisible periodic sync.
- Full Python package rename from `openbiliclaw` to `openyoutubeclaw` is high-churn; defer until after product behavior works.
- The DB has legacy `bvid` names; avoid schema rename in MVP and rely on universal `content_id` / `source_platform` fields.
