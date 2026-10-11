"""Read-only inspection of retained epoch-state packets, without native/test execution."""
import ast,datetime,hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path('/private/tmp/truss-security-main-integration')
BASE=ROOT/'docs/helix/04-build/evidence/python-catalog-report-release'
RUNS={None:'f9e2ffff-8440-48ca-b01c-283e453bae9a','epoch-issuer-fence':'3c46a193-21d2-47af-945e-c0e1d2aa9ecc','epoch-table-fence':'9d6cdef3-75cf-4f88-99af-5019844e9ed3','epoch-writer-order':'0e06eff0-5ea5-4963-a8ce-185574f3ee6f','ordinary':'26be17fa-8fa2-434a-a59c-7543113a211c'}
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
 ordinary=kind=='ordinary';counter=kind not in (None,'ordinary');expected_native=23 if ordinary else 10
 folder=BASE/run;raw=(folder/'receipt.json').read_bytes();r=json.loads(raw);pins=r['sourceDigests'];failures=[]
 def ck(ok,label):
  if not ok:failures.append(label)
 out={'runId':run,'kind':kind,'receiptStatus':r['status'],'receiptSha256':sha(raw),'zipSha256':sha((folder/'sources.zip').read_bytes()),'integrityFailures':failures}
 ck(r['runId']==run and r['status']==('countercontrol-reproduced' if counter else 'component-passed'),'receipt status/identity')
 ck(r.get('countercontrol') is counter and r.get('countercontrolKind')==(kind if counter else None) and r.get('epochStateFenceProfile') is (not ordinary) and r.get('selfWriteFenceProfile') is False,'exact epoch profile flags')
 ck(type(r['testExitCode']) is int and r['testExitCode']==int(counter) and type(r['nativeTests']) is int and r['nativeTests']==expected_native,'test count and exit code')
 ck(r['testCommand'][7]==('test_catalog_*release*native.py' if ordinary else 'test_epoch_state_fence_native.py'),'selected discovery file')
 drift=[{'path':p,'retainedSha256':h,'currentSha256':sha(Path(p).read_bytes()) if Path(p).is_file() else None} for p,h in pins.items() if not Path(p).is_file() or sha(Path(p).read_bytes())!=h]
 out.update(sourceCount=len(pins),currentSourceDrift=drift);ck(len(pins)==282,'282 declared source pins')
 with zipfile.ZipFile(folder/'sources.zip') as z:
  ns=z.namelist();expect={p.lstrip('/') for p in pins};extra=sorted(set(ns)-expect);missing=sorted(expect-set(ns));duplicates=len(ns)-len(set(ns));bad=[p for p,h in pins.items() if p.lstrip('/') in ns and sha(z.read(p.lstrip('/')))!=h]
  out['zip']={'entryCount':len(ns),'duplicates':duplicates,'extra':extra,'missing':missing,'digestMismatches':bad};ck(len(ns)==282 and not(extra or missing or duplicates or bad),'exact source ZIP')
  def src(rel):return z.read(str(ROOT/rel).lstrip('/'))
  def methods(module,cls=None):
   t=ast.parse(src('packages/python/tests/'+module+'.py'))
   return [f'{module}.{c.name}.{f.name}' for c in t.body if isinstance(c,ast.ClassDef) and (cls is None or c.name==cls) for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')]
  native=(methods('test_catalog_report_release_native')+methods('test_catalog_configured_release_stage_native')) if ordinary else methods('test_epoch_state_fence_native');dispatch=methods('test_native_catalog_dispatch','NativeCatalogDispatchTests');aux=methods('test_catalog_source_candidate')+methods('test_configured_catalog_stage')
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
 p,r=audit(kind,run);packets['positive' if kind is None else kind]=p;receipts.append(r)
integrity=[{'packet':k,'finding':v} for k,p in packets.items() for v in p['integrityFailures']];same_source=all(r['sourceDigests']==receipts[0]['sourceDigests'] for r in receipts);same_bins=all(r['nativeBinaryDigests']==receipts[0]['nativeBinaryDigests'] for r in receipts)
if not same_source or not same_bins:integrity.append({'finding':'packet original pins differ'})
has_drift=any(p['currentSourceDrift'] for p in packets.values())
result={'auditKind':'independent final epoch-state fence and ordinary retained native evidence audit','auditedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'integrationRoot':str(ROOT),'status':'integrity-findings' if integrity else 'historical-source-drift' if has_drift else 'scoped-evidence-matches','executionsPerformed':'Local file/hash/ZIP/AST/log inspection only; no native, tests, producers or repository edits.','sameRetainedSourceMaps':same_source,'sameNativeMaps':same_bins,'packets':packets,'integrityFindings':integrity,'qualificationLimits':['Read-only inspection of retained native execution; the auditor did not execute the tests or native binaries.','Issuer-predicate control independently distinguishes entry refusal from marker lock wait.','Writer-order control observes both granted RowExclusiveLock modes while issuer is blocked by the independent marker holder, and checks concurrent reader refusal; exact lock-omission mutant changes (2,55P03) to (0,success).','Table omission retains the independent immutable registry TRUNCATE guard; that case is an exact error-message discriminator, while nine assertions observe omitted refusal.','Private trusted administrative fixture component only; no authenticated issuer, full installed-source/authority or backend acceptance qualification.']}
out=Path('/private/tmp/astra-epoch-state-fence-native-audit.json');out.write_text(json.dumps(result,indent=2)+'\n')
Path('/private/tmp/astra-epoch-state-final-native-audit.json').write_bytes(out.read_bytes())
print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'status':result['status'],'integrityFindings':integrity,'packets':{k:{'runId':p['runId'],'receiptSha256':p['receiptSha256'],'zipSha256':p['zipSha256'],'sourceCount':p['sourceCount'],'nativeBinaryCount':p['nativeBinaryCount'],'currentSourceDrift':p['currentSourceDrift'],'status':p['status']} for k,p in packets.items()}},indent=2))
