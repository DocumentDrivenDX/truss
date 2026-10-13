from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import json,hashlib,importlib.util,sys,inspect
import truss._psycopg_epoch_cut as epoch
from truss._psycopg_fact_cut import _FactRelationComparison
from truss._security_mapping import PreparedSecurityMapping
from truss._psycopg_subject_observation import _SubjectSelection
from truss.psycopg_host import PsycopgHost
from truss.execution import Ok
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('review_subject',sys.argv[1]);read=importlib.util.module_from_spec(spec);sys.modules[spec.name]=read;spec.loader.exec_module(read);read.ROOT=ROOT
helper=ROOT/'scripts/security-catalog-subject.sql';original=helper.read_bytes();replacement=original.replace(b'AS $$',b'AS $$\n-- independent byte-custody countercontrol\n',1);assert original!=replacement
mapping=PreparedSecurityMapping(b'original-request',b'original-response',accepted_catalog_assessment=b'original-assessment')
selection=_SubjectSelection(mapping.original_request,(read.BASE/'document.json').read_bytes(),'m','Staff','pk','consumer','truss','catalog_subject_current',('staff_id',))
rels=(_FactRelationComparison('truss','object',10,12,'body'),_FactRelationComparison('truss','catalog_subject_map',11,12,'body'))
barrier=epoch._DDLBarrierComparison(12,13,'source')
profile=read.derive_catalog_source_epoch_profile(mapping,rels,barrier) if 'barrier' in inspect.signature(read.derive_catalog_source_epoch_profile).parameters else read.derive_catalog_source_epoch_profile(mapping,rels)
cut=(epoch._EpochComparison('installation','epoch','incarnation',profile,mapping.accepted_catalog_assessment),barrier)
caller=object.__new__(PsycopgHost);executor=object.__new__(PsycopgHost);reads=[];captured=[];actual=Path.read_bytes

def controlled(path):
 if path==helper:
  value=original if not reads else replacement;reads.append(hashlib.sha256(value).hexdigest());return value
 return actual(path)
def host_boundary(self,tx,callback,publisher):
 closure=dict(zip(callback.__code__.co_freevars,(v.cell_contents for v in callback.__closure__)))
 captured.append({'sourceSha256':hashlib.sha256(closure['source'].encode()).hexdigest(),'finalSourcePin':closure['source_pin'].hex(),'declaredHelperSha256':json.loads(profile)['subjectHelperSha256']})
 return Ok(b'synthetic host accepted preflight')
with patch.object(Path,'read_bytes',controlled),patch.object(read,'_prepare_subject_operation',lambda *a:lambda *a:None),patch.object(PsycopgHost,'_run_published_operation',host_boundary):
 try:r=read.publish_ddl_epoch_guarded_native_catalog_resource_read(caller,None,executor,None,mapping,selection,lambda *a:None,rels,cut,lambda p:None);outcome=r.status
 except Exception as e:outcome=type(e).__name__+': '+str(e)
record={'scope':'Actual source-binding preflight and captured callback closure; synthetic original inspector and host boundary, no native mutation/execution','sourceSha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),'helperReadDigests':reads,'outcome':outcome,'hostEntries':captured}
Path(sys.argv[2]).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
