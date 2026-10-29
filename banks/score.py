import json,math,re,sys,datetime as dt,urllib.request,os
from collections import defaultdict
items=json.load(open('items.json'))
meta=json.load(open('input.json'))['brokers']
news=json.load(open('news_curated.json'))
GROUP={"sbi":"PSB","pnb":"PSB","bank-of-baroda":"PSB","canara-bank":"PSB","au-bank":"SFB"}
# RBI RB-IOS FY25 Appendix 1.5: non-digital complaints /1000 accts, digital /1000 txns
RBI={"PSB":(0.037,0.00018),"PVT":(0.079,0.00048),"SFB":(0.046,0.00066)}
# Bank-own disclosure (RBI Master Direction 'Disclosure of complaints'): maintainable complaints received from RBI Ombudsman offices (OBOs), FY2024-25,
# normalised per lakh customers (customer base from bank disclosures, approx). Standardised category across banks; raw 'complaints received' totals
# are not comparable because banks classify differently (e.g. SBI 28.5 lakh vs IDFC 21.6k).
OBO={"sbi":(27338,52.0,"FY25"),"indusind-bank":(6563,4.2,"FY25"),"idfc-first-bank":(3682,3.6,"FY25"),"hdfc-bank":(14563,9.3,"FY24")}
def obo_score(slug):
    if slug not in OBO: return None,None
    c,cr,fy=OBO[slug]; rate=c/(cr*100); return round(max(0,min(10,10-0.4*(rate-4))),2),round(rate,2)
def rbi_score(g):
    nd,d=RBI[g]; return round(10-2.5*(nd/0.037-1)-1.5*(d/0.00018-1)/2,2)
POS=set("good great excellent best smooth easy nice awesome love helpful fast amazing super superb useful convenient".split())
NEG=set("worst bad poor slow useless pathetic fraud scam terrible horrible issue problem error fail failed failing crash crashes hang stuck not waste disappointed annoying irritating".split())
TH={"service":r"customer care|customer service|support|branch|call cent|helpline|response|complain|executive|relationship manager",
"reliab":r"crash|server|down|not working|not open|otp|login|log in|error|failed|failure|hang|stuck|slow|loading|technical",
"fees":r"charge|fee|deduct|hidden|penalt|minimum balance|amc|interest rate|gst",
"fraud":r"fraud|scam|freez|frozen|blocked|debit without|unauthori",
"feature":r"feature|update|new ui|design|upi|fd|investment|easy to use|user friendly"}
def sent(it):
    if it.get('rating'): return (it['rating']-3)/2
    w=re.findall(r"[a-z']+",(it.get('title','')+' '+it.get('text','')).lower())
    p=sum(x in POS for x in w); n=sum(x in NEG for x in w)
    return 0 if p+n==0 else (p-n)/(p+n)
now=dt.datetime.now(dt.timezone.utc)
def age_w(it):
    t=it.get('created_utc')
    try:
        d=dt.datetime.fromtimestamp(float(t),dt.timezone.utc) if isinstance(t,(int,float)) or str(t).replace('.','').isdigit() else dt.datetime.fromisoformat(str(t).replace('Z','+00:00'))
        if d.tzinfo is None: d=d.replace(tzinfo=dt.timezone.utc)
        days=(now-d).days
    except Exception: days=15
    return 0.5**(max(days,0)/14)  # 14-day half-life
by=defaultdict(list)
for it in items: by[it.get('broker')].append(it)
raw={}
for m in meta:
    L=by.get(m['name'],[]); rv=[i for i in L if i['source'] in('play_store','app_store')]; so=[i for i in L if i['source'] in('reddit','youtube')]
    def wavg(xs,f):
        ws=[age_w(i) for i in xs]; return (sum(w*f(i) for w,i in zip(ws,xs))/sum(ws),sum(ws)) if xs else (None,0)
    def themeneg(t):
        xs=[i for i in L if re.search(TH[t],(i.get('text') or '').lower())]
        neg=sum(1 for i in xs if sent(i)<0); return neg,len(L)
    stars,wn=wavg(rv,lambda i:i['rating'])
    s_all,_=wavg(so,sent)
    raw[m['slug']]=dict(name=m['name'],n=len(L),n_rev=len(rv),n_soc=len(so),stars=stars,wn=wn,soc=s_all,
        counts={s:sum(1 for i in L if i['source']==s) for s in ('play_store','app_store','reddit','youtube')},
        th={t:themeneg(t) for t in ('service','reliab','fees','fraud')},
        feat_pos=sum(1 for i in L if re.search(TH['feature'],(i.get('text') or '').lower()) and sent(i)>0),
        L=L)
vals=[r['stars'] for r in raw.values() if r['stars']]; MU=sum(vals)/len(vals)
K=15
def shrink(x,n,mu,k=K): return mu if x is None else (n*x+k*mu)/(n+k)
def rate_score(neg,n,mu_rate):
    r=(neg+K*mu_rate)/(n+K) if n else mu_rate; return max(0,min(10,10-r*25))
mus={t:sum(r['th'][t][0] for r in raw.values())/max(1,sum(r['th'][t][1] for r in raw.values())) for t in ('service','reliab','fees','fraud')}
out=[]
for slug,r in raw.items():
    g=GROUP.get(slug,"PVT"); nw=news.get(slug,{})
    app=round((shrink(r['stars'],r['wn'],MU)-1)/4*10,1)
    svc=round(rate_score(*r['th']['service'],mus['service']),1)
    os_,orate=obo_score(slug)
    base=os_ if os_ is not None else 0.7*rbi_score(g)+0.3*7.5
    comp=round(0.5*base+0.5*rate_score(*r['th']['fraud'],mus['fraud']),1)
    rel=round(max(0,rate_score(*r['th']['reliab'],mus['reliab'])-1.0*nw.get('outages',0)),1)
    fee=round(rate_score(*r['th']['fees'],mus['fees']),1)
    inn=round(min(10,5+1.2*nw.get('features',0)+0.15*r['feat_pos']),1)
    buzz=round(5+4*shrink(r['soc'],r['n_soc'],0,10)+min(1,math.log10(1+r['n_soc'])/2),1)
    P=dict(app_experience=app,customer_service=svc,complaints_rbi=comp,digital_reliability=rel,fees_transparency=fee,innovation=inn,social_buzz=buzz)
    W=dict(app_experience=.22,customer_service=.15,complaints_rbi=.15,digital_reliability=.18,fees_transparency=.10,innovation=.10,social_buzz=.10)
    overall=round(sum(P[k]*W[k] for k in P),1)
    conf="High" if r['n']>=60 else "Medium" if r['n']>=25 else "Low"
    rv=sorted([i for i in r['L'] if i.get('text')],key=lambda i:-age_w(i))
    quotes=[dict(text=i['text'][:220],source=i['source'],rating=i.get('rating'),url=i.get('url'),sentiment="positive" if sent(i)>0 else "negative" if sent(i)<0 else "neutral") for i in (rv[:3]+[x for x in rv if sent(x)<0][:2]+[x for x in rv if sent(x)>0][:2])]
    seen=set(); quotes=[q for q in quotes if not (q['text'] in seen or seen.add(q['text']))][:6]
    themes=sorted([(t,r['th'][t][0]) for t in r['th']],key=lambda x:-x[1])
    out.append(dict(slug=slug,name=r['name'],group={"PSB":"Public sector","PVT":"Private sector","SFB":"Small finance"}[g],overall=overall,params=P,complaints_source=('Bank disclosure (OBO maintainable, %s): %s per lakh customers'%(OBO[slug][2],orate)) if orate else 'Estimated (bank disclosure not found; RBI peer-group rate, dampened)',confidence=conf,
      counts=r['counts'],avg_stars=round(r['stars'],2) if r['stars'] else None,
      top_complaint_themes=[dict(theme={"service":"Customer service","reliab":"App reliability / login / OTP","fees":"Charges & fees","fraud":"Fraud / blocked accounts"}[t],mentions=c) for t,c in themes if c],
      news=nw.get('items',[]),quotes=quotes))
out.sort(key=lambda x:-x['overall'])
for i,o in enumerate(out,1): o['rank']=i
json.dump(dict(category="banks",week=dt.date.today().strftime("%G-W%V"),generated_at=now.isoformat(),banks=out,category_mean_stars=round(MU,2)),open('bank_report.json','w'),indent=1,ensure_ascii=False)
for o in out: print(o['rank'],o['name'],o['overall'],o['confidence'],o['counts'],o['params'])
