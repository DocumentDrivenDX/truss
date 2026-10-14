"""Exact copied0.2 inspection correspondence; no native authority credential."""
import json
from hashlib import sha256
from truss._owner_evidence_json import decode_owner_evidence_json
from truss._security_relationship_source import capture_relationship_source_comparison


def inspected_relationship_publication(receipt):
 limits={'request':4000000,'output':16000000,'operandBatch':4000000,'batch':4000000,'resultCheck':65536}
 copied={k:receipt[k] for k in limits}
 if any(type(v) is not str or not 1<=len(v.encode())<=limits[k] for k,v in copied.items()):raise ValueError('Bounded original relational publication required')
 capture_relationship_source_comparison(copied['request'].encode(),copied['output'].encode())
 packet=decode_owner_evidence_json(copied['output'].encode());checked=decode_owner_evidence_json(copied['resultCheck'].encode());operands=decode_owner_evidence_json(copied['operandBatch'].encode());batch=decode_owner_evidence_json(copied['batch'].encode())
 expected={'version':'weft.truss.security.relational-result.inspected/0.2-candidate','securityReady':False,'inspected':True,'sourceRequestSha256':sha256(copied['request'].encode()).hexdigest(),'sourceOutputSha256':sha256(copied['output'].encode()).hexdigest(),'sourceContextSha256':packet['sourceContextSha256'],'queryContextSha256':packet['queryContextSha256'],'operandBatchSha256':sha256(copied['operandBatch'].encode()).hexdigest(),'batchSha256':sha256(copied['batch'].encode()).hexdigest(),'nativeAdmission':'required'}
 counts={scan['scan']:len(scan['rows']) for scan in operands['scans']}
 if (checked.get('securityReady') is not False or checked.get('inspected') is not True or set(checked)!=set(expected)|{'operandCounts'} or any(checked[k]!=v for k,v in expected.items()) or checked['operandCounts']!=counts or len(counts)!=len(operands['scans']) or any(type(v) is not int for v in checked['operandCounts'].values()) or batch['resultContractSha256']!=packet['resultContractSha256'] or sha256(packet['resultContractJson'].encode()).hexdigest()!=packet['resultContractSha256']):raise ValueError('Original inspected relational publication correspondence required')
 raw=json.dumps({'version':'truss.guarded-query-result/0.2-candidate','securityReady':False,'sourceContextSha256':packet['sourceContextSha256'],'queryContextSha256':packet['queryContextSha256'],'resultContractJson':packet['resultContractJson'],'batchJson':copied['batch']},separators=(',',':')).encode()
 if len(raw)>4000000:raise ValueError('Bounded original relational publication required')
 return raw
