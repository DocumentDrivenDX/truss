"""Separate relational0.2 source correspondence; no native codec/admission token."""
from ._security_guarded_source import _capture_source_comparison
from ._owner_evidence_json import decode_owner_evidence_json


def capture_relational_source_comparison(original_request,original_output):
 if type(original_request) is not bytes or not 1<=len(original_request)<=4000000:raise ValueError('Bounded original relational source request required')
 request=decode_owner_evidence_json(original_request)
 profile=decode_owner_evidence_json(request['queryProfileJson'].encode())
 if profile.get('version')!='weft.security.query-profile/0.1.0':raise ValueError('Distinct original relational source profile required')
 fields={'version','securityReady','sourceRequestSha256','sourceContextJson','sourceContextSha256','queryContextSha256','executionSql','checks','operandReads','operandDemands','parameters','resultContract','resultContractJson','resultContractSha256','nativeAdmission','nativeCodecAdmission','nativePopulationAndSelection','releaseProtection'}
 return _capture_source_comparison(original_request,original_output,fields,'weft.truss.security.relational-candidate/0.2-candidate',('nativeAdmission','nativeCodecAdmission','nativePopulationAndSelection','releaseProtection'))
