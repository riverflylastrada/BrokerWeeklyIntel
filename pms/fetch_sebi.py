"""Monthly SEBI PMS compliance-report refresh (sebi.gov.in OtherAction.do?doPmr=yes). Low and slow: one request at a time, 15-25s jitter.
Writes pms/sebi_monthly.json keyed by slug -> {YYYY-MM: parsed}. Keeps previously fetched months; only fetches missing ones."""
import json, os, re, random, sys, time, datetime as dt, http.cookiejar, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
U = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doPmr=yes"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def get(data=None):
    r = urllib.request.Request(U, data=urllib.parse.urlencode(data).encode() if data else None,
        headers={"User-Agent": UA, "Referer": U, "Origin": "https://www.sebi.gov.in"})
    return op.open(r, timeout=60).read().decode("utf-8", "ignore")
def toks(h):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    return [x.strip() for x in re.sub(r"<[^>]+>", "\n", t).replace("&nbsp;", "").split("\n") if x.strip()]
def num(x):
    try: return float(x.replace(",", ""))
    except Exception: return None
def after(T, label, k=0):
    for i, x in enumerate(T):
        if x.startswith(label): return T[i + 1 + k]
def parse(h):
    T = toks(h)
    if "Total Assets under Management (AUM) as on last day of the month (Amount in INR crores)" not in " ".join(T[:400]) and not any(x.startswith("Total Assets under Management") for x in T): return None
    d = dict(clients=num(after(T, "No. of clients as on last day")), aum=num(after(T, "Total Assets under Management")))
    # discretionary perf table (first "Performance Data")
    s = T.index("Performance Data"); e = T.index("Name of the Portfolio Manager", s + 3)
    P = T[s:e]; strat = []; cat = None; i = P.index("Since Inception") + 1
    while i < len(P):
        x = P[i]
        if x in ("EQUITY", "DEBT", "MULTI ASSET", "HYBRID"): cat = x; i += 1; continue
        if i + 10 < len(P) and all(num(v) is not None for v in P[i+1:i+11]) and P[i+11].startswith("Benchmark"):
            r = [num(v) for v in P[i+1:i+11]]; b = [num(v) for v in P[i+12:i+21]]
            strat.append(dict(cat=cat, name=x, aum=r[0], ret=dict(zip(["1m","3m","6m","1y","2y","3y","4y","5y","si"], r[1:])),
                              bench_name=P[i+11].replace("Benchmark:", "").strip(), bench=dict(zip(["1m","3m","6m","1y","2y","3y","4y","5y","si"], b))))
            i += 21; continue
        i += 1
    d["strategies"] = strat
    # complaints: last "Total" row after "Data on Complaints"
    try:
        c = max(i for i, x in enumerate(T) if x == "Data on Complaints"); j = T.index("Total", c)
        d["complaints"] = dict(zip(["pending_start", "received", "resolved", "pending_end"], [num(v) for v in T[j+1:j+5]]))
    except ValueError: d["complaints"] = None
    # discretionary FY net flow: "Total" row in section C
    try:
        c = T.index("Funds Inflow/ Outflow"); j = T.index("Total", c + 5)
        v = [num(x) for x in T[j+1:j+7]]; d["flows"] = dict(in_m=v[0], out_m=v[1], net_m=v[2], in_fy=v[3], out_fy=v[4], net_fy=v[5])
    except (ValueError, IndexError): d["flows"] = None
    return d
if __name__ == "__main__":
    meta = json.load(open(os.path.join(HERE, "pms_list.json")))
    OUT = os.path.join(HERE, "sebi_monthly.json"); db = json.load(open(OUT)) if os.path.exists(OUT) else {}
    today = dt.date.today(); m0 = (today.replace(day=1) - dt.timedelta(days=20)).replace(day=1)  # SEBI data lags ~1 month
    if today.day < 12: m0 = (m0 - dt.timedelta(days=1)).replace(day=1)
    def back(m, k):
        y, mo = m.year, m.month - k
        while mo <= 0: mo += 12; y -= 1
        return dt.date(y, mo, 1)
    months = [back(m0, k) for k in (0, 1, 2, 12)]
    get(); ok = fail = 0
    for p in meta:
        rec = db.setdefault(p["slug"], {})
        for m in months:
            key = m.strftime("%Y-%m")
            if rec.get(key): continue
            time.sleep(random.uniform(15, 25))
            try:
                d = parse(get(dict(pmrId=f"{p['reg']}@@{p['reg']}@@{p['sebi_name']}", year=m.year, month=m.month)))
                if d and d["aum"]: rec[key] = d; ok += 1
                else: print(f"WARN {p['slug']} {key}: no data"); fail += 1
            except Exception as e:
                print(f"WARN {p['slug']} {key}: {type(e).__name__}"); fail += 1
        json.dump(db, open(OUT, "w"), indent=0)
    print(f"sebi pms: {ok} fetched, {fail} failed, months {[m.strftime('%Y-%m') for m in months]}")
