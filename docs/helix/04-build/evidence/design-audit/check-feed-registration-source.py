"""Independent registration source oracle; no native execution or authority proof."""
import copy,hashlib,json
from pathlib import Path
base=Path('docs/helix/04-build/evidence/design-audit')
def require(ok,msg):
 if not ok: raise ValueError(msg)
def strings(n):return tuple(i['members']['String']['members']['sval']['value'] for i in n['items'])
def expr(n):
 require(len(n['members'])==1,'one expression');k,x=next(iter(n['members'].items()));x=x['members']
 if k=='ColumnRef':
  require(set(x)=={'fields','location'},'closed column');return ('col',)+strings(x['fields'])
 if k=='ParamRef':
  require(set(x)=={'number','location'},'closed parameter');return ('param',x['number']['value'])
 if k=='TypeCast':
  require(set(x)=={'arg','typeName','location'},'closed cast');t=x['typeName']['members'];require(set(t)=={'names','typemod','location'} and t['typemod']['value']=='-1','unmodified native type');return ('cast',expr(x['arg']),strings(t['names']))
 if k=='A_Expr':
  require(set(x)=={'kind','name','lexpr','rexpr','location'} and x['kind']['value']=='AEXPR_OP' and len(strings(x['name']))==1,'closed operator');return (strings(x['name'])[0],expr(x['lexpr']),expr(x['rexpr']))
 if k=='BoolExpr':
  require(set(x)=={'boolop','args','location'} and x['boolop']['value']=='AND_EXPR','closed conjunction');return ('and',tuple(expr(i) for i in x['args']['items']))
 if k=='FuncCall':
  require(set(x) in [{'funcname','funcformat','location'},{'funcname','args','funcformat','location'}] and x['funcformat']['value']=='COERCE_EXPLICIT_CALL','closed native call');return ('call',strings(x['funcname']),tuple(expr(a) for a in x.get('args',{'items':[]})['items']))
 if k=='NullTest':
  require(set(x)=={'arg','nulltesttype','location'} and x['nulltesttype']['value']=='IS_NOT_NULL','closed not-null test');return ('not_null',expr(x['arg']))
 if k=='A_Const':
  if x.get('isnull',{}).get('value') is True:
   require(set(x)=={'isnull','location'},'closed null');return ('null',)
  for f in ['ival','fval','sval']:
   if f in x:
    require(set(x)=={f,'location'},'closed literal');inner=x[f]['members'];require(set(inner)=={f} or (f=='ival' and not inner),'closed literal carrier');return (f,inner.get(f,{'value':'0'})['value'])
 raise ValueError('unsupported expression '+k)
c=lambda a,n:('col',a,n)
p=lambda i,t:('cast',('param',str(i)),('pg_catalog',t))
eq=lambda a,b:('=',a,b)
context=[eq(c('t','source_epoch'),p(1,'text')),eq(c('t','feed_profile'),p(2,'text')),eq(c('t','original_writer_xid'),('call',('pg_catalog','pg_current_xact_id_if_assigned'),()))]
max8=('cast',('fval','9223372036854775807'),('pg_catalog','int8'))
txcols=['source_epoch','feed_profile','original_writer_xid','registration_counter','prerequisite_registration_counter','configuration_registration_counter','membership_generation','finalized_generation','original_context_bytes','manifest_profile_bytes','manifest_bytes','manifest_sha256']
mcols=['source_epoch','feed_profile','original_writer_xid','registration_address','fact_kind','original_fact_key_bytes','original_fact_key_profile_bytes','original_payload_bytes','original_payload_profile_bytes','original_payload_sha256','original_owner_context_bytes','original_write_at','original_fact_clock_bytes','delivery_ordinal']
def descriptor(n,alias,cols):
 found=[]
 for target in n['returningList']['items']:
  x=target['members']['ResTarget']['members'];require(set(x) in [{'val','location'},{'name','val','location'}],'closed result target');v=expr(x['val']);name=cols[len(found)] if len(found)<len(cols) else '?'
  form='hex' if 'bytes' in name or 'sha256' in name else 'direct' if name in ['source_epoch','feed_profile','fact_kind'] else 'text'
  expected=c(alias,name) if form=='direct' else ('cast',c(alias,name),('pg_catalog','text')) if form=='text' else ('call',('pg_catalog','encode'),(c(alias,name),('sval','hex')))
  require(v==expected,'ordered returned carrier');require(x.get('name',{}).get('value',name)==name+('_hex' if form=='hex' else ''),'returned alias');found.append(name)
 require(found==cols,'complete descriptor')
def relation(n,name,alias):
 x=n['members'];require(set(x)=={'schemaname','relname','inh','relpersistence','alias','location'} and x['inh']['value'] is True and x['relpersistence']['value']=='p' and set(x['alias']['members'])=={'aliasname'},'closed relation');require(x['schemaname']['value']=='truss' and x['relname']['value']==name and x['alias']['members']['aliasname']['value']==alias,'original relation')
items=[];pins=[]
for family,kind in [('feed-member-counter-reservation','UpdateStmt'),('feed-member-insert','InsertStmt'),('feed-transaction-create','InsertStmt')]:
 r=json.loads((base/(family+'-source.json')).read_text());o=r['observations'][0]
 for field,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:require(hashlib.sha256(Path(o[field]).read_bytes()).hexdigest()==o[h],'original source '+field)
 m=json.loads(Path(o['artifactPath']).read_text());stmts=m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items'];require(len(stmts)==1,'one original statement');items.append(stmts[0]['members']['stmt']['members'][kind]['members']);pins.append(o)
def verify(xs):
 require(len(xs)==3,'complete three-statement membership');u,i,j=xs;require(set(u)=={'relation','targetList','whereClause','returningList'},'closed update');relation(u['relation'],'feed_tx','t')
 targets=[]
 for target in u['targetList']['items']:
  t=target['members']['ResTarget']['members'];require(set(t)=={'name','val','location'},'closed counter assignment');targets.append((t['name']['value'],expr(t['val'])))
 require(targets==[(n,('+',c('t',n),('ival','1'))) for n in ['registration_counter','membership_generation']],'exact counter mask')
 require(expr(u['whereClause'])==('and',tuple(context+[eq(c('t','registration_counter'),p(3,'int8')),eq(c('t','membership_generation'),p(4,'int8')),eq(c('t','original_context_bytes'),p(5,'bytea')),eq(c('t','manifest_profile_bytes'),p(6,'bytea')),('<',c('t','registration_counter'),max8),('<',c('t','membership_generation'),max8)])),'reservation predicates');descriptor(u,'t',txcols)
 require(set(i)=={'relation','cols','selectStmt','returningList','override'},'closed insert');require(i['override']['value']=='OVERRIDING_NOT_SET','no override');relation(i['relation'],'feed_member','m')
 require(all(set(x['members']['ResTarget']['members'])=={'name','location'} for x in i['cols']['items']),'closed member insert columns');require([x['members']['ResTarget']['members']['name']['value'] for x in i['cols']['items']]==mcols,'all insert columns')
 s=i['selectStmt']['members']['SelectStmt']['members'];require(set(s)=={'targetList','fromClause','whereClause','limitOption','op'} and s['op']['value']=='SETOP_NONE' and s['limitOption']['value']=='LIMIT_OPTION_DEFAULT','closed select');require(len(s['fromClause']['items'])==1,'one parent');relation(s['fromClause']['items'][0]['members']['RangeVar'],'feed_tx','t')
 expected=[c('t',n) for n in txcols[:3]]+[p(3,'int8'),p(5,'text')]+[p(j,'bytea') for j in range(6,12)]+[p(12,'timestamptz'),p(13,'bytea'),('cast',('null',),('pg_catalog','int8'))]
 require(all(set(t['members']['ResTarget']['members'])=={'val','location'} for t in s['targetList']['items']),'closed member source targets');require([expr(t['members']['ResTarget']['members']['val']) for t in s['targetList']['items']]==expected,'exact insertion carriers')
 require(expr(s['whereClause'])==('and',tuple(context+[eq(c('t','registration_counter'),p(3,'int8')),eq(c('t','membership_generation'),p(4,'int8')),eq(c('t','original_context_bytes'),p(14,'bytea')),eq(c('t','manifest_profile_bytes'),p(15,'bytea')),('>',p(3,'int8'),('ival','0')),('>',p(4,'int8'),('ival','0'))])),'insert parent predicates');descriptor(i,'m',mcols)
 require(set(j)=={'relation','cols','selectStmt','returningList','override'} and j['override']['value']=='OVERRIDING_NOT_SET','closed initial insert');relation(j['relation'],'feed_tx','t')
 require(all(set(x['members']['ResTarget']['members'])=={'name','location'} for x in j['cols']['items']),'closed initial columns');require([x['members']['ResTarget']['members']['name']['value'] for x in j['cols']['items']]==txcols,'complete initial columns')
 initial=j['selectStmt']['members']['SelectStmt']['members'];require(set(initial)=={'targetList','whereClause','limitOption','op'} and initial['op']['value']=='SETOP_NONE' and initial['limitOption']['value']=='LIMIT_OPTION_DEFAULT','closed initial select')
 native_xid=('call',('pg_catalog','pg_current_xact_id_if_assigned'),());zero=('cast',('ival','0'),('pg_catalog','int8'));null8=('cast',('null',),('pg_catalog','int8'));nullbytes=('cast',('null',),('pg_catalog','bytea'))
 require(all(set(t['members']['ResTarget']['members'])=={'val','location'} for t in initial['targetList']['items']),'closed initial source targets');require([expr(t['members']['ResTarget']['members']['val']) for t in initial['targetList']['items']]==[p(1,'text'),p(2,'text'),native_xid,zero,zero,zero,zero,null8,p(3,'bytea'),p(4,'bytea'),nullbytes,nullbytes],'complete initial carriers')
 require(expr(initial['whereClause'])==('not_null',native_xid),'assigned native transaction condition');descriptor(j,'t',txcols)
verify(items);controls=[]
for label,mutate in [('counter target indirection',lambda x:x[0]['targetList']['items'][0]['members']['ResTarget']['members'].update(indirection={})),('extra initial source alias',lambda x:x[2]['selectStmt']['members']['SelectStmt']['members']['targetList']['items'][0]['members']['ResTarget']['members'].update(name={'value':'forged'}))]:
 x=copy.deepcopy(items);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)

for label,mutate in [('omitted initial counter',lambda x:x[2]['cols']['items'].pop(4)),('reordered initial carriers',lambda x:x[2]['selectStmt']['members']['SelectStmt']['members']['targetList']['items'].reverse()),('initial conflict suppression',lambda x:x[2].update(onConflictClause={})),('omitted assigned-xid condition',lambda x:x[2]['selectStmt']['members']['SelectStmt']['members'].pop('whereClause')),('initial result omission',lambda x:x[2]['returningList']['items'].pop())]:
 x=copy.deepcopy(items);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)

for label,mutate in [('hidden function filter',lambda x:x[0]['whereClause']['members']['BoolExpr']['members']['args']['items'][2]['members']['A_Expr']['members']['rexpr']['members']['FuncCall']['members'].update(agg_filter={})),('type precision modifier',lambda x:x[1]['selectStmt']['members']['SelectStmt']['members']['targetList']['items'][11]['members']['ResTarget']['members']['val']['members']['TypeCast']['members']['typeName']['members']['typemod'].update(value='3')),('result indirection',lambda x:x[0]['returningList']['items'][0]['members']['ResTarget']['members'].update(indirection={})),('relation inheritance substitution',lambda x:x[1]['relation']['members']['inh'].update(value=False))]:
 x=copy.deepcopy(items);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)

for label,mutate in [('extra counter target',lambda x:x[0]['targetList']['items'].append(copy.deepcopy(x[0]['targetList']['items'][0]))),('missing overflow guard',lambda x:x[0]['whereClause']['members']['BoolExpr']['members']['args']['items'].pop()),('missing original parent check',lambda x:x[1]['selectStmt']['members']['SelectStmt']['members']['whereClause']['members']['BoolExpr']['members']['args']['items'].pop(5)),('omitted insert column',lambda x:x[1]['cols']['items'].pop()),('reordered original values',lambda x:x[1]['selectStmt']['members']['SelectStmt']['members']['targetList']['items'].reverse()),('added conflict suppression',lambda x:x[1].update(onConflictClause={})),('omitted returned clock',lambda x:x[1]['returningList']['items'].pop(12)),('reordered parent result',lambda x:x[0]['returningList']['items'].reverse())]:
 x=copy.deepcopy(items);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
(base/'feed-registration-source-oracle.json').write_text(json.dumps({'scope':'Three complete authored registration statement masks/predicates/slot-carriers/ordered descriptors and original source pins; no native authority, completion, privileges, clocks, resource or atomic registration qualification','sourcePins':pins,'controls':controls,'nativeExecution':False,'complete':False},indent=2)+'\n')
print(json.dumps({'statements':3,'refusals':len(controls),'nativeExecution':False}))
# Prerequisite reservation is a separately scoped original family/receipt.
o=json.loads((base/'feed-prerequisite-counter-reservation-source.json').read_text())['observations'][0]
for field,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:require(hashlib.sha256(Path(o[field]).read_bytes()).hexdigest()==o[h],'prerequisite original source '+field)
m=json.loads(Path(o['artifactPath']).read_text());raw=m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items'];require(len(raw)==2,'two prerequisite statements')
prerequisites=[r['members']['stmt']['members']['UpdateStmt']['members'] for r in raw]
def verify_prerequisites(xs):
 require(len(xs)==2,'complete prerequisite families')
 for n,family in zip(xs,['prerequisite_registration_counter','configuration_registration_counter']):
  require(set(n)=={'relation','targetList','whereClause','returningList'},'closed prerequisite update');relation(n['relation'],'feed_tx','t')
  targets=[]
  for target in n['targetList']['items']:
   t=target['members']['ResTarget']['members'];require(set(t)=={'name','val','location'},'closed assignment');targets.append((t['name']['value'],expr(t['val'])))
  require(targets==[(name,('+',c('t',name),('ival','1'))) for name in [family,'membership_generation']],'independent family mutation mask')
  expected=context+[eq(c('t',family),p(3,'int8')),eq(c('t','membership_generation'),p(4,'int8')),eq(c('t','original_context_bytes'),p(5,'bytea')),eq(c('t','manifest_profile_bytes'),p(6,'bytea')),('<',c('t',family),max8),('<',c('t','membership_generation'),max8)]
  require(expr(n['whereClause'])==('and',tuple(expected)),'complete prerequisite predicates');descriptor(n,'t',txcols)
verify_prerequisites(prerequisites);pc=[]
for label,mutate in [('wrong family target',lambda x:x[0]['targetList']['items'][0]['members']['ResTarget']['members']['name'].update(value='configuration_registration_counter')),('semantic member address mutation',lambda x:x[1]['targetList']['items'][0]['members']['ResTarget']['members']['name'].update(value='registration_counter')),('omitted generation mutation',lambda x:x[0]['targetList']['items'].pop()),('missing original profile predicate',lambda x:x[1]['whereClause']['members']['BoolExpr']['members']['args']['items'].pop(6)),('omitted overflow bound',lambda x:x[0]['whereClause']['members']['BoolExpr']['members']['args']['items'].pop()),('reordered families',lambda x:x.reverse()),('changed returning mask',lambda x:x[1]['returningList']['items'].pop(3)),('hidden update FROM',lambda x:x[0].update(fromClause={}))]:
 x=copy.deepcopy(prerequisites);mutate(x)
 try:verify_prerequisites(x)
 except ValueError:pc.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
(base/'feed-prerequisite-counter-source-oracle.json').write_text(json.dumps({'scope':'Two exact prerequisite reservation masks, complete predicates and twelve-column source projections; no prerequisite insert or native enforcement proof','sourcePins':[o],'controls':pc,'nativeExecution':False,'complete':False},indent=2)+'\n')
print(json.dumps({'prerequisiteStatements':2,'refusals':len(pc),'nativeExecution':False}))
# Independently authored closure insertion columns and native slot domains.
o=json.loads((base/'feed-prerequisite-insert-source.json').read_text())['observations'][0]
for field,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:require(hashlib.sha256(Path(o[field]).read_bytes()).hexdigest()==o[h],'closure insert original source '+field)
m=json.loads(Path(o['artifactPath']).read_text());raw=m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items'];require(len(raw)==2,'two closure insert statements')
closure_inserts=[r['members']['stmt']['members']['InsertStmt']['members'] for r in raw]
closure_specs=[('feed_prerequisite','prerequisite_registration_counter',['source_epoch','feed_profile','original_writer_xid','prerequisite_address','original_revision','original_artifact_identity_bytes','original_definition_bytes','original_definition_profile_bytes','original_definition_sha256','original_owner_context_bytes'],['int8','bytea','bytea','bytea','bytea','bytea'],11,12),('feed_configuration_prerequisite','configuration_registration_counter',['source_epoch','feed_profile','original_writer_xid','configuration_address','original_installation_identity_bytes','original_configuration_generation','original_configuration_profile_bytes','original_configuration_bytes','original_producer_inventory_bytes','original_configuration_sha256','original_owner_context_bytes'],['bytea','int8','bytea','bytea','bytea','bytea','bytea'],12,13)]
def verify_closure_inserts(xs):
 require(len(xs)==2,'complete closure insertion membership')
 for n,(table,counter,cols,types,contextslot,profileslot) in zip(xs,closure_specs):
  require(set(n)=={'relation','cols','selectStmt','returningList','override'} and n['override']['value']=='OVERRIDING_NOT_SET','closed closure insert');relation(n['relation'],table,'p')
  names=[]
  for target in n['cols']['items']:
   x=target['members']['ResTarget']['members'];require(set(x)=={'name','location'},'closed insertion column');names.append(x['name']['value'])
  require(names==cols,'complete original closure columns')
  s=n['selectStmt']['members']['SelectStmt']['members'];require(set(s)=={'targetList','fromClause','whereClause','limitOption','op'} and s['op']['value']=='SETOP_NONE' and s['limitOption']['value']=='LIMIT_OPTION_DEFAULT','closed closure parent select');require(len(s['fromClause']['items'])==1,'one original closure parent');relation(s['fromClause']['items'][0]['members']['RangeVar'],'feed_tx','t')
  values=[]
  for target in s['targetList']['items']:
   x=target['members']['ResTarget']['members'];require(set(x)=={'val','location'},'closed original closure value');values.append(expr(x['val']))
  require(values==[c('t',name) for name in cols[:3]]+[p(3,'int8')]+[p(slot,kind) for slot,kind in enumerate(types,5)],'independent closure slot meanings')
  expected=context+[eq(c('t',counter),p(3,'int8')),eq(c('t','membership_generation'),p(4,'int8')),eq(c('t','original_context_bytes'),p(contextslot,'bytea')),eq(c('t','manifest_profile_bytes'),p(profileslot,'bytea')),('>',p(3,'int8'),('ival','0')),('>',p(4,'int8'),('ival','0'))]
  require(expr(s['whereClause'])==('and',tuple(expected)),'complete closure parent predicates');descriptor(n,'p',cols)
verify_closure_inserts(closure_inserts);cc=[]
for label,mutate in [('missing complete inventory column',lambda x:x[1]['cols']['items'].pop(8)),('reordered original closure values',lambda x:x[0]['selectStmt']['members']['SelectStmt']['members']['targetList']['items'].reverse()),('wrong configuration generation slot',lambda x:x[1]['selectStmt']['members']['SelectStmt']['members']['targetList']['items'][5]['members']['ResTarget']['members']['val']['members']['TypeCast']['members']['arg']['members']['ParamRef']['members']['number'].update(value='5')),('missing original parent profile',lambda x:x[0]['selectStmt']['members']['SelectStmt']['members']['whereClause']['members']['BoolExpr']['members']['args']['items'].pop(6)),('conflict suppression',lambda x:x[1].update(onConflictClause={})),('omitted returned original owner',lambda x:x[0]['returningList']['items'].pop()),('extra parent LIMIT',lambda x:x[1]['selectStmt']['members']['SelectStmt']['members'].update(limitCount={})),('reordered closure families',lambda x:x.reverse())]:
 x=copy.deepcopy(closure_inserts);mutate(x)
 try:verify_closure_inserts(x)
 except ValueError:cc.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
(base/'feed-prerequisite-insert-source-oracle.json').write_text(json.dumps({'scope':'Two closure insertion column/parameter/parent predicate/result source correspondences; no original archive/hash/owner authority or native registration proof','sourcePins':[o],'controls':cc,'nativeExecution':False,'complete':False},indent=2)+'\n')
print(json.dumps({'closureInsertStatements':2,'refusals':len(cc),'nativeExecution':False}))
