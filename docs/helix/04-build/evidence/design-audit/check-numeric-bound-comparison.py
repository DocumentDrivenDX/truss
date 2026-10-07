"""Finite design experiment; no original codec or native comparator qualification."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,re
path=Path(__file__).resolve().parents[3]/'02-design/contracts/bindings/numeric-bound-comparison-v0.1.vectors.json'
raw=path.read_bytes()
if len(raw)>32768:raise ValueError('experiment fixture bound')
fixture=json.loads(raw)
def admitted(w):
 d,e=w['digits'],w['exponent']
 if type(w['negative']) is not bool or len(d)>256 or len(e)>16:raise ValueError('experiment bound')
 if re.fullmatch(r'0|[1-9][0-9]*',d) is None or re.fullmatch(r'0|-?[1-9][0-9]*',e) is None:raise ValueError('witness grammar')
 if d=='0' and (w['negative'] or e!='0'):raise ValueError('noncanonical zero')
 if d!='0' and d.endswith('0'):raise ValueError('nonnormalized coefficient')
 return d,int(e),(-1 if w['negative'] else 1) if d!='0' else 0
sign=lambda n:(n>0)-(n<0)
def compare(a,b):
 ad,ae,asign=admitted(a);bd,be,bsign=admitted(b)
 if asign!=bsign:return sign(asign-bsign),0
 if asign==0:return 0,0
 am,bm=len(ad)+ae,len(bd)+be
 if am!=bm:return asign*sign(am-bm),0
 visits=0
 for i in range(max(len(ad),len(bd))):
  visits+=1
  x=ad[i] if i<len(ad) else '0';y=bd[i] if i<len(bd) else '0'
  if x!=y:return asign*sign(ord(x)-ord(y)),visits
 return 0,visits
def rational(w):
 d,e,s=admitted(w)
 if abs(e)>40:raise ValueError('independent rational experiment bound')
 return Fraction(s*int(d)*10**max(e,0),10**max(-e,0))
ids=set();rational_count=0;maxvisits=0
for pair in fixture['pairs']:
 if pair['id'] in ids:raise ValueError('duplicate case identity')
 ids.add(pair['id'])
 order,visits=compare(pair['left'],pair['right']);maxvisits=max(maxvisits,visits)
 if order!=pair['expectedOrder'] or visits>max(len(pair['left']['digits']),len(pair['right']['digits'])):raise ValueError(pair['id'])
 reverse,_=compare(pair['right'],pair['left'])
 if reverse!=-order:raise ValueError('antisymmetry '+pair['id'])
 if pair['independentRationalCheck']:
  rational_count+=1
  if sign(rational(pair['left'])-rational(pair['right']))!=pair['expectedOrder']:raise ValueError('independent oracle '+pair['id'])
if raw!=path.read_bytes():raise ValueError('fixture changed')
result={'status':'pass','cases':len(ids),'independentRationalCases':rational_count,'maxDigitVisits':maxvisits,'fixtureSha256':hashlib.sha256(raw).hexdigest(),'scope':fixture['scope'],'nativeExecuted':False,'profileAdopted':False}
Path(__file__).with_name('numeric-bound-comparison-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'pass','cases':len(ids),'independentRationalCases':rational_count,'maxDigitVisits':maxvisits}))
