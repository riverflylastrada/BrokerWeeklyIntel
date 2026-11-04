"""Builds pms/pms_site.json for the PaisaInsights PMS pages (complaints, penalties, history charts, client-type AUM split).
Pure transform of sebi_monthly.json + regulatory.json + pms_report.json; no network."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); J = lambda f, d=None: json.load(open(os.path.join(HERE, f))) if os.path.exists(os.path.join(HERE, f)) else d
meta, sebi, reg, rep = J("pms_list.json"), J("sebi_monthly.json", {}), J("regulatory.json", {}), J("pms_report.json", {"pms": []})
R = {p["slug"]: p for p in rep["pms"]}
def eq_ret(m):
    eq = [s for s in m.get("strategies", []) if s["cat"] == "EQUITY" and (s["aum"] or 0) >= 5 and s["ret"].get("1y") and s["bench"].get("1y")]
    w = sum(s["aum"] for s in eq)
    if not w: return None, None
    return round(sum(s["aum"] * s["ret"]["1y"] for s in eq) / w, 2), round(sum(s["aum"] * s["bench"]["1y"] for s in eq) / w, 2)
providers = []
for p in meta:
    rec = sebi.get(p["slug"], {}); months = sorted(m for m in rec if rec[m].get("aum"))
    if not months: continue
    hist = []
    for m in months:
        d = rec[m]; c = d.get("complaints") or {}; b = d.get("breakup") or None; r1, b1 = eq_ret(d)
        row = dict(month=m, aum_cr=round(d["aum"], 1), clients=int(d.get("clients") or 0), equity_ret_1y=r1, bench_ret_1y=b1,
                   complaints_received=c.get("received"), complaints_resolved=c.get("resolved"), complaints_pending=c.get("pending_end"),
                   net_flow_month_cr=(d.get("flows") or {}).get("net_m"))
        if b:
            epf = b.get("pf_epfo") or {}; ret = [b.get(k) or {} for k in ("non_corporates", "non_residents")]
            row.update(epfo_aum_cr=round(epf.get("aum") or 0, 1), epfo_clients=int(epf.get("clients") or 0),
                       corporate_aum_cr=round((b.get("corporates") or {}).get("aum") or 0, 1),
                       retail_aum_cr=round(sum(x.get("aum") or 0 for x in ret), 1), retail_clients=int(sum(x.get("clients") or 0 for x in ret)),
                       fpi_other_aum_cr=round(sum((b.get(k) or {}).get("aum") or 0 for k in ("fpi", "others")), 1))
        hist.append(row)
    last3 = hist[-3:]; cur = hist[-1]
    rcv = sum(h["complaints_received"] or 0 for h in last3); res = sum(h["complaints_resolved"] or 0 for h in last3)
    rcv12 = sum(h["complaints_received"] or 0 for h in hist[-12:])
    providers.append(dict(slug=p["slug"], name=p["name"], rank=R.get(p["slug"], {}).get("rank"), overall=R.get(p["slug"], {}).get("overall"),
        as_of_month=cur["month"], clients=cur["clients"], aum_cr=cur["aum_cr"],
        epfo_share_pct=round(100 * cur["epfo_aum_cr"] / cur["aum_cr"], 1) if cur.get("epfo_aum_cr") is not None and cur["aum_cr"] else None,
        aum_ex_epfo_cr=round(cur["aum_cr"] - cur["epfo_aum_cr"], 1) if cur.get("epfo_aum_cr") is not None else None,
        complaints=dict(received_3m=rcv, resolved_3m=res, pending=cur["complaints_pending"] or 0, received_12m=rcv12, months_covered_12m=len(hist[-12:]),
                        resolution_rate_pct=round(100 * res / rcv, 1) if rcv else None,
                        per_1000_clients_annualised=round(rcv / max(cur["clients"], 1) * 1000 * 12 / max(len(last3), 1), 2)),
        regulatory=reg.get(p["slug"], []), history=hist))
out = dict(generated_from="SEBI monthly PMS compliance reports + SEBI orders", week=rep.get("week"), providers=providers,
           totals=dict(providers=len(providers), complaints_received_3m=sum(x["complaints"]["received_3m"] for x in providers),
                       pending=sum(x["complaints"]["pending"] for x in providers), sebi_actions=sum(len(x["regulatory"]) for x in providers)))
json.dump(out, open(os.path.join(HERE, "pms_site.json"), "w"), indent=0, ensure_ascii=False)
print(f"pms_site.json: {len(providers)} providers, months per provider {min(len(x['history']) for x in providers)}-{max(len(x['history']) for x in providers)}")
