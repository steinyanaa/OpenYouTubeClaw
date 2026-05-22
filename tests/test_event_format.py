"""Tests for the unified YouTube event format.

Pins the shape contract so downstream consumers (preference analyzer,
awareness analyzer, profile builder) always see a consistent structure.
"""

from __future__ import annotations

import json

from openbiliclaw.sources.event_format import (
    SOURCE_YOUTUBE,
    build_event,
    classify_event_satisfaction,
    format_event_context,
)
from openbiliclaw.storage.database import Database

# ---------------------------------------------------------------------------
# format_event_context: deterministic natural-language sentence builder


def test_format_context_youtube_view_with_author() -> None:
    text = format_event_context(
        event_type="view",
        source_platform=SOURCE_YOUTUBE,
        title="Python Is Slow",
        author="Arjan Codes",
    )
    assert "YouTube" in text
    assert "Python Is Slow" in text
    assert "Arjan Codes" in text


def test_format_context_youtube_like_with_author() -> None:
    text = format_event_context(
        event_type="like",
        source_platform=SOURCE_YOUTUBE,
        title="How Git Works",
        author="Fireship",
    )
    assert "YouTube" in text
    assert "How Git Works" in text
    assert "Fireship" in text


def test_format_context_unknown_event_type_falls_back() -> None:
    text = format_event_context(
        event_type="custom_action",
        source_platform=SOURCE_YOUTUBE,
        title="某内容",
    )
    assert "YouTube" in text
    assert "《某内容》" in text
    assert "记录了" in text  # generic fallback verb


def test_format_context_missing_title_uses_placeholder() -> None:
    text = format_event_context(
        event_type="favorite",
        source_platform=SOURCE_YOUTUBE,
        title="",
    )
    assert "一条内容" in text


# ---------------------------------------------------------------------------
# build_event: shape contract


def test_build_event_emits_unified_shape() -> None:
    event = build_event(
        event_type="favorite",
        source_platform=SOURCE_YOUTUBE,
        title="History of Linux",
        url="https://www.youtube.com/watch?v=abc123",
        author="TechChannel",
        metadata={"vid": "abc123"},
    )
    assert event["event_type"] == "favorite"
    assert event["title"] == "History of Linux"
    assert event["url"] == "https://www.youtube.com/watch?v=abc123"
    assert event["context"]
    assert event["metadata"]["source_platform"] == SOURCE_YOUTUBE
    assert event["metadata"]["author"] == "TechChannel"
    assert event["metadata"]["vid"] == "abc123"


def test_build_event_explicit_context_wins_over_auto_generated() -> None:
    event = build_event(
        event_type="favorite",
        source_platform=SOURCE_YOUTUBE,
        title="任何标题",
        author="作者",
        context="自定义描述",
    )
    assert event["context"] == "自定义描述"


def test_build_event_url_omitted_when_empty() -> None:
    event = build_event(
        event_type="follow",
        source_platform=SOURCE_YOUTUBE,
        title="某频道",
        author="某频道",
    )
    assert "url" not in event


def test_build_event_metadata_source_platform_explicit_wins() -> None:
    event = build_event(
        event_type="view",
        source_platform=SOURCE_YOUTUBE,
        title="...",
        metadata={"source_platform": "custom"},
    )
    assert event["metadata"]["source_platform"] == "custom"


# ---------------------------------------------------------------------------
# Shape invariant helper


def _has_unified_shape(event: dict) -> bool:
    if not isinstance(event, dict):
        return False
    for key in ("event_type", "title", "context", "metadata"):
        if key not in event:
            return False
    if not isinstance(event["metadata"], dict):
        return False
    if not event["metadata"].get("source_platform"):
        return False
    return isinstance(event["context"], str) and bool(event["context"])


def test_youtube_view_event_has_unified_shape() -> None:
    event = build_event(
        event_type="view",
        source_platform=SOURCE_YOUTUBE,
        title="Python Tips",
        author="Real Python",
        metadata={"vid": "xyz789", "signal_source": "recommended"},
    )
    assert _has_unified_shape(event)
    assert event["metadata"]["source_platform"] == SOURCE_YOUTUBE
    assert event["event_type"] == "view"
    assert "Real Python" in event["context"]
    assert "Python Tips" in event["context"]


# ---------------------------------------------------------------------------
# DB round-trip


def test_event_db_round_trip_preserves_context_string_verbatim(tmp_path) -> None:
    """Context column must be the raw natural-language string, not JSON-quoted."""
    import asyncio

    from openbiliclaw.memory.manager import MemoryManager

    db_path = tmp_path / "events.db"
    db = Database(db_path)
    db.initialize()
    manager = MemoryManager(data_dir=tmp_path, database=db)

    yt_event = build_event(
        event_type="favorite",
        source_platform=SOURCE_YOUTUBE,
        title="Async Python",
        url="https://www.youtube.com/watch?v=yt1",
        author="Tech Teach",
        metadata={"vid": "yt1"},
    )
    asyncio.run(manager.propagate_event(yt_event))

    rows = db.get_recent_events(limit=5)
    assert len(rows) == 1
    assert rows[0]["context"] == yt_event["context"]
    assert not rows[0]["context"].startswith('"')


def test_event_db_round_trip_legacy_dict_context_still_works(tmp_path) -> None:
    """Legacy dict-shaped context must be JSON-encoded on storage."""
    db_path = tmp_path / "events.db"
    db = Database(db_path)
    db.initialize()

    legacy_dict_context = {"video_id": "yt1", "ts": 12345}
    db.insert_event(
        "click",
        title="legacy click",
        context=legacy_dict_context,
        metadata={"source_platform": "youtube"},
    )
    rows = db.get_recent_events(limit=5)
    assert rows
    decoded = json.loads(rows[0]["context"])
    assert decoded == legacy_dict_context


# ---------------------------------------------------------------------------
# classify_event_satisfaction


def test_classify_explicit_like_is_positive() -> None:
    category, reason = classify_event_satisfaction(
        {"event_type": "like", "metadata": {}}
    )
    assert category == "positive"
    assert reason == "explicit_engagement"


def test_classify_quick_exit_is_negative() -> None:
    category, reason = classify_event_satisfaction(
        {"event_type": "click", "metadata": {"watch_seconds": 2}}
    )
    assert category == "negative"
    assert reason == "quick_exit"


def test_classify_meaningful_dwell_is_positive() -> None:
    category, reason = classify_event_satisfaction(
        {
            "event_type": "click",
            "metadata": {
                "watch_seconds": 120,
                "video_duration_seconds": 300,
            },
        }
    )
    assert category == "positive"
    assert reason == "meaningful_dwell"
