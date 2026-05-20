# YouTube module

## Overview

YouTube is the only active platform source in OpenYouTubeClaw. It provides cold-start signals through Google Takeout, optional browser-extension bootstrap, and runtime discovery through search, trending, and subscribed-channel strategies.

## Implemented features

| Feature | Status |
|---|---|
| Google Takeout watch/subscription/like parser | Implemented |
| Extension bootstrap task queue (`yt_history`, `yt_subscriptions`, `yt_likes`) | Implemented |
| Discovery strategies (`yt_search`, `yt_trending`, `yt_channel`) | Implemented |
| YouTube-only runtime source policy | Implemented |

## Public API

```bash
openyoutubeclaw import-youtube ./takeout.zip
openyoutubeclaw fetch-youtube
openyoutubeclaw discover --source youtube --strategy yt_search
```

## Configuration

```toml
[sources.youtube]
enabled = true
daily_search_budget = 6
daily_trending_budget = 50
daily_channel_budget = 10
request_interval_seconds = 2

[scheduler.pool_source_shares]
youtube = 1
```

## Design decisions

- Keep internal Python imports under `openbiliclaw` for the first hard-fork phase.
- Keep legacy DB aliases such as `bvid`; use `source_platform = "youtube"` and `content_url` for source-aware behavior.
- YouTube browser collection is explicit and user-triggered; no background account sync steals focus.
