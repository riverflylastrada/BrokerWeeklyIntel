"""Source fetchers. Each returns a list of normalized dicts:
source, broker, title, text, url, author, created_utc, score, num_comments, rating, subreddit"""
import time, re, json, random
from datetime import datetime, timezone, timedelta
import httpx

UA = "BrokerWeeklyIntel/0.1 (public research; contact via GitHub riverflylastrada/BrokerWeeklyIntel)"

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

DELAY = (8.0, 15.0)          # low and slow: randomized delay between requests
BACKOFF = (60, 120, 300)     # exponential-ish backoff on HTTP 429

def pause():
    time.sleep(random.uniform(*DELAY))

def get_polite(client, url, **kw):
    """Single request with randomized delay and 429 backoff (concurrency 1)."""
    r = client.get(url, **kw); pause()
    for wait in BACKOFF:
        if r.status_code != 429: break
        time.sleep(wait)
        r = client.get(url, **kw); pause()
    return r

def _cutoff(days): return (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()

def reddit(client, broker, subreddits, days, limit, top_comments, sleep=2.0):
    out, cut = [], _cutoff(days)
    subs = "+".join(subreddits)
    for kw in broker.get("keywords") or [broker["name"]]:
        params = {"q": kw, "restrict_sr": 1, "sort": "new", "t": "month", "limit": min(limit, 100), "raw_json": 1}
        r = None
        for host in ("https://www.reddit.com", "https://old.reddit.com", "https://api.reddit.com"):
            for ua in (UA, BROWSER_UA):
                r = get_polite(client, f"{host}/r/{subs}/search.json" if "api." not in host else f"{host}/r/{subs}/search", params=params, headers={"User-Agent": ua})
                if r.status_code == 200: break
            if r.status_code == 200: break
        r.raise_for_status()
        for c in r.json()["data"]["children"]:
            d = c["data"]
            if d["created_utc"] < cut: continue
            item = dict(source="reddit", broker=broker["name"], title=d["title"], text=(d.get("selftext") or "")[:2000],
                        url="https://www.reddit.com" + d["permalink"], author=d.get("author"), subreddit=d["subreddit"],
                        created_utc=d["created_utc"], score=d["score"], num_comments=d["num_comments"], comments=[])
            if top_comments and d["num_comments"]:
                cr = get_polite(client, f"https://old.reddit.com{d['permalink']}.json", params={"sort": "top", "limit": top_comments})
                if cr.status_code == 200:
                    for cc in cr.json()[1]["data"]["children"][:top_comments]:
                        if cc["kind"] == "t1":
                            item["comments"].append(dict(text=cc["data"]["body"][:600], score=cc["data"]["score"],
                                                         url="https://www.reddit.com" + cc["data"]["permalink"]))
            out.append(item)
    seen = set(); return [i for i in out if not (i["url"] in seen or seen.add(i["url"]))][:limit]

def play_store(broker, days, limit):
    from google_play_scraper import reviews, Sort
    if not broker.get("play_store_id"): return []
    rv, _ = reviews(broker["play_store_id"], lang="en", country="in", sort=Sort.NEWEST, count=limit)
    cut = _cutoff(days); app = broker["play_store_id"]
    return [dict(source="play_store", broker=broker["name"], title="", text=x["content"][:2000], rating=x["score"],
                 url=f"https://play.google.com/store/apps/details?id={app}&reviewId={x['reviewId']}",
                 author=None, created_utc=x["at"].replace(tzinfo=timezone.utc).timestamp(), score=x["thumbsUpCount"], num_comments=0)
            for x in rv if x["at"].replace(tzinfo=timezone.utc).timestamp() >= cut]

def app_store(client, broker, days, limit):
    aid = broker.get("app_store_id")
    if not aid: return []
    out, cut = [], _cutoff(days)
    for page in (1, 2):
        r = get_polite(client, f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={aid}/sortby=mostrecent/json")
        if r.status_code != 200:
            print(f"app_store {broker['name']} p{page}: HTTP {r.status_code}"); break
        for e in r.json().get("feed", {}).get("entry", [])[1 if page == 1 else 0:]:
            if "im:rating" not in e: continue
            ts = datetime.fromisoformat(e["updated"]["label"]).timestamp()
            if ts < cut: continue
            out.append(dict(source="app_store", broker=broker["name"], title=e["title"]["label"], text=e["content"]["label"][:2000],
                            rating=int(e["im:rating"]["label"]), url=f"https://apps.apple.com/in/app/id{aid}?see-all=reviews",
                            author=e["author"]["name"]["label"], created_utc=ts, score=0, num_comments=0))
    return out[:limit]

def youtube(broker, days, limit, videos=3):
    """Comments on recent videos matching the broker query (no API key; uses public pages)."""
    from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
    q = broker.get("youtube_query") or f"{broker['name']} app review"
    html = httpx.get("https://www.youtube.com/results", params={"search_query": q, "sp": "CAI%3D"},
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=20).text
    ids = list(dict.fromkeys(re.findall(r'"videoId":"([\w-]{11})"', html)))[:videos]
    dl, out = YoutubeCommentDownloader(), []
    per = max(1, limit // max(1, len(ids)))
    for vid in ids:
        for i, c in enumerate(dl.get_comments_from_url(f"https://www.youtube.com/watch?v={vid}", sort_by=SORT_BY_POPULAR)):
            if i >= per: break
            out.append(dict(source="youtube", broker=broker["name"], title=vid, text=c["text"][:1500],
                            url=f"https://www.youtube.com/watch?v={vid}&lc={c['cid']}", author=c.get("author"),
                            created_utc=c.get("time_parsed"), score=int(str(c.get("votes") or 0).replace(",", "") or 0) if str(c.get("votes") or "0").replace(",", "").isdigit() else 0,
                            num_comments=0))
    return out

def linkedin(client, broker, limit):
    """Public company page only (no login). LinkedIn usually serves an auth wall; we report that instead of bypassing it."""
    slug = broker.get("linkedin_slug")
    if not slug: return []
    r = get_polite(client, f"https://www.linkedin.com/company/{slug}/")
    if r.status_code != 200 or "authwall" in str(r.url) or "Sign in" in r.text[:5000]:
        return [dict(source="linkedin", broker=broker["name"], title="BLOCKED", text=f"LinkedIn auth wall (HTTP {r.status_code}); public data not available without login",
                     url=f"https://www.linkedin.com/company/{slug}/", author=None, created_utc=None, score=0, num_comments=0)]
    posts = re.findall(r'"commentary":\{"text":\{"text":"(.*?)"', r.text)[:limit]
    if not posts:
        return [dict(source="linkedin", broker=broker["name"], title="NO_PUBLIC_POSTS", text="Public company page has no posts without login",
                     url=f"https://www.linkedin.com/company/{slug}/", author=None, created_utc=None, score=0, num_comments=0)]
    return [dict(source="linkedin", broker=broker["name"], title="", text=p[:1500], url=f"https://www.linkedin.com/company/{slug}/",
                 author=slug, created_utc=None, score=0, num_comments=0) for p in posts]


def reddit_rss(client, broker, subreddits, days, limit, top_comments, sleep=2.0):
    """Fallback when Reddit's JSON API returns 403: public Atom feeds (no score/num_comments)."""
    import xml.etree.ElementTree as ET, html as H
    ns = {"a": "http://www.w3.org/2005/Atom"}
    strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", H.unescape(s or ""))).strip()
    out, cut, seen = [], _cutoff(days), set()
    for sub in subreddits:
        for kw in broker.get("keywords") or [broker["name"]]:
            r = get_polite(client, f"https://www.reddit.com/r/{sub}/search.rss",
                           params={"q": kw, "restrict_sr": 1, "sort": "new", "t": "month", "limit": 25},
                           headers={"User-Agent": BROWSER_UA})
            if r.status_code != 200: continue
            for e in ET.fromstring(r.text).findall("a:entry", ns):
                url = e.find("a:link", ns).attrib["href"]
                ts = datetime.fromisoformat(e.find("a:updated", ns).text).timestamp()
                if url in seen or ts < cut: continue
                seen.add(url)
                body = strip((e.find("a:content", ns).text if e.find("a:content", ns) is not None else ""))
                body = re.sub(r"submitted by .*$", "", body).strip()
                item = dict(source="reddit", broker=broker["name"], title=e.find("a:title", ns).text, text=body[:2000], url=url,
                            author=(e.find("a:author/a:name", ns).text if e.find("a:author/a:name", ns) is not None else None),
                            subreddit=sub, created_utc=ts, score=None, num_comments=None, comments=[])
                if top_comments:
                    cr = get_polite(client, url.rstrip("/") + "/.rss", params={"sort": "top", "limit": top_comments + 1}, headers={"User-Agent": BROWSER_UA})
                    if cr.status_code == 200:
                        for ce in ET.fromstring(cr.text).findall("a:entry", ns)[1:top_comments + 1]:
                            item["comments"].append(dict(text=strip(ce.find("a:content", ns).text)[:600], url=ce.find("a:link", ns).attrib["href"]))
                out.append(item)
    return out[:limit]
