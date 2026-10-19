// SPDX-License-Identifier: MIT OR Apache-2.0
/** Thin bounded host bridge; all key semantics remain in the original UMF owner. */
import {encodeCoreKeyTuple,readCoreKeyTupleBytes,readJsonValue} from './producer.js';
try {
  const raw=await Bun.stdin.text();
  if(Buffer.byteLength(raw)>1048576)throw Error('key input budget');
  const input=JSON.parse(raw);
  if(Object.keys(input).sort().join(',')!=='requests,sourceText' || typeof input.sourceText!=='string'
      || !Array.isArray(input.requests) || input.requests.length<1 || input.requests.length>512)throw Error('key request shape');
  const source=readJsonValue(input.sourceText,'json');
  if(Buffer.byteLength(input.sourceText)*input.requests.length>4194304)throw Error('aggregate source budget');
  const parts=[];let total=64;
  for(const request of input.requests){
    const shape=Object.keys(request).sort().join(',');
    if(shape!=='identity,values'&&shape!=='identity,literalTexts')throw Error('key request shape');
    if(shape==='identity,literalTexts'&&(!Array.isArray(request.literalTexts)||request.literalTexts.length<1||request.literalTexts.length>32||request.literalTexts.some(v=>typeof v!=='string')))throw Error('literal input shape');
    const values=shape==='identity,literalTexts'?request.literalTexts.map(text=>readJsonValue(text,'json')):request.values;
    const receipt=encodeCoreKeyTuple(source,request.identity,values);
    const bytes=readCoreKeyTupleBytes(receipt,source);
    if(Buffer.from(bytes).toString('hex')!==receipt.bytesHex)throw Error('original key byte correspondence');
    const part=JSON.stringify(JSON.stringify(receipt));total+=Buffer.byteLength(part)+1;
    if(total>8388608)throw Error('key output budget');
    parts.push(part);
  }
  const response='{"status":"encoded","receiptTexts":['+parts.join(',')+']}';
  process.stdout.write(response);
} catch(error) {
  process.stdout.write(JSON.stringify({status:'refused',reason:'owner_refusal',code:error?.code??'KEY_INPUT'}));
}
