"""Build processed NSE investor-services data from raw Report files in brokers/nse/raw/.
Outputs (brokers/nse/): complaints_1a.json, penalties_4b.json, arbitration_1c.json, arbitrators_3b.json, nse_broker_summary.json
Reports: 1A complaint-level (per TM), 1C redressal + arbitration per TM, 3B arbitrator disposal (no TM names), 4A/4B penal actions per TM."""
import pandas as pd, re, json, glob, os, datetime as dt, statistics, collections
D=os.path.dirname(os.path.abspath(__file__)); R=os.path.join(D,'raw')
SRC='https://nsearchives.nseindia.com/miscellaneous/ArbitrationReports/'
TRACK=[('zerodha','zerodha'),('groww','groww|nextbillion'),('upstox','rksv|upstox'),('angel-one','angel (one|broking)'),('dhan','raise securities|moneylicious'),
 ('kotak-securities','kotak securities'),('icici-direct','icici securities'),('hdfc-sky','hdfc securities'),('sharekhan','sharekhan'),('5paisa','5paisa'),
 ('fyers','fyers'),('sahi-broking','aaritya')]
def slug_of(n):
    l=n.lower()
    for s,p in TRACK:
        if re.search(p,l): return s
def key(n):  # canonical TM key for all brokers
    s=slug_of(n)
    if s: return s
    n=re.sub(r'\(.*?\)','',n.lower()); n=re.sub(r'\b(private|pvt|limited|ltd|llp|the|co|company|india)\b|[^a-z0-9 ]',' ',n)
    return '-'.join(n.split())
BAD=[]
def rx(f):
    try: return pd.read_excel(f,header=None,dtype=str,engine_kwargs=dict(ignore_workbook_corruption=True))
    except Exception as e:
        BAD.append(os.path.basename(f)); return None
def fy_of(f): m=re.search(r'_(\d{4})\.xls',f); return f"20{m.group(1)[:2]}-{m.group(1)[2:]}" if m else None
def num(x):
    try:
        f=float(str(x).replace(',',''));return 0.0 if f!=f else f
    except: return 0.0
def date(x):
    s=str(x).strip()
    for f in ('%Y-%m-%d %H:%M:%S','%d-%b-%y','%d-%b-%Y','%d/%m/%Y','%d-%m-%Y','%Y-%m-%d','%d.%m.%Y'):
        try: return dt.datetime.strptime(s,f).date()
        except: pass
TYPES={'I':'Payment delay / non-receipt','II':'Securities delay / non-receipt','III':'Documents not received','IV':'Unauthorised trades / misappropriation',
 'V':'Service related','VI':'Square-off / close-out','VII':'Arbitration award not implemented','VIII':'IPO related','IX':'Others'}
STAT={'I':'non_actionable','II':'resolved','III':'under_process','IV':'arbitration'}
def stat(s):
    s=str(s).strip(); u=s.upper()
    if u in STAT: return STAT[u]
    l=s.lower()
    if 'resolv' in l: return 'resolved'
    if 'non' in l: return 'non_actionable'
    if 'arbitr' in l: return 'arbitration'
    if 'process' in l or 'pending' in l: return 'under_process'
    return 'other'
def types(s):
    s=str(s).upper().replace('TYPE','')
    out=set()
    for t in re.findall(r'\b(IX|VIII|VII|VI|V|IV|III|II|I)\b',s): out.add(t)
    return out or {'IX'}
# ---------- 1A ----------
c1a=collections.defaultdict(lambda: collections.defaultdict(lambda: dict(total=0,types=collections.Counter(),status=collections.Counter(),res_days=[])))
names={}; files1a=[]
for f in sorted(glob.glob(f'{R}/isc_report1A_*.xls')):
    v=rx(f)
    if v is None: continue
    files1a.append(dict(fy=fy_of(f),file=SRC+os.path.basename(f),title=str(v.iloc[0,0])[:200]))
    hdr=next(i for i in range(10) if any('NAME OF TM' in str(x).upper() for x in v.iloc[i]))
    H={str(x).upper().strip():j for j,x in enumerate(v.iloc[hdr])}
    col=lambda k: next(j for h,j in H.items() if k in h)
    cd,ct,cn,cs,csd=col('DATE OF RECEIPT'),col('TYPE OF COMPLAINT'),col('NAME OF TM'),col('STATUS*'),col('STATUS DATE')
    for i in range(hdr+1,len(v)):
        r=v.iloc[i]; d=date(r[cd]); n=str(r[cn]).strip()
        if not d or n in('nan','-',''): continue
        k=key(n); names.setdefault(k,n); m=c1a[k][d.strftime('%Y-%m')]
        m['total']+=1
        for t in types(r[ct]): m['types'][t]+=1
        st=stat(r[cs]); m['status'][st]+=1
        sd=date(r[csd])
        if st in('resolved','non_actionable') and sd and sd>=d: m['res_days'].append((sd-d).days)
out1a={}
for k,ms in c1a.items():
    mo={}
    for mk,m in sorted(ms.items()):
        rd=m.pop('res_days'); mo[mk]=dict(total=m['total'],types=dict(m['types']),status=dict(m['status']),median_resolution_days=statistics.median(rd) if rd else None,resolved_n=len(rd))
    out1a[k]=dict(name=names[k],slug=slug_of(names[k]),months=mo)
json.dump(dict(report='NSE Report 1A: complaints received from clients against Trading Members (complaint-level, aggregated per TM per month of receipt)',
  type_legend=TYPES,status_legend=STAT,files=files1a,note='Status is as of the file\'s last update; resolution days = status date - receipt date for resolved/non-actionable complaints.',brokers=out1a),
  open(f'{D}/complaints_1a.json','w'),separators=(',',':'))
# ---------- 4A/4B ----------
pen=collections.defaultdict(dict); files4=[]
for f in sorted(glob.glob(f'{R}/isc_report4[AB]_*.xls')):
    v=rx(f)
    if v is None: continue
    fy=fy_of(f); files4.append(dict(fy=fy,file=SRC+os.path.basename(f)))
    for i in range(len(v)):
        r=v.iloc[i]
        if not re.fullmatch(r'\d+',str(r[0]).strip()) or str(r[1])=='nan': continue
        n=str(r[1]).strip(); k=key(n); names.setdefault(k,n)
        vals=[num(r[j]) if j<len(r) else 0 for j in range(3,9)]
        e=pen[k].setdefault(fy,dict(name=n,registration=str(r[2]).strip(),complaints=0,penal_orders_complaints=0,penal_orders_others=0,penalty_lakh_complaints=0.0,penalty_lakh_others=0.0,arbitration_awards_against=0))
        # 4B lists one row per penal order in recent years: sum orders/penalties, keep max of per-TM counts
        e['complaints']=max(e['complaints'],int(vals[0])); e['arbitration_awards_against']=max(e['arbitration_awards_against'],int(vals[5]))
        e['penal_orders_complaints']+=int(vals[1]); e['penal_orders_others']+=int(vals[2])
        e['penalty_lakh_complaints']=round(e['penalty_lakh_complaints']+vals[3],4); e['penalty_lakh_others']=round(e['penalty_lakh_others']+vals[4],4)
outp={k:dict(name=names[k],slug=slug_of(names[k]),years=dict(sorted(y.items()))) for k,y in pen.items()}
json.dump(dict(report='NSE Report 4A/4B: penal actions against Trading Members (per FY)',files=files4,
  note='Penalties in Rs lakh. Orders/penalties may relate to the TM, its sub-brokers or authorised persons. Older files may leave blank columns (treated as 0).',brokers=outp),
  open(f'{D}/penalties_4b.json','w'),separators=(',',':'))
# ---------- 1C arbitration + complaints per TM (latest copy per FY) ----------
arb={}; files1c=[]
best={}
for f in sorted(glob.glob(f'{R}/wb_*.xls'))+sorted(glob.glob(f'{R}/isc_report1C_*.xls')):
    m=re.search(r'1C_(\d{4})',f) or re.search(r'wb_(\d{4})_',f)
    best[m.group(1)]=f  # sorted => live isc_report1C_* and latest wayback last
for code,f in sorted(best.items()):
    v=rx(f)
    if v is None: continue
    fy=f"20{code[:2]}-{code[2:]}"; files1c.append(dict(fy=fy,file=SRC+f"isc_report1C_{code}.xls",title=str(v.iloc[0,0])[:160]))
    hdr=next(i for i in range(12) if any('NAME OF THE TM' in str(x).upper() for x in v.iloc[i]))
    H={}
    for i in range(hdr,hdr+3):
        for j,x in enumerate(v.iloc[i]):
            x=str(x).upper()
            if 'NAME OF THE TM' in x:H['name']=j
            elif 'ARBITRATION FILED' in x:H['filed']=j
            elif 'IN FAVOUR OF CLIENTS' in x or 'IN FAVOR OF CLIENTS' in x:H['fav']=j
            elif 'DECIDED BY THE ARBITRATORS' in x or ('DECIDED BY' in x and 'FAVO' not in x):H['decided']=j
            elif 'RECEIVED AGAINST TM' in x:H['complaints']=j
            elif 'ACTIVE CLIENTS' in x and 'PERCENT' not in x:H['active']=j
    for i in range(hdr+1,len(v)):
        r=v.iloc[i]
        if not re.fullmatch(r'\d+',str(r[0]).strip()): continue
        n=str(r[H['name']]).strip(); k=key(n); names.setdefault(k,n)
        g=lambda c: int(num(r[H[c]])) if c in H else None
        arb.setdefault(k,dict(name=n,slug=slug_of(n),years={}))['years'][fy]=dict(complaints=g('complaints'),active_clients=g('active'),arbitration_filed=g('filed'),arbitration_decided=g('decided'),decided_for_client=g('fav'))
json.dump(dict(report='NSE Report 1C: redressal of complaints and arbitration per TM (financial-year-to-date, latest copy per FY)',files=files1c,brokers=arb),
  open(f'{D}/arbitration_1c.json','w'),separators=(',',':'))
# ---------- 3B industry arbitration (per arbitrator; no TM names) ----------
ind={}
for f in sorted(glob.glob(f'{R}/isc_report3B*_*.xls')):
    v=rx(f)
    if v is None: continue
    fy=fy_of(f); kind='appellate' if '3B2' in f else 'arbitration'
    aw=ap=fav=0
    for i in range(len(v)):
        r=v.iloc[i]
        if re.fullmatch(r'\d+',str(r[0]).strip()): aw+=num(r[2]); ap+=num(r[3]); fav+=num(r[4])+num(r[5])
    ind.setdefault(fy,{})[kind]=dict(awards_arbitration=int(aw),awards_appellate=int(ap),awards_in_client_favour=int(fav) if kind=='arbitration' else None,file=SRC+os.path.basename(f))
json.dump(dict(report='NSE Report 3B: disposal of arbitration by arbitrator (industry totals; NSE does not name the TM in 3B)',years=ind),open(f'{D}/arbitrators_3b.json','w'),indent=0)
print('unreadable',BAD);print('1A TMs',len(out1a),'4B TMs',len(outp),'1C TMs',len(arb),'3B years',len(ind))
for s,_ in TRACK:
    a=out1a.get(s,{}).get('months',{}); p=outp.get(s,{}).get('years',{}); c=arb.get(s,{}).get('years',{})
    print(s,'1A months',len(a),sum(x['total'] for x in a.values()),'| 4B',{y:(x['penal_orders_complaints']+x['penal_orders_others'],x['penalty_lakh_complaints']+x['penalty_lakh_others']) for y,x in p.items() if y>='2023'},'| arb',{y:(x['arbitration_decided'],x['decided_for_client']) for y,x in c.items() if y>='2024'})
