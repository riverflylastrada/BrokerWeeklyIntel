#!/usr/bin/env python
"""
BrokerWeeklyIntel - Weekly Intelligence Run Script

This is the main entry point for the automated weekly collection.

It now uses the real Data Collection Layer.

Usage:
    # From project root
    python -m backend.scripts.run_weekly

    # Or directly
    python backend/scripts/run_weekly.py

Environment variables (optional):
    SUPABASE_URL / SUPABASE_KEY  # brokers + source toggles from admin DB
    BROKERS="Zerodha,Groww,Fyers"  # fallback list if DB unreachable
    DRY_RUN=true               # only resolve brokers/sources, no scraping
    REPORT_OUTPUT_DIR="./reports"
    ENABLE_APIFY=true          # Requires APIFY_API_TOKEN
    ENABLE_FIRECRAWL=true      # Requires FIRECRAWL_API_KEY
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure we can import the app package
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.data_collection.collector import run_weekly_collection
from app.data_collection.broker_registry import load_registry


async def main():
    print("=" * 70)
    print("🚀 BrokerWeeklyIntel - Weekly Intelligence Collection")
    print("=" * 70)

    # Determine the week (previous full Monday–Sunday by default)
    today = datetime.utcnow().date()
    days_since_monday = today.weekday()
    week_start = datetime.combine(
        today - timedelta(days=days_since_monday + 7), datetime.min.time()
    )
    week_end = week_start + timedelta(days=6)

    print(f"Week:           {week_start.date()} → {week_end.date()}")
    registry = load_registry(settings.brokers)
    brokers = registry.broker_names
    # Admin toggles gate the opt-in connectors (env flags must also allow them)
    use_apify = settings.enable_apify and bool(registry.enabled_sources & {"play_store", "app_store", "youtube", "x", "reddit"})
    use_firecrawl = settings.enable_firecrawl and bool(registry.enabled_sources & {"web", "news"})
    print(f"Broker source:  {registry.origin}")
    print(f"Brokers:        {', '.join(brokers)}")
    print(f"Sources on:     {', '.join(sorted(registry.enabled_sources))}")
    print(f"Apify/Firecrawl:{use_apify}/{use_firecrawl}")
    print(f"Environment:    {settings.environment}")
    print()

    if os.getenv("DRY_RUN", "").lower() in ("1", "true", "yes"):
        print("DRY_RUN set: skipping collection.")
        return

    try:
        # Run the real data collection using the new DataCollector
        # Advanced connectors (Apify / Firecrawl) are controlled via ENABLE_APIFY and ENABLE_FIRECRAWL
        result = await run_weekly_collection(
            week_start=week_start,
            week_end=week_end,
            brokers=brokers,
            use_apify=use_apify,
            use_firecrawl=use_firecrawl,
            # output_dir can be overridden via env if needed
        )

        print("\n✅ Collection completed successfully!")
        print("-" * 50)
        print(f"Run ID:         {result.run.run_id}")
        print(f"Raw results:    {result.run.total_raw_results}")
        print(f"Normalized:     {result.run.total_normalized_mentions}")
        print(f"Connectors:     {', '.join(result.run.sources_used)}")
        print(f"Errors:         {len(result.run.errors)}")

        if result.normalized_artifacts_path:
            print(f"\nArtifacts saved to:\n  {result.normalized_artifacts_path}")

        if result.run.errors:
            print("\n⚠️  Errors encountered:")
            for err in result.run.errors:
                print(f"  - {err}")

        # TODO (future):
        # - Pass result to Analysis Layer
        # - Generate Markdown + PDF report
        # - Store final WeeklyReport + v2.1 JSON snapshot

        print("\n" + "=" * 70)
        print("Next steps (to be implemented):")
        print("  1. Run analysis & scoring on collected data")
        print("  2. Generate BrokerWeeklyIntel report (Markdown + PDF)")
        print("  3. Save final snapshot to data/historical/")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
