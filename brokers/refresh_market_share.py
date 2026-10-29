"""Monthly refresh: append new NSE active-client months from the TradingQnA thread.
Polite: 2 requests, then exits. No-op if no new month."""
import json,re,html,csv,time,urllib.request,os,sys
H={'User-Agent':'PaisaInsights-bot (+https://paisainsights.in)'}
D=os.path.dirname(os.path.abspath(__file__));F=os.path.join(D,'market_share_history.json')
def get(u):
    time.sleep(3);return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60))
MA={m:i+1 for i,m in enumerate('jan feb mar apr may jun jul aug sep oct nov dec'.split())}
N=[('zerodha','Zerodha'),('groww|nextbillion','Groww'),('rksv|upstox','Upstox'),('angel','Angel One'),('icici sec','ICICI Direct'),('hdfc sec','HDFC Securities'),('kotak sec','Kotak Securities'),('sharekhan','Sharekhan'),('5paisa','5Paisa'),('motilal','Motilal Oswal'),('axis sec','Axis Direct'),('sbicap','SBI Securities'),('iifl|india infoline','IIFL Securities'),('paytm','Paytm Money'),('raise sec','Dhan'),('fyers','Fyers'),('karvy','Karvy'),('geojit','Geojit'),('indstocks|indmoney','INDmoney'),('aaritya','Sahi'),('choice equity','Choice'),('edelweiss|nuvama','Nuvama (Edelweiss)'),('alice blue','Alice Blue'),('samco','Samco'),('religare','Religare'),('smc global','SMC Global'),('m stock|mirae','m.Stock (Mirae)'),('dhan','Dhan')]
def norm(n):
    for k,v in N:
        if re.search(k,n.lower()): return v
    return n.title().replace(' Limited','').replace(' Ltd.','').strip()
def parse(p):
    c=re.sub(r'<aside.*?</aside>','',p['cooked'],flags=re.S)
    if '<table' not in c: return None
    pre=html.unescape(re.sub('<[^>]+>',' ',c.split('<table')[0]))[:400]
    m=re.search(r'data for\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(20\d\d)',pre,re.I)
    if not m: return None
    month=f"{m.group(2)}-{MA[m.group(1).lower()]:02d}";agg={}
    for tr in re.findall(r'<tr>(.*?)</tr>',c,re.S):
        cells=[html.unescape(re.sub('<[^>]+>','',x)).strip() for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',tr,re.S)]
        name=next((x for x in cells if re.search('[A-Za-z]{3}',x) and not x.startswith(':')),None)
        nums=[int(x.replace(',','')) for x in cells if re.fullmatch(r'[\d,]{4,}',x)]
        if name and nums: agg.setdefault(norm(name),(nums[0],name))
    rows=sorted(agg.items(),key=lambda x:-x[1][0])
    if len(rows)<10: return None
    return dict(month=month,source_url=f"https://tradingqna.com/t/who-are-the-largest-brokerage-firms-in-india/17308/{p['post_number']}",posted=p['created_at'][:10],brokers=[dict(rank=i+1,broker=b,legal_name=ln,active_clients=v) for i,(b,(v,ln)) in enumerate(rows)])
data=json.load(open(F));have={m['month'] for m in data['months']}
ids=get('https://tradingqna.com/t/17308.json')['post_stream']['stream'][-20:]
posts=get('https://tradingqna.com/t/17308/posts.json?'+'&'.join(f'post_ids[]={i}' for i in ids))['post_stream']['posts']
new=[r for r in map(parse,posts) if r and r['month'] not in have]
if not new: print('no new month');sys.exit(0)
data['months']=sorted(data['months']+new,key=lambda m:m['month']);data['last_month']=data['months'][-1]['month']
json.dump(data,open(F,'w'),indent=1)
with open(F.replace('.json','.csv'),'w') as f:
    w=csv.writer(f);w.writerow(['month','rank','broker','legal_name','active_clients','source_url'])
    for m in data['months']:
        for r in m['brokers']: w.writerow([m['month'],r['rank'],r['broker'],r['legal_name'],r['active_clients'],m['source_url']])
print('added',[m['month'] for m in new])
