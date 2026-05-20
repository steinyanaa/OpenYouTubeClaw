"""Shared discovery source switch and pool-share policy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SOURCE_ORDER = ("youtube",)
DEFAULT_SOURCE_ENABLED = {
    "youtube": True,
}
DEFAULT_POOL_SOURCE_SHARES = {
    "youtube": 1,
}


def source_enabled_map(config: Any) -> dict[str, bool]:
    """Return enabled state for pool-accounted discovery sources."""

    sources_cfg = getattr(config, "sources", None)
    enabled: dict[str, bool] = {}
    for source in SOURCE_ORDER:
        source_cfg = getattr(sources_cfg, source, None) if sources_cfg is not None else None
        default = DEFAULT_SOURCE_ENABLED[source]
        enabled[source] = bool(getattr(source_cfg, "enabled", default))
    return {source: enabled.get(source, False) for source in SOURCE_ORDER}


def effective_pool_source_shares(config: Any) -> dict[str, int]:
    """Return configured source shares after disabled sources are removed."""

    scheduler = getattr(config, "scheduler", None)
    raw_shares = getattr(scheduler, "pool_source_shares", None)
    shares = _normalize_shares(raw_shares)
    enabled = source_enabled_map(config)
    return {source: share for source, share in shares.items() if enabled.get(source, False)}


def suggest_pool_source_shares(
    event_counts: Mapping[str, int] | None,
    *,
    enabled_sources: Mapping[str, bool] | None = None,
    configured_shares: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """Suggest integer pool shares from observed platform event counts.

    Counts are square-root damped and scaled around the core Bilibili
    default. This keeps large imports from dominating while still giving
    active optional platforms visible quota.
    """

    enabled = _normalize_enabled_sources(enabled_sources)
    if not enabled.get("youtube", False):
        return {}
    fallback = _normalize_shares(configured_shares)
    return {"youtube": int(fallback.get("youtube", DEFAULT_POOL_SOURCE_SHARES["youtube"]))}


def _normalize_enabled_sources(enabled_sources: Mapping[str, bool] | None) -> dict[str, bool]:
    if enabled_sources is None:
        return dict(DEFAULT_SOURCE_ENABLED)
    enabled: dict[str, bool] = {}
    for source in SOURCE_ORDER:
        enabled[source] = bool(enabled_sources.get(source, DEFAULT_SOURCE_ENABLED[source]))
    return {source: enabled.get(source, False) for source in SOURCE_ORDER}


def _normalize_shares(value: Mapping[str, int] | Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return dict(DEFAULT_POOL_SOURCE_SHARES)

    shares: dict[str, int] = {}
    for raw_source, raw_share in value.items():
        source = str(raw_source).strip().lower()
        if source not in SOURCE_ORDER:
            continue
        try:
            share = int(raw_share)
        except (TypeError, ValueError):
            continue
        if share > 0:
            shares[source] = share
    return shares or dict(DEFAULT_POOL_SOURCE_SHARES)
