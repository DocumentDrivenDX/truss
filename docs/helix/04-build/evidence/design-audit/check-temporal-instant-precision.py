"""Exact parsed-parts arithmetic experiment; no production temporal codec."""
from pathlib import Path
from datetime import date
from fractions import Fraction
import hashlib,json,re
path=Path(__file__).resolve().parents[3]/'02-design/contracts/bindings/temporal-instant-precision-v0.1.vectors.json'
raw=path.read_bytes()
if len(raw)>16384:raise ValueError('experiment fixture bound')
fixture=json.loads(raw)
def ordinal(y,m,d):
 if not 1<=y<=9999 or not 1<=m<=12:raise ValueError('experiment Gregorian range')
 leap=y%4==0 and (y%100!=0 or y%400==0)
 days=[31,29 if leap else 28,31,30,31,30,31,31,30,31,30,31]
 if not 1<=d<=days[m-1]:raise ValueError('day')
 prior=y-1
 return 365*prior+prior//4-prior//100+prior//400+sum(days[:m-1])+d
ids=set();exact=0;refused=0
for c in fixture['cases']:
 if c['id'] in ids:raise ValueError('duplicate identity')
 ids.add(c['id'])
 y,m,d,h,minute,s=c['calendar'];f=c['fractionDigits'];p=c['nativePrecision'];offset=c['offsetMinutes']
 if len(f)>64 or re.fullmatch('[0-9]*',f) is None or not 0<=p<=6:raise ValueError('experiment fraction bound')
 if not 0<=h<24 or not 0<=minute<60 or not 0<=s<60 or not -1439<=offset<=1439:raise ValueError('experiment clock/offset range')
 seconds=(ordinal(y,m,d)-719163)*86400+h*3600+minute*60+s-offset*60
 independently=(date(y,m,d)-date(1970,1,1)).days*86400+h*3600+minute*60+s-offset*60
 if seconds!=independently:raise ValueError('independent calendar mismatch')
 if any(digit!='0' for digit in f[p:]):
  observed=None;refused+=1
 else:
  micros=seconds*1000000+int((f[:6]+'000000')[:6]);observed=str(micros);exact+=1
  rational=Fraction(independently)+Fraction(int(f or '0'),10**len(f))
  if rational*1000000!=micros:raise ValueError('independent fraction mismatch')
 rational=Fraction(independently)+Fraction(int(f or '0'),10**len(f))
 lattice=rational*10**p
 independent_observed=str(int(rational*1000000)) if lattice.denominator==1 else None
 if observed!=independent_observed:raise ValueError('independent precision mismatch '+c['id'])
 if observed!=c['expectedMicroseconds']:raise ValueError(c['id'])
if path.read_bytes()!=raw:raise ValueError('fixture changed')
result={'status':'pass','cases':len(ids),'exact':exact,'refused':refused,'fixtureSha256':hashlib.sha256(raw).hexdigest(),'scope':fixture['scope'],'nativeExecuted':False,'profileAdopted':False}
Path(__file__).with_name('temporal-instant-precision-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'pass','cases':len(ids),'exact':exact,'refused':refused}))
