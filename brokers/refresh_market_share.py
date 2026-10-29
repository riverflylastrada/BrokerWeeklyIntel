"""Monthly refresh of brokers/market_share_history.json from NSE Report 1C
(broker-wise active clients, UCCs, complaints). Runs from .github/workflows/nse-report-1c.yml
on the 2nd and 4th of each month. Polite: <=4 requests with 3s gaps. No-op if the month exists."""
import json,re,os,sys,time,csv,datetime,io,urllib.request,http.cookiejar
import pandas as pd
D=os.path.dirname(os.path.abspath(__file__));F=os.path.join(D,'market_share_history.json')
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
import pandas as pd,re,glob,json,datetime,sys
MA={m:i+1 for i,m in enumerate('jan feb mar apr may jun jul aug sep oct nov dec'.split())}
def parse(path):
    v=pd.read_excel(path,header=None,dtype=str)
    title=' '.join(str(x) for x in v.iloc[0] if str(x)!='nan')
    m=re.search(r'Updated on\s*(\d{1,2})[- ]([A-Za-z]+)[- ](\d{4})',title)
    upd=datetime.date(int(m.group(3)),MA[m.group(2)[:3].lower()],int(m.group(1)))
    fy=re.search(r'during (\d{4})-(\d{2,4})',title)
    # month of active client data: last day of month <= upd; if upd day<25 use previous month
    y,mo=upd.year,upd.month
    if upd.day<25: mo-=1; y-= mo==0; mo=mo or 12
    # but cap at FY end (March)
    fyend=(int(fy.group(1))+1,3)
    if (y,mo)>fyend: y,mo=fyend
    hdr=None
    for i in range(15):
        row=[str(x).upper() for x in v.iloc[i]]
        if any('NAME OF THE TM' in x for x in row): hdr=i;break
    H={}
    for i in range(hdr,hdr+3):
        for j,x in enumerate(v.iloc[i]):
            x=str(x).upper()
            if 'NAME OF THE TM' in x:H['name']=j
            elif 'BEGINNING OF THE YEAR' in x:H['total_ucc']=j
            elif 'ACTIVE CLIENTS' in x and 'PERCENT' not in x:H['active']=j
            elif 'RECEIVED AGAINST TM' in x:H['complaints']=j
            elif 'RESOLVED THROUGH' in x:H['resolved']=j
            elif 'PENDING FOR REDRESSAL WITH EXCHANGE' in x:H['pending']=j
            elif 'ARBITRATION FILED' in x:H['arb_filed']=j
    rows=[]
    def num(x):
        try: return int(float(str(x).replace(',','')))
        except: return None
    for i in range(hdr+1,len(v)):
        r=v.iloc[i];n=str(r[H['name']]).strip()
        if not re.match(r'^\d+$',str(r[0]).strip()): continue
        d=dict(legal_name=n,active_clients=num(r[H['active']]))
        for k in ['total_ucc','complaints','resolved','pending','arb_filed']:
            if k in H: d[k]=num(r[H[k]])
        rows.append(d)
    return dict(month=f"{y}-{mo:02d}",updated=str(upd),fy=fy.group(0)[7:],rows=rows,cols=sorted(H))
N=[('zerodha','Zerodha'),('groww|nextbillion','Groww'),('rksv|upstox','Upstox'),('angel','Angel One'),('icici sec','ICICI Direct'),('hdfc sec','HDFC Securities'),('kotak sec','Kotak Securities'),('sharekhan','Sharekhan'),('5paisa','5Paisa'),('motilal','Motilal Oswal'),('axis sec','Axis Direct'),('sbicap','SBI Securities'),('iifl|india infoline','IIFL Securities'),('paytm','Paytm Money'),('raise sec','Dhan'),('fyers','Fyers'),('karvy','Karvy'),('geojit','Geojit'),('indstocks|indmoney','INDmoney'),('aaritya','Sahi'),('choice equity','Choice'),('edelweiss|nuvama','Nuvama (Edelweiss)'),('alice blue','Alice Blue'),('samco','Samco'),('religare','Religare'),('smc global','SMC Global'),('m stock|mirae','m.Stock (Mirae)')]
def norm(n):
    for k,v in N:
        if re.search(k,n.lower()): return v
    return re.sub(r'\s+(Limited|Ltd\.?|Pvt\.?|Private)\b.*$','',n.strip(),flags=re.I).title()

def fy_code(d):
    y=d.year if d.month>=4 else d.year-1
    return f"{y%100:02d}{(y+1)%100:02d}"
def fetch():
    today=datetime.date.today();prev=(today.replace(day=1)-datetime.timedelta(days=1))
    code=fy_code(prev);url=f"https://nsearchives.nseindia.com/miscellaneous/ArbitrationReports/isc_report1C_{code}.xls"
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    h={'User-Agent':UA,'Accept':'*/*','Accept-Language':'en-US,en;q=0.9','Referer':'https://www.nseindia.com/invest/arbitration-status'}
    for u in ['https://www.nseindia.com/','https://www.nseindia.com/invest/arbitration-status']:
        try: op.open(urllib.request.Request(u,headers=h),timeout=30).read()
        except Exception as e: print('warmup',u,e)
        time.sleep(3)
    try:
        b=op.open(urllib.request.Request(url,headers=h),timeout=60).read();src=url
    except Exception as e:
        print('NSE live failed',e,'-> wayback');time.sleep(3)
        b=urllib.request.urlopen(urllib.request.Request('https://web.archive.org/web/2id_/'+url,headers={'User-Agent':UA}),timeout=120).read();src='https://web.archive.org/web/'+url
    p=os.path.join('/tmp',f'isc_report1C_{code}.xls');open(p,'wb').write(b);return p,src,prev.strftime('%Y-%m')
data=json.load(open(F));have={m['month'] for m in data['months']}
today=datetime.date.today();want=(today.replace(day=1)-datetime.timedelta(days=1)).strftime('%Y-%m')
if want in have and not os.environ.get('FORCE'): print('month',want,'already present; no-op');sys.exit(0)
p,src,_=fetch();r=parse(p)
if r['month'] in have and not os.environ.get('FORCE'): print('file still shows',r['month'],'(not yet updated by NSE); no-op');sys.exit(0)
agg={}
for x in r['rows']:
    if not x['active_clients']: continue
    b=norm(x['legal_name'])
    if b in agg: b=x['legal_name'].title()
    agg[b]=dict(broker=b,legal_name=x['legal_name'],active_clients=x['active_clients'],**{k:x[k] for k in ['total_ucc','complaints','resolved','pending','arb_filed'] if x.get(k) is not None})
rows=sorted(agg.values(),key=lambda x:-x['active_clients'])
for i,x in enumerate(rows): x['rank']=i+1
data['months']=[m for m in data['months'] if m['month']!=r['month']]+[dict(month=r['month'],source='NSE Report 1C (isc_report1C)',source_url=src,nse_updated=r['updated'],fy=r['fy'],broker_count=len(rows),brokers=rows)]
data['months'].sort(key=lambda m:m['month']);data['last_month']=data['months'][-1]['month']
json.dump(data,open(F,'w'),indent=0,separators=(',',':'))
cols=['month','rank','broker','legal_name','active_clients','total_ucc','complaints','resolved','pending','arb_filed','source_url']
with open(F.replace('.json','.csv'),'w') as f:
    w=csv.writer(f);w.writerow(cols)
    for m in data['months']:
        for x in m['brokers']: w.writerow([m['month']]+[x.get(c,'') for c in cols[1:-1]]+[m['source_url']])
print('added',r['month'],len(rows),'brokers')
