"""Original exact owner-mode gates; no fixture, network, Docker or native setup."""
from pathlib import Path
import ast,json,types,hashlib
root=Path('/private/tmp/helper-acl-review-20261013');service=Path('/private/tmp/truss-security-main-integration/scripts/security_channel_composition_service.py');compose=Path('/private/tmp/truss-security-linux-composition/compose.py');st=ast.parse(service.read_text());ct=ast.parse(compose.read_text());rows=[]
class Entered(Exception):pass
calls=[]
def factory(*args):calls.append(True);raise Entered()
fn=next(n for n in st.body if isinstance(n,ast.FunctionDef) and n.name=='serve');env={'native':types.SimpleNamespace(AuthenticatedCatalogChannelTests=factory)};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(service),'exec'),env)
for field in ('refuse_event_triggers','refuse_helper_public_grant'):
 for value in (None,0,1,[],(),object(),'','False'):
  calls.clear()
  try:env['serve'](**{field:value})
  except ValueError as e:assert str(e)=='Exact owner fixture mode required'
  else:raise AssertionError(field)
  assert not calls;rows.append({'control':field+':nonbool:'+str(len(rows)),'passed':True})
for a,b in [(False,False),(True,False),(False,True),(True,True)]:
 calls.clear()
 try:env['serve'](refuse_event_triggers=a,refuse_helper_public_grant=b)
 except Entered:assert not(a and b)
 except ValueError:assert a and b and not calls
 else:raise AssertionError((a,b))
 rows.append({'control':'boolean_pair:'+str((a,b)),'passed':True})
event='--refuse-event-triggers';grant='--refuse-helper-public-grant'
for args,ok in [([],True),([event],True),([grant],True),(['bad'],False),([event,event],False),([grant,grant],False),([event,grant],False),([grant,event],False),([grant+'=true'],False)]:
 for name,body in [('service_cli',[st.body[-1]]),('orchestrator_cli',ct.body[1:3])]:
  invoked=[];e={'__name__':'__main__','sys':types.SimpleNamespace(argv=['script']+args),'serve':lambda **kw:invoked.append(kw)}
  try:exec(compile(ast.Module(body=body,type_ignores=[]),name,'exec'),e)
  except ValueError:assert not ok and not invoked
  else:
   assert ok
   if name=='service_cli':assert invoked==[{'refuse_event_triggers':args==[event],'refuse_helper_public_grant':args==[grant]}]
   else:assert e['refuse'] is bool(args)
  rows.append({'control':name+':'+repr(args),'passed':True})
r={'scope':'Original service function admission and unchanged original CLI AST blocks; no native operation or external peer independently run','passed':len(rows),'controls':rows,'sourcePins':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [service,compose]}};(root/'owner-mode-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':len(rows),'sourcePins':r['sourcePins']}))
