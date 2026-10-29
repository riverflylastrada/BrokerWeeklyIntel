"""Weekly Bank Pulse run: Apify private actor (low and slow) -> score.py -> ingest-category-report edge function (upserts category_reports).
Env: APIFY_API_TOKEN, INGEST_URL, INGEST_TOKEN. Never log secrets."""
import json, os, subprocess, datetime as dt, urllib.request
from apify_client import ApifyClient
HERE = os.path.dirname(os.path.abspath(__file__))
inp = json.load(open(os.path.join(HERE, "input.json")))
# Low and slow is mandatory: concurrency 1, 8-15s jitter, 30s between banks, India residential proxy, reddit via RSS.
inp.update(maxConcurrency=1, minDelaySecs=max(8, inp.get("minDelaySecs", 8)), maxDelaySecs=max(15, inp.get("maxDelaySecs", 15)),
           pauseBetweenBrokersSecs=max(30, inp.get("pauseBetweenBrokersSecs", 30)), useResidentialProxy=True, redditMode="rss")
client = ApifyClient(os.environ["APIFY_API_TOKEN"])
run = client.actor("zippy_jogger/broker-intel").call(run_input=inp, timeout_secs=3 * 3600)
items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
json.dump(items, open(os.path.join(HERE, "items.json"), "w"))
subprocess.run(["python", "score.py"], cwd=HERE, check=True)
rep = json.load(open(os.path.join(HERE, "bank_report.json")))
# score.py sorts by unrounded overall, tie-break Complaints; keep ranks contiguous and in that order.
rep["banks"].sort(key=lambda b: b["rank"])
for i, b in enumerate(rep["banks"], 1): b["rank"] = i
week = dt.date.today().strftime("%G-W%V"); rep["week"] = week
req = urllib.request.Request(os.environ["INGEST_URL"],
    data=json.dumps({"category": "banks", "week": week, "report": rep}).encode(), method="POST",
    headers={"x-ingest-token": os.environ["INGEST_TOKEN"], "Content-Type": "application/json"})
urllib.request.urlopen(req, timeout=60)
print(f"banks {week}: {len(items)} items, {len(rep['banks'])} banks scored")
