"""Distinct relationship source byte archive; not native/SQL authority.

Trusted original relationship producer custody remains a host premise. Native
installer/epoch/fact/release composition is separate and currently unavailable.
"""
from dataclasses import dataclass,field,replace
from hashlib import sha256
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence
from ._security_guarded_source import _capture_source_comparison

FIELDS={'version','securityReady','sourceRequestSha256','sourceContextJson','sourceContextSha256','queryContextSha256','executionSql','checks','operandReads','operandDemands','parameters','resultContract','resultContractJson','resultContractSha256','nativeAdmission','nativeCodecAdmission','nativePopulationAndSelection','releaseProtection'}

def capture_relationship_source_comparison(request,output):
 if type(request) is not bytes or not 1<=len(request)<=4000000:raise ValueError('Bounded original relationship source request required')
 original=decode_owner_evidence_json(request)
 profile=decode_owner_evidence_json(original['queryProfileJson'].encode())
 binding=decode_owner_evidence_json(original['bindingJson'].encode())
 if profile.get('version')!='weft.security.query-profile/0.2-candidate' or binding.get('version')!='weft.truss.security.graph-source/0.2-candidate':raise ValueError('Distinct original relationship source versions required')
 return _capture_source_comparison(request,output,FIELDS,'weft.truss.security.relational-candidate/0.2-candidate',('nativeAdmission','nativeCodecAdmission','nativePopulationAndSelection','releaseProtection'))

@dataclass(frozen=True,slots=True)
class PreparedRelationshipSecuritySource:
 original_request:bytes # physical original catalog request
 accepted_catalog_assessment:bytes
 native_dependencies:bytes # original authored relationship compiler request
 original_response:bytes # original separate relationship producer output
 security_ready:bool=field(default=False,init=False)


def snapshot_relationship_security_source(value):
 if type(value) is not PreparedRelationshipSecuritySource or value.security_ready is not False:raise ValueError('Distinct original relationship source archive required')
 value=replace(value)
 for raw,limit in ((value.original_request,4000000),(value.accepted_catalog_assessment,1048576),(value.native_dependencies,4000000),(value.original_response,8000000)):
  if type(raw) is not bytes or not 1<=len(raw)<=limit:raise ValueError('Bounded original relationship source archive required')
 physical=decode_owner_evidence_json(value.original_request)
 assessment=decode_owner_evidence_json(value.accepted_catalog_assessment)
 request=decode_owner_evidence_json(value.native_dependencies)
 binding=decode_owner_evidence_json(request['bindingJson'].encode())
 revision=assessment.get('revision')
 if (type(revision) is not str or not 1<=len(revision)<=19 or not revision.isascii() or not revision.isdigit() or revision[0]=='0' or int(revision)>9223372036854775807
     or binding.get('nativeSchemaRevision')!=revision
     or binding.get('inventoryJson','').encode()!=value.accepted_catalog_assessment
     or type(physical.get('modules')) is not list or len(physical['modules'])!=1
     or not same_owner_evidence(binding.get('physicalModule'),{**physical['modules'][0],'selectedModuleIds':['m']})):
  raise ValueError('Exact original relationship physical source correspondence required')
 module=binding['physicalModule'];pin=module.get('pin');document=module.get('documentJson')
 if (type(pin) is not dict or set(pin)!={'documentId','revision','umfVersion','sha256'} or any(type(v) is not str or not v for v in pin.values())
     or type(document) is not str or pin['sha256']!=sha256(document.encode()).hexdigest()
     or decode_owner_evidence_json(document.encode()).get('id')!=pin['documentId']):raise ValueError('Exact authored relationship physical pin required')
 capture_relationship_source_comparison(value.native_dependencies,value.original_response)
 return value


def relationship_source_archives(value,release):
 value=snapshot_relationship_security_source(value)
 if type(release) is not bytes or not 1<=len(release)<=1048576:raise ValueError('Bounded original release archive required')
 capsule=capture_relationship_source_comparison(value.native_dependencies,value.original_response)
 return [('bundle','relationship:original-release-manifest',release),
         ('expected_inventory','relationship:original-accepted-assessment',value.accepted_catalog_assessment),
         ('installed_inventory','relationship:recaptured-accepted-assessment',value.accepted_catalog_assessment),
         ('input','relationship:original-physical-request',value.original_request),
         ('input','relationship:original-compiler-request',value.native_dependencies),
         ('input','relationship:original-compiler-output',value.original_response),
         ('input','relationship:original-source-context',capsule.source_bytes)]
