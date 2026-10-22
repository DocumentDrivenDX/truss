import argparse,datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--wheel',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
root=Path('/Users/erik/Projects/truss');dest=a.output.resolve();dest.mkdir(parents=True,exist_ok=False)
py=sys.executable
def source_basis():
 paths=[q for q in (root/'packages/python/src/truss').rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.suffix!='.pyc']
 paths+=list((root/'packages/python/tests').glob('*.py'))
 paths+=[root/'scripts'/n for n in ('native_fixture.py','run-python-installed-workers.py','run-python-test-module.py','check-python-installed-suite.py','qualify-runtime-migrations.py','benchmark-public-workflows.py','performance_workloads.py')]
 return {str(q.relative_to(root)):hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted(paths)}
before=source_basis();record={'scope':'Local macOS ARM64 qualification only; actual Lakebase and consumer adoption are separate gates','startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'wheel':str(a.wheel.resolve()),'wheelSha256':hashlib.sha256(a.wheel.read_bytes()).hexdigest(),'inputBasis':before,'steps':[],'lakebaseAcceptance':'not_run'}
receipt=dest/'qualification.json'
def save():receipt.write_text(json.dumps(record,indent=2)+'\n')
env={**os.environ,'PYTHONPATH':str(root/'scripts'),'TRUSS_INSTALLED_SUITE_WORKERS':'2','TRUSS_INSTALLED_SUITE_TIMEOUT':'1800'}
installed=dest/'installed-suite';installed.mkdir();env['TRUSS_NATIVE_EVIDENCE_DIR']=str(installed)
commands=[('boundaries',[py,str(root/'scripts/check-module-boundaries.py')]),('boundary-controls',[py,str(root/'scripts/check-module-boundaries-controls.py')]),('installed-suite',[py,str(root/'scripts/check-python-installed-suite.py'),str(a.wheel.resolve()),'--corrected-pgserver','installed-suite.json']),('migrations',[py,str(root/'scripts/qualify-runtime-migrations.py'),'--installed-package','--wheelhouse','/private/tmp/truss-runtime-migration-wheelhouse','--output',str(dest/'migrations/qualification.json')]),('public-workload',[py,str(root/'scripts/benchmark-public-workflows.py'),'--truss-root',str(root),'--installed-package','--count-sql-submissions','--matrix-case','small','--bulk-size','1000','--read-samples','1000','--write-samples','200','--output',str(dest/'public-workload/report.json')])]
save()
for label,command in commands:
 row={'name':label,'command':command,'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log':str(dest/(label+'.log'))};record['steps'].append(row);save();print('Starting '+label,flush=True)
 with (dest/(label+'.log')).open('x') as output: result=subprocess.run(command,cwd=root,env=env,stdout=output,stderr=subprocess.STDOUT)
 row['returncode']=result.returncode;row['completedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(label+' exit '+str(result.returncode),flush=True)
 if result.returncode:record['passed']=False;record['inputBasisUnchanged']=source_basis()==before;save();sys.exit(result.returncode)
record['inputBasisUnchanged']=source_basis()==before;record['passed']=record['inputBasisUnchanged'];record['completedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
print(json.dumps({'passed':record['passed'],'inputBasisUnchanged':record['inputBasisUnchanged'],'receipt':str(receipt)}),flush=True)
sys.exit(0 if record['passed'] else 2)
