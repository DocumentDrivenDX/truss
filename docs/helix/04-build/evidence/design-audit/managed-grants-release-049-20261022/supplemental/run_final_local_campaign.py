"""Final installed49 local campaign; Linux publication and Lakebase are separate gates."""
import argparse,datetime,hashlib,importlib.metadata,json,os,platform,shutil,subprocess,sys
from pathlib import Path
import pgserver,truss
import weft
import weft.weft as weft_native
from truss._runtime_profile import RUNTIME_DISTRIBUTION,RUNTIME_VERSION
from truss._current_query_originals import _actual_consumer as current_query_consumer
p=argparse.ArgumentParser();p.add_argument('--wheel',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[7];out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def basis():
 paths=[]
 for prefix in ['packages/python/src/truss','packages/python/tests','packages/python/examples','packages/browser/fixtures','tests/fixtures','scripts']:
  paths.extend(p for p in (root/prefix).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
 paths.extend([root/'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json',root/'docs/helix/03-test/acceptance-outer-json-expected.proposal.json',root/'docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json',root/'docs/helix/02-design/contracts/bindings/bootstrap-permit-arithmetic-v0.1.proposal.json',root/'docs/helix/03-test/python-exact-value-vectors.proposal.json',root/'docs/helix/04-build/evidence/receipt-position-locator-vectors.json',root/'docs/helix/02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql',root/'docs/helix/04-build/evidence/design-audit/managed-grants-release-049-20261022/supplemental/managed_grants_lifecycle_installed.py',Path(__file__).resolve()])
 return {str(p.relative_to(root)):digest(p) for p in sorted(paths)}
owner=Path(os.environ.get('UMF_OWNER_ROOT','')).resolve()
bun=os.environ.get('TRUSS_BUN_EXECUTABLE') or shutil.which('bun') or 'bun'
bun_path=Path(shutil.which(bun) or bun).resolve()
supplemental_bun=Path('/opt/homebrew/bin/bun').resolve()
owner_revision=subprocess.check_output(['git','-C',str(owner),'rev-parse','HEAD'],text=True).strip()
owner_status=subprocess.check_output(['git','-C',str(owner),'status','--porcelain','--','src','package.json','bun.lock'],text=True)
postgres=Path(pgserver.__file__).resolve().parent/'pginstall/bin/postgres'
native_version=subprocess.check_output([str(postgres),'--version'],text=True).strip()
compiler_version=subprocess.check_output([bun,'--version'],text=True).strip()
supplemental_bun_version=subprocess.check_output([str(supplemental_bun),'--version'],text=True).strip()
runtime_distribution_version=importlib.metadata.version(RUNTIME_DISTRIBUTION)
weft_version=importlib.metadata.version('weft-sql')
installed_version=importlib.metadata.version('truss-toolkit')
weft_native_path=Path(weft_native.__file__).resolve()
weft_native_sha256=digest(weft_native_path)
weft_cohort=current_query_consumer()
if owner_revision!='5ba77cff91a121a44c82f6bce32a78d8842161b5' or owner_status:
 raise ValueError('Exact clean pinned UMF independent oracle required')
if compiler_version!='1.4.3':
 raise ValueError('Bun 1.4.3 required for the independent owner oracle')
if bun_path!=supplemental_bun or supplemental_bun_version!=compiler_version or digest(supplemental_bun)!=digest(bun_path):
 raise ValueError('Lifecycle producer Bun must match the selected oracle compiler binary')
if runtime_distribution_version!=RUNTIME_VERSION:
 raise ValueError('Selected PostgreSQL runtime distribution/version mismatch')
if weft_version!='0.4.51':
 raise ValueError('Weft SQL 0.4.51 required for the final49 cohort')
if installed_version!='0.0.49':
 raise ValueError('Installed truss-toolkit 0.0.49 required for final49 cohort')
if weft_cohort.get('weftModuleSha256')!=weft_native_sha256:
 raise ValueError('Selected native Weft module does not match the current-query cohort verifier')
record={'scope':__doc__,'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'producerSha256':digest(Path(__file__)),'wheelSha256':digest(a.wheel),'inputBasis':basis(),'steps':[],'passed':False,'hostedLinux':'separate_gate','lakebaseAcceptance':'not_run',
 'identity':{'platform':platform.platform(),'python':sys.version,'wheelVersion':installed_version,'loadedPackage':str(Path(truss.__file__).resolve().parent),'nativeManifestSha256':digest(root/'packages/python/src/truss/_catalog_runtime/manifest.json'),
  'runtime':{'distribution':RUNTIME_DISTRIBUTION,'version':runtime_distribution_version,'serverVersion':native_version},
  'nativeWorker':{'modulePath':str(Path(pgserver.__file__).resolve()),'moduleSha256':digest(Path(pgserver.__file__).resolve()),'postgresPath':str(postgres),'postgresVersion':native_version,'postgresSha256':digest(postgres)},
  'weft':{'distribution':'weft-sql','version':weft_version,'packageModulePath':str(Path(weft.__file__).resolve()),'packageModuleSha256':digest(Path(weft.__file__).resolve()),
   'nativeModulePath':str(weft_native_path),'nativeModuleSha256':weft_native_sha256,'currentQueryCohort':weft_cohort},
  'independentOracle':{'path':str(owner),'sourceCommit':owner_revision,'sourceClean':not owner_status,'packageJsonSha256':digest(owner/'package.json'),'lockSha256':digest(owner/'bun.lock')},
  'compiler':{'path':str(bun_path),'version':compiler_version,'sha256':digest(bun_path)},
  'lifecycleCompiler':{'path':str(supplemental_bun),'version':supplemental_bun_version,'sha256':digest(supplemental_bun)}}
 }
receipt=out/'qualification.json'
def save():receipt.write_text(json.dumps(record,indent=2)+'\n')
env={**os.environ,'GITHUB_SHA':record['sourceCommit'],'PYTHONPATH':str(root/'scripts')+os.pathsep+str(root/'packages/python/tests'),'TRUSS_BUN_EXECUTABLE':bun,'TRUSS_CENSUS_POSTGRES_BIN':str(Path(pgserver.__file__).resolve().parent/'pginstall/bin'),'TRUSS_DISCLOSURE_NATIVE_QUALIFICATION':'1','TRUSS_EXPECTED_PACKAGE_VERSION':'0.0.49','TRUSS_QUALIFICATION_WHEEL':str(a.wheel.resolve()),'TRUSS_EXPECTED_WHEEL_SHA256':digest(a.wheel),'TRUSS_EXPECTED_RUNTIME_MANIFEST_SHA256':digest(root/'packages/python/src/truss/_catalog_runtime/manifest.json')}
commands=[
 ('boundaries',[sys.executable,str(root/'scripts/check-module-boundaries.py')]),
 ('boundary-controls',[sys.executable,str(root/'scripts/check-module-boundaries-controls.py')]),
 ('managed',[sys.executable,str(root/'scripts/qualify-managed-platform-grants.py'),'--wheel',str(a.wheel.resolve()),'--output',str(out/'managed')]),
 ('supplemental',[sys.executable,str(out/'lifecycle/managed_grants_lifecycle_installed.py')]),
 ('hf-corpus',[sys.executable,str(root/'scripts/run-hf-conformance.py'),'--installed-package','--output',str(out/'hf-corpus/qualification.json')]),
 ('protected',[sys.executable,str(root/'scripts/run-python-test-module.py'),'discover','-s',str(root/'packages/python/tests'),'-p','test_current_disclosure_runtime_native.py','-v']),
 ('migrations',[sys.executable,str(root/'scripts/qualify-runtime-migrations.py'),'--installed-package','--wheelhouse','/private/tmp/truss-runtime-migration-wheelhouse','--output',str(out/'migrations/qualification.json')]),
 ('public-workload',[sys.executable,str(root/'scripts/benchmark-public-workflows.py'),'--truss-root',str(root),'--installed-package','--count-sql-submissions','--matrix-case','small','--bulk-size','1000','--read-samples','1000','--write-samples','200','--output',str(out/'public-workload/report.json')])]
life_source=root/'docs/helix/04-build/evidence/design-audit/managed-grants-release-049-20261022/supplemental/managed_grants_lifecycle_installed.py'
life_copy=out/'lifecycle/managed_grants_lifecycle_installed.py'
life_copy.parent.mkdir(parents=True)
life_copy.write_bytes(life_source.read_bytes())
if digest(life_copy)!=digest(life_source):
 raise ValueError('Installed lifecycle producer copy differs from pinned source')
record['lifecycleProducer']={'source':str(life_source.relative_to(root)),'sourceSha256':digest(life_source),'executedCopy':str(life_copy.relative_to(out)),'executedCopySha256':digest(life_copy)}
save()
for name,command in commands:
 row={'name':name,'command':command,'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log':name+'.log'};record['steps'].append(row);save();print('Starting '+name,flush=True)
 with (out/row['log']).open('x') as f:result=subprocess.run(command,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
 row.update(returncode=result.returncode,logSha256=digest(out/row['log']),completedAt=datetime.datetime.now(datetime.timezone.utc).isoformat());save();print(name+' exit '+str(result.returncode),flush=True)
 if name=='supplemental' and result.returncode==0:
  generated=life_copy.with_name('managed_grants_lifecycle_installed.json')
  if not generated.is_file():
   row['passed']=False;row['missingGeneratedReceipt']=True;save();sys.exit(2)
  record['lifecycleProducer'].update(generatedReceipt=str(generated.relative_to(out)),generatedReceiptSha256=digest(generated))
  save()
 if result.returncode:record['inputsUnchanged']=basis()==record['inputBasis'];save();sys.exit(result.returncode)
record['inputsUnchanged']=basis()==record['inputBasis'];record['wheelUnchanged']=digest(a.wheel)==record['wheelSha256'];
def payload(directory):return {str(p.relative_to(directory)):digest(p) for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
record['installedPayloadUnchanged']=payload(root/'packages/python/src/truss')==payload(Path(truss.__file__).resolve().parent)
record['identityUnchanged']=(subprocess.check_output(['git','-C',str(owner),'rev-parse','HEAD'],text=True).strip()==owner_revision
 and not subprocess.check_output(['git','-C',str(owner),'status','--porcelain','--','src','package.json','bun.lock'],text=True)
 and digest(owner/'package.json')==record['identity']['independentOracle']['packageJsonSha256']
 and digest(owner/'bun.lock')==record['identity']['independentOracle']['lockSha256']
 and subprocess.check_output([bun,'--version'],text=True).strip()==record['identity']['compiler']['version']
 and digest(bun_path)==record['identity']['compiler']['sha256']
 and subprocess.check_output([str(supplemental_bun),'--version'],text=True).strip()==record['identity']['lifecycleCompiler']['version']
 and digest(supplemental_bun)==record['identity']['lifecycleCompiler']['sha256']==record['identity']['compiler']['sha256']
 and importlib.metadata.version(RUNTIME_DISTRIBUTION)==RUNTIME_VERSION==record['identity']['runtime']['version']
 and importlib.metadata.version('weft-sql')==record['identity']['weft']['version']
 and digest(Path(pgserver.__file__).resolve())==record['identity']['nativeWorker']['moduleSha256']
 and digest(Path(weft.__file__).resolve())==record['identity']['weft']['packageModuleSha256']
 and digest(weft_native_path)==record['identity']['weft']['nativeModuleSha256']
 and current_query_consumer().get('weftModuleSha256')==record['identity']['weft']['nativeModuleSha256']
 and subprocess.check_output([str(postgres),'--version'],text=True).strip()==native_version
 and digest(postgres)==record['identity']['nativeWorker']['postgresSha256'])
record['identityUnchanged']=record['identityUnchanged'] and importlib.metadata.version('truss-toolkit')==record['identity']['wheelVersion']
record['passed']=record['inputsUnchanged'] and record['wheelUnchanged'] and record['installedPayloadUnchanged'] and record['identityUnchanged'] and 'generatedReceiptSha256' in record['lifecycleProducer'];record['completedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(json.dumps({'passed':record['passed'],'receipt':str(receipt)}),flush=True);sys.exit(0 if record['passed'] else 2)
