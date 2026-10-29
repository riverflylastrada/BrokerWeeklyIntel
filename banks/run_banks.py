"""Weekly Bank Pulse run: Apify private actor (low and slow) -> score.py -> ingest-category-report edge function (upserts category_reports).
Env: APIFY_API_TOKEN, INGEST_URL, INGEST_TOKEN. Never log secrets."""
import json, os, random, subprocess, sys, time, datetime as dt, urllib.request
from apify_client import ApifyClient
HERE = os.path.dirname(os.path.abspath(__file__))
inp = json.load(open(os.path.join(HERE, "input.json")))
# Low and slow is mandatory: concurrency 1, 8-15s jitter, 30s between banks, India residential proxy, reddit via RSS.
inp.update(maxConcurrency=1, minDelaySecs=max(8, inp.get("minDelaySecs", 8)), maxDelaySecs=max(15, inp.get("maxDelaySecs", 15)),
           pauseBetweenBrokersSecs=max(30, inp.get("pauseBetweenBrokersSecs", 30)), useResidentialProxy=True, redditMode="rss")
client = ApifyClient(os.environ["APIFY_API_TOKEN"])
run = client.actor("zippy_jogger/broker-intel").call(run_input=inp, timeout_secs=3 * 3600)
items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

# App Store backfill. Apple's public review RSS intermittently returns non-200/empty to the actor's
# Apify IP (W44 run: 9/12 banks got 0, silently). Retry here from the runner, low and slow.
def app_store_rss(b, days=inp.get("daysBack", 30), limit=inp.get("maxItemsPerSource", 30)):
    aid, out = b.get("app_store_id"), []
    if not aid: return out
    cut = time.time() - days * 86400
    for page in (1, 2):
        entries = None
        for attempt in range(4):
            time.sleep(random.uniform(8, 15) * (1 + attempt))
            try:
                r = urllib.request.urlopen(urllib.request.Request(
                    f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={aid}/sortby=mostrecent/json",
                    headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
                entries = json.load(r).get("feed", {}).get("entry", [])
                if entries: break
            except Exception as e:
                print(f"WARN app_store {b['slug']} p{page} attempt {attempt+1}: {type(e).__name__}")
        for e in (entries or []):
            if "im:rating" not in e: continue
            ts = dt.datetime.fromisoformat(e["updated"]["label"]).timestamp()
            if ts < cut: continue
            out.append(dict(source="app_store", broker=b["name"], title=e["title"]["label"], text=e["content"]["label"][:2000],
                            rating=int(e["im:rating"]["label"]), url=f"https://apps.apple.com/in/app/id{aid}?see-all=reviews",
                            author=e["author"]["name"]["label"], created_utc=ts, score=0, num_comments=0))
    return out[:limit]

have = {(i.get("broker"), i.get("source")) for i in items}
for b in inp["brokers"]:
    if (b["name"], "app_store") not in have:
        extra = app_store_rss(b); items += extra
        print(f"app_store backfill {b['slug']}: {len(extra)}")
        time.sleep(30)
json.dump(items, open(os.path.join(HERE, "items.json"), "w"))
subprocess.run(["python", "score.py"], cwd=HERE, check=True)
rep = json.load(open(os.path.join(HERE, "bank_report.json")))
# score.py sorts by unrounded overall, tie-break Complaints; keep ranks contiguous and in that order.
rep["banks"].sort(key=lambda b: b["rank"])
for i, b in enumerate(rep["banks"], 1): b["rank"] = i
week = dt.date.today().strftime("%G-W%V"); rep["week"] = week

# Publish guard: compare with the last published report (banks/last_published.json, committed by the workflow).
LAST = os.path.join(HERE, "last_published.json")
if os.path.exists(LAST):
    prev = {b["slug"]: b["counts"] for b in json.load(open(LAST))["banks"]}
    problems = []
    for b in rep["banks"]:
        for src, n in (prev.get(b["slug"]) or {}).items():
            if n > 0 and b["counts"].get(src, 0) == 0: problems.append(f"{b['slug']}/{src}: {n} -> 0")
    tot_prev = sum(sum(c.values()) for c in prev.values()); tot_now = sum(sum(b["counts"].values()) for b in rep["banks"])
    if tot_prev and tot_now < 0.6 * tot_prev: problems.append(f"total data points {tot_prev} -> {tot_now} (>40% drop)")
    if len(rep["banks"]) < len(prev): problems.append(f"banks {len(prev)} -> {len(rep['banks'])}")
    if problems:
        print("::warning::Bank report NOT published; previous report kept. " + "; ".join(problems))
        sys.exit(0)
req = urllib.request.Request(os.environ["INGEST_URL"],
    data=json.dumps({"category": "banks", "week": week, "report": rep}).encode(), method="POST",
    headers={"x-ingest-token": os.environ["INGEST_TOKEN"], "Content-Type": "application/json"})
urllib.request.urlopen(req, timeout=60)
json.dump({"week": week, "banks": [{"slug": b["slug"], "counts": b["counts"]} for b in rep["banks"]]}, open(LAST, "w"), indent=1)
print(f"banks {week}: {len(items)} items, {len(rep['banks'])} banks scored")
