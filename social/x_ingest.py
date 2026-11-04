"""Ingest X (Twitter) search results into social_mentions (source='x').
Input: JSON files from Grok Bot's free public X search (search_posts_all), one per category, passed as CATEGORY=path args.
Entity is matched by the same keywords the Apify social-buzz tasks use (social/entities.jsonl). Ingest credentials are
URL/publishable key come from the Apify task input; the X ingest token from X_INGEST_TOKEN or ~/.config/paisainsights/x_ingest_token (never printed). Usage: python x_ingest.py brokers=a.json banks=b.json pms=c.json"""
import json, os, re, sys, urllib.request
from datetime import datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "actors", "broker-intel"))
from src.mentions import classify
ENT = {json.loads(l)["category"]: json.loads(l)["entities"] for l in open(os.path.join(HERE, "entities.jsonl"))}
TASK = {"brokers": "zippy_jogger~social-buzz-brokers", "banks": "zippy_jogger~social-buzz-banks", "pms": "zippy_jogger~social-buzz-pms"}
tok = os.environ["APIFY_TOKEN"]
X_TOKEN = os.environ.get("X_INGEST_TOKEN") or open(os.path.expanduser("~/.config/paisainsights/x_ingest_token")).read().strip()  # separate token (ingest_tokens.social-mentions-x)
def load(p):
    t = open(p).read(); t = t[t.index("{"):t.rindex("}") + 1]; return json.loads(t)
def creds(cat):
    r = urllib.request.Request(f"https://api.apify.com/v2/actor-tasks/{TASK[cat]}", headers={"Authorization": f"Bearer {tok}"})
    i = json.load(urllib.request.urlopen(r, timeout=60))["data"]["input"]; return i["ingestUrl"], i["ingestApiKey"], X_TOKEN
for arg in sys.argv[1:]:
    cat, path = arg.split("=", 1); d = load(path); rows = []
    users = {u["id"]: u.get("username") for u in (d.get("includes") or {}).get("users", [])}
    for p in d.get("data", []):
        text = p.get("text") or ""; low = text.lower()
        hits = [e for e in ENT[cat] if any(re.search(r"(?<![a-z0-9])" + re.escape(k.lower()) + r"(?![a-z0-9])", low) for k in e["keywords"])]
        for e in hits[:2]:  # a post naming several entities counts for at most two
            s, issue = classify(text)
            m = p.get("public_metrics") or {}
            rows.append(dict(entity_slug=e["slug"], entity_name=e["name"], source="x", url=p["url"] + ("" if e is hits[0] else f"#e={e['slug']}"),
                             title="", text=text[:2000], rating=None, posted_utc=datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")).timestamp(),
                             sentiment=s, issue_tag=issue, engagement=(m.get("like_count") or 0) + (m.get("retweet_count") or 0) + (m.get("reply_count") or 0),
                             author=users.get(p.get("author_id"))))
    url, key, token = creds(cat); res = {"received": 0, "inserted": 0}
    if rows:
        body = dict(p_token=token, p_category=cat, p_run_id=f"x-{datetime.now():%Y%m%d%H%M}", p_trigger="grok-x-search", p_items=rows)
        r = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={"apikey": key, "Content-Type": "application/json", "User-Agent": "paisainsights-x-ingest/1.0"})
        try: res = json.load(urllib.request.urlopen(r, timeout=60))
        except urllib.error.HTTPError as e: print(f"x/{cat}: ingest HTTP {e.code} {e.read()[:200]!r}"); continue
    print(f"x/{cat}: {len(d.get('data', []))} posts, {len(rows)} matched, ingest {res}")
