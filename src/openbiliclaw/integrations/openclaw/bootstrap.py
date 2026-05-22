"""Dependency bootstrap for the OpenClaw adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openbiliclaw.config import Config, load_config
from openbiliclaw.discovery.engine import ContentDiscoveryEngine, DiscoveryConcurrencyController
from openbiliclaw.discovery.strategies.youtube import (
    YoutubeChannelStrategy,
    YoutubeSearchStrategy,
    YoutubeTrendingStrategy,
)
from openbiliclaw.llm import build_llm_registry
from openbiliclaw.llm.service import LLMService, module_overrides_from_config
from openbiliclaw.memory.manager import MemoryManager
from openbiliclaw.recommendation.curator import PoolCurator
from openbiliclaw.recommendation.engine import RecommendationEngine
from openbiliclaw.runtime.account_sync import AccountSyncService
from openbiliclaw.runtime.presence import PresenceTracker
from openbiliclaw.runtime.refresh import ContinuousRefreshController
from openbiliclaw.runtime.source_policy import effective_pool_source_shares
from openbiliclaw.soul.engine import SoulEngine
from openbiliclaw.storage.database import Database
from openbiliclaw.youtube.client import YtScraperClient

from .operations import OpenClawAdapter


@dataclass(slots=True)
class OpenClawAdapterServices:
    """Shared services bundle used by the OpenClaw adapter."""

    config: Config | Any
    database: Database | Any
    memory_manager: MemoryManager | Any
    soul_engine: SoulEngine | Any
    llm_service: LLMService | Any
    discovery_engine: ContentDiscoveryEngine | Any
    recommendation_engine: RecommendationEngine | Any
    runtime_controller: ContinuousRefreshController | Any
    account_sync_service: AccountSyncService | Any


def build_openclaw_adapter_services() -> OpenClawAdapterServices:
    """Build the shared service bundle for the OpenClaw adapter."""
    config = load_config()
    llm_registry = build_llm_registry(config)
    module_overrides = module_overrides_from_config(config)

    database = Database(config.data_path / "openbiliclaw.db")
    database.initialize()

    memory_manager = MemoryManager(config.data_path, database=database)
    memory_manager.initialize()

    soul_engine = SoulEngine(
        llm=llm_registry,
        memory=memory_manager,
        module_overrides=module_overrides,
    )
    llm_service = LLMService(
        registry=llm_registry,
        memory=memory_manager,
        module_overrides=module_overrides,
    )
    from openbiliclaw.llm.registry import build_embedding_service

    embedding_service = build_embedding_service(config, llm_registry)

    curator = PoolCurator(database)
    recommendation_engine = RecommendationEngine(
        llm=llm_service,
        database=database,
        curator=curator,
        embedding_service=embedding_service,
    )

    yt_client = YtScraperClient()
    concurrency = DiscoveryConcurrencyController(
        llm_evaluation_concurrency=4,
        search_budget_total=30,
    )
    discovery_engine = ContentDiscoveryEngine(
        llm_service=llm_service,
        database=database,
        embedding_service=embedding_service,
        concurrency=concurrency,
    )
    discovery_engine.register_strategy(
        YoutubeSearchStrategy(
            client=yt_client,
            llm_service=llm_service,
            concurrency=concurrency,
        )
    )
    discovery_engine.register_strategy(
        YoutubeTrendingStrategy(
            client=yt_client,
            llm_service=llm_service,
            concurrency=concurrency,
        )
    )
    discovery_engine.register_strategy(
        YoutubeChannelStrategy(
            client=yt_client,
            llm_service=llm_service,
            memory=memory_manager,
            concurrency=concurrency,
        )
    )

    presence = PresenceTracker()
    runtime_controller = ContinuousRefreshController(
        memory_manager=memory_manager,
        database=database,
        soul_engine=soul_engine,
        discovery_engine=discovery_engine,
        recommendation_engine=recommendation_engine,
        pool_target_count=config.scheduler.pool_target_count,
        pool_source_shares=effective_pool_source_shares(config),
        scheduler_config=config.scheduler,
        presence=presence,
    )
    account_sync_service = AccountSyncService(
        memory_manager=memory_manager,
    )

    return OpenClawAdapterServices(
        config=config,
        database=database,
        memory_manager=memory_manager,
        soul_engine=soul_engine,
        llm_service=llm_service,
        discovery_engine=discovery_engine,
        recommendation_engine=recommendation_engine,
        runtime_controller=runtime_controller,
        account_sync_service=account_sync_service,
    )


def build_openclaw_adapter() -> OpenClawAdapter:
    """Build a ready-to-use OpenClaw adapter."""
    return OpenClawAdapter(services=build_openclaw_adapter_services())
