"""F05 original source/manifest/AST consistency only, not native support."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[5]
P=R/'docs/helix/02-design/contracts/bindings/bootstrap-foreign-mapping-query-set-v0.1.proposal.json'
a=json.loads(P.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def u(n):
 if n['kind']=='object':return {k:u(v) for k,v in n['members'].items()}
 if n['kind']=='array':return [u(v) for v in n['items']]
 return n.get('value')
def strings(v):return [x['String']['sval'] for x in v]
assert a['interfaceVersion']=='truss-bootstrap-foreign-mapping-query-set/0.1.0'
assert a['parameterGrammar']=={'type':'pg_catalog.oid[]','dimensions':1,'lowerBound':1,'countInclusive':[1,256],'nonzero':True,'unique':True,'nullItems':False}
expected=[('foreign-mapping-header','original-admitted-server-oids','umserver',['catalog_class_oid','mapping_oid','local_role_oid','server_oid'],[False]*4),('foreign-mapping-options','original-admitted-mapping-oids','oid',['catalog_class_oid','mapping_oid','options_native_text','options_native_dimensions'],[False,False,True,True])]
assert len(a['entries'])==2
for e,(query,domain,selector,aliases,nullable) in zip(a['entries'],expected):
 assert (e['query'],e['parameterDomain'],e['selectorColumn'])==(query,domain,selector)
 for key in ['source','archive','export']:assert sha(R/e[key])==e[key+'Sha256']
 assert [v['name'] for v in e['columns']]==aliases
 assert [v['nullable'] for v in e['columns']]==nullable
 assert all(v['transport']=='original native text' and v['meaning'].strip() for v in e['columns'])
 assert e['disclosure'].strip() and e['resultCorrespondence'].strip()
 document=json.loads((R/e['archive']).read_text())
 tree=u(document['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
 assert len(tree['stmts'])==1
 s=tree['stmts'][0]['stmt']['SelectStmt']
 assert [t['ResTarget']['name'] for t in s['targetList']]==aliases
 assert set(s)=={'targetList','fromClause','whereClause','sortClause','limitOption','op'}
 assert s['op']=='SETOP_NONE' and s['limitOption']=='LIMIT_OPTION_DEFAULT'
 source_columns=['tableoid','oid','umuser','umserver'] if selector=='umserver' else ['tableoid','oid','umoptions','umoptions']
 for index,(target,column) in enumerate(zip(s['targetList'],source_columns)):
  value=target['ResTarget']['val']
  if selector=='oid' and index==3:
   call=value['FuncCall'];assert strings(call['funcname'])==['pg_catalog','array_dims'] and len(call['args'])==1
   assert set(call)=={'funcname','args','funcformat','location'} and call['funcformat']=='COERCE_EXPLICIT_CALL'
   ref=call['args'][0]['ColumnRef']
  else:
   cast=value['TypeCast'];assert strings(cast['typeName']['names'])==['pg_catalog','text']
   ref=cast['arg']['ColumnRef']
  assert strings(ref['fields'])==['c',column]
 order=[strings(v['SortBy']['node']['ColumnRef']['fields']) for v in s['sortClause']]
 assert order==([['c','umserver'],['c','oid']] if selector=='umserver' else [['c','oid']])
 assert all(v['SortBy']['sortby_dir']=='SORTBY_DEFAULT' and v['SortBy']['sortby_nulls']=='SORTBY_NULLS_DEFAULT' for v in s['sortClause'])
 assert len(s['fromClause'])==1
 f=s['fromClause'][0]['RangeVar'];assert (f['schemaname'],f['relname'],f['alias']['aliasname'])==('pg_catalog','pg_user_mapping','c')
 w=s['whereClause']['A_Expr'];assert w['kind']=='AEXPR_OP_ANY' and strings(w['name'])==['=']
 assert strings(w['lexpr']['ColumnRef']['fields'])==['c',selector]
 cast=w['rexpr']['TypeCast'];assert cast['arg']['ParamRef']['number']=='1'
 assert strings(cast['typeName']['names'])==['pg_catalog','oid'] and len(cast['typeName']['arrayBounds'])==1
 assert not any(k in s for k in ['limitCount','limitOffset','distinctClause','groupClause','havingClause'])
report={'status':'pass','scope':'two original source/archive/export pins, parameter-domain/selector, full source-column/cast/array-dimension expressions, clause/order shape and ordered result/nullability manifest consistency only; no native disclosure/cut/array/role/resource or route qualification','manifestSha256':sha(P),'queries':2,'registeredRoutesChanged':False}
Path(__file__).with_name('bootstrap-foreign-mapping-query-set-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
