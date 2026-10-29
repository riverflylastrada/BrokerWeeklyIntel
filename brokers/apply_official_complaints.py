"""Blend the Official Complaints sub-score (SEBI-mandated broker disclosures) into broker weekly reports.
Same rule for every week, so trends stay comparable:
  month used for a week = latest month whose data was due (month end + 10 days) by the week's end date
  window = that month and the 2 before it (only months the broker has published; uses latest available if behind)
  rate  = average monthly complaints received / NSE active clients x 1,00,000   (per lakh active clients)
  rate_score = clamp(10 - 0.4 x (rate - 2), 0, 10)       (2 per lakh/month or less = 10; every +2.5 costs 1 point)
  resolution = resolved in window / (carried in at start + received in window), capped at 1
  official   = 0.7 x rate_score + 0.3 x (10 x resolution)
  support    = 0.5 x reviews-based support + 0.5 x official      (only when official data exists; otherwise unchanged)
Overall = same 7-parameter weights; Historical trend is re-chained week to week. Idempotent: the reviews-based value is kept in
rating_breakdown.support_reviews and always used as the input.
Usage: python apply_official_complaints.py official_complaints.json report1.json [report2.json ...]  (in week order; rewritten in place)\n       SEED_FIRST=1 python apply_official_complaints.py oc.json previous_week.json new_week.json   (weekly run: only new_week is rewritten)"""
import json, os, sys, datetime as dt
W = dict(technical_reliability=.20, sentiment=.15, new_feature_response=.15, engagement=.15, support=.15, historical_trend=.10, transparency=.10)
cl = lambda x: round(max(1, min(9.8, x)), 1)
def month_for(week_end):
    e = dt.date.fromisoformat(week_end); m = e.replace(day=1)
    while True:
        m = (m - dt.timedelta(days=1)).replace(day=1); nxt = (m.replace(day=28) + dt.timedelta(days=5)).replace(day=1)
        if nxt + dt.timedelta(days=9) <= e: return m.strftime("%Y-%m")
def official(b, oc, week_end):
    months = oc.get("months") or {}; act = oc.get("active_clients")
    target = month_for(week_end); avail = sorted(k for k in months if k <= target)
    if not avail or not act: return None
    win = avail[-3:]; rows = [months[k] for k in win]
    rec = sum(r["received"] for r in rows) / len(rows); rate = rec / act * 1e5
    rs = max(0.0, min(10.0, 10 - 0.4 * (rate - 2)))
    denom = rows[0].get("carried_forward", 0) + sum(r["received"] for r in rows)
    res = min(1.0, sum(r["resolved"] for r in rows) / denom) if denom else 1.0
    sc = round(0.7 * rs + 0.3 * res * 10, 1)
    return dict(score=sc, rate_per_lakh=round(rate, 2), rate_score=round(rs, 1), resolution_rate=round(res * 100, 1), months_used=win,
                target_month=target, stale=win[-1] != target, avg_monthly_received=round(rec, 1), active_clients=act,
                latest=dict(month=win[-1], **{k: rows[-1][k] for k in ("received", "resolved", "pending_end")}))
NSE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nse", "nse_brokers_tracked.json")
NSE = json.load(open(NSE_PATH)) if os.path.exists(NSE_PATH) else {"brokers": {}}
def _prev_months(m, n):
    y, mo = map(int, m.split("-")); out = []
    for _ in range(n):
        out.append(f"{y}-{mo:02d}"); mo -= 1
        if mo == 0: y, mo = y - 1, 12
    return out
def _fy(m):
    y, mo = map(int, m.split("-")); s = y if mo >= 4 else y - 1; return f"{s}-{(s+1)%100:02d}"
def nse_component(slug, week_end):
    """NSE Report 1A: complaints lodged at NSE against the broker, 3 months ending the week's target month,
    per lakh NSE active clients. nse_score = clamp(10 - 1.0 x (rate - 1), 0, 10)  (1 per lakh/month or less = 10)."""
    t = NSE["brokers"].get(slug)
    if not t: return None
    target = month_for(week_end); win = _prev_months(target, 3); ms = t["months"]
    act = next((ms[m]["active_clients"] for m in win if m in ms and ms[m].get("active_clients")), None)
    if act is None:
        cand = [m for m in ms if m <= target and ms[m].get("active_clients")]
        act = ms[max(cand)]["active_clients"] if cand else None
    if not act: return None
    n = sum(ms.get(m, {}).get("total", 0) for m in win) / 3; rate = n / act * 1e5
    sc = round(max(0.0, min(10.0, 10 - 1.0 * (rate - 1))), 1)
    types = {}
    for m in win:
        for k, v in ms.get(m, {}).get("types", {}).items(): types[k] = types.get(k, 0) + v
    return dict(score=sc, rate_per_lakh=round(rate, 2), avg_monthly=round(n, 1), active_clients=act, months_used=win, top_types=sorted(types.items(), key=lambda x: -x[1])[:3])
def penalty_component(slug, week_end):
    """NSE Report 4A/4B: penal orders in the week's financial year + the previous one, per 10 lakh active clients.
    transparency_penalty = min(1.0, 0.2 x sqrt(orders_per_10_lakh))."""
    t = NSE["brokers"].get(slug)
    if not t: return None
    target = month_for(week_end); fy = _fy(target); y = int(fy[:4]); prev = f"{y-1}-{y%100:02d}"
    p = t.get("penalties", {}); orders = sum(p.get(f, {}).get("penal_orders_complaints", 0) + p.get(f, {}).get("penal_orders_others", 0) for f in (fy, prev))
    lakh = round(sum(p.get(f, {}).get("penalty_lakh_complaints", 0) + p.get(f, {}).get("penalty_lakh_others", 0) for f in (fy, prev)), 2)
    ms = t["months"]; cand = [m for m in ms if m <= target and ms[m].get("active_clients")]
    act = ms[max(cand)]["active_clients"] if cand else None
    per = orders / act * 1e6 if act else 0
    return dict(penalty=round(min(1.0, 0.2 * per ** 0.5), 2), orders=orders, penalty_lakh=lakh, orders_per_10_lakh=round(per, 2), years=[prev, fy])
def main():
    oc = json.load(open(sys.argv[1])); prev = {}; files = sys.argv[2:]
    if os.getenv("SEED_FIRST") == "1":  # first file = previous published week: only seeds Historical trend, left untouched
        seed = json.load(open(files[0])); new = json.load(open(files[1]))
        if dt.date.fromisoformat(seed["week_end"]) + dt.timedelta(days=7) != dt.date.fromisoformat(new["week_end"]):
            sys.exit(f"skip: {files[0]} is not the week before {files[1]}")
        prev = {b["slug"]: b["overall_rating"] for b in seed["brokers"]}; files = files[1:]
    for path in files:
        rep = json.load(open(path))
        for b in rep["brokers"]:
            rb = b["rating_breakdown"]; rb.setdefault("support_reviews", rb["support"]); rb.setdefault("transparency_base", rb["transparency"])
            o = official(b, oc["brokers"].get(b["slug"], {}), rep["week_end"])
            n = nse_component(b["slug"], rep["week_end"])
            parts = [x["score"] for x in (o, n) if x]
            off = sum(parts) / len(parts) if parts else None
            rb["support"] = cl(0.5 * rb["support_reviews"] + 0.5 * off) if off is not None else rb["support_reviews"]
            b["official_complaints"] = o or dict(score=None, status="not published")
            b["nse_complaints"] = n or dict(score=None, status="no NSE data")
            b["official_combined_score"] = round(off, 2) if off is not None else None
            pz = penalty_component(b["slug"], rep["week_end"])
            rb["transparency"] = cl(rb["transparency_base"] - (pz["penalty"] if pz else 0))
            b["regulatory_actions"] = pz or dict(penalty=0, orders=0)
            rb["historical_trend"] = 5.0; p = prev.get(b["slug"])
            if p is not None: rb["historical_trend"] = cl(5 + (sum(rb[k] * w for k, w in W.items()) - p) * 2)
            r = round(sum(rb[k] * w for k, w in W.items()), 1)
            b["overall_rating"] = r
            if p is not None: b.update(previous_rating=p, trend="Stable" if abs(r - p) < 0.3 else ("Improving" if r > p else "Declining"))
            prev[b["slug"]] = r
        rep["brokers"].sort(key=lambda b: -b["overall_rating"])
        note = (" Support blends Official Complaints (50%): SEBI-mandated monthly investor-complaint disclosures per lakh NSE active clients "
                "(score 10-0.4x(rate-2), 70%) and resolution rate (30%), 3-month window of months published by the week's end.")
        if note not in rep.get("methodology_note", ""): rep["methodology_note"] = rep.get("methodology_note", "") + note
        note2 = (" Official complaints = average of the broker-disclosure score and the NSE score (NSE Report 1A complaints per lakh NSE active clients, "
                 "3 months ending the week's data month, score 10-1.0x(rate-1)); if only one exists it is used alone. Transparency is reduced by "
                 "min(1.0, 0.2 x sqrt(NSE penal orders per 10 lakh active clients) over the current and previous financial year) from Report 4A/4B.")
        if note2 not in rep["methodology_note"]: rep["methodology_note"] += note2
        if path == sys.argv[-1]: rep["official_complaints_data"] = oc  # full monthly figures + source links, latest week only
        else: rep.pop("official_complaints_data", None)
        json.dump(rep, open(path, "w"), ensure_ascii=False, indent=1)
        print(rep["week"], " ".join(f"{b['slug'][:6]}={b['overall_rating']}" for b in rep["brokers"]))
if __name__ == "__main__": main()
