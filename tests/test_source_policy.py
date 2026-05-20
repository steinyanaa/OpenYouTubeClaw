"""Tests for YouTube-only discovery source policy helpers."""

from openbiliclaw.config import Config
from openbiliclaw.runtime.source_policy import (
    DEFAULT_POOL_SOURCE_SHARES,
    effective_pool_source_shares,
    source_enabled_map,
    suggest_pool_source_shares,
)


def test_source_enabled_map_is_youtube_only_by_default() -> None:
    config = Config()

    assert source_enabled_map(config) == {"youtube": True}


def test_source_enabled_map_reads_youtube_switch_only() -> None:
    config = Config()
    config.sources.bilibili.enabled = True
    config.sources.xiaohongshu.enabled = True
    config.sources.douyin.enabled = True
    config.sources.youtube.enabled = False

    assert source_enabled_map(config) == {"youtube": False}


def test_effective_pool_source_shares_keep_only_enabled_youtube() -> None:
    config = Config()
    config.scheduler.pool_source_shares = {
        "bilibili": 8,
        "xiaohongshu": 3,
        "douyin": 2,
        "youtube": 4,
    }
    config.sources.bilibili.enabled = True
    config.sources.xiaohongshu.enabled = True
    config.sources.douyin.enabled = True
    config.sources.youtube.enabled = True

    assert effective_pool_source_shares(config) == {"youtube": 4}


def test_effective_pool_source_shares_empty_when_youtube_disabled() -> None:
    config = Config()
    config.sources.youtube.enabled = False

    assert effective_pool_source_shares(config) == {}


def test_effective_pool_source_shares_fall_back_to_youtube_default() -> None:
    config = Config()
    config.scheduler.pool_source_shares = {}

    assert DEFAULT_POOL_SOURCE_SHARES == {"youtube": 1}
    assert effective_pool_source_shares(config) == {"youtube": 1}


def test_suggest_pool_source_shares_is_youtube_only() -> None:
    suggestion = suggest_pool_source_shares(
        {"bilibili": 900, "xiaohongshu": 100, "douyin": 9, "youtube": 400},
        enabled_sources={
            "bilibili": True,
            "xiaohongshu": True,
            "douyin": True,
            "youtube": True,
        },
        configured_shares={
            "bilibili": 8,
            "xiaohongshu": 2,
            "douyin": 1,
            "youtube": 3,
        },
    )

    assert suggestion == {"youtube": 3}


def test_suggest_pool_source_shares_returns_empty_when_youtube_disabled() -> None:
    suggestion = suggest_pool_source_shares(
        {"youtube": 900},
        enabled_sources={"youtube": False},
    )

    assert suggestion == {}
