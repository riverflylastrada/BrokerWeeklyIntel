"""PMS Trust Score: SEBI monthly PMS reports (returns vs benchmark, consistency, complaints, growth, disclosure) + SEBI orders + public sentiment."""
import json, math, os, re, statistics as st, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); J = lambda f, d=None: json.load(open(os.path.join(HERE, f))) if os.path.exists(os.path.join(HERE, f)) else d
meta, sebi, reg = J("pms_list.json"), J("sebi_monthly.json", {}), J("regulatory.json", {})
items = J("items.json", []); news = J("news_curated.json", {})
cl = lambda x, a=0, b=10: max(a, min(b, x))
POS = set("good great excellent best outperform consistent transparent trust trusted solid strong recommend happy".split())
NEG = set("worst bad poor underperform loss losses fraud scam terrible expensive hidden lock-in misleading penalty mis-selling disappointed avoid".split())
def sent(it):
    w = re.findall(r"[a-z'-]+", (it.get("title", "") + " " + it.get("text", "")).lower()); p = sum(x in POS for x in w); n = sum(x in NEG for x in w)
    return 0 if p + n == 0 else (p - n) / (p + n)
out = []
for p in meta:
    rec = sebi.get(p["slug"], {})
    if not rec: continue
    months = sorted(rec); cur = rec[months[-1]]
    if not cur.get("aum"): continue
    yago = rec.get(f"{int(months[-1][:4]) - 1}{months[-1][4:]}")
    eq = [s for s in cur["strategies"] if s["cat"] == "EQUITY" and (s["aum"] or 0) >= 5 and s["ret"]["1y"]]
    W = sum(s["aum"] for s in eq) or 1
    def ex(h): 
        xs = [(s["aum"], s["ret"][h] - s["bench"][h]) for s in eq if s["ret"].get(h) and s["bench"].get(h)]
        return sum(a * x for a, x in xs) / sum(a for a, _ in xs) if xs else None
    e1, e3 = ex("1y"), ex("3y")
    excess = e1 if e3 is None else 0.4 * e1 + 0.6 * e3 if e1 is not None else e3
    ret_s = round(cl(5 + excess / 2), 1) if excess is not None else 5.0
    beats = [(s["aum"], s["ret"][h] > s["bench"][h]) for s in eq for h in ("1y", "3y", "5y") if s["ret"].get(h) and s["bench"].get(h)]
    cons = round(10 * sum(a for a, b in beats if b) / sum(a for a, _ in beats), 1) if beats else 5.0
    comp = [rec[m].get("complaints") or {} for m in months[-3:]]
    rcv = sum(c.get("received") or 0 for c in comp); pend = (comp[-1] or {}).get("pending_end") or 0
    rate = rcv / max(cur["clients"] or 1, 1) * 1000 * (12 / max(len(comp), 1))  # annualised per 1000 clients
    comp_s = round(cl(10 - 2.5 * rate - 1.5 * min(pend, 2)), 1)
    R = reg.get(p["slug"], []); reg_s = round(cl(10 - sum(2.5 * x.get("severity", 1) for x in R)), 1)
    g_aum = (cur["aum"] / yago["aum"] - 1) * 100 if yago and yago.get("aum") else None
    g_cl = (cur["clients"] / yago["clients"] - 1) * 100 if yago and yago.get("clients") else None
    nf = (cur.get("flows") or {}).get("net_fy"); nf_pct = nf / cur["aum"] * 100 if nf is not None else None
    parts = [x for x in (g_cl and cl(5 + g_cl / 6), g_aum and cl(5 + g_aum / 8), nf_pct is not None and cl(5 + nf_pct / 2)) if x not in (None, False)]
    gro = round(sum(parts) / len(parts), 1) if parts else 5.0
    disc = round(10 * (0.5 * (len([s for s in cur["strategies"] if s["bench_name"]]) / max(len(cur["strategies"]), 1)) + 0.25 * (cur.get("complaints") is not None) + 0.25 * (len(months) >= 3)), 1)
    L = [i for i in items if i.get("broker") == p["name"]]; ss = [sent(i) for i in L]
    nw = news.get(p["slug"], {}); n = len(ss)
    soc = (sum(ss) + 0) / (n + 8) if n else 0
    sen = round(cl(6 + 4 * soc + 0.5 * nw.get("tone", 0)), 1)
    P = dict(returns_vs_benchmark=ret_s, consistency=cons, complaints_sebi=comp_s, regulatory_record=reg_s, aum_client_growth=gro, disclosure_transparency=disc, sentiment=sen)
    Wt = dict(returns_vs_benchmark=.25, consistency=.15, complaints_sebi=.15, regulatory_record=.15, aum_client_growth=.10, disclosure_transparency=.10, sentiment=.10)
    raw = sum(P[k] * Wt[k] for k in P)
    top = sorted(eq, key=lambda s: -s["aum"])[:5]
    out.append(dict(slug=p["slug"], name=p["name"], sebi_reg=p["reg"], legal_name=p["sebi_name"].strip(), as_of_month=months[-1], overall=round(raw, 1), _raw=raw, params=P,
        aum_cr=round(cur["aum"], 1), clients=int(cur["clients"] or 0), aum_yoy_pct=g_aum and round(g_aum, 1), clients_yoy_pct=g_cl and round(g_cl, 1),
        net_flows_fy_cr=nf, excess_1y_pp=e1 and round(e1, 2), excess_3y_pp=e3 and round(e3, 2),
        complaints=dict(received_3m=rcv, pending=pend, per_1000_clients_annualised=round(rate, 2)),
        regulatory_actions=R, top_strategies=[dict(name=s["name"].title(), aum_cr=s["aum"], ret_1y=s["ret"]["1y"], bench_1y=s["bench"]["1y"], ret_3y=s["ret"]["3y"] or None, bench_3y=s["bench"]["3y"] or None, benchmark=s["bench_name"]) for s in top],
        counts=dict(social=n), confidence="High" if len(months) >= 4 and eq else "Medium" if eq else "Low",
        quotes=[dict(text=(i.get("text") or i.get("title", ""))[:220], source=i["source"], url=i.get("url"), sentiment="positive" if sent(i) > 0 else "negative" if sent(i) < 0 else "neutral") for i in L[:4]],
        news=nw.get("items", [])))
out.sort(key=lambda x: (-x["_raw"], -x["params"]["regulatory_record"]))
for i, o in enumerate(out, 1): o.pop("_raw"); o["rank"] = i
rep = dict(category="pms", week=os.getenv("WEEK") or dt.date.today().strftime("%G-W%V"), generated_at=dt.datetime.now(dt.timezone.utc).isoformat(), pms=out,
    methodology=dict(weights={"returns_vs_benchmark": 25, "consistency": 15, "complaints_sebi": 15, "regulatory_record": 15, "aum_client_growth": 10, "disclosure_transparency": 10, "sentiment": 10},
        sources=["SEBI monthly PMS compliance reports (sebi.gov.in)", "SEBI enforcement orders", "Reddit / YouTube / news"],
        notes="Returns are AUM-weighted TWRR of discretionary equity strategies vs each strategy's SEBI-reported benchmark (0.4x 1Y + 0.6x 3Y excess). Fees are not publicly disclosed per client, so transparency measures completeness of SEBI disclosures."))
json.dump(rep, open(os.path.join(HERE, "pms_report.json"), "w"), indent=1, ensure_ascii=False)
for o in out: print(o["rank"], o["name"], o["overall"], o["aum_cr"], o["params"])
