"""Rebuild Bank Pulse items as they would have looked at each past week's end and score them with banks/score.py
(same code path as the live week: 30 newest Play + 30 newest App Store reviews within 30 days, 14-day half-life,
Bayesian shrinkage K=15 toward the category mean, confidence by data points). Reddit/YouTube: only dated items
already collected for W44 that fall inside the window. Complaints and news-based inputs are held at current values.
Usage: python score_banks_history.py raw_banks.json ../banks/items.json out_dir"""
import json, os, subprocess, sys, datetime as dt
raw, live_items, outd = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__)); BANKS = os.path.join(HERE, "..", "banks")
d = json.load(open(raw)); social = [i for i in json.load(open(live_items)) if i["source"] in ("reddit", "youtube")]
os.makedirs(outd, exist_ok=True)
def ts(x): return dt.datetime.fromisoformat(x).replace(tzinfo=dt.timezone.utc).timestamp()
for wk in range(int(os.getenv("FROM_WEEK", 36)), 44):
    ws = dt.datetime.combine(dt.date.fromisocalendar(2026, wk, 1), dt.time(), dt.timezone.utc); end = ws + dt.timedelta(days=7); start = end - dt.timedelta(days=30)
    items = []
    for s, v in d.items():
        for src in ("play_store", "app_store"):
            rv = sorted([x for x in v["reviews"] if x["source"] == src and start.timestamp() <= ts(x["at"]) < end.timestamp()], key=lambda x: x["at"], reverse=True)[:30]
            items += [dict(source=src, broker=v["name"], title=x.get("title", ""), text=x["text"], rating=x["rating"], url="", author=None, created_utc=ts(x["at"]), score=x["thumbs"], num_comments=0) for x in rv]
    items += [i for i in social if isinstance(i.get("created_utc"), (int, float)) and start.timestamp() <= i["created_utc"] < end.timestamp()]
    f = os.path.join(outd, f"items-W{wk}.json"); json.dump(items, open(f, "w"))
    out = os.path.join(outd, f"2026-W{wk:02d}.json")
    subprocess.run([sys.executable, "score.py"], cwd=BANKS, check=True, stdout=subprocess.DEVNULL,
                   env=dict(os.environ, ITEMS_FILE=os.path.abspath(f), ASOF=end.isoformat(), WEEK=f"2026-W{wk:02d}", OUT_FILE=os.path.abspath(out)))
    rep = json.load(open(out)); rep["backfilled"] = True
    rep["methodology_note"] = ("Backfilled on 29 Oct 2026 with the live scoring code (banks/score.py) as of this week's end: 30 newest Play Store and App Store reviews "
        "per bank within 30 days, dated Reddit/YouTube items where available. Complaints (RBI/bank disclosures) and news-based Innovation/outage inputs are held at current values.")
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1)
    print(rep["week"], len(items), " ".join(f"{b['slug'][:6]}={b['overall']}{'*' if b['confidence']=='Low' else ''}" for b in rep["banks"]))
