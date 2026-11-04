"""Incremental social listening ("mentions" mode): classify, dedupe, track last-seen, post to PaisaInsights.
Sentiment/issue tagging is keyword + star-rating based (cheap, deterministic, no LLM)."""
import hashlib, json, re


ISSUES = [  # first match wins, most specific first
    ("withdrawal", r"\b(withdraw\w*|payout|fund(s)? (transfer|stuck|not)|money (stuck|deducted|not)|refund\w*|not credited|debited|upi (fail|issue))\b"),
    ("outage", r"\b(down|outage|not (working|loading|opening)|crash\w*|server (issue|error|down)|glitch|hang(s|ing)?|stuck|frozen|freez\w*|technical (issue|glitch))\b"),
    ("login", r"\b(log ?in|logged out|otp|password|2fa|tpin|pin reset|authenticat\w*|session expired)\b"),
    ("charges", r"\b(brokerage|hidden charge\w*|charges?|fees?|amc|dp charge\w*|penalt\w*|overcharg\w*)\b"),
    ("support", r"\b(customer (care|support|service)|no response|support team|ticket|helpline|call back|chat support|worst service)\b"),
    ("kyc", r"\b(kyc|account opening|re-?kyc|verification pending|account (blocked|frozen|closed))\b"),
    ("fraud", r"\b(fraud|scam|unauthori[sz]ed|hack\w*|cheat\w*)\b"),
]
NEG = r"\b(worst|bad|poor|terrible|horrible|useless|pathetic|disappoint\w*|issue|problem|fail\w*|error|bug\w*|slow|lag\w*|frustrat\w*|never|loss|cheat|fraud|scam|hate|annoy\w*|waste|uninstall\w*|hidden|overcharg\w*|looted|loot)\b"
POS = r"\b(good|great|best|excellent|awesome|amazing|love|nice|smooth|easy|helpful|fast|super|perfect|thank\w*|recommend\w*|seamless|happy|satisf\w*|reliable)\b"

def classify(text, rating=None):
    t = (text or "").lower()
    issue = next((tag for tag, rx in ISSUES if re.search(rx, t)), None)
    neg, pos = len(re.findall(NEG, t)), len(re.findall(POS, t))
    if rating is not None:
        r = float(rating)
        sent = "negative" if r <= 2 else "positive" if r >= 4 else "neutral"
        if sent == "positive" and issue in ("outage", "login", "withdrawal", "fraud") and neg > pos: sent = "neutral"
    else:
        sent = "negative" if (neg > pos or issue in ("outage", "withdrawal", "fraud", "login")) and neg + (issue is not None) > 0 else "positive" if pos > neg else "neutral"
    if issue is None and sent == "positive": issue = "praise"
    return sent, issue

def stable_url(it, slug):
    """Unique URL per mention. App Store RSS gives one URL per app, so add a content hash fragment."""
    url = it.get("url")
    if not url or it.get("source") == "app_store":
        h = hashlib.sha1(json.dumps([it.get("source"), slug, it.get("author"), it.get("title"), (it.get("text") or "")[:500]], ensure_ascii=False).encode()).hexdigest()[:16]
        url = f"{url or 'urn:' + str(it.get('source'))}#m={h}"
    return url

def to_rows(items, slug, name, cutoff, last_seen):
    rows, newest = [], last_seen
    for it in items:
        if it.get("title") in ("ERROR", "BLOCKED", "NO_PUBLIC_POSTS"): continue
        ts = it.get("created_utc")
        if ts is None or ts < cutoff: continue          # daysBack window (also drops undated YouTube rows)
        if last_seen and ts < last_seen - 43200: continue  # older than last-seen minus 12h grace (stores publish late); URL dedupe handles the overlap
        text = " ".join(x for x in [it.get("title") if it.get("source") in ("reddit", "news") else None, it.get("text")] if x)
        sent, issue = classify(text, it.get("rating"))
        rows.append(dict(entity_slug=slug, entity_name=name, source=it.get("source"), url=stable_url(it, slug),
                         title=(it.get("title") or "")[:300], text=(it.get("text") or "")[:2000], rating=it.get("rating"),
                         posted_utc=ts, sentiment=sent, issue_tag=issue, engagement=it.get("score"), author=it.get("author")))
        newest = max(newest or 0, ts)
    return rows, newest

def post(url, apikey, token, category, run_id, trigger, rows):
    out = {"received": 0, "inserted": 0, "alerts": 0}
    for i in range(0, len(rows), 200):
        import httpx
        r = httpx.post(url, timeout=60, headers={"apikey": apikey, "Content-Type": "application/json"},
                       json={"p_token": token, "p_category": category, "p_run_id": run_id, "p_trigger": trigger, "p_items": rows[i:i + 200]})
        r.raise_for_status()
        d = r.json()
        for k in out: out[k] += int(d.get(k) or 0)
    return out
