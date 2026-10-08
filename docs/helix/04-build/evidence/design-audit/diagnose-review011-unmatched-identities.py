"""Unmatched source diagnostics only; never identity assignment/native equivalence."""
import collections
import hashlib
import json
import runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
BASE=ROOT/'docs/helix/04-build/evidence/design-audit'
m=runpy.run_path(str(BASE/'find-review011-original-node-correspondence.py'))
composition=json.loads((BASE/'request-receipt-layout-profile-composition.json').read_text())
ast_bytes=(ROOT/composition['astPath']).read_bytes()
if hashlib.sha256(ast_bytes).hexdigest()!=composition['astSha256']:raise ValueError('stale AST')
ast=json.loads(ast_bytes)
index=collections.defaultdict(list)
def normalized_hash(v):return m['node_hash'](m['without_locations'](v))
def walk(v,pointer):
 if isinstance(v,(dict,list)):
  index[normalized_hash(v)].append(pointer)
  for key,child in (v.items() if isinstance(v,dict) else enumerate(v)):
   walk(child,pointer+'/'+str(key).replace('~','~0').replace('/','~1'))
walk(ast,'')
entries=[]
for e in m['rows']:
 if e['state']!='no_exact_node_candidate':continue
 loc=e['originalLocator'];path=loc.get('modelPath',loc.get('model'))
 original=m['decode'](m['at'](m['models'][path],loc['jsonPointer']))
 candidates=index.get(normalized_hash(original),[])
 entries.append({'authoredId':e['authoredId'],'catalogPath':e['catalogPath'],
                 'originalLocator':loc,'originalTaggedNodeSha256':e['originalTaggedNodeSha256'],
                 'originalNativeDefinition':original,
                 'diagnosticNativeAstPointers':candidates,
                 'state':'unique_ignoring_parser_locations' if len(candidates)==1 else 'ambiguous_ignoring_parser_locations' if candidates else 'no_equivalent_definition_candidate'})
# Qualify the diagnostic comparator: ignore positions only, preserve meaning-bearing fields.
probe={'location':1,'stmt_location':2,'stmt_len':3,'name':'original','definition':{'value':'0.10','order':['a','b']}}
locations={**probe,'location':9,'stmt_location':10,'stmt_len':11}
if normalized_hash(probe)!=normalized_hash(locations):raise ValueError('position-only comparison failed')
controls=[]
for name,changed in [('name',{**probe,'name':'other'}),('numeric_token',{**probe,'definition':{'value':'0.1','order':['a','b']}}),('order',{**probe,'definition':{'value':'0.10','order':['b','a']}})]:
 if normalized_hash(probe)==normalized_hash(changed):raise ValueError('semantic change hidden: '+name)
 controls.append({'case':name,'distinct':True})
result={'scope':'Diagnostic native-definition comparison removing only location/stmt_location/stmt_len; no identity correspondence adoption, no native equivalence or installation qualification',
        'astPath':composition['astPath'],'astSha256':composition['astSha256'],
        'counts':dict(collections.Counter(e['state'] for e in entries)),
        'catalogCounts':dict(collections.Counter(e['catalogPath'] for e in entries)),
        'positionOnlyControlEqual':True,'semanticDifferenceControls':controls,
        'entries':entries,'identityAssignmentsMade':0,'nativeQualified':False}
(BASE/'review011-unmatched-identity-diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['counts']))
