"""Read retained bytes/logs only; does not execute repository tests, SQL or native tools."""
import ast,collections,datetime,hashlib,json,re,zipfile
from pathlib import Path

ROOT=Path('/private/tmp/truss-security-main-integration')
BASE=ROOT/'docs/helix/04-build/evidence/python-catalog-report-release'
OUTPUT=Path('/private/tmp/astra-archive-self-write-fence-audit.json')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
POS='c07496ad-5c5f-47d5-bf3f-52761aa4983f'
NEG='f0d2f27a-035a-4a31-8de4-1a00e38880f5'
OLD='c38f1554-68dc-481f-b1a7-b3f407d1ae4e'
SINGLE_FAILURES={'test_change_restore_cannot_begin_under_original_cut','test_lock_upgrade_keeps_original_fence_visible','test_release_reparents_fence_and_later_rollback_preserves_it','test_replica_mode_does_not_disable_fence'}
SUBTEST_METHOD='test_all_write_events_and_noop_statements_are_fenced'

def audit(run,negative):
 folder=BASE/run;receipt_bytes=(folder/'receipt.json').read_bytes();r=json.loads(receipt_bytes);pins=r['sourceDigests'];findings=[]
 def check(value,label):
  if not value:findings.append(label)
 out={'runId':run,'auditFailures':findings,'receiptSha256':sha(receipt_bytes),'zipSha256':sha((folder/'sources.zip').read_bytes()),'receiptStatus':r['status']}
 check(r['runId']==run and r['status']==('countercontrol-reproduced' if negative else 'component-passed'),'receipt identity/status')
 check(r.get('countercontrol') is negative and r.get('selfWriteFenceProfile') is True and r.get('countercontrolKind')==('self-write-fence' if negative else None),'exact selected profile')
 check(type(r['nativeTests']) is int and r['nativeTests']==8 and type(r['testExitCode']) is int and r['testExitCode']==int(negative),'native count/exit')
 check(r['testCommand'][7]=='test_archive_self_write_fence_native.py','exact selected test file')
 bad=[p for p,h in pins.items() if not Path(p).is_file() or sha(Path(p).read_bytes())!=h]
 out.update(sourceCount=len(pins),currentSourceMismatches=bad);check(len(pins)==273 and not bad,'273 current source/dependency pins')
 with zipfile.ZipFile(folder/'sources.zip') as z:
  names=z.namelist();expected={p.lstrip('/') for p in pins};duplicates=len(names)-len(set(names));extra=sorted(set(names)-expected);missing=sorted(expected-set(names));mismatches=[p for p,h in pins.items() if p.lstrip('/') in names and sha(z.read(p.lstrip('/')))!=h]
  out['zip']={'entryCount':len(names),'duplicates':duplicates,'extra':extra,'missing':missing,'digestMismatches':mismatches}
  check(len(names)==273 and not(duplicates or extra or missing or mismatches),'exact source ZIP')
  def source(relative):return z.read(str(ROOT/relative).lstrip('/'))
  def methods(module,cls=None):
   t=ast.parse(source('packages/python/tests/'+module+'.py'))
   return [f'{module}.{c.name}.{f.name}' for c in t.body if isinstance(c,ast.ClassDef) and (cls is None or c.name==cls) for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')]
  native=methods('test_archive_self_write_fence_native');dispatch=methods('test_native_catalog_dispatch','NativeCatalogDispatchTests');aux=methods('test_catalog_source_candidate')+methods('test_configured_catalog_stage')
  check((len(native),len(dispatch),len(aux))==(8,14,15),'frozen declared method populations')
  tree=ast.parse(source('packages/python/tests/test_archive_self_write_fence_native.py'))
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ArchiveSelfWriteFenceNativeTests')
  method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==SUBTEST_METHOD)
  sqls=next(ast.literal_eval(n.iter) for n in method.body if isinstance(n,ast.For))
  check(len(sqls)==len(set(sqls))==6,'six distinct declared write controls')
  fence=source('packages/postgresql/native/catalog-report/archive-self-write-fence.sql')
  release=source('packages/postgresql/native/catalog-report/release-selection.sql')
  check(r['executedReleaseSqlSha256']==sha(release),'unchanged executed release selector digest')
  if negative:
   marker=b' IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l';replacement=b' IF FALSE AND EXISTS(SELECT 1 FROM pg_catalog.pg_locks l';variant=(folder/'countercontrol-archive-self-write-fence.sql').read_bytes()
   exact=fence.count(marker)==1 and variant==fence.replace(marker,replacement)
   out['counterVariant']={'originalSha256':sha(fence),'variantSha256':sha(variant),'markerCount':fence.count(marker),'exactSingleReplacement':exact};check(exact,'exact one-marker fence omission')
  policy=json.loads(source('packages/python/src/truss/_profiles/catalog-report-release.json'));resources=[]
  for row in policy['resources']:
   body=source(row['path']);resources.append({'path':row['path'],'bytes':len(body),'sha256':sha(body),'matchesPolicyAndPin':sha(body)==row['sha256']==pins[str(ROOT/row['path'])]})
  out['declaredResources']={'count':len(resources),'totalBytes':sum(i['bytes'] for i in resources),'rows':resources}
  check(len(resources)==21 and len({i['path'] for i in resources})==21 and all(i['matchesPolicyAndPin'] for i in resources) and sum(i['bytes'] for i in resources)==101453,'unchanged declared resource closure')
  deps={}
  for package in ('pg8000','scramp','asn1crypto','dateutil','six'):
   files=[p for p in pins if p.endswith('.py') and (package in Path(p).parts or package=='six' and Path(p).name=='six.py')]
   distribution='python_dateutil' if package=='dateutil' else package
   metadata=[p for p in pins if Path(p).name=='METADATA' and Path(p).parent.name.startswith(distribution+'-')]
   deps[package]={'pythonFiles':len(files),'metadataFiles':len(metadata),'versions':[re.search(rb'^Version: (.+)$',z.read(p.lstrip('/')),re.M).group(1).decode() for p in metadata]};check(bool(files) and len(metadata)==1,'dependency '+package)
  out['dependencies']=deps
  packagefiles=[p for p in (ROOT/'packages/python/src/truss').rglob('*') if p.is_file() and '__pycache__' not in p.parts];uncaptured=[str(p) for p in packagefiles if str(p) not in pins]
  out['currentPythonPackageFileCount']=len(packagefiles);out['uncapturedCurrentPythonPackageFiles']=uncaptured;check(not uncaptured,'whole Python package capture')
  check(str(ROOT/'packages/postgresql/native/canonical-tree-bytes.sql') in pins,'native codec captured')
 log=(folder/'tests.stderr.log').read_text()
 rows=re.findall(r'^test_\S+ \(([^)]+)\) \.\.\.[ \t]*(ok|FAIL|ERROR)?[ \t]*$',log,re.M)
 names=[n for n,s in rows];subrows=re.findall(r'^  test_\S+ \(([^)]+)\) \(sql=(.+)\) \.\.\. (FAIL|ok|ERROR)$',log,re.M)
 subs=[{'method':n,'sql':ast.literal_eval(s),'result':state} for n,s,state in subrows]
 failheaders=re.findall(r'^FAIL: (.+)$',log,re.M)
 check(len(rows)==len(set(names))==8 and set(names)==set(native),'exact eight-method native log population')
 if negative:
  check(all(status==('' if name.rsplit('.',1)[1]==SUBTEST_METHOD else 'FAIL' if name.rsplit('.',1)[1] in SINGLE_FAILURES else 'ok') for name,status in rows),'exact expected native main-method statuses')
  check(len(subs)==6 and [s['sql'] for s in subs]==sqls and all(s['result']=='FAIL' and s['method'].endswith('.'+SUBTEST_METHOD) for s in subs),'exact six declared subtest failures')
  check(len(failheaders)==10 and log.count('AssertionError: DatabaseError not raised')==10 and 'FAILED (failures=10)' in log.splitlines(),'exact ten isolated missing-refusal failures')
 else:
  check(all(s=='ok' for n,s in rows) and not subs and not failheaders and 'OK' in log.splitlines(),'all eight positive methods passed')
 check(re.search(r'^Ran 8 tests in ',log,re.M) is not None and 'skipped' not in log and not re.search(r'^ERROR:',log,re.M),'native exact summary/no skips/errors')
 out['nativeMethods']={'expectedMethods':native,'observedMainResults':dict(rows),'subtestResults':subs,'declaredSubtestSql':sqls,'failureHeaders':failheaders,'missingRefusalFailureCount':log.count('AssertionError: DatabaseError not raised'),'summary':re.findall(r'^(?:Ran \d+ tests.*|OK|FAILED \(.*\))$',log,re.M)}
 def group(prefix,expected):
  t=(folder/(prefix+'.stderr.log')).read_text();records=re.findall(r'^test_\S+ \(([^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$',t,re.M);ns=[n for n,s in records]
  check(len(ns)==len(set(ns))==len(expected) and set(ns)==set(expected) and all(s=='ok' for n,s in records),'exact '+prefix+' inventory/status')
  check(re.search(r'^Ran '+str(len(expected))+r' tests in ',t,re.M) is not None and 'OK' in t.splitlines(),'exact '+prefix+' summary')
  return {'expectedMethods':expected,'observedCount':len(records),'results':dict(records)}
 out['dispatchMethods']=group('regression',dispatch);check(r['originalCatalogRegressions']==[n.rsplit('.',1)[1] for n in dispatch],'receipt exact dispatch inventory')
 if not negative:out['auxiliaryMethods']=group('auxiliary',aux);check(r['incomingCatalogRegressions']==aux,'receipt auxiliary inventory')
 else:out['auxiliaryLogFiles']=[p.name for p in folder.glob('auxiliary.*.log')];check(not out['auxiliaryLogFiles'] and r['incomingCatalogRegressions']==[],'counter explicitly omits auxiliary execution')
 binaries=r['nativeBinaryDigests'];bad_binary=[p for p,h in binaries.items() if not Path(p).is_file() or sha(Path(p).read_bytes())!=h]
 out.update(nativeBinaryCount=len(binaries),currentNativeBinaryMismatches=bad_binary);check(len(binaries)==1614 and not bad_binary,'1614 current binary files')
 server=(folder/'server.log').read_text();socket_match=re.search(r'listening on Unix socket "([^"]+)"',server);socket=Path(socket_match.group(1)) if socket_match else None;execution=Path(r['testCommand'][5]).parents[3]
 out['cleanup']={'receipt':r['cleanup'],'executionDirectory':str(execution),'executionDirectoryAbsent':not execution.exists(),'socketPath':str(socket) if socket else None,'socketParentAbsent':socket is not None and not socket.parent.exists(),'serverShutdownLogged':re.search(r'LOG:  database system is shut down\s*$',server) is not None}
 check(r['cleanup']=={'attempted':True,'stopExitCode':0,'statusExitCode':3,'socketAbsent':True} and not execution.exists() and socket is not None and not socket.exists() and not socket.parent.exists() and out['cleanup']['serverShutdownLogged'],'owned cleanup corroborated')
 out['boundaries']=(folder/'boundaries.stdout.log').read_text().strip();out['logHashes']={p.name:sha(p.read_bytes()) for p in folder.glob('*.log')}
 check((folder/'receipt.json').read_bytes()==receipt_bytes,'receipt unchanged through audit')
 old=json.loads((BASE/OLD/'receipt.json').read_bytes());a=old['sourceDigests'];b=pins
 out['priorCheckpointComparison']={'runId':OLD,'addedPaths':sorted(b.keys()-a.keys()),'removedPaths':sorted(a.keys()-b.keys()),'changedPaths':[{'path':p,'oldSha256':a[p],'newSha256':b[p]} for p in sorted(a.keys()&b.keys()) if a[p]!=b[p]],'sameNativeBinaryPins':old['nativeBinaryDigests']==binaries}
 check(set(out['priorCheckpointComparison']['addedPaths'])=={str(ROOT/'packages/python/tests/test_archive_self_write_fence_native.py'),str(ROOT/'packages/postgresql/native/catalog-report/archive-self-write-fence.sql')} and not out['priorCheckpointComparison']['removedPaths'] and {p['path'] for p in out['priorCheckpointComparison']['changedPaths']}=={str(ROOT/'scripts/check-python-catalog-report-release-native.py')},'only two added component files and runner changed from prior checkpoint')
 out['status']='scoped-evidence-matches' if not findings else 'findings'
 return out,r

positive,p=audit(POS,False);counter,n=audit(NEG,True)
findings=[{'packet':label,'finding':f} for label,out in [('positive',positive),('countercontrol',counter)] for f in out['auditFailures']]
same_sources=p['sourceDigests']==n['sourceDigests'];same_binary=p['nativeBinaryDigests']==n['nativeBinaryDigests']
if not same_sources or not same_binary:findings.append({'finding':'packet original pins differ'})
prior=Path('/private/tmp/astra-catalog-resources-merge-audit.json')
result={'auditKind':'independent retained native archive self-write fence component audit','auditedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'integrationRoot':str(ROOT),'status':'scoped-evidence-matches' if not findings else 'findings','executionsPerformed':'Only local file/hash/ZIP/AST/log inspection; no tests, native SQL/tools, producers or repository edits.','sameOriginalSourcePins':same_sources,'sameNativeBinaryPins':same_binary,'priorAuditPreserved':{'path':str(prior),'sha256':sha(prior.read_bytes())},'positive':positive,'countercontrol':counter,'findings':findings,'qualification':'Separate private native trigger component under its actual SHARE-lock lifetime. Eight fence methods plus fourteen dispatch and fifteen auxiliary positive methods; counter ten missing-refusal assertions across six write subtests and four other methods. No claim that the fence is installed in the configured release path, authenticated trigger/source authority, full host held-use lifetime or backend acceptance.'}
OUTPUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'path':str(OUTPUT),'sha256':sha(OUTPUT.read_bytes()),'status':result['status'],'findings':findings,'positiveReceiptSha256':positive['receiptSha256'],'counterReceiptSha256':counter['receiptSha256']},indent=2))
