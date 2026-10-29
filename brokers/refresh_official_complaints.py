"""Refresh SEBI-mandated 'Investor Complaints' disclosures for the 12 PaisaInsights brokers.
Low and slow: one request at a time, 8-15 s random pause, plain curl (no proxies). Never invents numbers:
a broker whose source can't be fetched/parsed keeps its previous months and gets fetch_status='stale'.
Output: brokers/official_complaints.json  (monthly totals: carried, received, resolved, pending; source URL + fetch date).
Active clients (normalisation): NSE broker-wise active clients, entered in ACTIVE below with source; update monthly."""
import json, re, os, subprocess, tempfile, time, random, datetime as dt, html as H
OUT = os.path.join(os.path.dirname(__file__), "official_complaints.json")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
MON = {m: i for i, m in enumerate(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"], 1)}
ACTIVE_SRC = dict(month="2026-09", source="NSE broker-wise active clients, September 2026 (as compiled from NSE disclosures)",
                  url="https://dhan.co/blog/stock-market/top-50-largest-stock-brokers-in-india-as-of-september-2026/")
ACTIVE = {"groww": 13448194, "zerodha": 6791541, "angel-one": 6755711, "icici-direct": 2160619, "upstox": 1854285,
          "kotak-securities": 1391840, "hdfc-sky": 1353843, "dhan": 1120901, "sharekhan": 527503, "5paisa": 321174,
          "sahi-broking": 281028, "fyers": 197380}
ENTITY = {"zerodha": "Zerodha Broking Ltd", "groww": "Groww Invest Tech Pvt Ltd", "angel-one": "Angel One Ltd", "upstox": "Upstox Securities Pvt Ltd",
          "dhan": "Raise Securities Pvt Ltd", "fyers": "Fyers Securities Pvt Ltd", "sahi-broking": "Aaritya Broking Pvt Ltd",
          "kotak-securities": "Kotak Securities Ltd", "hdfc-sky": "HDFC Securities Ltd (HDFC Sky)", "icici-direct": "ICICI Securities Ltd",
          "5paisa": "5paisa Capital Ltd", "sharekhan": "Sharekhan Ltd"}
SRC = {
 "zerodha": dict(kind="zerodha_csv", url="https://docs.google.com/spreadsheets/d/12_L4ku18tU12orNkyFJIY2Kkv03YNssT8GNK8tNdf_c/export?format=csv",
                 page="https://zerodha.com/disclosure/"),
 "kotak-securities": dict(kind="html", url="https://www.kotakneo.com/contact-us/investor-grievance-report-stock-brokers/"),
 "hdfc-sky": dict(kind="html", url="https://hdfcsec.com/investor-complaints-data-stock-broking"),
 "icici-direct": dict(kind="pdf", url="https://secure.icicidirect.com/customer/staticdata/Annexure-B_Complaint%20format_Stock%20broker.pdf",
                      page="https://www.icicidirect.com/grievance-redressal/grievance-redressal.html"),
 "upstox": dict(kind="pdf_via_page", page="https://upstox.com/investor-complaint-details", base="https://assets.upstox.com/content/assets/pdfs/cms/investor-details/",
                pat=r"investor-charterwebsitedatasecurities[a-z0-9]+\.pdf"),
 "sahi-broking": dict(kind="pdf_via_page", page="https://www.sahi.com/investor-charters-and-grievance", base="https://www.sahi.com/assets/uploads/",
                      pat=r"[A-Z][a-z]{2}_20\d\d_[0-9a-f]{10}\.pdf"),
 "dhan": dict(kind="pdf", url="https://dhan.co/download-centre-pdf/Grievances.pdf", latest_order="cf,rec,res,pend"),
 "sharekhan": dict(kind="pdf", url="https://www.sharekhan.com/MediaGalary/Newsletter/Stock-Broker-Complaint-Data-271124.pdf",
                   page="https://www.sharekhan.com/MediaGalary/Newsletter/ComplaintDisclosure-271124.html"),
 "5paisa": dict(kind="pdf_monthly_guess", tmpl="https://storage.googleapis.com/5paisa-prod-storage/files/investor_charter/{upl}/stock-broker-{mon}.pdf"),
 "groww": dict(kind="manual", page="https://groww.in/investor-relations",
               note="Groww posts each month as a new PDF with a hashed file name; no stable index page found. Last file found: June 2026."),
 "angel-one": dict(kind="missing", page="https://www.angelone.in/investor-charter",
                   note="Investor charter page shows only blank SEBI templates; no filled monthly stock-broker complaint data found."),
 "fyers": dict(kind="missing", page="https://fyers.in/investor-charter-stock-brokers",
               note="Investor charter page has no monthly complaint figures; no data file found."),
}
def get(url, binary=False):
    time.sleep(random.uniform(8, 15))
    r = subprocess.run(["curl", "-sfL", "-m", "60", "-A", UA, url], capture_output=True)
    if r.returncode: raise RuntimeError(f"HTTP fail {url}")
    return r.stdout
def pdftext(b):
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(b); f.flush()
        return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True).stdout
def htmltext(b):
    t = b.decode("utf8", "ignore"); t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"</t[dh]>", " | ", t); t = re.sub(r"</tr>|<br\s*/?>", "\n", t); t = re.sub(r"<[^>]+>", " ", t)
    return H.unescape(t)
N = r"(\d[\d,]*)"; S = r"[\s|,]+"
MPAT = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?[\s,\-]*(20)?(2\d)\b" + (S + N) * 4)
def ym(m, y): return f"20{y}-{MON[m.lower()[:3]]:02d}"
def trend(text):
    out = {}
    for m in MPAT.finditer(text):
        k = ym(m.group(1), m.group(3))
        if k in out: continue  # first table on the page = stock broking
        cf, rec, res, pend = (int(x.replace(",", "")) for x in m.groups()[3:7])
        out[k] = dict(carried_forward=cf, received=rec, resolved=res, pending_end=pend)
    return out
def latest_block(text, order):
    m = re.search(r"(?i)month ending\W+(?:\d\d/(\d\d)/20(\d\d)|([A-Za-z]+)\W*(?:20)?(\d\d)\b)", text)
    g = re.search(r"(?i)grand\s+total" + (S + N) * 4, text)
    if not (m and g): return {}
    k = f"20{m.group(2)}-{m.group(1)}" if m.group(1) else ym(m.group(3), m.group(4)[-2:])
    v = dict(zip(order.split(","), (int(x.replace(",", "")) for x in g.groups())))
    return {k: dict(carried_forward=v["cf"], received=v["rec"], resolved=v["res"], pending_end=v["pend"])}
def avg_days(text):
    g = re.search(r"(?i)grand\s+total[^\n]*", text)
    return None
def zerodha(text):
    out = {}; cur = None
    for line in text.splitlines():
        c = [x.strip() for x in line.split(",")]
        if len(c) > 2 and re.fullmatch(r"[A-Z][a-z]+ 20\d\d", c[1]) and not any(c[2:5]): cur = ym(c[1][:3], c[1][-2:]); continue
        if cur and len(c) > 9 and c[1] == "Total":
            try: out[cur] = dict(carried_forward=int(c[2] or 0), received=int(c[3]), resolved=int(c[6]), pending_end=int(c[7] or 0),
                                 avg_resolution_days=float(c[9]) if c[9] else None)
            except ValueError: pass
            cur = None
    return out
def fetch(slug, cfg):
    k = cfg["kind"]
    if k == "zerodha_csv": return zerodha(get(cfg["url"]).decode()), cfg["url"]
    if k == "html": return trend(htmltext(get(cfg["url"]))), cfg["url"]
    if k in ("pdf", "pdf_via_page"):
        url = cfg.get("url")
        if k == "pdf_via_page":
            names = [n for n in re.findall(cfg["pat"], get(cfg["page"]).decode("utf8", "ignore"))]
            if not names: raise RuntimeError("no data link on page")
            url = cfg["base"] + names[0]
        t = pdftext(get(url)); d = trend(t)
        if cfg.get("latest_order"):
            for kk, v in latest_block(t, cfg["latest_order"]).items(): d.setdefault(kk, v)
        return d, url
    if k == "pdf_monthly_guess":
        today = dt.date.today(); best = None
        for back in range(1, 4):
            m = (today.replace(day=1) - dt.timedelta(days=28 * back)).replace(day=1); up = (m.replace(day=28) + dt.timedelta(days=5)).replace(day=1)
            url = cfg["tmpl"].format(upl=up.strftime("%Y-%m"), mon=m.strftime("%b").lower())
            try: return trend(pdftext(get(url))), url
            except RuntimeError: continue
        raise RuntimeError("no monthly file found")
    raise RuntimeError(k)
def main():
    prev = json.load(open(OUT)) if os.path.exists(OUT) else {"brokers": {}}
    today = dt.date.today().isoformat(); res = {}
    for slug, cfg in SRC.items():
        p = prev["brokers"].get(slug, {})
        b = dict(entity=ENTITY[slug], active_clients=ACTIVE.get(slug), source_page=cfg.get("page") or cfg.get("url"), months=p.get("months", {}),
                 data_url=p.get("data_url"), fetched_on=p.get("fetched_on"), fetch_status=cfg["kind"] if cfg["kind"] in ("manual", "missing") else "stale",
                 note=cfg.get("note", ""))
        if cfg["kind"] not in ("manual", "missing"):
            try:
                d, url = fetch(slug, cfg)
                d = {k: v for k, v in d.items() if k >= "2025-10"}
                if d:
                    for k, v in d.items(): b["months"][k] = {**b["months"].get(k, {}), **{x: y for x, y in v.items() if y is not None}}
                    b.update(data_url=url, fetched_on=today, fetch_status="ok")
            except Exception as e: b["note"] = f"refresh failed {today}: {e}"
        b["months"] = dict(sorted(b["months"].items()))
        res[slug] = b; print(slug, b["fetch_status"], list(b["months"])[-3:] if b["months"] else "-")
    json.dump(dict(updated=today, active_clients_source=ACTIVE_SRC,
                   definition="Monthly totals across all sources (direct, SEBI SCORES, exchanges, other) from the broker's SEBI-mandated Investor Complaints disclosure.",
                   brokers=res), open(OUT, "w"), indent=1)
if __name__ == "__main__": main()
