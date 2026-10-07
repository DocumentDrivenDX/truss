"""Original native AST projection correspondence only; no runtime decoder proof."""
from pathlib import Path
import json,hashlib,copy
if not __debug__:
 raise SystemExit("This source audit requires assertions; optimized execution is refused.")
R=Path(__file__).resolve().parents[3]
C=R/'02-design/contracts'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unpack(n):
 if n['kind']=='object':return {k:unpack(v) for k,v in n['members'].items()}
 if n['kind']=='array':return [unpack(v) for v in n['items']]
 return n.get('value')
def tree(stem):
 return unpack(json.loads((C/(stem+'.umf.json')).read_text())['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])
def names(v):return [i['String']['sval'] for i in v]
def pin(stem,receipt):
 a=json.loads((Path(__file__).parent/receipt).read_text())
 if 'observations' in a:a=a['observations'][0]
 assert sha(C/(stem+'.sql'))==a['sourceSha256']
 assert sha(C/(stem+'.umf.json'))==a['artifactSha256']
pin('row-operation-registry-observation-v0.1.proposal','row-operation-registry-observation-source.json')
pin('row-home-operation-v0.1.proposal','row-home-operation-source.json')
def without_locations(v):
 if isinstance(v,dict):return {k:without_locations(x) for k,x in v.items() if k!='location'}
 if isinstance(v,list):return [without_locations(x) for x in v]
 return v
def strings(*values):return [{'String':{'sval':v}} for v in values]
def column(name):return {'ColumnRef':{'fields':strings('o',name)}}
def text_cast(arg):return {'TypeCast':{'arg':arg,'typeName':{'names':strings('pg_catalog','text'),'typemod':'-1'}}}
def assigned_xid():return {'FuncCall':{'funcname':strings('pg_catalog','pg_current_xact_id_if_assigned'),'funcformat':'COERCE_EXPLICIT_CALL'}}

def validate_projection(observation,operation):
 columns=[v['ColumnDef'] for v in operation['stmts'][0]['stmt']['CreateStmt']['tableElts'] if 'ColumnDef' in v]
 s=observation['stmts']
 assert len(s)==2
 select=s[1]['stmt']['SelectStmt'];targets=select['targetList']
 assert set(select)=={'targetList','fromClause','whereClause','limitOption','op'}
 assert select['op']=='SETOP_NONE' and select['limitOption']=='LIMIT_OPTION_DEFAULT'
 assert len(select['fromClause'])==1
 assert len(columns)==len(targets)==16
 assert not any(k in select for k in ('limitCount','distinctClause','groupClause','havingClause','sortClause'))
 f=select['fromClause'][0]['RangeVar'];assert (f['schemaname'],f['relname'],f['alias']['aliasname'])==('truss','row_home_operation','o')
 where=select['whereClause']['A_Expr'];assert names(where['name'])==['=']
 assert names(where['lexpr']['ColumnRef']['fields'])==['o','original_writer_xid']
 assert where['kind']=='AEXPR_OP'
 current=where['rexpr']['FuncCall']
 assert names(current['funcname'])==['pg_catalog','pg_current_xact_id_if_assigned']
 assert set(current)=={'funcname','funcformat','location'} and current['funcformat']=='COERCE_EXPLICIT_CALL'
 identity_select=s[0]['stmt']['SelectStmt']
 assert set(identity_select)=={'targetList','limitOption','op'}
 assert identity_select['op']=='SETOP_NONE' and identity_select['limitOption']=='LIMIT_OPTION_DEFAULT'
 first=identity_select['targetList'];assert len(first)==1
 assert first[0]['ResTarget']['name']=='original_writer_xid'
 assert names(first[0]['ResTarget']['val']['TypeCast']['typeName']['names'])==['pg_catalog','text']
 arg=first[0]['ResTarget']['val']['TypeCast']['arg']['FuncCall'];assert names(arg['funcname'])==['pg_catalog','pg_current_xact_id_if_assigned']
 assert set(arg)=={'funcname','funcformat','location'} and arg['funcformat']=='COERCE_EXPLICIT_CALL'
 assert without_locations(select['fromClause'])==[{'RangeVar':{'schemaname':'truss','relname':'row_home_operation','inh':True,'relpersistence':'p','alias':{'aliasname':'o'}}}]
 assert without_locations(select['whereClause'])=={'A_Expr':{'kind':'AEXPR_OP','name':strings('='),'lexpr':column('original_writer_xid'),'rexpr':assigned_xid()}}
 assert without_locations(first)==[{'ResTarget':{'name':'original_writer_xid','val':text_cast(assigned_xid())}}]
 result=[]
 for c,t in zip(columns,targets):
  t=t['ResTarget'];name=c['colname'];bytea=names(c['typeName']['names'])==['bytea']
  assert t['name']==name+('_hex' if bytea else '')
  expected_value={'FuncCall':{'funcname':strings('pg_catalog','encode'),'args':[column(name),{'A_Const':{'sval':{'sval':'hex'}}}],'funcformat':'COERCE_EXPLICIT_CALL'}} if bytea else text_cast(column(name))
  assert without_locations(t)=={'name':name+('_hex' if bytea else ''),'val':expected_value}
  if bytea:
   call=t['val']['FuncCall'];assert names(call['funcname'])==['pg_catalog','encode'] and len(call['args'])==2
   assert call['args'][1]['A_Const']['sval']['sval']=='hex';ref=call['args'][0]['ColumnRef']
  else:
   cast=t['val']['TypeCast'];assert names(cast['typeName']['names'])==['pg_catalog','text'];ref=cast['arg']['ColumnRef']
  assert names(ref['fields'])==['o',name]
  nullable=not any(v['Constraint']['contype']=='CONSTR_NOTNULL' for v in c.get('constraints',[]))
  result.append({'ordinal':len(result),'sourceColumn':name,'outputColumn':t['name'],'nullable':nullable,'carrier':'hex-text' if bytea else 'native-text'})
 assert [x['sourceColumn'] for x in result if x['nullable']]==['readiness_generation','sealed_generation','application_generation','application_result_bytes']
 return result

observation=tree('row-operation-registry-observation-v0.1.proposal')
operation=tree('row-home-operation-v0.1.proposal')
result=validate_projection(observation,operation)
# Independently named corruption controls exercise the original source contract.
controls=[]
def refuses(name,mutate):
 candidate=copy.deepcopy(observation);decl=copy.deepcopy(operation)
 mutate(candidate,decl)
 try: validate_projection(candidate,decl)
 except AssertionError: controls.append({'case':name,'status':'expected-refusal'})
 else: raise RuntimeError('Source audit accepted corruption: '+name)
def q2(v):return v['stmts'][1]['stmt']['SelectStmt']
def q1(v):return v['stmts'][0]['stmt']['SelectStmt']
refuses('omit-last-projected-column',lambda v,d:q2(v)['targetList'].pop())
refuses('reorder-original-projection',lambda v,d:q2(v)['targetList'].reverse())
refuses('substitute-original-relation',lambda v,d:q2(v)['fromClause'][0]['RangeVar'].update(relname='row_home_scalar'))
refuses('duplicate-result-alias',lambda v,d:q2(v)['targetList'][1]['ResTarget'].update(name='original_writer_xid'))
refuses('add-limit-hides-surviving-operations',lambda v,d:q2(v).update(limitCount={'A_Const':{'ival':{'ival':1}}}))
refuses('add-distinct-collapses-observations',lambda v,d:q2(v).update(distinctClause=[{}]))
refuses('add-caller-parameter-to-xid-producer',lambda v,d:q2(v)['whereClause']['A_Expr']['rexpr']['FuncCall'].update(args=[{'ParamRef':{'number':1}}]))
refuses('allocate-xid-in-identity-observation',lambda v,d:q1(v)['targetList'][0]['ResTarget']['val']['TypeCast']['arg']['FuncCall']['funcname'][-1]['String'].update(sval='pg_current_xact_id'))
refuses('allocate-xid-in-operation-selection',lambda v,d:q2(v)['whereClause']['A_Expr']['rexpr']['FuncCall']['funcname'][-1]['String'].update(sval='pg_current_xact_id'))
refuses('unqualified-xid-producer',lambda v,d:q2(v)['whereClause']['A_Expr']['rexpr']['FuncCall']['funcname'].pop(0))
hex_target=next(t for t in q2(observation)['targetList'] if t['ResTarget']['name'].endswith('_hex'))['ResTarget']['name']
def wrong_hex(v,d):
 t=next(t for t in q2(v)['targetList'] if t['ResTarget']['name']==hex_target)
 t['ResTarget']['val']['FuncCall']['args'][1]['A_Const']['sval']['sval']='base64'
refuses('substitute-byte-carrier-encoding',wrong_hex)
def hex_modifier(v,d):
 t=next(t for t in q2(v)['targetList'] if t['ResTarget']['name']==hex_target)
 t['ResTarget']['val']['FuncCall']['agg_distinct']=True
refuses('add-aggregate-modifier-to-byte-carrier',hex_modifier)
refuses('add-array-cast-to-native-text',lambda v,d:q2(v)['targetList'][0]['ResTarget']['val']['TypeCast']['typeName'].update(arrayBounds=[{'Integer':{'ival':-1}}]))
refuses('add-result-indirection',lambda v,d:q2(v)['targetList'][0]['ResTarget'].update(indirection=[{'String':{'sval':'unexpected'}}]))
refuses('restrict-inheritance-observation',lambda v,d:q2(v)['fromClause'][0]['RangeVar'].update(inh=False))
refuses('substitute-cross-database-relation',lambda v,d:q2(v)['fromClause'][0]['RangeVar'].update(catalogname='other'))
def wrong_nullable(v,d):
 cols=d['stmts'][0]['stmt']['CreateStmt']['tableElts']
 c=next(x['ColumnDef'] for x in cols if 'ColumnDef' in x and x['ColumnDef']['colname']=='readiness_generation')
 c.setdefault('constraints',[]).append({'Constraint':{'contype':'CONSTR_NOTNULL'}})
refuses('erase-original-nullable-generation',wrong_nullable)
report={'status':'pass','scope':'source-pinned original UMF native ASTs: sixteen ordered column expressions and nullable declarations; no SQL execution, transport/decoder/authority/resource qualification','corruptionControls':controls,'columns':result,'sourcePins':{str(p.relative_to(R)):sha(p) for p in [C/'row-operation-registry-observation-v0.1.proposal.sql',C/'row-home-operation-v0.1.proposal.sql']}}
Path(__file__).with_name('row-operation-registry-projection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'pass','projectedColumns':16,'nullableColumns':4,'nativeExecution':False,'expectedRefusals':len(controls)}))
