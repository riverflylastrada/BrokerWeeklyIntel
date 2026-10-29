"""Build compact site datasets from processed NSE files + market_share_history.json.
nse_brokers_tracked.json : per tracked slug -> monthly 1A complaints (types/status/resolution), active clients, per-lakh rate,
                           penalties per FY (4A/4B), arbitration per FY (1C) + pooled client-win rate.
nse_industry.json        : per month (FY2017-18+) -> every TM with complaints: count, types, active clients, per-lakh; plus penalties per FY for all TMs.
Run after build_nse.py."""
import json,os,re,math,collections
D=os.path.dirname(os.path.abspath(__file__))
exec(open(f'{D}/build_nse.py').read().split('BAD=[]')[0])  # imports, TRACK, slug_of, key
c1a=json.load(open(f'{D}/complaints_1a.json')); pen=json.load(open(f'{D}/penalties_4b.json')); arb=json.load(open(f'{D}/arbitration_1c.json')); a3b=json.load(open(f'{D}/arbitrators_3b.json'))
ms=json.load(open(f'{D}/../market_share_history.json'))['months']
act=collections.defaultdict(dict)
for m in ms:
    for b in m['brokers']:
        k=key(b['legal_name']); act[k][m['month']]=max(act[k].get(m['month'],0),b['active_clients'])
def active_at(k,mo):
    a=act.get(k,{}); c=[x for x in a if x<=mo]
    if not c: c=sorted(a)[:1]
    return (a[max(c)],max(c)) if c else (None,None)
def fy_of_month(mo):
    y,m=map(int,mo.split('-')); s=y if m>=4 else y-1; return f"{s}-{(s+1)%100:02d}"
tracked={}
for s,_ in TRACK:
    cm=c1a['brokers'].get(s,{}).get('months',{}); months={}
    for mo,x in sorted(cm.items()):
        if mo<'2017-04': continue
        a,am=active_at(s,mo)
        months[mo]=dict(x,active_clients=a,active_month=am,per_lakh=round(x['total']/a*1e5,2) if a else None)
    py=pen['brokers'].get(s,{}).get('years',{}); ay=arb['brokers'].get(s,{}).get('years',{})
    dec=sum((v['arbitration_decided'] or 0) for v in ay.values()); fav=sum((v['decided_for_client'] or 0) for v in ay.values())
    tracked[s]=dict(nse_name=c1a['brokers'].get(s,{}).get('name') or pen['brokers'].get(s,{}).get('name'),months=months,
        penalties={y:{k:v for k,v in d.items() if k not in('name',)} for y,d in py.items()},
        arbitration={y:d for y,d in ay.items()},
        arbitration_pooled=dict(decided=dec,decided_for_client=fav,client_win_rate=round(fav/dec*100,1) if dec else None,years=f"{min(ay) if ay else ''}..{max(ay) if ay else ''}"))
meta=dict(sources=dict(page='https://www.nseindia.com/invest/arbitration-status',report_1a=c1a['files'],report_4b=pen['files'],report_1c=arb['files'],report_3b=a3b),
  type_legend=c1a['type_legend'],status_legend=c1a['status_legend'],
  notes=['1A status is as of the file update date; resolution days = status date - receipt date (resolved/non-actionable).',
         'Per lakh = complaints received at NSE in the month / NSE active clients (Report 1C / market-share data, latest month <= complaint month) x 1,00,000.',
         '4B lists penal orders against the TM, its sub-brokers or authorised persons; most are for inspection/operational lapses ("for others"), not client complaints.',
         'Arbitration via NSE largely moved to SEBI SMART ODR from Aug 2023, so 1C arbitration counts are ~0 from FY2024-25; client-win rate is pooled over FY2016-17 to FY2023-24.',
         '3B is reported per arbitrator (NSE does not name the TM), so it is shown only as industry context.'])
json.dump(dict(meta,brokers=tracked),open(f'{D}/nse_brokers_tracked.json','w'),separators=(',',':'))
ind=collections.defaultdict(list)
for k,b in c1a['brokers'].items():
    for mo,x in b['months'].items():
        if mo<'2017-04': continue
        a,_=active_at(k,mo)
        ind[mo].append(dict(k=k,n=b['name'],s=b['slug'],c=x['total'],t=x['types'],st=x['status'],r=x['median_resolution_days'],a=a,pl=round(x['total']/a*1e5,2) if a else None))
pall={}
for k,b in pen['brokers'].items():
    for y,d in b['years'].items():
        if y>='2017-18': pall.setdefault(y,[]).append(dict(k=k,n=b['name'],s=b['slug'],o=d['penal_orders_complaints']+d['penal_orders_others'],l=round(d['penalty_lakh_complaints']+d['penalty_lakh_others'],3),c=d['complaints'],aw=d['arbitration_awards_against']))
for y in pall: pall[y].sort(key=lambda x:-x['l'])
json.dump(dict(meta,legend_keys=dict(k='tm key',n='NSE name',s='tracked slug or null',c='complaints',t='by type',st='by status',r='median resolution days',a='active clients',pl='per lakh active',o='penal orders',l='penalty Rs lakh',aw='arbitration awards against'),
  months={m:sorted(v,key=lambda x:-x['c']) for m,v in sorted(ind.items())},penalties=dict(sorted(pall.items()))),open(f'{D}/nse_industry.json','w'),separators=(',',':'))
print('tracked',len(tracked),'industry months',len(ind),min(ind),max(ind),'size',os.path.getsize(f'{D}/nse_industry.json')//1024,'KB',os.path.getsize(f'{D}/nse_brokers_tracked.json')//1024,'KB')
for s,t in tracked.items(): print(s,t['arbitration_pooled'])
