"""Backfill collector: dated Play Store (all entities) + App Store RSS (banks) reviews back to a cutoff.
Low and slow: one request at a time, random 8-15s between pages, 30s between apps, exponential backoff on errors/429."""
import json, os, random, sys, time, datetime as dt, urllib.request
from google_play_scraper import reviews, Sort
CUT = dt.datetime(2026, 8, 31)  # Monday of ISO 2026-W36
MAXPAGES = int(os.getenv("MAXPAGES", "25"))
OUT = sys.argv[1]
ents = json.load(open(sys.argv[2]))
done = json.load(open(OUT)) if os.path.exists(OUT) else {}
nap = lambda m=1: time.sleep(random.uniform(8, 15) * m)
def play(app):
    out, tok = [], None
    for p in range(MAXPAGES):
        for a in range(4):
            try:
                rv, tok = reviews(app, lang="en", country="in", sort=Sort.NEWEST, count=200, continuation_token=tok); break
            except Exception as e:
                print("  backoff", app, type(e).__name__, flush=True); nap(4 * (a + 1)); rv = []
        out += [dict(source="play_store", rating=x["score"], text=x["content"] or "", at=x["at"].isoformat(), thumbs=x["thumbsUpCount"]) for x in rv]
        if not rv or rv[-1]["at"] < CUT or tok is None: break
        nap()
    return out
def appstore(aid):
    out = []
    for page in range(1, 11):
        es = None
        for a in range(4):
            nap(1 + a)
            try:
                es = json.load(urllib.request.urlopen(urllib.request.Request(f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={aid}/sortby=mostrecent/json", headers={"User-Agent": "Mozilla/5.0"}), timeout=30)).get("feed", {}).get("entry", [])
                break
            except Exception as e: print("  as backoff", aid, type(e).__name__, flush=True)
        es = [e for e in (es or []) if "im:rating" in e]
        out += [dict(source="app_store", rating=int(e["im:rating"]["label"]), text=e["content"]["label"][:2000], title=e["title"]["label"], at=e["updated"]["label"][:19], thumbs=0) for e in es]
        if not es or es[-1]["updated"]["label"][:10] < CUT.date().isoformat(): break
    return out
for e in ents:
    if e["slug"] in done: continue
    r = play(e["play_store_id"]) if e.get("play_store_id") else []
    if e.get("app_store_id"): r += appstore(e["app_store_id"])
    done[e["slug"]] = dict(name=e["name"], reviews=r)
    json.dump(done, open(OUT, "w"))
    print(e["slug"], len(r), min((x["at"] for x in r), default=None), flush=True)
    time.sleep(30)
