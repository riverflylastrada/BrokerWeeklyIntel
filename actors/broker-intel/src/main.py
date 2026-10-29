from apify import Actor
import httpx
from . import sources as S

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
        stats = {}
        for b in inp.get("brokers", []):
            for src in sorted(srcs):
                try:
                    if src == "reddit":
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
                    elif src == "play_store": items = S.play_store(b, days, lim)
                    elif src == "app_store": items = S.app_store(plain, b, days, lim)
                    elif src == "youtube": items = S.youtube(b, days, lim)
                    elif src == "linkedin": items = S.linkedin(web, b, lim)
                    else: continue
                except Exception as e:
                    Actor.log.warning(f"{b.get('name')}/{src} failed: {type(e).__name__}: {str(e)[:200]}")
                    items = [dict(source=src, broker=b.get("name"), title="ERROR", text=f"{type(e).__name__}", url=None)]
                stats[f"{b.get('slug')}/{src}"] = len(items)
                if items: await Actor.push_data(items)
        await Actor.set_value("STATS", stats)
        Actor.log.info(f"Done: {stats}")
