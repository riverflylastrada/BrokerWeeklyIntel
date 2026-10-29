"""Recompute broker weekly reports for past ISO weeks with the W44 7-parameter method (intel build.py core):
newest 60 Google Play reviews as of each week's end -> Technical reliability, Sentiment, Support from review-theme shares.
Engagement, Transparency and New-feature response are held at their W44 values (no dated history for them).
Historical trend chains week to week (first backfilled week = 5.0). W44 keeps its own params; only its
historical_trend/previous_rating are re-based on the recomputed W43 (the May W19-W21 reports used a different method).
Usage: python score_brokers_history.py raw_brokers.json ../data/historical/BrokerWeeklyIntel-2026-W44.json out_dir"""
import json, re, sys, datetime as dt, os
raw, w44p, outd = sys.argv[1:4]
d = json.load(open(raw)); w44 = json.load(open(w44p))
W = dict(technical_reliability=.20, sentiment=.15, new_feature_response=.15, engagement=.15, support=.15, historical_trend=.10, transparency=.10)
TH = {"Performance": r"lag|slow|buffer|hang|freez|stuck|load",
 "Reliability": r"crash|close[sd]? automatically|not open|force|glitch|technical|down|not working|error|bug|order.*(not|fail|reject)|login",
 "Support": r"support|customer care|customer service|ticket|response|kyc|waited|no reply",
 "Charges": r"charge|brokerage|fee|hidden|deduct|expensive|highest",
 "UX": r"ui\b|user.friendly|pop.?up|interface|design|chart|graph|old app",
 "Features/Gaps": r"feature|option|add |please add|doesn.t have|missing|trail",
 "Transparency": r"cheat|fraud|scam|loot|lutne|dhokhe|धोखे|without inform|silently|chupchap"}
PLAY = {"5paisa":"com.fivepaisa.trade","angel-one":"com.msf.angelmobile","dhan":"com.dhan.live","fyers":"com.fyers.trader","groww":"com.nextbillion.groww","hdfc-sky":"com.cloudtradetech.sky","icici-direct":"com.icicidirect.idirectsuper","kotak-securities":"com.kotak.neo","sahi-broking":"com.aaritya.sahi_trade_app","sharekhan":"com.sharekhan.androidsharemobile","upstox":"in.upstox.app","zerodha":"com.zerodha.kite3"}
cl = lambda x: round(max(1, min(9.8, x)), 1)
sev = lambda c: "critical" if c >= 12 else "high" if c >= 6 else "medium" if c >= 3 else "low"
base = {b["slug"]: b for b in w44["brokers"]}
WEEKS = [(2026, w) for w in range(int(os.getenv("FROM_WEEK", 36)), int(os.getenv("TO_WEEK", 44)))]
prev = {}; reports = []
for y, wk in WEEKS:
    ws = dt.date.fromisocalendar(y, wk, 1); we = ws + dt.timedelta(days=6); end = (we + dt.timedelta(days=1)).isoformat()
    B = []
    for s, v in d.items():
        b44 = base[s]
        rv = sorted([x for x in v["reviews"] if x["source"] == "play_store" and x["at"] < end], key=lambda x: x["at"], reverse=True)[:60]
        if len(rv) < 20: continue
        n = len(rv); avg = sum(x["rating"] for x in rv) / n
        inweek = sum(1 for x in rv if x["at"] >= ws.isoformat())
        neg = [x for x in rv if x["rating"] <= 2]; themes = {}
        for x in neg:
            t = x["text"].lower()
            for k, p in TH.items():
                if re.search(p, t): themes.setdefault(k, []).append(x)
            if not any(x in xs for xs in themes.values()): themes.setdefault("Other", []).append(x)
        tech = list({id(x): x for k in ("Reliability", "Performance") for x in themes.get(k, [])}.values())
        rb = dict(technical_reliability=cl(10 - len(tech) / n * 30), sentiment=cl((avg - 1) / 4 * 10),
                  new_feature_response=b44["rating_breakdown"]["new_feature_response"], engagement=b44["rating_breakdown"]["engagement"],
                  support=cl(10 - len(themes.get("Support", [])) / n * 40), transparency=b44["rating_breakdown"]["transparency"], historical_trend=5.0)
        p = prev.get(s)
        if p is not None: rb["historical_trend"] = cl(5 + (sum(rb[k] * w for k, w in W.items()) - p) * 2)
        r = round(sum(rb[k] * w for k, w in W.items()), 1)
        url = f"https://play.google.com/store/apps/details?id={PLAY[s]}&hl=en_IN"
        qs = [dict(quote=x["text"], context=f"Google Play review, {x['rating']}★, {x['at'][:10]}", sentiment="positive" if x["rating"] >= 4 else "negative",
                   source_url=url, platform="other", broker=v["name"], sentimentScore=round((x["rating"] - 3) / 2, 2))
              for x in sorted(neg, key=lambda x: -x["thumbs"])[:2] + sorted([x for x in rv if x["rating"] >= 5], key=lambda x: -x["thumbs"])[:1]]
        ti = [dict(broker=v["name"], description=f"{k}: {len(xs)} of last {n} Play reviews report it", severity=sev(len(xs)), issue_type="platform_wide" if k == "Reliability" else "feature_specific",
                   volume=len(xs), first_seen=min(x["at"] for x in xs)[:10], last_seen=max(x["at"] for x in xs)[:10]) for k in ("Reliability", "Performance") for xs in [themes.get(k, [])] if xs]
        conf = "High" if inweek >= 40 else "Medium" if inweek >= 20 else "Low"
        B.append(dict(broker=v["name"], slug=s, overall_rating=r, trend="Stable" if p is None or abs(r - p) < 0.3 else ("Improving" if r > p else "Declining"),
                      **({"previous_rating": p} if p is not None else {}), rating_breakdown=rb, new_features=[], key_quotes=qs,
                      negative_themes=[dict(theme=k, count=len(xs), severity=sev(len(xs)), example_quotes=[x["text"][:160] for x in xs[:2]]) for k, xs in sorted(themes.items(), key=lambda kv: -len(kv[1]))],
                      technical_issues=ti, watch_items=[], confidence=conf,
                      sample=dict(play_reviews=n, in_week=inweek, from_date=rv[-1]["at"][:10], to_date=rv[0]["at"][:10])))
        prev[s] = r
    B.sort(key=lambda b: -b["overall_rating"])
    rep = dict(week=f"{y}-W{wk:02d}", week_start=ws.isoformat(), week_end=we.isoformat(), report_version="2.1", overall_sentiment="mixed", brokers=B, backfilled=True,
               industry_themes=dict(positive=[], negative=[], emerging=[], implications_for_socialcoffee=""), new_features_summary=[], watch_items_next_2_weeks=[],
               methodology_note="Backfilled on 29 Oct 2026 with the same 7-parameter method as W44 (Tech 20%, Sentiment/New-feature/Engagement/Support 15% each, Historical 10%, Transparency 10%). "
               "Evidence: newest 60 Google Play reviews per broker as of the week's end (dated, India store). Technical reliability, Sentiment and Support are recomputed for the week; "
               "Engagement, Transparency and New-feature response are held at W44 values (no dated history). X/Reddit/App Store enrichment used in W44 is not available for past weeks. "
               "Confidence: High if 40+ of the 60 reviews fall inside the week, Medium 20-39, Low under 20.")
    reports.append(rep)
# Re-base W44 historical trend on recomputed W43
for b in w44["brokers"]:
    p = prev.get(b["slug"]); rb = b["rating_breakdown"]
    if p is None: continue
    rb["historical_trend"] = 5.0
    rb["historical_trend"] = cl(5 + (sum(rb[k] * w for k, w in W.items()) - p) * 2)
    r = round(sum(rb[k] * w for k, w in W.items()), 1)
    b.update(overall_rating=r, previous_rating=p, trend="Stable" if abs(r - p) < 0.3 else ("Improving" if r > p else "Declining"))
    b["watch_items"] = [w_ for w_ in b.get("watch_items", []) if "vs W21" not in w_]
w44["brokers"].sort(key=lambda b: -b["overall_rating"])
w44["methodology_note"] += " Historical trend re-based on 29 Oct against the recomputed W43 (backfilled W36-W43 replace the May W19-W21 reports, which used a different method)."
os.makedirs(outd, exist_ok=True)
EXTRA = [] if int(os.getenv("TO_WEEK", 44)) > 44 else [w44]
for rep in reports + EXTRA: json.dump(rep, open(f"{outd}/{rep['week']}.json", "w"), ensure_ascii=False, indent=1)
for rep in reports + EXTRA: print(rep["week"], " ".join(f"{b['slug'][:6]}={b['overall_rating']}{'' if b.get('confidence','High')!='Low' else '*'}" for b in rep["brokers"]))
