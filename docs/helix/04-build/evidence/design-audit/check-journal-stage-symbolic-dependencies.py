"""Independently authored syntactic counts/names; no native dependency resolution."""
import copy,hashlib,json
from collections import Counter
from pathlib import Path
def require(ok,message):
    if not ok:raise ValueError(message)
p=Path('docs/helix/04-build/evidence/design-audit/journal-stage-symbolic-dependencies.json');v=json.loads(p.read_text())
for source in v['inputs']:require(hashlib.sha256(Path(source['path']).read_bytes()).hexdigest()==source['sha256'],'stale source')
def verify(refs):
    require(len(refs)==59 and len({(r['source'],r['pointer']) for r in refs})==59,'complete original occurrence inventory')
    require(Counter(r['kind'] for r in refs)=={'type-name':22,'function-call':9,'collation-name':3,'operator-expression':25},'kind counts')
    def counted(kind):return Counter(tuple(r['nameParts']) for r in refs if r['kind']==kind)
    require(counted('type-name')=={('xid8',):1,('pg_catalog','xid8'):1,('pg_catalog','int8'):8,('text',):2,('pg_catalog','text'):1,('bytea',):8,('pg_catalog','bytea'):1},'source type spellings/counts')
    require(counted('function-call')=={('octet_length',):8,('pg_catalog','octet_length'):1},'source function spellings/counts')
    require(all(r['argumentCount']==1 for r in refs if r['kind']=='function-call'),'original arity')
    require(counted('collation-name')=={('pg_catalog','C'):3},'original collations')
    require(counted('operator-expression')=={('=',):11,('>=',):5,('>',):9},'original constraint operators')
    require(Counter(r['expressionKind'] for r in refs if r['kind']=='operator-expression')=={'AEXPR_IN':2,'AEXPR_OP':23},'original expression kinds')
    require(all(r['nativeResolution']=='unresolved' for r in refs),'unqualified source status')
verify(v['references']);controls=[]
for name in ['omitted_reference','duplicate_pointer','changed_type','changed_function','changed_collation','changed_operator','invented_resolution']:
    refs=copy.deepcopy(v['references'])
    if name=='omitted_reference':refs.pop()
    elif name=='duplicate_pointer':refs[1]['source']=refs[0]['source'];refs[1]['pointer']=refs[0]['pointer']
    elif name=='invented_resolution':refs[0]['nativeResolution']='qualified'
    else:
        kind={'changed_type':'type-name','changed_function':'function-call','changed_collation':'collation-name','changed_operator':'operator-expression'}[name]
        next(r for r in refs if r['kind']==kind)['nameParts']=['substituted']
    try:verify(refs)
    except ValueError:controls.append(name)
    else:raise ValueError('missed '+name)
print(json.dumps({'scope':'independent syntactic original occurrence counts/names/kinds only; not full expression semantics or native resolution','helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inventorySha256':hashlib.sha256(p.read_bytes()).hexdigest(),'occurrences':59,'negativeControls':controls,'nativeExecuted':False},indent=2))
