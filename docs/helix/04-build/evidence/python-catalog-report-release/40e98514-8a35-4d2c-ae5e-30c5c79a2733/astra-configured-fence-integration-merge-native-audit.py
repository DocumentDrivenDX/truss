"""Independent retained-evidence inspection; no repository/native/test execution."""
import ast,datetime,hashlib,json,re,zipfile
from pathlib import Path

ROOT=Path('/private/tmp/truss-security-main-integration')
BASE=ROOT/'docs/helix/04-build/evidence/python-catalog-report-release'
OUTPUT=Path('/private/tmp/astra-configured-fence-integration-merge-native-audit.json')
RUNS={None: '40e98514-8a35-4d2c-ae5e-30c5c79a2733', 'fence-correspondence': 'b75402b0-cae1-4d56-8f49-f8e8820e0e3a', 'fence-body-hash': 'aef34088-2853-4f8b-8320-348731644781', 'resource-digest': '97de4b9a-6e91-4b86-be76-109f0fcf208d', 'archive-lock': '3b64709a-7ce2-4183-9916-62ed096fc7c1', 'self-write-fence': '18787d50-2a41-4dcc-b29d-56fd407ba7e2'}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
DRIFT='test_missing_or_changed_fence_refuses_before_first_effect'
LATE='test_late_fence_source_change_refuses_and_rolls_back'
WRITES='test_all_write_events_and_noop_statements_are_fenced'
SINGLES={None:set(),'fence-correspondence':{LATE},'fence-body-hash':{LATE},'resource-digest':{'test_resource_archive_damage_refuses_before_first_catalog_effect'},'archive-lock':{'test_concurrent_archive_writes_excluded_until_transaction_end','test_later_rollback_and_savepoint_release_preserve_archive_cut','test_preexisting_archive_writer_refuses_without_waiting','test_rollback_across_selection_releases_archive_cut_same_xid'},'self-write-fence':{'test_change_restore_cannot_begin_under_original_cut','test_lock_upgrade_keeps_original_fence_visible','test_release_reparents_fence_and_later_rollback_preserves_it','test_replica_mode_does_not_disable_fence'}}
VARIANTS={
 'fence-correspondence':('configured-stage.sql',b' PERFORM truss.runtime_require_selected_archive_write_fence();',b' -- Deliberate paired omission: installed fence correspondence absent.',2,'countercontrol-configured-stage.sql'),
 'fence-body-hash':('archive-write-fence-current.sql',b'  OR sha256(convert_to(routine.prosrc,',b'  OR FALSE AND sha256(convert_to(routine.prosrc,',1,'countercontrol-archive-write-fence-current.sql'),
 'resource-digest':('resource-selection.sql',b'  IF NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=row.archive_row_id',b'  IF FALSE AND NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=row.archive_row_id',1,'countercontrol-resource-selection.sql'),
 'archive-lock':('release-selection.sql',b' LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;',b' -- Deliberate negative control: archive table lock omitted.',1,'countercontrol-release-selection.sql'),
 'self-write-fence':('archive-self-write-fence.sql',b' IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l',b' IF FALSE AND EXISTS(SELECT 1 FROM pg_catalog.pg_locks l',1,'countercontrol-archive-self-write-fence.sql')}

def constants(tree,fence):
 """Interpret only pure constant-string expressions; never import/execute fixture code."""
 env={'FENCE_SOURCE':fence.decode()}
 def value(n):
  if isinstance(n,ast.Constant):return n.value
  if isinstance(n,ast.Name):return env[n.id]
  if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add):return value(n.left)+value(n.right)
  if isinstance(n,ast.Subscript):return value(n.value)[value(n.slice)]
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='len':return len(value(n.args[0]))
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('split','encode','ljust','replace'):
   return getattr(value(n.func.value),n.func.attr)(*[value(x) for x in n.args])
  if isinstance(n,ast.List):return [value(x) for x in n.elts]
  raise ValueError('Unsupported constant expression: '+ast.dump(n))
 for n in tree.body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   name=n.targets[0].id
   if name in ('FENCE_BODY','ALTERED_FENCE_BODY','ALTERED_FENCE_DEFINITION','SET_FENCE_DEFINITION','DEFAULT_ACL_FENCE_DEFINITION'):env[name]=value(n.value)
 return env,value

def audit(kind,run):
 folder=BASE/run;rb=(folder/'receipt.json').read_bytes();r=json.loads(rb);pins=r['sourceDigests'];findings=[]
 def ck(v,label):
  if not v:findings.append(label)
 out={'runId':run,'kind':kind,'auditFailures':findings,'receiptStatus':r['status'],'receiptSha256':sha(rb),'zipSha256':sha((folder/'sources.zip').read_bytes())}
 ck(r['status']==('component-passed' if kind is None else 'countercontrol-reproduced') and r['runId']==run,'receipt identity/status')
 ck(r.get('countercontrol') is (kind is not None) and r.get('countercontrolKind')==kind and r.get('selfWriteFenceProfile') is (kind=='self-write-fence'),'exact profile flags')
 ck(type(r['testExitCode']) is int and r['testExitCode']==int(kind is not None),'test exit code')
 bad=[p for p,h in pins.items() if not Path(p).is_file() or sha(Path(p).read_bytes())!=h]
 out.update(sourceCount=len(pins),currentSourceMismatches=bad);ck(len(pins)==276 and not bad,'276 current source/dependency pins')
 with zipfile.ZipFile(folder/'sources.zip') as z:
  names=z.namelist();expected={p.lstrip('/') for p in pins};duplicates=len(names)-len(set(names));extra=sorted(set(names)-expected);missing=sorted(expected-set(names));zipbad=[p for p,h in pins.items() if p.lstrip('/') in names and sha(z.read(p.lstrip('/')))!=h]
  out['zip']={'entryCount':len(names),'duplicates':duplicates,'extra':extra,'missing':missing,'digestMismatches':zipbad};ck(len(names)==276 and not(duplicates or extra or missing or zipbad),'exact frozen ZIP')
  def src(relative):return z.read(str(ROOT/relative).lstrip('/'))
  def sql(name):return src('packages/postgresql/native/catalog-report/'+name)
  def tree(module):return ast.parse(src('packages/python/tests/'+module+'.py'))
  def methods(module,cls=None):return [f'{module}.{c.name}.{n.name}' for c in tree(module).body if isinstance(c,ast.ClassDef) and (cls is None or cls==c.name) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
  release=methods('test_catalog_report_release_native');configured=methods('test_catalog_configured_release_stage_native');standalone=methods('test_archive_self_write_fence_native');dispatch=methods('test_native_catalog_dispatch','NativeCatalogDispatchTests');aux=methods('test_catalog_source_candidate')+methods('test_configured_catalog_stage')
  ck(tuple(map(len,(release,configured,standalone,dispatch,aux)))==(12,11,8,14,15),'frozen AST populations12/11/8/14/15')
  native=standalone if kind=='self-write-fence' else release if kind=='archive-lock' else release+configured
  ck(type(r['nativeTests']) is int and r['nativeTests']==len(native),'selected native count')
  pattern='test_archive_self_write_fence_native.py' if kind=='self-write-fence' else 'test_catalog_report_release_native.py' if kind=='archive-lock' else 'test_catalog_*release*native.py'
  ck(r['testCommand'][7]==pattern,'exact discovery pattern')
  fence=sql('archive-self-write-fence.sql');verifier=sql('archive-write-fence-current.sql');ctree=tree('test_catalog_configured_release_stage_native');env,value=constants(ctree,fence)
  c=next(n for n in ctree.body if isinstance(n,ast.ClassDef) and n.name=='ConfiguredReleaseStageNativeTests');m=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==DRIFT)
  drifts=next(value(n.value) for n in m.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cases' for t in n.targets))
  stree=tree('test_archive_self_write_fence_native');sc=next(n for n in stree.body if isinstance(n,ast.ClassDef));sm=next(n for n in sc.body if isinstance(n,ast.FunctionDef) and n.name==WRITES);writes=next(ast.literal_eval(n.iter) for n in sm.body if isinstance(n,ast.For))
  body=env['FENCE_BODY'].encode();altered=env['ALTERED_FENCE_BODY'].encode()
  out['bodyAndDriftControls']={'originalBodyBytes':len(body),'originalBodySha256':sha(body),'alteredBodyBytes':len(altered),'alteredBodySha256':sha(altered),'driftCount':len(drifts),'uniqueDrifts':len(set(drifts)),'declaredDrifts':drifts}
  ck(len(body)==len(altered)==694 and body!=altered and sha(body).encode() in verifier and len(drifts)==len(set(drifts))==21 and len(writes)==6,'exact body length/digest and independent control inventories')
  executed={n:sql(n) for n in ('archive-self-write-fence.sql','archive-write-fence-current.sql','configured-stage.sql','release-selection.sql','resource-selection.sql')}
  if kind is not None:
   name,marker,replacement,count,variant_name=VARIANTS[kind];original=executed[name];variant=(folder/variant_name).read_bytes();exact=original.count(marker)==count and variant==original.replace(marker,replacement);ck(exact,'exact declared marker-only variant');executed[name]=variant
   out['variant']={'path':str(folder/variant_name),'originalSha256':sha(original),'variantSha256':sha(variant),'markerCount':original.count(marker),'exactReplacement':exact}
  for field,name in [('executedFenceSqlSha256','archive-self-write-fence.sql'),('executedFenceComparisonSqlSha256','archive-write-fence-current.sql'),('executedConfiguredStageSqlSha256','configured-stage.sql'),('executedReleaseSqlSha256','release-selection.sql')]:ck(r[field]==sha(executed[name]),'executed digest '+field)
  policy=json.loads(src('packages/python/src/truss/_profiles/catalog-report-release.json'));resources=[{'path':x['path'],'bytes':len(src(x['path'])),'sha256':sha(src(x['path'])),'matchesPolicyAndPin':sha(src(x['path']))==x['sha256']==pins[str(ROOT/x['path'])]} for x in policy['resources']]
  out['resources']={'count':len(resources),'totalBytes':sum(x['bytes'] for x in resources),'rows':resources};ck(len(resources)==21 and len({x['path'] for x in resources})==21 and sum(x['bytes'] for x in resources)==101453 and all(x['matchesPolicyAndPin'] for x in resources),'21 exact original resource inputs')
  pkg=[p for p in (ROOT/'packages/python/src/truss').rglob('*') if p.is_file() and '__pycache__' not in p.parts];uncaptured=[str(p) for p in pkg if str(p) not in pins];out['uncapturedPythonFiles']=uncaptured;out['currentPythonPackageFileCount']=len(pkg);ck(not uncaptured,'whole Python package capture')
  deps={}
  for package in ('pg8000','scramp','asn1crypto','dateutil','six'):
   fs=[p for p in pins if p.endswith('.py') and (package in Path(p).parts or package=='six' and Path(p).name=='six.py')];dist='python_dateutil' if package=='dateutil' else package;meta=[p for p in pins if Path(p).name=='METADATA' and Path(p).parent.name.startswith(dist+'-')]
   deps[package]={'pythonFiles':len(fs),'metadataFiles':len(meta),'versions':[re.search(rb'^Version: (.+)$',z.read(p.lstrip('/')),re.M).group(1).decode() for p in meta]};ck(bool(fs) and len(meta)==1,'dependency closure '+package)
  out['dependencies']=deps;ck(str(ROOT/'packages/postgresql/native/canonical-tree-bytes.sql') in pins,'codec source captured')
 log=(folder/'tests.stderr.log').read_text();rows=re.findall(r'^test_\S+ \(([^)]+)\) \.\.\.[ \t]*(ok|FAIL|ERROR)?[ \t]*$',log,re.M);ns=[n for n,s in rows];subs=[{'method':n,'sql':ast.literal_eval(s),'result':state} for n,s,state in re.findall(r'^  test_\S+ \(([^)]+)\) \(sql=(.+)\) \.\.\. (FAIL|ok|ERROR)$',log,re.M)]
 expected_subs=drifts if kind=='fence-correspondence' else [env['ALTERED_FENCE_DEFINITION']] if kind=='fence-body-hash' else writes if kind=='self-write-fence' else []
 submethod=DRIFT if kind in ('fence-correspondence','fence-body-hash') else WRITES if kind=='self-write-fence' else None
 failure_count=len(expected_subs)+len(SINGLES[kind]);heads=re.findall(r'^FAIL: (.+)$',log,re.M)
 ck(len(ns)==len(set(ns))==len(native) and set(ns)==set(native),'exact native method log inventory')
 ck(all(status==('' if name.rsplit('.',1)[1]==submethod else 'FAIL' if name.rsplit('.',1)[1] in SINGLES[kind] else 'ok') for name,status in rows),'exact native main-method outcomes')
 ck(len(subs)==len(expected_subs) and [x['sql'] for x in subs]==expected_subs and all(x['result']=='FAIL' and x['method'].endswith('.'+submethod) for x in subs),'exact isolated subtest identities/order')
 ck(len(heads)==failure_count and log.count('AssertionError: DatabaseError not raised')==failure_count,'exact intended missing-refusal failures')
 ck(re.search(r'^Ran '+str(len(native))+r' tests in ',log,re.M) is not None and ('OK' if kind is None else f'FAILED (failures={failure_count})') in log.splitlines() and 'skipped' not in log and not re.search(r'^ERROR:',log,re.M),'exact native terminal summary/no errors/skips')
 out['nativeInventory']={'expectedMethods':native,'mainResults':dict(rows),'expectedFailureCount':failure_count,'subtestResults':subs,'failureHeaders':heads,'summary':re.findall(r'^(?:Ran \d+ tests.*|OK|FAILED \(.*\))$',log,re.M)}
 def group(prefix,expected):
  if not expected:
   logs=[p.name for p in folder.glob(prefix+'.*.log')];ck(not logs,prefix+' explicitly unexecuted');return {'executed':False,'logFiles':logs}
  t=(folder/(prefix+'.stderr.log')).read_text();rs=re.findall(r'^test_\S+ \(([^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$',t,re.M);names=[n for n,s in rs];ck(len(names)==len(set(names))==len(expected) and set(names)==set(expected) and all(s=='ok' for n,s in rs),prefix+' exact methods/statuses');ck(re.search(r'^Ran '+str(len(expected))+r' tests in ',t,re.M) is not None and 'OK' in t.splitlines(),prefix+' exact summary');return {'executed':True,'expectedMethods':expected,'results':dict(rs),'count':len(rs)}
 selected_dispatch=[] if kind=='self-write-fence' else dispatch;selected_aux=aux if kind is None else []
 out['dispatch']=group('regression',selected_dispatch);out['auxiliary']=group('auxiliary',selected_aux);ck(r['originalCatalogRegressions']==[x.rsplit('.',1)[1] for x in selected_dispatch] and r['incomingCatalogRegressions']==selected_aux,'receipt exact executed regression inventories')
 bins=r['nativeBinaryDigests'];badbin=[p for p,h in bins.items() if not Path(p).is_file() or sha(Path(p).read_bytes())!=h];out.update(nativeBinaryCount=len(bins),currentNativeBinaryMismatches=badbin);ck(len(bins)==1614 and not badbin,'1614 current native binary/file pins')
 server=(folder/'server.log').read_text();sm=re.search(r'listening on Unix socket "([^"]+)"',server);socket=Path(sm.group(1)) if sm else None;execution=Path(r['testCommand'][5]).parents[3]
 out['cleanup']={'receipt':r['cleanup'],'executionDirectory':str(execution),'executionDirectoryAbsent':not execution.exists(),'socketPath':str(socket) if socket else None,'socketParentAbsent':socket is not None and not socket.parent.exists(),'serverShutdownLogged':re.search(r'LOG:  database system is shut down\s*$',server) is not None};ck(r['cleanup']=={'attempted':True,'stopExitCode':0,'statusExitCode':3,'socketAbsent':True} and not execution.exists() and socket is not None and not socket.exists() and not socket.parent.exists() and out['cleanup']['serverShutdownLogged'],'corroborated owned fixture cleanup')
 out['boundaries']=(folder/'boundaries.stdout.log').read_text().strip();out['logHashes']={p.name:sha(p.read_bytes()) for p in folder.glob('*.log')};ck((folder/'receipt.json').read_bytes()==rb,'receipt stable through audit');out['status']='scoped-evidence-matches' if not findings else 'findings'
 return out,r

reports={};receipts=[]
for kind,run in RUNS.items():
 out,r=audit(kind,run);reports['positive' if kind is None else kind]=out;receipts.append(r)
findings=[{'packet':key,'finding':f} for key,out in reports.items() for f in out['auditFailures']]
same_source=all(r['sourceDigests']==receipts[0]['sourceDigests'] for r in receipts);same_bins=all(r['nativeBinaryDigests']==receipts[0]['nativeBinaryDigests'] for r in receipts)
if not same_source or not same_bins:findings.append({'finding':'final packet original source/native pin maps differ'})
prior=Path('/private/tmp/astra-configured-fence-integration-native-audit.json')
result={'auditKind':'independent merged configured fence integration retained native evidence audit','mergedCommit':'19f1a223','incomingMain':'9fc23a75','auditedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'integrationRoot':str(ROOT),'status':'scoped-evidence-matches' if not findings else 'findings','executionsPerformed':'Only local file/hash/ZIP/AST/log inspection; no tests, SQL/native execution, producers or repository edits.','sameSourcePinMaps':same_source,'sameNativePinMaps':same_bins,'priorAuditPreserved':{'path':str(prior),'sha256':sha(prior.read_bytes())},'packets':reports,'findings':findings,'qualification':'Private configured before/after fence correspondence and archive-cut component under trusted administrative fixture. Does not authenticate verifier/issuer, establish complete installation/dependency source authority, host lifetime/final disclosure, complete accepted report, or backend acceptance. Raw archive and standalone fence omission populations are explicitly distinct from configured paths.'}

old_runs={None:'fa97ed77-c2b0-426c-85ce-892bc46e5c4b','fence-correspondence':'f8c0cabd-08bf-47fc-9c0c-a8fce0380a9e','fence-body-hash':'4fb3bf2e-f812-44eb-9a83-249cb074e5e6','resource-digest':'50c1ff15-08ee-4b64-9083-ef0c94d53304','archive-lock':'d54640f1-c4f3-41d1-b0d7-cc093bc16e38','self-write-fence':'9b421857-df35-45e3-be72-fb2fc0d51ac1'}
expected_added={str(ROOT/x) for x in ('packages/python/src/truss/_borrowed_host.py','packages/python/src/truss/_native_attachment.py')}
expected_changed={str(ROOT/x) for x in ('packages/python/src/truss/host.py','packages/python/src/truss/_native_pg8000.py','packages/python/src/truss/__init__.py','packages/python/tests/test_catalog_configured_release_stage_native.py','packages/postgresql/native/catalog-report/configured-stage.sql','scripts/check-python-catalog-report-release-native.py','scripts/check-module-boundaries.py')}
comparisons={}
for kind,new_id in RUNS.items():
 old_raw=(BASE/old_runs[kind]/'receipt.json').read_bytes();old=json.loads(old_raw);new=json.loads((BASE/new_id/'receipt.json').read_bytes());a,b=old['sourceDigests'],new['sourceDigests'];label='positive' if kind is None else kind
 changed=[{'path':p,'oldSha256':a[p],'newSha256':b[p]} for p in sorted(a.keys()&b.keys()) if a[p]!=b[p]]
 comparisons[label]={'previousRunId':old_runs[kind],'previousReceiptSha256':sha(old_raw),'currentRunId':new_id,'addedPaths':sorted(b.keys()-a.keys()),'removedPaths':sorted(a.keys()-b.keys()),'changedPaths':changed,'sameNativeBinaryPins':old['nativeBinaryDigests']==new['nativeBinaryDigests']}
 if set(comparisons[label]['addedPaths'])!=expected_added or comparisons[label]['removedPaths'] or {p['path'] for p in changed}!=expected_changed or not comparisons[label]['sameNativeBinaryPins']:findings.append({'packet':label,'finding':'unexpected merged source/native delta'})
result['comparisonsToPriorConfiguredFenceCheckpoint']=comparisons
result['status']='scoped-evidence-matches' if not findings else 'findings'

OUTPUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'path':str(OUTPUT),'sha256':sha(OUTPUT.read_bytes()),'status':result['status'],'findings':findings,'packets':{key:{'runId':out['runId'],'receiptSha256':out['receiptSha256'],'zipSha256':out['zipSha256'],'sourceCount':out['sourceCount'],'nativeBinaryCount':out['nativeBinaryCount'],'nativeMethods':len(out['nativeInventory']['mainResults']),'expectedFailures':out['nativeInventory']['expectedFailureCount']} for key,out in reports.items()}},indent=2))
