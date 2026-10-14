"""Original guarded source bytes, separate from query and native authority.

Trusted original compiler custody is a premise. These snapshots are comparisons,
not SQL admission, native source authentication or publication credentials.
"""
from dataclasses import dataclass,replace
from hashlib import sha256
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence

@dataclass(frozen=True,slots=True)
class GuardedSourceComparison:
 source_bytes:bytes
 source_sha256:str


def capture_guarded_source_comparison(original_request,original_output):
 for raw,limit in ((original_request,4000000),(original_output,16000000)):
  if type(raw) is not bytes or not 1<=len(raw)<=limit:
   raise ValueError('Bounded original guarded compiler bytes required')
 request=decode_owner_evidence_json(original_request)
 output=decode_owner_evidence_json(original_output)
 fields={'version','securityReady','sourceRequestSha256','sourceContextJson','sourceContextSha256','queryContextSha256','query','policyParameterBindings','subjectParameterBinding','nativeAdmission'}
 if (type(output) is not dict or set(output)!=fields
     or output['version']!='weft.truss.security.guarded-candidate/0.1-candidate'
     or output['securityReady'] is not False or output['nativeAdmission']!='required'
     or output['sourceRequestSha256']!=sha256(original_request).hexdigest()
     or type(output['sourceContextJson']) is not str):
  raise ValueError('Original guarded source correspondence required')
 raw=output['sourceContextJson'].encode()
 if not 1<=len(raw)<=16000000 or output['sourceContextSha256']!=sha256(raw).hexdigest():
  raise ValueError('Exact original guarded source bytes required')
 capsule=decode_owner_evidence_json(raw)
 source_fields={'version','securityReady','modules','policyJson','ontologyJson','queryProfileJson','bindingJson','backendId','backendVersion','targetProfile'}
 if (type(capsule) is not dict or set(capsule)!=source_fields
     or capsule['version']!='weft.security.source-context/0.1-candidate'
     or capsule['securityReady'] is not False
     or any(not same_owner_evidence(capsule[k],request[k]) for k in source_fields-{'version','securityReady'})):
  raise ValueError('Exact original guarded source request required')
 return GuardedSourceComparison(raw,sha256(raw).hexdigest())


def require_same_guarded_source(comparison,original_request,original_output):
 if (type(comparison) is not GuardedSourceComparison or type(comparison.source_bytes) is not bytes
     or not 1<=len(comparison.source_bytes)<=16000000
     or type(comparison.source_sha256) is not str
     or sha256(comparison.source_bytes).hexdigest()!=comparison.source_sha256):
  raise ValueError('Original bounded guarded source comparison required')
 captured=capture_guarded_source_comparison(original_request,original_output)
 if captured!=replace(comparison):raise ValueError('Original selected guarded source changed')
 return captured
