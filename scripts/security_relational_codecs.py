"""Original PostgreSQL codec preflight; no SQL/session/authority admission."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from truss._owner_evidence_json import decode_owner_evidence_json
from truss._security_relational_source import capture_relational_source_comparison


def prepare_owned_relational_codec_checker(binary):
 binary=Path(binary).resolve();digest=sha256(binary.read_bytes()).digest()
 source=Path(__file__);source_digest=sha256(source.read_bytes()).digest()
 def check(request,output,operands=None):
  capture_relational_source_comparison(request,output)
  packet=decode_owner_evidence_json(output)
  payload={'requestJson':request.decode()};operand_count=0
  if operands is not None:
   if type(operands) is not bytes or not 1<=len(operands)<=4000000:raise ValueError('Bounded original codec operands required')
   payload['operandBatchJson']=operands.decode()
   captures=decode_owner_evidence_json(operands)
   operand_count=sum(len(row['operands']) for scan in captures['scans'] for row in scan['rows'])
  raw=json.dumps(payload,separators=(',',':')).encode()
  if len(raw)>16000000:raise ValueError('Bounded original codec preflight required')
  result=subprocess.run([str(binary)],input=raw,capture_output=True,timeout=15)
  if result.returncode or not 1<=len(result.stdout)<=65536:raise ValueError('Original PostgreSQL codec preflight refused')
  checked=decode_owner_evidence_json(result.stdout)
  expected={'version':'weft.postgresql.codecs.inspected/0.1-candidate','securityReady':False,'contextSha256':packet['queryContextSha256'],'parameterCount':sum(p['channel']!='subject' for p in packet['parameters']),'operandCount':operand_count,'nativeSessionAdmission':'required'}
  if (type(checked) is not dict or checked!=expected or checked.get('securityReady') is not False or any(type(checked.get(k)) is not int for k in ('parameterCount','operandCount'))):raise ValueError('Original PostgreSQL codec lineage required')
  if sha256(binary.read_bytes()).digest()!=digest or sha256(source.read_bytes()).digest()!=source_digest:raise ValueError('Original PostgreSQL codec sources changed')
  return bytes(result.stdout)
 return check
