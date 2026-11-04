"""Weekly PMS Pulse: (monthly) SEBI refresh -> Apify sentiment (low and slow) -> score.py -> ingest (category=pms).
Env: APIFY_API_TOKEN, INGEST_URL, INGEST_TOKEN. Never log secrets."""
import json, os, subprocess, sys, datetime as dt, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(HERE, "pms_list.json")))
# SEBI monthly data: fetch_sebi.py only pulls months not yet stored, so weekly calls are cheap; failures keep the committed data.
subprocess.run([sys.executable, "-u", "fetch_sebi.py"], cwd=HERE)
items = []
if os.getenv("APIFY_API_TOKEN"):
    try:
        from apify_client import ApifyClient
        inp = dict(sources=["reddit", "youtube"], daysBack=30, maxItemsPerSource=15, maxConcurrency=1, minDelaySecs=10, maxDelaySecs=20,
                   pauseBetweenBrokersSecs=30, useResidentialProxy=True, redditMode="rss",
                   brokers=[dict(name=p["name"], slug=p["slug"], keywords=[p["name"] + " PMS"], youtube_query=p["name"] + " PMS review") for p in meta])
        c = ApifyClient(os.environ["APIFY_API_TOKEN"])
        run = c.actor("zippy_jogger/broker-intel").call(run_input=inp, timeout_secs=2 * 3600)
        items = list(c.dataset(run["defaultDatasetId"]).iterate_items())
    except Exception as e:
        print(f"::warning::PMS sentiment scrape failed ({type(e).__name__}); scoring with neutral sentiment")
json.dump(items, open(os.path.join(HERE, "items.json"), "w"))
subprocess.run([sys.executable, "score.py"], cwd=HERE, check=True)
subprocess.run([sys.executable, "build_site_data.py"], cwd=HERE, check=True)
rep = json.load(open(os.path.join(HERE, "pms_report.json"))); week = rep["week"]
if len(rep["pms"]) < 10:
    print(f"::warning::PMS report NOT published: only {len(rep['pms'])} providers scored"); sys.exit(0)
req = urllib.request.Request(os.environ["INGEST_URL"], data=json.dumps({"category": "pms", "week": week, "report": rep}).encode(), method="POST",
    headers={"x-ingest-token": os.environ["INGEST_TOKEN"], "Content-Type": "application/json"})
print("ingest", urllib.request.urlopen(req, timeout=60).status)
print(f"pms {week}: {len(items)} social items, {len(rep['pms'])} PMS scored")
