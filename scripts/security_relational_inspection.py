"""Pinned original relational inspector; correspondence, never native admission."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from truss._owner_evidence_json import decode_owner_evidence_json
from truss._security_relational_source import capture_relational_source_comparison


def prepare_owned_relational_inspector(binary):
 binary=Path(binary).resolve();digest=sha256(binary.read_bytes()).digest()
 source=Path(__file__);source_digest=sha256(source.read_bytes()).digest()
 def inspect(request,output,operands,batch):
  for raw,limit in ((request,4000000),(output,16000000),(operands,4000000),(batch,4000000)):
   if type(raw) is not bytes or not 1<=len(raw)<=limit:raise ValueError('Bounded original relational inspection required')
  comparison=capture_relational_source_comparison(request,output)
  packet=decode_owner_evidence_json(output)
  payload=json.dumps({'version':'weft.truss.security.relational-result/0.2-candidate','sourceRequestJson':request.decode(),'sourceOutputJson':output.decode(),'operandBatchJson':operands.decode(),'batchJson':batch.decode()},separators=(',',':')).encode()
  if len(payload)>32000000:raise ValueError('Bounded original relational inspection required')
  result=subprocess.run([str(binary)],input=payload,capture_output=True,timeout=15)
  if result.returncode or not 1<=len(result.stdout)<=65536:raise ValueError('Original relational inspection refused')
  checked=decode_owner_evidence_json(result.stdout)
  expected={'version':'weft.truss.security.relational-result.inspected/0.2-candidate','securityReady':False,'inspected':True,'sourceRequestSha256':sha256(request).hexdigest(),'sourceOutputSha256':sha256(output).hexdigest(),'sourceContextSha256':comparison.source_sha256,'queryContextSha256':packet['queryContextSha256'],'operandBatchSha256':sha256(operands).hexdigest(),'batchSha256':sha256(batch).hexdigest(),'nativeAdmission':'required'}
  if type(checked) is not dict or set(checked)!=set(expected)|{'operandCounts'} or checked.get('securityReady') is not False or checked.get('inspected') is not True or any(checked.get(k)!=v for k,v in expected.items()):raise ValueError('Original relational inspection lineage required')
  if sha256(binary.read_bytes()).digest()!=digest or sha256(source.read_bytes()).digest()!=source_digest:raise ValueError('Original relational inspector sources changed')
  return bytes(result.stdout)
 return inspect
