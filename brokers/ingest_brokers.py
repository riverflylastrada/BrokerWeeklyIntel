"""POST the latest broker week (data/historical) to the site ingest route (category=brokers -> weekly_reports).
Env: INGEST_URL, INGEST_TOKEN. Usage: python brokers/ingest_brokers.py [report.json]. Never logs secrets."""
import glob, json, os, sys, urllib.request
path = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob("data/historical/BrokerWeeklyIntel-20??-W??.json"))[-1]
rep = json.load(open(path)); rep.pop("official_complaints_data", None) if os.getenv("SLIM") == "1" else None
req = urllib.request.Request(os.environ["INGEST_URL"], method="POST",
    data=json.dumps({"category": "brokers", "week": rep["week"], "report": rep}, ensure_ascii=False).encode(),
    headers={"x-ingest-token": os.environ["INGEST_TOKEN"], "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60) as r: print("brokers", rep["week"], r.status, r.read().decode()[:200])
