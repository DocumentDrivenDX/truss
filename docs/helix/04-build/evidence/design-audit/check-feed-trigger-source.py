"""Four authored trigger scheduling declarations only; no native firing proof."""
import copy,hashlib,json
from pathlib import Path
base=Path('docs/helix/04-build/evidence/design-audit')
def require(ok,msg):
 if not ok:raise ValueError(msg)
r=json.loads((base/'feed-current-union-triggers-source.json').read_text());o=r['observations'][0]
for field,h in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:require(hashlib.sha256(Path(o[field]).read_bytes()).hexdigest()==o[h],'original source '+field)
m=json.loads(Path(o['artifactPath']).read_text());raw=m['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items'];require(len(raw)==4,'four source statements');nodes=[n['members']['stmt']['members']['CreateTrigStmt']['members'] for n in raw]
# REL_17_9 pg_trigger.h: INSERT 4 | DELETE 8 | UPDATE 16; ROW separate.
tables=['feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite']
def verify(xs):
 require(len(xs)==4,'complete four-store coverage')
 for n,table in zip(xs,tables):
  require(set(n)=={'isconstraint','trigname','relation','funcname','row','events','deferrable','initdeferred'},'closed unfiltered deferred AFTER trigger')
  require(n['isconstraint']['value'] is True and n['row']['value'] is True and n['deferrable']['value'] is True and n['initdeferred']['value'] is True,'constraint row/deferred flags')
  require(n['events']['value']=='28' and n['trigname']['value']==table+'_current_union_guard','all original events and name')
  x=n['relation']['members'];require(set(x)=={'schemaname','relname','inh','relpersistence','location'} and x['schemaname']['value']=='truss' and x['relname']['value']==table and x['inh']['value'] is True and x['relpersistence']['value']=='p','original table source')
  require(tuple(a['members']['String']['members']['sval']['value'] for a in n['funcname']['items'])==('truss','feed_current_union_check'),'original private callable')
verify(nodes);controls=[]
for label,mutate in [('omitted store',lambda x:x.pop()),('duplicate table coverage',lambda x:x[3]['relation']['members']['relname'].update(value='feed_tx')),('missing DELETE',lambda x:x[0]['events'].update(value='20')),('TRUNCATE substitution',lambda x:x[1]['events'].update(value='52')),('nondeferred flag',lambda x:x[2]['initdeferred'].update(value=False)),('statement-level substitution',lambda x:x[3]['row'].update(value=False)),('skipping WHEN',lambda x:x[0].update(whenClause={})),('UPDATE OF filter',lambda x:x[1].update(columns={})),('alternate function',lambda x:x[2]['funcname']['items'][1]['members']['String']['members']['sval'].update(value='feed_repair')),('caller arguments',lambda x:x[3].update(args={})),('BEFORE timing',lambda x:x[0].update(timing={'value':'2'}))]:
 x=copy.deepcopy(nodes);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
(base/'feed-trigger-source-oracle.json').write_text(json.dumps({'scope':'Four exact original CreateTrigStmt source schedules/names/tables/functions/flags, no native constraint/trigger inventory, function body or firing/bypass qualification','postgresqlEventBitSource':'https://raw.githubusercontent.com/postgres/postgres/REL_17_9/src/include/catalog/pg_trigger.h','sourcePins':[o],'controls':controls,'nativeExecution':False,'complete':False},indent=2)+'\n')
print(json.dumps({'statements':4,'refusals':len(controls),'nativeExecution':False}))
