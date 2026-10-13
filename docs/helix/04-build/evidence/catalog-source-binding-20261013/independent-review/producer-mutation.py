from pathlib import Path
from unittest.mock import patch
import json,hashlib,importlib.util,sys
from truss._security_mapping import PreparedSecurityMapping
from truss._psycopg_fact_cut import _FactRelationComparison
from truss._psycopg_epoch_cut import _DDLBarrierComparison
ROOT=Path('/private/tmp/truss-security-main-integration')
spec=importlib.util.spec_from_file_location('review_producer',sys.argv[1]);r=importlib.util.module_from_spec(spec);sys.modules[spec.name]=r;spec.loader.exec_module(r);r.ROOT=ROOT
m=PreparedSecurityMapping(b'original',b'{}',accepted_catalog_assessment=b'assessment');relation=_FactRelationComparison('truss','object',10,12,'body');barrier=_DDLBarrierComparison(12,13,'DDL')
real=Path.read_bytes;helper=ROOT/'scripts/security-catalog-subject.sql';expected=r.derive_catalog_source_epoch_profile(m,(relation,),barrier,subject_source=real(helper))
def read(p):
 if p==helper:
  object.__setattr__(m,'original_request',bytearray(b'replaced mutable source'))
  object.__setattr__(relation,'oid',True)
  object.__setattr__(barrier,'function_oid',False)
 return real(p)
with patch.object(Path,'read_bytes',read): raw=r.derive_catalog_source_epoch_profile(m,(relation,),barrier)
packet=json.loads(raw)
result={'scope':'Actual standalone producer; deterministic input replacement during helper file read; no native execution','equalOriginalPacket':raw==expected,'acceptedRequestHash':packet['requestSha256'],'matchesInvalidMutableReplacement':packet['requestSha256']==hashlib.sha256(m.original_request).hexdigest(),'factOid':packet['factCuts'][0]['oid'],'barrierFunctionOid':packet['ddlBarrier']['functionOid'],'sourceSha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()}
Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
