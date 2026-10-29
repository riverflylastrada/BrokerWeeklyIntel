"""
Broker registry: loads ACTIVE brokers and enabled data sources from the
BrokerPulse (Lovable Cloud / Supabase) database via its REST API.

Env vars (set as GitHub Actions secrets, never committed):
    SUPABASE_URL  - e.g. https://<project-ref>.supabase.co
    SUPABASE_KEY  - anon/publishable key (read-only via RLS) is sufficient

If the vars are missing or the DB is unreachable, falls back to the
hardcoded defaults in settings.brokers with all core sources enabled.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional, Set

import httpx

logger = logging.getLogger(__name__)

DEFAULT_SOURCES: Set[str] = {"x", "reddit", "web"}


@dataclass
class BrokerProfile:
    name: str
    slug: str = ""
    website: Optional[str] = None
    x_handle: Optional[str] = None
    app_store_id: Optional[str] = None
    play_store_id: Optional[str] = None
    search_keywords: List[str] = field(default_factory=list)
    reddit_keywords: List[str] = field(default_factory=list)


@dataclass
class Registry:
    brokers: List[BrokerProfile]
    enabled_sources: Set[str]
    origin: str  # "supabase" or "fallback"

    @property
    def broker_names(self) -> List[str]:
        return [b.name for b in self.brokers]


def _fallback(default_names: List[str], reason: str) -> Registry:
    logger.warning("Broker registry fallback (%s); using hardcoded list", reason)
    return Registry(
        brokers=[BrokerProfile(name=n, slug=n.lower().replace(" ", "-")) for n in default_names],
        enabled_sources=set(DEFAULT_SOURCES),
        origin=f"fallback: {reason}",
    )


def load_registry(default_names: List[str], timeout: float = 10.0) -> Registry:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        return _fallback(default_names, "SUPABASE_URL/SUPABASE_KEY not set")

    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    try:
        with httpx.Client(base_url=f"{url}/rest/v1", headers=headers, timeout=timeout) as c:
            b = c.get("/brokers", params={
                "select": "name,slug,website,x_handle,app_store_id,play_store_id,search_keywords,reddit_keywords",
                "active": "eq.true", "order": "name.asc",
            })
            b.raise_for_status()
            s = c.get("/source_settings", params={"select": "key", "enabled": "eq.true"})
            s.raise_for_status()
    except Exception as e:  # network, auth, schema errors
        return _fallback(default_names, f"DB unreachable: {type(e).__name__}")

    rows = b.json() or []
    if not rows:
        return _fallback(default_names, "no active brokers in DB")

    brokers = [
        BrokerProfile(
            name=r["name"], slug=r.get("slug") or "",
            website=r.get("website"), x_handle=r.get("x_handle"),
            app_store_id=r.get("app_store_id"), play_store_id=r.get("play_store_id"),
            search_keywords=r.get("search_keywords") or [],
            reddit_keywords=r.get("reddit_keywords") or [],
        )
        for r in rows
    ]
    sources = {r["key"] for r in (s.json() or [])}
    return Registry(brokers=brokers, enabled_sources=sources, origin="supabase")
