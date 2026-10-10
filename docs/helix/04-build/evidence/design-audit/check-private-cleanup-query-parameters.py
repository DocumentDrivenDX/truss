"""Original parameter/projection AST correspondence only; no native execution."""
import copy,hashlib,json
from pathlib import Path
manifest_path=Path('docs/helix/02-design/contracts/bindings/truss-private-cleanup-query-parameters-v0.1.proposal.json')
manifest=json.loads(manifest_path.read_text())
def require(condition,message):
    if not condition:raise ValueError(message)
def decode(node):
    kind=node['kind']
    if kind=='object':return {k:decode(v) for k,v in node['members'].items()}
    if kind=='array':return [decode(v) for v in node['items']]
    if kind=='number':return int(node['value'])
    if kind=='null':return None
    return node['value']
def walk(node):
    yield node
    if isinstance(node,dict):
        for v in node.values():yield from walk(v)
    elif isinstance(node,list):
        for v in node:yield from walk(v)
def validate(candidate):
    require(len(candidate['queries'])==6,'six original statements required')
    expected_members={('private-custody-cleanup-identity-page-v0.1.proposal.sql',i) for i in range(1,5)}|{('private-custody-cleanup-selected-row-observation-v0.1.proposal.sql',i) for i in range(1,3)}
    actual_members=set()
    for q in candidate['queries']:
        source=Path(q['sourcePath']);identity=(source.name,q['statementOrdinal'])
        require(identity in expected_members and identity not in actual_members,'statement membership')
        actual_members.add(identity)
        require(hashlib.sha256(source.read_bytes()).hexdigest()==q['sourceSha256'],'source hash')
        archive=source.with_suffix('.umf.json')
        stem=source.name.removesuffix('-v0.1.proposal.sql')
        captured=json.loads(Path('docs/helix/04-build/evidence/design-audit',stem+'-source.json').read_text())
        original=next(o for o in captured['observations'] if o['path']==str(source))
        require(original['sourceSha256']==q['sourceSha256'],'original source receipt')
        require(hashlib.sha256(archive.read_bytes()).hexdigest()==original['artifactSha256'],'original archive receipt')
        model=json.loads(archive.read_text())
        root=decode(model['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
        select=root['stmts'][q['statementOrdinal']-1]['stmt']['SelectStmt']
        aliases=[t['ResTarget']['name'] for t in select['targetList']]
        require(aliases==q['outputAliases'],'projection order')
        require(set(q['nullableOutputAliases'])<=set(aliases),'nullable alias membership')
        refs=[n['ParamRef']['number'] for n in walk(select) if isinstance(n,dict) and 'ParamRef' in n]
        positions=[p['position'] for p in q['parameters']]
        require(refs==positions and positions==list(range(1,len(positions)+1)),'parameter occurrence/order')
        casts={}
        for n in walk(select):
            if not isinstance(n,dict) or 'TypeCast' not in n:continue
            cast=n['TypeCast'];nested=[x['ParamRef']['number'] for x in walk(cast['arg']) if isinstance(x,dict) and 'ParamRef' in x]
            names='.'.join(v['String']['sval'] for v in cast['typeName']['names'])
            for position in nested:casts.setdefault(position,[]).append(names)
        for p in q['parameters']:
            observed=casts[p['position']];expected=p['nativeCast'].split(' with ')[0]
            require(observed==([expected,'pg_catalog.text'] if expected!='pg_catalog.text' else ['pg_catalog.text']),'parameter native cast')
    require(actual_members==expected_members,'complete membership')
validate(manifest)
controls=[]
for name,mutate in [
 ('missing query',lambda x:x['queries'].pop()),
 ('wrong source hash',lambda x:x['queries'][0].update(sourceSha256='0'*64)),
 ('reordered projection',lambda x:x['queries'][0]['outputAliases'].reverse()),
 ('wrong parameter position',lambda x:x['queries'][1]['parameters'][1].update(position=1)),
 ('narrowed native cast',lambda x:x['queries'][1]['parameters'][1].update(nativeCast='pg_catalog.int4'))]:
    corrupted=copy.deepcopy(manifest);mutate(corrupted)
    try:validate(corrupted)
    except ValueError:controls.append({'name':name,'expectedRefusal':True})
    else:raise ValueError('corruption accepted '+name)
receipt={'scope':'Six original AST statement memberships, source hashes, parameter occurrence/order/native casts and projection aliases only; nullable membership is not nullable type proof. No origin authenticity, native binding, collation/operator resolution, resource, role/cut, settlement or execution qualification.','manifestPath':str(manifest_path),'manifestSha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'queries':6,'expectedRefusals':controls}
Path('docs/helix/04-build/evidence/design-audit/private-cleanup-query-parameters.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'queries':6,'expectedRefusals':len(controls),'nativeQualification':False}))
