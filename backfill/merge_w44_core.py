"""Put the live W44 broker report on the same scoring basis as the backfilled weeks: numeric scores from the
Play-review core method (as of W44 end), keeping W44's X/Reddit/App Store evidence (quotes, issues, features) as context."""
import json, sys
live, core, out = sys.argv[1:4]
L = json.load(open(live)); C = {b["slug"]: b for b in json.load(open(core))["brokers"]}
for b in L["brokers"]:
    c = C.get(b["slug"])
    if not c: continue
    for k in ("overall_rating", "rating_breakdown", "trend", "previous_rating", "confidence", "sample"):
        if k in c: b[k] = c[k]
    b["watch_items"] = [w for w in b.get("watch_items", []) if "vs W21" not in w]
L["brokers"].sort(key=lambda b: -b["overall_rating"])
L["methodology_note"] = ("Scores use the same 7-parameter method as the backfilled W36-W43 weeks: newest 60 Google Play reviews per broker drive Technical reliability, "
    "Sentiment and Support; Engagement, Transparency and New-feature response as of W44; Historical trend vs the previous week. X, Reddit, App Store and news items "
    "collected for W44 are shown as evidence (quotes, issues, features) but are not blended into scores, so weeks stay comparable. Re-based on 29 Oct 2026; replaces the May W19-W21 sample reports, which used a different method.")
json.dump(L, open(out, "w"), ensure_ascii=False, indent=1)
for b in L["brokers"]: print(b["broker"], b["overall_rating"], b["trend"], b.get("previous_rating"))
