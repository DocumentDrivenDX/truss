import importlib.util,json
from pathlib import Path
import z3
base=Path(__file__).resolve().parent
p=base/'retained-root/tools/security/prove-principal-acquisition-order.py'
spec=importlib.util.spec_from_file_location('reviewed',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
controls=[]
def check(name,guard=True,atomic=True,extras=lambda v,l,q:[]):
 constraints,l,q,v=m.scenario(guard,atomic);s=z3.Solver();s.add(*constraints,*extras(v,l,q));status=str(s.check());assert status=='sat',(name,status)
 controls.append({'name':name,'expected':'sat','observed':status,'witness':{str(x):str(s.model().eval(x,model_completion=True)) for x in v},'lease':str(s.model().eval(l,model_completion=True)),'quarantine':str(s.model().eval(q,model_completion=True))})
check('during-reset refusal premises are satisfiable',extras=lambda v,l,q:[v[5],v[0]<v[4],v[4]<v[1],q,z3.Not(l)])
check('closure after reset but before gate also quarantines',extras=lambda v,l,q:[v[5],v[1]<v[4],v[4]<v[2],q,z3.Not(l)])
check('failed-reset premise is satisfiable',extras=lambda v,l,q:[z3.Not(v[5]),v[3]<v[4],z3.Not(l)])
check('future-closed-acquisition premise is satisfiable',extras=lambda v,l,q:[v[4]<v[0],v[5],z3.Not(l)])
check('old escape survives strictly separated closure/reset/gate',guard=False,extras=lambda v,l,q:[v[0]<v[4],v[4]<v[1],v[1]<v[2],l])
check('inserted-yield escape has closure strictly inside gap',atomic=False,extras=lambda v,l,q:[l,v[2]<v[4],v[4]<v[3]])
(base/'premise-controls.json').write_text(json.dumps({'solver':z3.get_version_string(),'count':len(controls),'scope':'Independent satisfiability checks for nonvacuity and event-equality independence in the retained abstract model; no runtime refinement.', 'controls':controls},indent=2)+'\n')
print(json.dumps({'premiseControls':len(controls),'all':'sat'}))
