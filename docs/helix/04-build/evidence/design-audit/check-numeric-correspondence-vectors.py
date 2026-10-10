"""Independent Decimal oracle for authored mathematical witnesses, not Truss parser."""
from pathlib import Path
from decimal import Decimal
import json,hashlib
p=Path(__file__).resolve().parents[3]/'02-design/contracts/bindings/numeric-correspondence-v0.1.vectors.json'
a=json.loads(p.read_text());assert len(a['vectors'])==11 and len(a['pairs'])==7
values=[]
for v in a['vectors']:
 digits=v['digits'];assert digits=='0' or (digits[0]!='0' and digits[-1]!='0')
 assert digits.isascii() and digits.isdigit()
 if digits=='0':assert not v['negative'] and v['exponent']=='0'
 original=Decimal(v['token']);assert original.is_finite()
 witness=Decimal((int(v['negative']),tuple(int(d) for d in digits),int(v['exponent'])))
 assert original==witness
 values.append(original)
for pair in a['pairs']:
 left,right=pair['left'],pair['right']
 assert (values[left]==values[right])==pair['mathematicallyEqual']
 assert (a['vectors'][left]['token']==a['vectors'][right]['token'])==pair['lexicallyEqual']
report={'status':'pass','scope':'eleven authored witnesses/seven mathematical versus lexical pairs checked by independent Python Decimal construction/equality; no Truss implementation, original grammar/facets/native representability/resource/enforcement qualification','vectorsSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'witnesses':11,'pairs':7,'nativeExecution':False}
Path(__file__).with_name('numeric-correspondence-vectors-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
