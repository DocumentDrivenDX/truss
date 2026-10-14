from pathlib import Path
from dataclasses import replace
from hashlib import sha256
from contextlib import nullcontext
from unittest.mock import patch
import importlib.util,json,sys
from truss._security_graph_source import PreparedGraphSecuritySource
from truss._security_graph_epoch_read import GraphEpochReadContext,PendingGraphEpochReadCut,_DIGEST
from truss._psycopg_epoch_cut import _EpochComparison
from truss.psycopg_host import PsycopgHost
from truss._security_graph_subject_installation import PendingGraphSubjects
base=Path(__file__).resolve().parent;root=Path('/private/tmp/truss-security-main-integration');e=root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
oldm=load('truss.review_pre_registration',base/'registration-before.py');oldapi=load('review_pre_composition',base/'composition-before.py')
subjects0=oldm.PendingGraphSubjects('installation',100,b'profile',((123,'Alice'),))
try:oldm.verify_registered_graph_subjects_with_cursor(None,subjects0,caller_pid='42')
except ValueError as ex:assert str(ex)=='Original graph Subject caller backend required';pid_error=str(ex)
else:raise AssertionError('Expected native text PID refusal')
native=json.loads((e/'native-source-epoch.json').read_bytes());source=PreparedGraphSecuritySource(*((e/f).read_bytes() for f in ('physical-request.json','compiler-output.json','accepted-catalog.json','compiler-request.json')),native_guard=(native['installation'].encode(),b'original authored profile',1))
profile=json.loads((e/'issued-profile.json').read_bytes());profile['subjectHelperSha256']=sha256((base/'composition-before.py').read_bytes()).hexdigest()
ctx=GraphEpochReadContext(source,_EpochComparison(native['installation'],native['epoch'],native['incarnation'],json.dumps(profile).encode(),source.accepted_catalog_assessment),PendingGraphEpochReadCut(native['installation'],10,12345,_DIGEST),(base/'composition-before.py').read_bytes())
reg=json.loads((e/'subject-profile.json').read_bytes());reg['policySha256']='0'*64
subjects=PendingGraphSubjects(native['installation'],100,json.dumps(reg).encode(),((123,'Alice'),))
class EnteredHost(Exception):pass
with patch.object(oldapi,'_HostPairReservation',return_value=nullcontext()),patch.object(PsycopgHost,'_run_published_operation',side_effect=EnteredHost):
 try:oldapi.publish_native_ontology_resource_read(object.__new__(PsycopgHost),None,object.__new__(PsycopgHost),None,source.original_request,subjects.bindings,lambda b:None,compiler=lambda *a:{},cut_issuer=(10,12345),source_epoch=ctx,subject_registration=subjects)
 except EnteredHost:pass
 else:raise AssertionError('Expected missing registration/source gate witness')
result={'scope':'Offline actual pre-fix function controls with synthetic host-entry sentinel and selected comparison context; not native authority or successful disclosure','nativeTextPidRefuses':pid_error,'differentRegistrationPolicyHashReachesHost':True,'sourceSha256':{n:sha256((base/n).read_bytes()).hexdigest() for n in ('registration-before.py','composition-before.py')}}
(base/'before.json').write_text(json.dumps(result,indent=2)+'\n');print('Two original-source countercontrols reproduced')
