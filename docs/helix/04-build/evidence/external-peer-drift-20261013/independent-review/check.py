"""Bounded original-source mode admission controls; no service/native/Docker setup."""
from pathlib import Path
import ast,json,types,hashlib
base=Path('/private/tmp/channel-composition-review-20261013');service=Path('/private/tmp/truss-security-main-integration/scripts/security_channel_composition_service.py');compose=Path('/private/tmp/truss-security-linux-composition/compose.py');st=ast.parse(service.read_text());ct=ast.parse(compose.read_text());rows=[]
serve=next(n for n in st.body if isinstance(n,ast.FunctionDef) and n.name=='serve')
class EnteredFixture(Exception):pass
entered=[]
def factory(*args):entered.append(True);raise EnteredFixture()
env={'native':types.SimpleNamespace(AuthenticatedCatalogChannelTests=factory)};exec(compile(ast.Module(body=[serve],type_ignores=[]),str(service),'exec'),env)
for value in (None,0,1,[],(),object(),'','False'):
 entered.clear()
 try:env['serve'](refuse_event_triggers=value)
 except ValueError as e:assert str(e)=='Exact owner fixture mode required'
 else:raise AssertionError('non-bool accepted')
 assert not entered;rows.append({'control':'service_reject_'+type(value).__name__+'_'+str(len(rows)),'passed':True})
for value in (False,True):
 try:env['serve'](refuse_event_triggers=value)
 except EnteredFixture:pass
 else:raise AssertionError('valid exact bool did not enter fixture')
 rows.append({'control':'service_accept_'+str(value),'passed':True})
main=st.body[-1]
choices=[([],False),(['--refuse-event-triggers'],True),(['other'],None),(['--refuse-event-triggers','--refuse-event-triggers'],None),(['--refuse-event-triggers','other'],None),(['--refuse-event-triggers=true'],None)]
for args,expected in choices:
 for which in ('service_cli','orchestrator_cli'):
  calls=[];e={'__name__':'__main__','sys':types.SimpleNamespace(argv=['script']+args),'serve':lambda **kw:calls.append(kw)}
  # Orchestrator's exact unchanged owner-flag expression and guard, before root/I/O.
  body=[main] if which=='service_cli' else ct.body[1:3]
  try:exec(compile(ast.Module(body=body,type_ignores=[]),which,'exec'),e)
  except ValueError:assert expected is None
  else:
   assert expected is not None
   if which=='service_cli':assert calls==[{'refuse_event_triggers':expected}]
   else:assert e['refuse'] is expected
  if expected is None:assert not calls
  rows.append({'control':which+'_'+repr(args),'passed':True})
r={'scope':'Original service function preflight and exact service/orchestration owner CLI AST controls; fixture factory is a sentinel, no Docker, sockets, native SQL or encoder invoked','passed':len(rows),'controls':rows,'sourcePins':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [service,compose]}};(base/'drift-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':len(rows),'sourcePins':r['sourcePins']}))
