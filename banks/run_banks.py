"""Weekly Bank Pulse run: Apify private actor (low and slow) -> score.py -> Supabase category_reports.
Env: APIFY_API_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY. Never log secrets."""
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
week = dt.date.today().strftime("%G-W%V"); rep["week"] = week
req = urllib.request.Request(os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/category_reports?on_conflict=category,week",
    data=json.dumps([{"category": "banks", "week": week, "report": rep}]).encode(), method="POST",
    headers={"apikey": os.environ["SUPABASE_SERVICE_ROLE_KEY"], "Authorization": "Bearer " + os.environ["SUPABASE_SERVICE_ROLE_KEY"],
             "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
urllib.request.urlopen(req, timeout=60)
print(f"banks {week}: {len(items)} items, {len(rep['banks'])} banks scored")
