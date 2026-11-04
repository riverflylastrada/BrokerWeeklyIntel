from apify import Actor
import httpx
from . import sources as S
from . import mentions as M
import time

async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        srcs = set(inp.get("sources") or ["reddit", "play_store", "app_store", "youtube"])
        days, lim = int(inp.get("daysBack", 28)), int(inp.get("maxItemsPerSource", 30))
        proxy_url = None
        if inp.get("useResidentialProxy", True) and srcs & {"reddit", "linkedin"}:
            try:
                pc = await Actor.create_proxy_configuration(groups=["RESIDENTIAL"], country_code="IN")
                proxy_url = await pc.new_url() if pc else None
                Actor.log.info(f"Proxy: {'RESIDENTIAL/IN' if proxy_url else 'none'}")
            except Exception as e:
                Actor.log.warning(f"Residential proxy unavailable ({type(e).__name__}); using direct connection")
        web = httpx.Client(headers={"User-Agent": S.UA}, timeout=30, follow_redirects=True, proxy=proxy_url)
        plain = httpx.Client(headers={"User-Agent": S.UA}, timeout=30)
        S.DELAY = (float(inp.get("minDelaySecs", 8)), float(inp.get("maxDelaySecs", 15)))
        pause_between = int(inp.get("pauseBetweenBrokersSecs", 30))
        stats = {}
        if inp.get("redditMode") == "rss": stats["_reddit_json_blocked"] = 1
        import asyncio
        mode = inp.get("mode") or "weekly"
        category = inp.get("category") or "brokers"
        state_store = await Actor.open_key_value_store(name="social-listening-state") if mode == "mentions" else None
        state = (await state_store.get_value(category) or {}) if state_store else {}
        cutoff = time.time() - days * 86400
        all_rows, new_state = [], dict(state)
        for n, b in enumerate(inp.get("brokers", [])):
            if n: await asyncio.sleep(pause_between)  # sequential, one broker at a time
            for src in sorted(srcs):
                try:
                    if src == "reddit" and mode == "mentions":
                        subs = inp.get("subreddits") or ["IndianStreetBets", "IndiaInvestments", "IndianStockMarket"]
                        items = S.reddit_rss_multi(web, b, subs, days, lim)
                    elif src == "reddit":
                        subs = inp.get("subreddits") or ["IndianStreetBets", "IndiaInvestments", "IndianStockMarket"]
                        items = None
                        if not stats.get("_reddit_json_blocked"):
                            try:
                                items = S.reddit(web, b, subs, days, lim, int(inp.get("topComments", 3)))
                            except Exception as e:
                                Actor.log.info(f"Reddit JSON blocked ({type(e).__name__}); using RSS for the rest of the run")
                                stats["_reddit_json_blocked"] = 1
                        if items is None:
                            items = S.reddit_rss(web, b, subs, days, lim, int(inp.get("topComments", 3)))
                    elif src == "play_store": items = S.play_store(b, days, lim); S.pause()
                    elif src == "app_store": items = S.app_store(plain, b, days, lim)
                    elif src == "youtube": items = S.youtube(b, days, lim)
                    elif src == "linkedin": items = S.linkedin(web, b, lim)
                    else: continue
                except Exception as e:
                    Actor.log.warning(f"{b.get('name')}/{src} failed: {type(e).__name__}: {str(e)[:200]}")
                    items = [dict(source=src, broker=b.get("name"), title="ERROR", text=f"{type(e).__name__}", url=None)]
                stats[f"{b.get('slug')}/{src}"] = len(items)
                if mode == "mentions":
                    key = f"{b.get('slug')}/{src}"
                    rows, newest = M.to_rows(items, b.get("slug"), b.get("name"), cutoff, state.get(key))
                    if newest: new_state[key] = newest
                    stats[key] = len(rows)
                    all_rows += rows
                    if rows: await Actor.push_data(rows)
                elif items: await Actor.push_data(items)
        if mode == "mentions":
            res = {"received": len(all_rows), "inserted": 0, "alerts": 0}
            if all_rows and inp.get("ingestUrl") and inp.get("ingestToken"):
                res = M.post(inp["ingestUrl"], inp.get("ingestApiKey") or "", inp["ingestToken"], category,
                             Actor.configuration.actor_run_id or "local", inp.get("trigger") or "apify-schedule", all_rows)
            elif inp.get("ingestUrl") and inp.get("ingestToken"):  # still record the run so the backup cron sees it
                res = M.post(inp["ingestUrl"], inp.get("ingestApiKey") or "", inp["ingestToken"], category,
                             Actor.configuration.actor_run_id or "local", inp.get("trigger") or "apify-schedule", [])
            await state_store.set_value(category, new_state)  # only after a successful post
            pos = sum(r["sentiment"] == "positive" for r in all_rows); neg = sum(r["sentiment"] == "negative" for r in all_rows)
            stats["_ingest"] = {**res, "positive": pos, "negative": neg, "neutral": len(all_rows) - pos - neg}
        await Actor.set_value("STATS", stats)
        Actor.log.info(f"Done: {stats}")
