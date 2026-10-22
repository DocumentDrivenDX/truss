from pathlib import Path
import json,hashlib,subprocess,os,sys,time,datetime,re
root=Path('/Users/erik/Projects/truss');dest=root/'docs/helix/04-build/evidence/hohfeld-followup-20261021/hf02-hf03-source-v2';dest.mkdir(parents=True,exist_ok=True)
modules=['test_person_invocation_native.PersonInvocationNativeTests','test_group_request_recovery_native.GroupRequestRecoveryNativeTests','test_group_create_native.PublicCreateGroupTests.test_asymmetric_relationship_minimum_is_checked_on_the_right_endpoint','test_edge_mutations_native.EdgeMutationTests','test_required_ddd_evolution_native.RequiredDDDEvolutionTests','test_catalog_compatible_acceptance_native.CompatibleCatalogTests','test_hohfeld_disputes_native.HohfeldDisputesNativeTests.test_capture_import_minimum_and_group_finalization','test_hohfeld_disputes_native.HohfeldDisputesNativeTests.test_capture_import_maximum']
# Keep only actual selected methods; no filtered discovery/skips qualify a gate.
last=root/'packages/python/tests/test_hohfeld_disputes_native.py'
text=last.read_text();methods=re.findall(r'def (test_\w+)\(',text);print('Multiplicity probes:',[m for m in methods if 'maximum' in m or 'minimum' in m],flush=True)
modules[-1]='test_hohfeld_disputes_native.HohfeldDisputesNativeTests.'+next(m for m in methods if 'maximum' in m)
command=[sys.executable,'-m','unittest',*modules,'-v'];env=dict(os.environ,PYTHONPATH='packages/python/src:packages/python/tests')
paths=sorted((root/'packages/python/src/truss').rglob('*.py'))+sorted((root/'packages/python/src/truss/_catalog_runtime').glob('*'))
paths += [root/'packages/python/tests'/((m.split('.')[0])+'.py') for m in modules]
paths += [root/'scripts/check-module-boundaries.py']
sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
start=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (dest/'native.log').open('w') as log:r=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
elapsed=time.monotonic()-start;log=(dest/'native.log').read_text();count=re.search(r'Ran (\d+) tests? in ([\d.]+)s',log)
receipt={'scope':'Unreleased HF-02/03 source component qualification on development macOS ARM64 PostgreSQL18.6; not installed-package or release qualification','observedAt':stamp,'command':command,'environment':{'PYTHONPATH':env['PYTHONPATH']},'python':sys.version,'sourceSha256':sources,'exitCode':r.returncode,'passed':r.returncode==0 and log.rstrip().endswith('OK'),'tests':int(count.group(1)) if count else None,'testSeconds':float(count.group(2)) if count else None,'wallSeconds':elapsed,'unqualified':['expiry writer/protection lifecycle','lost commit acknowledgement recovery','Weft query changes','performance targets','completion and audit extensions','next native migration edge','clean installed packages','hosted Linux and public release']}
(dest/'qualification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='sourceSha256'}),flush=True)
raise SystemExit(r.returncode)
