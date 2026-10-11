"""Read-only inspection of retained epoch-state packets, without native/test execution."""
import ast,datetime,hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path('/private/tmp/truss-security-main-integration')
BASE=ROOT/'docs/helix/04-build/evidence/python-catalog-report-release'
RUNS={'ordinary':'4b98ea53-172f-4038-b68b-d4c76ac789c3'}
sha=lambda b:hashlib.sha256(b).hexdigest()
ISSUER='test_issuer_refuses_before_registry_first_effect'
ORDER='test_writer_modes_precede_marker_row_wait'
TABLES='test_all_statement_events_on_both_tables_are_fenced'
TABLE_SINGLES={'test_replica_and_ungranted_ordinary_role','test_writer_first_then_reader_rejects_all_later_writes'}
columns='installation_id,source_epoch,target_incarnation,predecessor_epoch,transition_reason,profile_bytes,evidence_bytes'
SQLS=[]
for table in ('source_epoch_current','source_epoch_registry'):
 insertion=f'INSERT INTO truss.{table}({columns}) SELECT {columns} FROM truss.{table} WHERE false' if table=='source_epoch_registry' else f'INSERT INTO truss.{table} SELECT * FROM truss.{table} WHERE false'
 SQLS.extend((insertion,f'UPDATE truss.{table} SET source_epoch=source_epoch WHERE false',f'DELETE FROM truss.{table} WHERE false',f'TRUNCATE truss.{table} CASCADE'))

def audit(kind,run):
 ordinary=kind=='ordinary';counter=kind not in (None,'ordinary');expected_native=15 if ordinary else 10
 folder=BASE/run;raw=(folder/'receipt.json').read_bytes();r=json.loads(raw);pins=r['sourceDigests'];failures=[]
 def ck(ok,label):
  if not ok:failures.append(label)
 out={'runId':run,'kind':'routine-ddl-barrier','receiptStatus':r['status'],'receiptSha256':sha(raw),'zipSha256':sha((folder/'sources.zip').read_bytes()),'integrityFailures':failures}
 ck(r['runId']==run and r['status']==('countercontrol-reproduced' if counter else 'component-passed'),'receipt status/identity')
 ck(r.get('countercontrol') is counter and r.get('countercontrolKind')==(kind if counter else None) and r.get('epochStateFenceProfile') is (not ordinary) and r.get('selfWriteFenceProfile') is False and r.get('routineDdlWriterBarrierProfile') is True and r.get('reportWriteCandidateProfile') is False,'exact epoch profile flags')
 ck(type(r['testExitCode']) is int and r['testExitCode']==int(counter) and type(r['nativeTests']) is int and r['nativeTests']==expected_native,'test count and exit code')
 ck(r['testCommand'][7]==('test_routine_ddl_barrier_native.py' if ordinary else 'test_epoch_state_fence_native.py'),'selected discovery file')
 drift=[{'path':p,'retainedSha256':h,'currentSha256':sha(Path(p).read_bytes()) if Path(p).is_file() else None} for p,h in pins.items() if not Path(p).is_file() or sha(Path(p).read_bytes())!=h]
 out.update(sourceCount=len(pins),currentSourceDrift=drift);ck(len(pins)==290,'290 declared source pins')
 with zipfile.ZipFile(folder/'sources.zip') as z:
  ns=z.namelist();expect={p.lstrip('/') for p in pins};extra=sorted(set(ns)-expect);missing=sorted(expect-set(ns));duplicates=len(ns)-len(set(ns));bad=[p for p,h in pins.items() if p.lstrip('/') in ns and sha(z.read(p.lstrip('/')))!=h]
  out['zip']={'entryCount':len(ns),'duplicates':duplicates,'extra':extra,'missing':missing,'digestMismatches':bad};ck(len(ns)==290 and not(extra or missing or duplicates or bad),'exact source ZIP')
  def src(rel):return z.read(str(ROOT/rel).lstrip('/'))
  def methods(module,cls=None):
   t=ast.parse(src('packages/python/tests/'+module+'.py'))
   return [f'{module}.{c.name}.{f.name}' for c in t.body if isinstance(c,ast.ClassDef) and (cls is None or c.name==cls) for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')]
  native=methods('test_routine_ddl_barrier_native') if ordinary else methods('test_epoch_state_fence_native');dispatch=methods('test_native_catalog_dispatch','NativeCatalogDispatchTests');aux=methods('test_catalog_source_candidate')+methods('test_configured_catalog_stage')
  ck((len(native),len(dispatch),len(aux))==(expected_native,14,15),'frozen AST selected native/14/15 inventory')
  epoch_sources={}
  for name in ('source-epoch-issue','source-epoch-read-fence','source-epoch-fenced-fresh-lock','source-epoch-lock','source-epoch-fresh-lock','source-epoch-immutability'):
   rel='packages/postgresql/native/'+name+'.sql';body=src(rel);epoch_sources[name]={'sha256':sha(body),'sourcePinMatches':pins.get(str(ROOT/rel))==sha(body)}
  out['epochSourceClosure']=epoch_sources;ck(all(x['sourcePinMatches'] for x in epoch_sources.values()),'six epoch SQL inputs captured')
  if counter:
   stem='source-epoch-issue' if kind in ('epoch-issuer-fence','epoch-writer-order') else 'source-epoch-read-fence';body=src('packages/postgresql/native/'+stem+'.sql');variant=(folder/('countercontrol-'+stem+'.sql')).read_bytes();marker=b' IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l';repl=b' IF FALSE AND EXISTS(SELECT 1 FROM pg_catalog.pg_locks l'
   if kind=='epoch-writer-order':marker=b' LOCK TABLE truss.source_epoch_current, truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT;';repl=b' -- Deliberate omitted upfront write table locks.'
   exact=body.count(marker)==1 and variant==body.replace(marker,repl)
   ck(sorted(p.name for p in folder.glob('countercontrol-*.sql'))==['countercontrol-'+stem+'.sql'],'only exact expected variant file')
   out['variant']={'originalSha256':sha(body),'variantSha256':sha(variant),'markerCount':body.count(marker),'exactOneMarkerReplacement':exact};ck(exact,'exact one-predicate omission')
  if not counter:ck(not list(folder.glob('countercontrol-*.sql')),'no mutation files for positive packets')
  for field,name in [('executedFenceSqlSha256','archive-self-write-fence'),('executedFenceComparisonSqlSha256','archive-write-fence-current'),('executedConfiguredStageSqlSha256','configured-stage'),('executedReleaseSqlSha256','release-selection')]:ck(r[field]==sha(src('packages/postgresql/native/catalog-report/'+name+'.sql')),'retained executed digest '+field)
  policy=json.loads(src('packages/python/src/truss/_profiles/catalog-report-release.json'));resources=[{'path':x['path'],'bytes':len(src(x['path'])),'sha256':sha(src(x['path'])),'matchesPolicyAndPin':sha(src(x['path']))==x['sha256']==pins[str(ROOT/x['path'])]} for x in policy['resources']]
  out['resources']={'count':len(resources),'totalBytes':sum(x['bytes'] for x in resources),'rows':resources};ck(len(resources)==21 and len({x['path'] for x in resources})==21 and sum(x['bytes'] for x in resources)==101453 and all(x['matchesPolicyAndPin'] for x in resources),'all21 declared resources')
  deps={}
  for package in ('pg8000','scramp','asn1crypto','dateutil','six'):
   files=[p for p in pins if p.endswith('.py') and (package in Path(p).parts or package=='six' and Path(p).name=='six.py')];dist='python_dateutil' if package=='dateutil' else package;meta=[p for p in pins if Path(p).name=='METADATA' and Path(p).parent.name.startswith(dist+'-')]
   deps[package]={'pythonFiles':len(files),'metadataFiles':len(meta),'versions':[re.search(rb'^Version: (.+)$',z.read(p.lstrip('/')),re.M).group(1).decode() for p in meta]};ck(bool(files) and len(meta)==1,'dependency '+package)
  out['dependencies']=deps
  pkgs=[p for p in (ROOT/'packages/python/src/truss').rglob('*') if p.is_file() and '__pycache__' not in p.parts];uncaptured=[str(p) for p in pkgs if str(p) not in pins];out['currentPythonPackageFileCount']=len(pkgs);out['uncapturedPythonFiles']=uncaptured;ck(not uncaptured,'whole current Python package captured')
 log=(folder/'tests.stderr.log').read_text();rows=re.findall(r'^test_\S+ \(([^)]+)\) \.\.\.[ \t]*(ok|FAIL|ERROR)?[ \t]*$',log,re.M);names=[n for n,s in rows]
 subs=[{'method':n,'sql':ast.literal_eval(sql),'result':s} for n,sql,s in re.findall(r'^  test_\S+ \(([^)]+)\) \(sql=(.+)\) \.\.\. (FAIL|ok|ERROR)$',log,re.M)]
 single={ORDER} if kind=='epoch-writer-order' else {ISSUER} if kind=='epoch-issuer-fence' else TABLE_SINGLES if kind=='epoch-table-fence' else set();sub=TABLES if kind=='epoch-table-fence' else None
 ck(len(names)==len(set(names))==expected_native and set(names)==set(native),'exact selected native methods')
 ck(all(s==('' if n.rsplit('.',1)[1]==sub else 'FAIL' if n.rsplit('.',1)[1] in single else 'ok') for n,s in rows),'exact main-method outcomes')
 ck(([s['sql'] for s in subs]==SQLS and all(s['result']=='FAIL' and s['method'].endswith('.'+TABLES) for s in subs)) if kind=='epoch-table-fence' else not subs,'exact eight table event controls')
 heads=re.findall(r'^FAIL: (.+)$',log,re.M);assertions=re.findall(r'^AssertionError: (.*)$',log,re.M);expected=0 if not counter else 1 if kind in ('epoch-issuer-fence','epoch-writer-order') else 10
 ck(len(heads)==len(assertions)==expected,'exact intended failure count')
 if kind=='epoch-issuer-fence':ck(assertions==["'55P03' != '55000'"],'issuer before-marker discriminator')
 elif kind=='epoch-writer-order':ck(assertions==["Tuples differ: (0, 'success') != (2, '55P03')"],'writer modes independently observed before marker acquisition')
 elif kind=='epoch-table-fence':ck(assertions.count('DatabaseError not raised')==9 and assertions.count("'original source epoch registry evidence are immutable' != 'selected epoch cut excludes same-backend writes'")==1,'table omission nine nonrefusals plus independent registry immutable fallback')
 ck(re.search(r'^Ran '+str(expected_native)+r' tests in ',log,re.M) is not None and ('FAILED (failures='+str(expected)+')' if counter else 'OK') in log.splitlines() and not re.search(r'^ERROR:',log,re.M) and 'skipped' not in log,'exact terminal summary/no errors/skips')
 out['nativeInventory']={'expectedMethods':native,'mainResults':dict(rows),'subtestResults':subs,'failureHeaders':heads,'assertions':assertions,'summary':re.findall(r'^(?:Ran \d+ tests.*|OK|FAILED \(.*\))$',log,re.M)}
 def group(prefix,expected):
  if not expected:
   paths=[p.name for p in folder.glob(prefix+'.*.log')];ck(not paths,prefix+' absent');return {'executed':False,'logFiles':paths}
  t=(folder/(prefix+'.stderr.log')).read_text();rs=re.findall(r'^test_\S+ \(([^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$',t,re.M);ns=[n for n,s in rs];ck(len(ns)==len(set(ns))==len(expected) and set(ns)==set(expected) and all(s=='ok' for n,s in rs) and 'OK' in t.splitlines() and re.search(r'^Ran '+str(len(expected))+r' tests in ',t,re.M) is not None,prefix+' exact inventory/outcomes');return {'executed':True,'expectedMethods':expected,'results':dict(rs),'count':len(rs)}
 out['dispatch']=group('regression',dispatch);out['auxiliary']=group('auxiliary',aux if not counter else []);ck(r['originalCatalogRegressions']==[x.rsplit('.',1)[1] for x in dispatch] and r['incomingCatalogRegressions']==(aux if not counter else []),'receipt regression inventories')
 bins=r['nativeBinaryDigests'];badbin=[p for p,h in bins.items() if not Path(p).is_file() or sha(Path(p).read_bytes())!=h];out.update(nativeBinaryCount=len(bins),currentNativeBinaryMismatches=badbin);ck(len(bins)==1614 and not badbin,'1614 current native files')
 server=(folder/'server.log').read_text();m=re.search(r'listening on Unix socket "([^"]+)"',server);socket=Path(m.group(1)) if m else None;execution=Path(r['testCommand'][5]).parents[3]
 out['cleanup']={'receipt':r['cleanup'],'executionDirectory':str(execution),'executionDirectoryAbsent':not execution.exists(),'socketPath':str(socket) if socket else None,'socketParentAbsent':socket is not None and not socket.parent.exists(),'serverShutdownLogged':re.search(r'LOG:  database system is shut down\s*$',server) is not None};ck(r['cleanup']=={'attempted':True,'stopExitCode':0,'statusExitCode':3,'socketAbsent':True} and not execution.exists() and socket is not None and not socket.exists() and not socket.parent.exists() and out['cleanup']['serverShutdownLogged'],'corroborated owned cleanup')
 out['boundaries']=(folder/'boundaries.stdout.log').read_text().strip();out['logHashes']={p.name:sha(p.read_bytes()) for p in folder.glob('*.log')};ck((folder/'receipt.json').read_bytes()==raw,'receipt unchanged during audit')
 out['status']='integrity-findings' if failures else 'historical-source-drift' if drift else 'scoped-evidence-matches'
 return out,r

packets={};receipts=[]
for kind,run in RUNS.items():
 p,r=audit(kind,run);packets['routine-ddl-barrier']=p;receipts.append(r)
integrity=[{'packet':k,'finding':v} for k,p in packets.items() for v in p['integrityFailures']];same_source=all(r['sourceDigests']==receipts[0]['sourceDigests'] for r in receipts);same_bins=all(r['nativeBinaryDigests']==receipts[0]['nativeBinaryDigests'] for r in receipts)
if not same_source or not same_bins:integrity.append({'finding':'packet original pins differ'})
has_drift=any(p['currentSourceDrift'] for p in packets.values())
result={'auditKind':'independent routine DDL barrier retained native packet audit','auditedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'integrationRoot':str(ROOT),'status':'integrity-findings' if integrity else 'historical-source-drift' if has_drift else 'scoped-evidence-matches','executionsPerformed':'Local file/hash/ZIP/AST/log inspection only; no native, tests, producers or repository edits.','sameRetainedSourceMaps':same_source,'sameNativeMaps':same_bins,'packets':packets,'integrityFindings':integrity,'qualificationLimits':['Read-only current source, ZIP, AST, log, census artifact and native-file inspection; no test or native execution by auditor.','Fifteen native barrier tests plus fourteen dispatch and fifteen incoming tests executed. Three erasure controls are passing tests asserting weakened behavior, not separate failing runner variants.','Six-tag administrative routine-DDL participation only. Successful DDL deliberately leaves epoch unchanged; fresh census remains necessary. Shared-role/cascade/grant/event-trigger administration and complete source/authority closure are excluded.','No automatic epoch issuer, authenticated installation, held business-use permit or backend acceptance qualification.']}
import gzip,collections
folder=BASE/'4b98ea53-172f-4038-b68b-d4c76ac789c3';packet=result['packets']['routine-ddl-barrier'];extra_fail=[]
def check(ok,label):
 if not ok:extra_fail.append(label)
logs=[json.loads(line) for line in (folder/'tests.stdout.log').read_text().splitlines() if line.strip()]
expected_pairs=[('test_omitted_table_modes_allow_pending_commit_source_change',('pending','committed'),'pg_proc','prosrc',[' SELECT 333 ',' SELECT 444 ']),('test_selected_ddl_changes_source_not_epoch',('before','after'),'pg_proc','prosrc',[' SELECT 333 ',' SELECT 444 ']),('test_shared_role_change_is_explicitly_outside_barrier',('before-role','after-role'),'pg_roles','bypass',[False,True])]
expected_files={test+'-'+label+'.census.txt.gz' for test,labels,*_ in expected_pairs for label in labels}
check({p.name for p in folder.glob('*.census.txt.gz')}==expected_files,'exact six retained census files')
check(len(logs)==6 and len({(r['test'],r['census']) for r in logs})==6,'six unique stdout census observations')
with zipfile.ZipFile(folder/'sources.zip') as z:
 barrier=z.read(str(ROOT/'packages/postgresql/native/source-epoch-routine-ddl-barrier.sql').lstrip('/')).decode()
 test_source=z.read(str(ROOT/'packages/python/tests/test_routine_ddl_barrier_native.py').lstrip('/')).decode()
 original_body=barrier.split('AS $$',1)[1].split('$$;',1)[0]
function=barrier.split('REVOKE ALL',1)[0].replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1)
lock_marker=' LOCK TABLE truss.source_epoch_current, truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT;'
own_marker=' IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l'
check(function.count(lock_marker)==function.count(own_marker)==1,'independent exact mutation marker counts')
mutant_body=original_body.replace(lock_marker,' -- Deliberate omitted writer table modes.')
image_details={};images={};tuples={}
for row in logs:
 name=row['test']+'-'+row['census']+'.census.txt.gz';data=gzip.decompress((folder/name).read_bytes());obj=json.loads(data);images[name]=obj
 check(type(row['octets']) is int and len(data)==row['octets']<=16777216 and sha(data)==row['sha256'],name+' hash/size stdout correspondence')
 check(obj['version']=='truss.security.query-source-census/0.1.0' and obj['serverVersion']=='160015' and obj['database']=='routine_ddl_barrier_component' and len(obj['sections'])==40,name+' census exact version/database/sections')
 sections={k:[json.loads(r) for r in rows] for k,rows in obj['sections'].items()}
 check(int(obj['rowCount'])==sum(len(rows) for rows in sections.values())<=100000 and all(len(rows)<=8192 for rows in sections.values()),name+' complete row count/bounds')
 def only(section,predicate):
  rows=[r for r in sections[section] if predicate(r)];check(len(rows)==1,name+' unique '+section);return rows[0]
 ns=only('pg_namespace',lambda r:r.get('nspname')=='truss')
 subject=only('pg_proc',lambda r:r.get('proname')=='ddl_subject' and r.get('pronamespace')==ns['oid'])
 hook=only('pg_event_trigger',lambda r:r.get('evtname')=='truss_routine_ddl_writer_barrier')
 routine=only('pg_proc',lambda r:r.get('oid')==hook['evtfoid'])
 ordinary=only('pg_roles',lambda r:r.get('name')=='ddl_barrier_ordinary')
 check(subject['pronargs']==0 and subject['proargtypes']==[] and subject['prorettype']=='23' and subject['prokind']=='f',name+' subject exact signature')
 check(hook['evtevent']=='ddl_command_start' and hook['evtenabled']=='A' and hook['evttags']==['CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION','CREATE PROCEDURE','ALTER PROCEDURE','DROP PROCEDURE'],name+' exact ALWAYS six-tag hook')
 expected_body=mutant_body if row['test'].startswith('test_omitted_table_modes_') else original_body
 check(routine['proname']=='runtime_fence_routine_ddl_writer' and routine['pronamespace']==ns['oid'] and routine['prosrc']==expected_body and routine['prosecdef'] is False and routine['provolatile']=='v' and routine['proconfig']==['search_path=pg_catalog, pg_temp'],name+' exact installed original/mutant body/linkage')
 tuples[name]={'namespaceOid':ns['oid'],'subjectOid':subject['oid'],'subjectBody':subject['prosrc'],'hookOid':hook['oid'],'hookRoutineOid':routine['oid'],'hookBodySha256':sha(routine['prosrc'].encode()),'hookBodyVariant':'omitted-table-modes' if expected_body==mutant_body else 'original','ordinaryRoleOid':ordinary['oid'],'ordinaryRoleBypass':ordinary['bypass']}
 image_details[name]={'compressedSha256':sha((folder/name).read_bytes()),'uncompressedSha256':sha(data),'octets':len(data),'rowCount':obj['rowCount'],'sectionCount':40,'tupleIdentities':tuples[name]}
diffs=[]
for test,labels,wanted_section,wanted_field,wanted_values in expected_pairs:
 names=[test+'-'+label+'.census.txt.gz' for label in labels];a,b=[images[n] for n in names];section_diffs={}
 for sec in a['sections']:
  x,y=collections.Counter(a['sections'][sec]),collections.Counter(b['sections'][sec]);left=list((x-y).elements());right=list((y-x).elements())
  if left or right:
   if len(left)==len(right)==1:
    old,new=json.loads(left[0]),json.loads(right[0]);fields={k:[old.get(k),new.get(k)] for k in old.keys()|new.keys() if old.get(k)!=new.get(k)}
   else:fields=None
   section_diffs[sec]={'removedRows':len(left),'addedRows':len(right),'fieldChanges':fields}
 check(section_diffs=={wanted_section:{'removedRows':1,'addedRows':1,'fieldChanges':{wanted_field:wanted_values}}},test+' exact one-field pair difference')
 check(all(tuples[names[0]][k]==tuples[names[1]][k] for k in ('namespaceOid','subjectOid','hookOid','hookRoutineOid','ordinaryRoleOid')),test+' original object identities retained')
 diffs.append({'test':test,'images':names,'differences':section_diffs})
restored='test_selected_ddl_changes_source_not_epoch-before.census.txt.gz'
check(tuples[restored]['hookBodyVariant']=='original','original hook body independently observed after both erasure tests')
check(image_details[restored]['uncompressedSha256']==image_details['test_shared_role_change_is_explicitly_outside_barrier-before-role.census.txt.gz']['uncompressedSha256'],'exact whole census restored after committed subject edit')
packet['censusAudit']={'images':image_details,'isolatedPairDifferences':diffs,'mutationMarkers':{'tableModeCount':function.count(lock_marker),'ownShareCount':function.count(own_marker)},'restorationEvidence':['Later census retains exact original hook body and ALWAYS metadata after both erasure tests and administrative hook-disable test.','Selected-change before census equals shared-role before census byte-for-byte, corroborating subject restoration.','Role reset runs successfully within the passing source test; no separate post-reset census is retained. Entire owned fixture is then removed.'],'findings':extra_fail}
for f in extra_fail:result['integrityFindings'].append({'packet':'routine-ddl-barrier','finding':f})
if extra_fail:result['status']='integrity-findings'

marker_row=' PERFORM 1 FROM truss.installation_marker m WHERE m.singleton_id=1 FOR UPDATE NOWAIT;'
check(function.count(marker_row)==1,'exact original marker row replacement site')
packet['censusAudit']['mutationMarkers']['markerRowCount']=function.count(marker_row)
packet['sourceControlReview']={'acquisitionTuple':'All12 returned fields compared to authored fixture inputs plus independently selected native xid/database OID/backend PID/session and effective actors.','everyTestRestoration':'tearDown restores original function, reads exact prosrc and ALWAYS six-tag hook linkage, observes subject333, and reacquires then checks renewed55000 refusal. All15 methods and tearDowns pass.','writerSerialization':'Normal second writer checks marker-specific55P03 error. Omitted marker control retains both table modes in both writers and permits distinct second_subject DDL, isolating marker exclusion from same-routine catalog contention.','mutationMechanism':'Each source marker has exact count1. Changes are installed from the frozen SQL function definition, and original function restored after each test.','historicalAuditPreserved':'/private/tmp/astra-routine-ddl-barrier-native-audit-4471-predecessor.json'}
previous_raw=(BASE/'4471bc46-d4d3-4390-8130-4055c68548e4/receipt.json').read_bytes();previous=json.loads(previous_raw);current=receipts[0]
x,y=previous['sourceDigests'],current['sourceDigests']
result['comparisonToPredecessor']={'priorRunId':previous['runId'],'priorReceiptSha256':sha(previous_raw),'addedPins':sorted(y.keys()-x.keys()),'removedPins':sorted(x.keys()-y.keys()),'changedPins':[{'path':p,'priorSha256':x[p],'currentSha256':y[p]} for p in sorted(x.keys()&y.keys()) if x[p]!=y[p]],'sameNativeMaps':previous['nativeBinaryDigests']==current['nativeBinaryDigests']}
if function.count(marker_row)!=1:result['integrityFindings'].append({'finding':'marker row replacement site count'});result['status']='integrity-findings'
out=Path('/private/tmp/astra-routine-ddl-barrier-native-audit.json');out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'status':result['status'],'integrityFindings':integrity,'packets':{k:{'runId':p['runId'],'receiptSha256':p['receiptSha256'],'zipSha256':p['zipSha256'],'sourceCount':p['sourceCount'],'nativeBinaryCount':p['nativeBinaryCount'],'currentSourceDrift':p['currentSourceDrift'],'status':p['status']} for k,p in packets.items()}},indent=2))
