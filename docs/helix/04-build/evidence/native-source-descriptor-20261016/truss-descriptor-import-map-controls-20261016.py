from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess
root=Path('/private/tmp/truss-disclosure-main-integration-20261016');path=root/'scripts/check-module-boundaries.py';before=subprocess.check_output(['git','show','HEAD:scripts/check-module-boundaries.py'],cwd=root).decode();after=path.read_text()
def mapping(s):return ast.literal_eval(next(n.value for n in ast.parse(s).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALLOWED' for t in n.targets)))
old,new=mapping(before),mapping(after);assert new.pop('_native_source_descriptor')=={'dataclasses','hashlib','json','re','truss._owner_evidence_json'};assert old==new
bt,at=ast.parse(before),ast.parse(after)
for t in [bt,at]:t.body=[n for n in t.body if not (isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='ALLOWED' for x in n.targets))]
assert ast.dump(bt)==ast.dump(at)
spec=importlib.util.spec_from_file_location('checked_boundaries',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=root/'packages/python/src/truss';errors,edges=m.inspect_sources(source);assert not errors,errors;controls=[]
for permission in sorted(m.ALLOWED['_native_source_descriptor']):
 m.ALLOWED['_native_source_descriptor'].remove(permission);errors,_=m.inspect_sources(source);assert any(e.startswith('_native_source_descriptor.py:') and 'forbidden import '+permission in e for e in errors),(permission,errors);m.ALLOWED['_native_source_descriptor'].add(permission);controls.append(permission)
Path('/private/tmp/truss-descriptor-import-map-controls-20261016.json').write_text(json.dumps({'status':'passed','imports':len(edges),'onlyNewEntry':True,'checkerAlgorithmUnchanged':True,'permissionRemovalControls':controls,'checkerSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'Root explicit import-map checks, not native/runtime qualification.'},indent=2)+'\n')
print('passed five exact permission-removal controls')
