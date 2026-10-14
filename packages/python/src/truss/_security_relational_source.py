"""Separate relational0.2 source correspondence; no native codec/admission token."""
from ._security_guarded_source import _capture_source_comparison


def capture_relational_source_comparison(original_request,original_output):
 fields={'version','securityReady','sourceRequestSha256','sourceContextJson','sourceContextSha256','queryContextSha256','executionSql','checks','operandReads','operandDemands','parameters','resultContract','resultContractJson','resultContractSha256','nativeAdmission','nativeCodecAdmission','nativePopulationAndSelection','releaseProtection'}
 return _capture_source_comparison(original_request,original_output,fields,'weft.truss.security.relational-candidate/0.2-candidate',('nativeAdmission','nativeCodecAdmission','nativePopulationAndSelection','releaseProtection'))
