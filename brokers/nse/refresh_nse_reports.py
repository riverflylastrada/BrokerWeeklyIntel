"""Download the current (and previous) financial year's NSE investor-services reports (1A, 1C, 3B, 4B) into raw/,
politely (3 s gaps, browser-like headers, Wayback fallback), then rebuild processed + site datasets.
Prints 'unchanged' and exits 0 if no file changed."""
import os,sys,time,hashlib,datetime,urllib.request,subprocess
D=os.path.dirname(os.path.abspath(__file__)); R=os.path.join(D,'raw')
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
B='https://nsearchives.nseindia.com/miscellaneous/ArbitrationReports/'
t=datetime.date.today(); s=t.year if t.month>=4 else t.year-1
codes=[f"{s%100:02d}{(s+1)%100:02d}"]+([f"{(s-1)%100:02d}{s%100:02d}"] if t.month<=6 else [])
h={'User-Agent':UA,'Referer':'https://www.nseindia.com/invest/arbitration-status','Accept':'*/*'}
changed=[]
for c in codes:
    for r in ('1A','1C','3B','4B'):
        n=f'isc_report{r}_{c}.xls'; p=os.path.join(R,n); b=None
        try: b=urllib.request.urlopen(urllib.request.Request(B+n,headers=h),timeout=90).read()
        except Exception as e:
            print(n,'live failed',e); time.sleep(3)
            try: b=urllib.request.urlopen(urllib.request.Request('https://web.archive.org/web/2id_/'+B+n,headers={'User-Agent':UA}),timeout=120).read()
            except Exception as e2: print(n,'wayback failed',e2)
        time.sleep(3)
        if not b or b[:4]!=b'\xd0\xcf\x11\xe0': continue
        old=open(p,'rb').read() if os.path.exists(p) else b''
        if hashlib.sha1(old).digest()!=hashlib.sha1(b).digest(): open(p,'wb').write(b); changed.append(n)
print('changed',changed or 'none')
for sc in (('build_nse.py',) if changed else ())+('build_site.py',): subprocess.run([sys.executable,os.path.join(D,sc)],check=True)  # site data also depends on active clients
