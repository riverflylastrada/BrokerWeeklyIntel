"""UCC client-base factor (NSE Report 1C), added to Engagement as a bounded +/-1.3 adjustment.
Data month = same month_for() rule as complaints (latest month due by week end; no lookahead).
  active_ratio = active clients / total UCC (UCC at start of FY; published from Jul 2026)
  ratio_c  = clamp((active_ratio / peer median - 1) / 0.5, -1, 1)            (peer = tracked brokers with data that month)
  growth   = 12-month active-client growth; if the month 12 back is missing, month-on-month growth x 12 (annualised)
  growth_c = clamp((growth - peer median growth) / 0.25, -1, 1)
  ucc_score = 5 + 2.5 x ratio_c + 2.5 x growth_c    (0-10; a missing part counts as 0 = neutral)
  engagement = engagement_base + 1.3 x (ucc_score - 5) / 5   (neutral at 5; +/-1.3 max = 13% of Engagement's 10-point range)
  -> Engagement weight 15% so overall moves at most +/-0.195. 12-month base under 5% of today's active = entity change -> MoM fallback.
No UCC data -> engagement unchanged, flagged ucc_factor.status = 'no UCC data'."""
import json, os, statistics as st
NAME = {"zerodha": "Zerodha", "groww": "Groww", "upstox": "Upstox", "angel-one": "Angel One", "dhan": "Dhan",
        "kotak-securities": "Kotak Securities", "icici-direct": "ICICI Direct", "hdfc-sky": "HDFC Securities",
        "sharekhan": "Sharekhan", "5paisa": "5Paisa", "fyers": "Fyers", "sahi-broking": "Sahi"}
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_share_history.json")
MS = {m["month"]: {b["broker"]: b for b in m["brokers"]} for m in json.load(open(P))["months"]} if os.path.exists(P) else {}
CAP = 1.3
clamp = lambda x, a=-1.0, b=1.0: max(a, min(b, x))
def _shift(m, k):
    y, mo = map(int, m.split("-")); t = y * 12 + mo - 1 - k; return f"{t // 12}-{t % 12 + 1:02d}"
def _raw(slug, month):
    row = MS.get(month, {}).get(NAME.get(slug, ""))
    if not row or not row.get("active_clients"): return None
    a = row["active_clients"]; tot = row.get("total_ucc"); r = dict(month=month, active=a, total_ucc=tot)
    r["active_ratio"] = round(a / tot, 4) if tot else None
    old = MS.get(_shift(month, 12), {}).get(NAME[slug]); prv = MS.get(_shift(month, 1), {}).get(NAME[slug])
    if old and old.get("active_clients", 0) > max(1000, 0.05 * a): r.update(growth=a / old["active_clients"] - 1, growth_basis="12m")
    elif prv and prv.get("active_clients", 0) > 1000: r.update(growth=(a / prv["active_clients"] - 1) * 12, growth_basis="MoM x12")
    else: r.update(growth=None, growth_basis=None)
    return r
def _month(target):
    cand = [m for m in MS if m <= target]; return max(cand) if cand else None
def ucc_component(slug, target):
    m = _month(target); me = _raw(slug, m) if m else None
    if not me: return None
    peers = [x for x in (_raw(s, m) for s in NAME) if x]
    rats = [x["active_ratio"] for x in peers if x["active_ratio"]]; grs = [x["growth"] for x in peers if x["growth"] is not None]
    rc = clamp((me["active_ratio"] / st.median(rats) - 1) / 0.5) if me["active_ratio"] and rats else 0.0
    gc = clamp((me["growth"] - st.median(grs)) / 0.25) if me["growth"] is not None and grs else 0.0
    sc = round(5 + 2.5 * rc + 2.5 * gc, 2)
    return dict(score=sc, data_month=m, active_clients=me["active"], total_ucc=me["total_ucc"], active_ratio_pct=round(me["active_ratio"] * 100, 1) if me["active_ratio"] else None,
                peer_median_ratio_pct=round(st.median(rats) * 100, 1) if rats else None, growth_pct=round(me["growth"] * 100, 1) if me["growth"] is not None else None,
                growth_basis=me["growth_basis"], peer_median_growth_pct=round(st.median(grs) * 100, 1) if grs else None, ratio_c=round(rc, 2), growth_c=round(gc, 2))
def apply(b, target, cl):
    rb = b["rating_breakdown"]; rb.setdefault("engagement_base", rb["engagement"])
    u = ucc_component(b["slug"], target)
    if not u:
        rb["engagement"] = rb["engagement_base"]; b["ucc_factor"] = dict(score=None, status="no UCC data", adjustment=0); return
    adj = CAP * (u["score"] - 5) / 5  # neutral at 5; full range +/-1.3 Engagement (~13% of the 10-point scale)
    rb["engagement"] = cl(rb["engagement_base"] + adj); u["adjustment"] = round(rb["engagement"] - rb["engagement_base"], 2); b["ucc_factor"] = u
