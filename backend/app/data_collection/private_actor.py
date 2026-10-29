"""
Runs the private Apify actor `broker-intel` (actors/broker-intel) for the
sources the admin has switched on (source_settings keys: reddit, play_store,
app_store, youtube, linkedin). X stays on the X API connector.

Env: APIFY_TOKEN (secret), BROKER_INTEL_ACTOR (e.g. "<username>/broker-intel").
Skips cleanly if either is missing.
"""
from __future__ import annotations
import json, logging, os
from pathlib import Path
from typing import List, Optional

from app.data_collection.broker_registry import Registry

logger = logging.getLogger(__name__)
ACTOR_SOURCES = {"reddit", "play_store", "app_store", "youtube", "linkedin"}


def run_broker_intel(registry: Registry, days_back: int = 28, max_items: int = 30,
                     out_dir: Optional[Path] = None) -> List[dict]:
    token, actor = os.getenv("APIFY_TOKEN"), os.getenv("BROKER_INTEL_ACTOR")
    sources = sorted(registry.enabled_sources & ACTOR_SOURCES)
    if not token or not actor:
        logger.warning("broker-intel actor skipped: APIFY_TOKEN/BROKER_INTEL_ACTOR not set")
        return []
    if not sources:
        logger.info("broker-intel actor skipped: no actor sources enabled in admin")
        return []
    from apify_client import ApifyClient
    brokers = [dict(name=b.name, slug=b.slug, keywords=(b.search_keywords or [b.name]),
                    play_store_id=b.play_store_id, app_store_id=b.app_store_id,
                    youtube_query=f"{b.name} app review") for b in registry.brokers]
    run = ApifyClient(token).actor(actor).call(
        run_input={"sources": sources, "brokers": brokers, "daysBack": days_back,
                   "maxItemsPerSource": max_items, "topComments": 3, "useResidentialProxy": True},
        timeout_secs=1800, memory_mbytes=512)
    items = list(ApifyClient(token).dataset(run["defaultDatasetId"]).iterate_items())
    logger.info("broker-intel: %d items from %s", len(items), ",".join(sources))
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "broker_intel_items.json").write_text(json.dumps(items, ensure_ascii=False, default=str))
    return items
