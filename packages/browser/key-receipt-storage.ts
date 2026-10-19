// SPDX-License-Identifier: MIT OR Apache-2.0
/** Private lossless seal encoding; public UMF receipts retain their full source. */
export const KEY_RECEIPT_ENCODING='model-source-once/1';
const members=['bytesHex','identity','keyPath','operation','profile','values','version'];
const object=(value:any)=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const exact=(value:any,keys:string[])=>object(value)&&Object.keys(value).sort().join(',')===keys.join(',');
const original=(receipt:any)=>receipt.operation==='encode-core-key-tuple'&&receipt.version==='3.0.0'&&receipt.profile==='umf-key-tuple-v1';
export function compactKeyReceipts(receipts:any[],model:any):any[]{
 if(!Array.isArray(receipts))throw Error('Original key receipts required');
 const source=JSON.stringify(model);
 return receipts.map(receipt=>{
  if(!exact(receipt,[...members,'source'].sort())||!original(receipt)||JSON.stringify(receipt.source)!==source)throw Error('Original key receipt source required');
  const {source:_source,...compact}=receipt;return compact;
 });
}
export function checkSealEncoding(source:any):void{
 if(source.profile==='truss-browser-seal/0.1'){
  if(Object.hasOwn(source,'keyReceiptEncoding'))throw Error('Original full key receipt encoding required');
  return;
 }
 if(source.profile!=='truss-browser-seal/0.2'||source.keyReceiptEncoding!==KEY_RECEIPT_ENCODING||!Array.isArray(source.keyReceipts)
  ||source.keyReceipts.some((receipt:any)=>!exact(receipt,members)||!original(receipt))
  ||source.keyReceipts.length!==JSON.parse(source.manifest.utf8).items.length)throw Error('Exact compact key receipt encoding required');
}
export function expandKeyReceipts(source:any):any[]{
 checkSealEncoding(source);if(source.profile==='truss-browser-seal/0.1')return source.keyReceipts;
 const model=JSON.parse(source.model.utf8);
 return source.keyReceipts.map((receipt:any)=>({operation:receipt.operation,version:receipt.version,profile:receipt.profile,source:model,
  identity:receipt.identity,values:receipt.values,keyPath:receipt.keyPath,bytesHex:receipt.bytesHex}));
}
/** Old jobs retain exact full-receipt intent; new jobs use the equivalent compact form. */
export function sealIntentUtf8(source:any,compact:boolean):string{
 checkSealEncoding(source);
 const {reference:_reference,profile:_profile,keyReceiptEncoding:_encoding,...intent}=source;
 if(compact&&source.profile==='truss-browser-seal/0.1')intent.keyReceipts=compactKeyReceipts(source.keyReceipts,JSON.parse(source.model.utf8));
 if(!compact&&source.profile==='truss-browser-seal/0.2')intent.keyReceipts=expandKeyReceipts(source);
 return JSON.stringify(intent);
}
