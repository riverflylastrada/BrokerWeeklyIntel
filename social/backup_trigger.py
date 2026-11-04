"""GitHub Actions backup for twice-daily social listening. Apify schedules are primary (brokers 8:00, banks 8:40, pms 9:20 IST, AM and PM).
If the Apify task has no healthy run since the current window start, start it once. Env: APIFY_API_TOKEN, CATEGORY."""
import json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone
TASKS = {"brokers": "zippy_jogger~social-buzz-brokers", "banks": "zippy_jogger~social-buzz-banks", "pms": "zippy_jogger~social-buzz-pms"}
IST = timezone(timedelta(hours=5, minutes=30))
tok, cat = os.environ["APIFY_API_TOKEN"], os.environ["CATEGORY"]
def api(method, path, body=None):
    req = urllib.request.Request("https://api.apify.com/v2" + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))["data"]
now = datetime.now(IST)
h0 = 9 if cat == "pms" else 8  # pms task runs 09:20 / 21:20 IST
start = now.replace(hour=h0 + 12 if now.hour >= h0 + 12 else h0, minute=0, second=0, microsecond=0)
if now.hour < h0: start = (now - timedelta(days=1)).replace(hour=h0 + 12, minute=0, second=0, microsecond=0)
runs = api("GET", f"/actor-tasks/{TASKS[cat]}/runs?desc=1&limit=5")["items"]
ok = [r for r in runs if datetime.fromisoformat(r["startedAt"].replace("Z", "+00:00")) >= start
      and r["status"] in ("READY", "RUNNING", "SUCCEEDED")]
if ok:
    print(f"{cat}: run {ok[0]['id']} ({ok[0]['status']}) already in window from {start:%Y-%m-%d %H:%M} IST; no-op"); sys.exit(0)
r = api("POST", f"/actor-tasks/{TASKS[cat]}/runs", {"trigger": "github-backup"})
print(f"{cat}: no run since {start:%Y-%m-%d %H:%M} IST; started backup run {r['id']}")
