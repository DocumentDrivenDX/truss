from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
import hashlib,importlib.util,json,sys
from truss._security_mapping import PreparedSecurityMapping
from truss._psycopg_fact_cut import _FactRelationComparison
from truss._psycopg_epoch_cut import _DDLBarrierComparison
ROOT=Path('/private/tmp/truss-security-main-integration')
spec=importlib.util.spec_from_file_location('review_wrapper',sys.argv[1]);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);m.ROOT=ROOT
original=PreparedSecurityMapping(b'original-request',b'{}',accepted_catalog_assessment=b'original-assessment')
relation=_FactRelationComparison('truss','object',10,12,'body');barrier=_DDLBarrierComparison(12,13,'DDL')
path=ROOT/'scripts/security-catalog-subject.sql';read=Path.read_bytes
before=m.derive_catalog_source_epoch_profile(original,(relation,),barrier,subject_source=read(path))
def substitute(p):
 if p==path:
  object.__setattr__(original,'original_request',b'replaced-request')
  object.__setattr__(relation,'oid',11)
  object.__setattr__(barrier,'function_oid',14)
 return read(p)
with patch.object(Path,'read_bytes',substitute):after=m.derive_catalog_source_epoch_profile(original,(relation,),barrier)
p=json.loads(after)
r={'scope':'Deterministic replacement during helper file I/O; reconstructed observed pre-fix wrapper body when filename says reconstructed, otherwise actual fixed wrapper. No native process','sourceSha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),'sameAsPreIOPacket':before==after,'usedReplacementRequest':p['requestSha256']==hashlib.sha256(b'replaced-request').hexdigest(),'factOid':p['factCuts'][0]['oid'],'functionOid':p['ddlBarrier']['functionOid']}
Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
