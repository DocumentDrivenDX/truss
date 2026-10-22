import argparse,datetime,hashlib,json,os,subprocess,sys
import pgserver
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--wheel',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
root=Path('/Users/erik/Projects/truss');dest=a.output.resolve();dest.mkdir(parents=True,exist_ok=False)
py=sys.executable;helper=Path('/private/tmp/truss-managed-grants-qualification/check-selected-components.py')
def source_basis():
 paths=[q for q in (root/'packages/python/src/truss').rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.suffix!='.pyc']
 paths+=list((root/'packages/python/tests').glob('*.py'))
 paths+=list((root/'scripts').glob('*.py'))
 paths+=[root/'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json',helper,Path(__file__)]
 return {str(q.relative_to(root)) if q.is_relative_to(root) else str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted(paths)}
before=source_basis();record={'scope':'Local macOS ARM64 explicit selected regression modules, HF corpus, protected regression, all admitted migrations and public workload. Unchanged legacy fullsuite rejected diagnostic attempt1; obsolete or opt-in campaigns are not qualified. This bounded receipt is not complete all-component or release acceptance.','startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'wheel':str(a.wheel.resolve()),'wheelSha256':hashlib.sha256(a.wheel.read_bytes()).hexdigest(),'inputBasis':before,'steps':[],'legacyFullSuite':'unresolved; failed diagnostic attempt-1 retained separately','lakebaseAcceptance':'not_run','hostedLinux':'not_run','publication':'not_run'}
receipt=dest/'qualification.json'
def save():receipt.write_text(json.dumps(record,indent=2)+'\n')
native=dest/'native';native.mkdir()
env={**os.environ,'PYTHONPATH':str(root/'scripts'),'TRUSS_INSTALLED_SUITE_WORKERS':'2','TRUSS_INSTALLED_SUITE_TIMEOUT':'1800','TRUSS_NATIVE_EVIDENCE_DIR':str(native),'UMF_OWNER_ROOT':'/Users/erik/Projects/umf','TRUSS_UMF_SOURCE_ROOT':'/Users/erik/Projects/umf','TRUSS_UMF_DOMAIN_PACK_ROOT':'/Users/erik/Projects/umf','TRUSS_BUN_EXECUTABLE':'/opt/homebrew/bin/bun','TRUSS_CENSUS_POSTGRES_BIN':str(Path(pgserver.__file__).resolve().parent/'pginstall/bin')}
record['selectedOwnerEnvironment']={k:env[k] for k in ('UMF_OWNER_ROOT','TRUSS_UMF_SOURCE_ROOT','TRUSS_UMF_DOMAIN_PACK_ROOT','TRUSS_BUN_EXECUTABLE','TRUSS_CENSUS_POSTGRES_BIN')}
commands=[
 ('boundaries',[py,str(root/'scripts/check-module-boundaries.py')]),
 ('boundary-controls',[py,str(root/'scripts/check-module-boundaries-controls.py')]),
 ('selected-components',[py,str(helper),'--wheel',str(a.wheel.resolve()),'--output',str(dest/'selected-components')]),
 ('hf-corpus',[py,str(root/'scripts/run-hf-conformance.py'),'--installed-package','--output',str(dest/'hf-corpus/qualification.json')]),
 ('protected-regression',[py,str(root/'scripts/run-python-test-module.py'),'discover','-s',str(root/'packages/python/tests'),'-p','test_current_disclosure_runtime_native.py','-v']),
 ('migrations',[py,str(root/'scripts/qualify-runtime-migrations.py'),'--installed-package','--wheelhouse','/private/tmp/truss-runtime-migration-wheelhouse','--output',str(dest/'migrations/qualification.json')]),
 ('public-workload',[py,str(root/'scripts/benchmark-public-workflows.py'),'--truss-root',str(root),'--installed-package','--count-sql-submissions','--matrix-case','small','--bulk-size','1000','--read-samples','1000','--write-samples','200','--output',str(dest/'public-workload/report.json')])]
save()
for label,command in commands:
 row={'name':label,'command':command,'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log':str(dest/(label+'.log'))};record['steps'].append(row);save();print('Starting '+label,flush=True)
 selected_env=dict(env)
 if label=='protected-regression':selected_env['TRUSS_DISCLOSURE_NATIVE_QUALIFICATION']='1';row['additionalEnvironment']={'TRUSS_DISCLOSURE_NATIVE_QUALIFICATION':'1'}
 with (dest/(label+'.log')).open('x') as output:result=subprocess.run(command,cwd=root,env=selected_env,stdout=output,stderr=subprocess.STDOUT)
 row['returncode']=result.returncode;row['completedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(label+' exit '+str(result.returncode),flush=True)
 if result.returncode:record['passed']=False;record['inputBasisUnchanged']=source_basis()==before;save();sys.exit(result.returncode)
record['inputBasisUnchanged']=source_basis()==before;record['passed']=record['inputBasisUnchanged'];record['completedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(json.dumps({'passed':record['passed'],'inputBasisUnchanged':record['inputBasisUnchanged'],'receipt':str(receipt)}),flush=True);sys.exit(0 if record['passed'] else 2)
