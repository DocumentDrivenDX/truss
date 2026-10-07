"""Exact selected-source delta only; missing routines/complete baseline prevent installation."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
old=json.loads((HERE/'row-home-native-guard-statement-composition.json').read_text())
new=json.loads((HERE/'row-home-edge-limit-guard-statement-composition.json').read_text())
om=json.loads((HERE/'row-home-native-guard-statement-mapping.json').read_text())
nm=json.loads((HERE/'row-home-edge-limit-guard-statement-mapping.json').read_text())
assert len(old['statements'])==20 and len(new['statements'])==23
extra='docs/helix/02-design/contracts/edge-limit-triggers-v0.1.proposal.umf.json'
retained=[s for s in new['statements'] if s['modelPath']!=extra]
assert [{k:v for k,v in s.items() if k!='ordinal'} for s in retained]==[{k:v for k,v in s.items() if k!='ordinal'} for s in old['statements']]
assert [s['modelPath'] for s in new['statements'][19:22]]==[extra]*3
assert new['statements'][-1]['executionKind']=='parameterized-initialization'
assert [x for x in new['inputs'] if x['modelPath']!=extra]==old['inputs']
ids=lambda m:{e['physicalIdentity'] for s in m['mapping'] for e in s['entries']}
oldids,newids=ids(om),ids(nm)
expected={'truss.edge-limit.trigger.edge_limit_edge_observe','truss.edge-limit.trigger.edge_limit_marker_observe','truss.edge-limit.trigger.edge_limit_catalog_observe'}
assert len(oldids)==139 and len(newids)==142 and newids-oldids==expected and oldids<=newids
assert not new['physicalCoverageComplete'] and not new['nativeExecution'] and not new['installable']
assert not nm['unmappedStatements']
result={'scope':'exact old twenty/new twenty-three selected source statements and three observer effect additions; no complete baseline, native bodies/dependencies/security or installation qualification','status':'pass','retainedStatements':20,'addedObserverStatements':3,'addedPhysicalIdentities':sorted(expected),'inputPins':[{'path':str(HERE/name),'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()} for name in ['row-home-native-guard-statement-composition.json','row-home-edge-limit-guard-statement-composition.json','row-home-native-guard-statement-mapping.json','row-home-edge-limit-guard-statement-mapping.json']]}
(HERE/'edge-limit-composition-delta.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'retainedStatements':20,'addedObservers':3,'status':'pass','installable':False}))
