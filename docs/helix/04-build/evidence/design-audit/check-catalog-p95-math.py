"""Independent Decimal order/comparison of authored design witnesses, no benchmark code."""
from pathlib import Path
from decimal import Decimal
import json,hashlib
B=Path(__file__).parent;R=B.parents[4];P=R/'docs/helix/02-design/contracts/bindings/catalog-p95-math-v0.1.vectors.json'
v=json.loads(P.read_text());results=[]
expected_ids={'below','equal','above','slow-outlier-retained','tied-all','ninety-nine-samples','hundred-and-one-samples','negative-duration','nonfinite-duration','duplicate-ordinal','missing-ordinal'}
if len(v['cases'])!=11 or {c['id'] for c in v['cases']}!=expected_ids:raise ValueError('incomplete/duplicate witness membership')
if (v['sampleCount'],v['rank'],v['thresholdMs'])!=(100,95,'20'):raise ValueError('changed governing mathematical profile')
for c in v['cases']:
 samples=[{'ordinal':i,'duration':d} for i,d in enumerate([r['durationMs'] for r in c['runs'] for _ in range(r['count'])])]
 if 'ordinalOverride' in c:samples[c['ordinalOverride']['sample']]['ordinal']=c['ordinalOverride']['ordinal']
 failure=None
 if len(samples)!=100:failure='sample-count'
 elif sorted(x['ordinal'] for x in samples)!=list(range(100)):failure='ordinal-membership'
 else:
  numbers=[Decimal(x['duration']) for x in samples]
  if any(not n.is_finite() or n<0 for n in numbers):failure='duration-domain'
 if failure:
  if c.get('expectedRefusal')!=failure:raise ValueError('wrong expected refusal: '+c['id'])
  results.append({'id':c['id'],'status':'expected-refusal','reason':failure});continue
 if 'expectedRefusal' in c:raise ValueError('missing refusal: '+c['id'])
 p95=sorted(numbers)[94];comparison='within-proposed-threshold' if p95<=Decimal('20') else 'above-proposed-threshold'
 if p95!=Decimal(c['expectedP95Ms']) or comparison!=c['expectedComparison']:raise ValueError('wrong mathematical witness: '+c['id'])
 results.append({'id':c['id'],'status':'pass','retainedSamples':len(samples),'p95Ms':str(p95),'comparison':comparison})
receipt={'scope':'Python Decimal independent finite mathematical rank-95 and 20ms comparison; malformed count/ordinal/domain witness refusal only; no Truss assessor/clock/grammar/result correctness/resource/native performance qualification','sourceSha256':hashlib.sha256(P.read_bytes()).hexdigest(),'cases':results,'nativeExecution':False}
(B/'catalog-p95-math.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'cases':len(results),'mathematicalCases':sum(x['status']=='pass' for x in results),'expectedRefusals':sum(x['status']=='expected-refusal' for x in results),'nativeExecution':False}))
