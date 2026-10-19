// SPDX-License-Identifier: MIT OR Apache-2.0
/** Truss UMFK1 realization over actual validated UMF 0.10 source. */
import {createHash} from 'node:crypto';
import {readJsonValue,validateSemanticTypesDocument as validateDocument,encodeCoreKeyTupleBody} from './producer.js';
const fail=()=>{throw Error('Unsupported current native key input');};
const sameKeys=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join(',')===[...keys].sort().join(',');
try {
  const raw=await Bun.stdin.text();
  if(Buffer.byteLength(raw)>1048576)fail();
  const input=JSON.parse(raw);
  if(!sameKeys(input,['requests','sourceText'])||typeof input.sourceText!=='string'||!Array.isArray(input.requests)||input.requests.length<1||input.requests.length>512)fail();
  const source=readJsonValue(input.sourceText,'json');
  if(source?.umf!=='0.10.0')fail();
  const validation=validateDocument(source);
  if(!validation.valid)fail();
  const elements=new Map(),keys=new Map();
  for(let mi=0;mi<source.modules.length;mi++){
    const module=source.modules[mi];
    for(let ei=0;ei<module.elements.length;ei++){
      const element=module.elements[ei],path=`/modules/${mi}/elements/${ei}`;
      elements.set(JSON.stringify([module.id,element.id]),{field:element,path});
      if(element.kind!=='record')continue;
      const members=new Map(element.members.map((ref,i)=>[JSON.stringify([ref.module,ref.element]),`${path}/members/${i}`]));
      for(let ki=0;ki<(element.keys??[]).length;ki++){
        const key=element.keys[ki];
        keys.set(JSON.stringify([module.id,element.id,key.id]),{record:element,recordPath:path,key,keyPath:`${path}/keys/${ki}`,members});
      }
    }
  }
  const sourceSha256=createHash('sha256').update(input.sourceText).digest('hex');
  const parts=[];let total=64;
  for(const request of input.requests){
    if(!sameKeys(request,['identity','values'])&&!sameKeys(request,['identity','literalTexts']))fail();
    if(!sameKeys(request.identity,['module','element','key']))fail();
    const identity=request.identity,selected=keys.get(JSON.stringify([identity.module,identity.element,identity.key]));
    if(!selected||!Array.isArray(selected.key.fields)||selected.key.fields.length<1||selected.key.fields.length>1024)fail();
    const fields=selected.fields??=selected.key.fields.map(ref=>{
      const address=JSON.stringify([ref.module,ref.element]),found=elements.get(address),member=selected.members.get(address);
      if(!found||member===undefined)fail();
      const field=found.field,facet=field.facets??{};
      if(field.kind!=='field'||field.cardinality!=='one'||field.nullability!=='required'||!['boolean','integer','decimal','string','binary'].includes(field.scalarType))fail();
      if(field.scalarType==='integer'){
        if(Object.keys(facet).length!==0&&!(sameKeys(facet,['integerWidth'])&&sameKeys(facet.integerWidth,['bits','signed'])&&facet.integerWidth.bits===64&&facet.integerWidth.signed===true))fail();
      }else if(field.scalarType==='decimal'){
        if(!sameKeys(facet,['precision','scale'])||!Number.isSafeInteger(facet.precision)||facet.precision<1||facet.precision>2147483647||!Number.isSafeInteger(facet.scale)||facet.scale<0||facet.scale>facet.precision)fail();
      }else if(!sameKeys(facet,[]))fail();
      return {field,path:found.path+'/facets',member};
    });
    let values=request.values;
    if(Object.hasOwn(request,'literalTexts')){
      if(!Array.isArray(request.literalTexts)||request.literalTexts.length<1||request.literalTexts.length>32||request.literalTexts.some(v=>typeof v!=='string'))fail();
      values=request.literalTexts.map(text=>readJsonValue(text,'json'));
    }
    const encoded=encodeCoreKeyTupleBody(source,identity,values,validation,undefined,{...selected,fields});
    const carrier={operation:'truss-encode-key-tuple',version:'1.0.0',profile:'umf-key-tuple-v1',sourceSha256,identity,values,keyPath:encoded.keyPath,bytesHex:encoded.bytesHex};
    const part=JSON.stringify(JSON.stringify(carrier));total+=Buffer.byteLength(part)+1;
    if(total>8388608)fail();
    parts.push(part);
  }
  process.stdout.write('{"status":"encoded","receiptTexts":['+parts.join(',')+']}');
} catch(error) {
  process.stdout.write(JSON.stringify({status:'refused',reason:'native_key_refusal',code:error?.code??'KEY_INPUT'}));
}
