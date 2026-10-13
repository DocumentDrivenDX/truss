from pathlib import Path
from hashlib import sha256
from subprocess import CompletedProcess
from unittest.mock import patch
import json,copy
from truss._umf_key_tuples import KeyTupleRequest,encode_string_key_tuples
root=Path('/private/tmp/truss-security-main-integration');out=Path(__file__).parent
fixture=json.loads((root/'packages/python/tests/fixtures/security-mapping-request.json').read_bytes());source=fixture['modules'][0]['documentJson'].encode();request=KeyTupleRequest('m','Staff','pk',('abc',));result=encode_string_key_tuples(source,(request,),bun_executable='/opt/homebrew/bin/bun')[0];original=json.loads(result.original_receipt_bytes)
assert original['version']=='3.0.0' and original['source']['umf']=='0.8.0';assert result.document_sha256==sha256(source).hexdigest();(out/'original-receipt.json').write_bytes(result.original_receipt_bytes)
results=[{'case':'genuineOriginal08Receipt','passed':True,'originalDocumentDigestRetained':True}]
for case in ('legacyReceiptVersion','unknownReceiptVersion','changedSourceVersion','changedSourceIdentity','changedValue','changedKeyIdentity','uppercaseBytes','unknownReceiptField','missingReceipt','unknownEnvelopeField','refusedEnvelope'):
 receipt=copy.deepcopy(original);response={'status':'encoded','receiptTexts':[]}
 if case=='legacyReceiptVersion':receipt['version']='2.0.0'
 if case=='unknownReceiptVersion':receipt['version']='4.0.0'
 if case=='changedSourceVersion':receipt['source']['umf']='0.7.0'
 if case=='changedSourceIdentity':receipt['source']['id']='other'
 if case=='changedValue':receipt['values']=[{'string':'different'}]
 if case=='changedKeyIdentity':receipt['identity']['key']='other'
 if case=='uppercaseBytes':receipt['bytesHex']=receipt['bytesHex'].upper()
 if case=='unknownReceiptField':receipt['extra']=True
 response['receiptTexts']=[json.dumps(receipt)]
 if case=='missingReceipt':response['receiptTexts']=[]
 if case=='unknownEnvelopeField':response['extra']=True
 if case=='refusedEnvelope':response['status']='refused'
 captures=[CompletedProcess([],0,b'1.4.2\n',b''),CompletedProcess([],0,json.dumps(response).encode(),b'')]
 with patch('truss._umf_key_tuples._capture',side_effect=captures):
  try:encode_string_key_tuples(source,(request,),bun_executable='/opt/homebrew/bin/bun')
  except ValueError as e:results.append({'case':case,'passed':True,'refused':str(e)})
  else:raise AssertionError(case+' unexpectedly accepted')
for version in ('0.6.0','0.9.0','0.8',True):
 invalid=json.loads(source);invalid['umf']=version
 with patch('truss._umf_key_tuples._capture') as capture:
  try:encode_string_key_tuples(json.dumps(invalid).encode(),(request,),bun_executable='/opt/homebrew/bin/bun')
  except ValueError:assert not capture.called;results.append({'case':'unsupportedSourceVersion','version':version,'passed':True,'beforeRuntime':True})
  else:raise AssertionError('invalid version accepted')
(out/'results.json').write_text(json.dumps({'scope':'Genuine packaged core0.8 owner receipt plus selected synthetic returned-packet refusals; not authentication of substituted runtime or general encoder theorem.','controls':results},indent=2)+'\n');print(json.dumps({'passed':len(results),'results':str(out/'results.json')}))
