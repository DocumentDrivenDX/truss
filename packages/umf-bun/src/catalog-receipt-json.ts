/** Exact receipt JSON custody checks; not UMF semantic verification or host containment. */
import {indexSourceJsonOccurrences,originalSourceOccurrenceBytes} from '../../postgresql/src/acceptance-json';
/** Normalize a finite JSON decimal without materializing its exponent. */
function decimal(text:string):string{
 const match=/^(-?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(text);if(!match)throw Error('Original receipt numeric meaning required');
 let digits=(match[2]!+(match[3]??'')).replace(/^0+/,'');if(!digits)return '0';
 const rawExponent=match[4]??'0';if(rawExponent.replace(/^[+-]/,'').replace(/^0+/,'').length>64)throw Error('Original receipt numeric meaning required');
 let exponent=BigInt(rawExponent)-BigInt((match[3]??'').length);const tail=/0+$/.exec(digits)?.[0].length??0;
 if(tail){digits=digits.slice(0,-tail);exponent+=BigInt(tail)}return match[1]+digits+'e'+exponent;
}
/** Preserve exact bytes independently. Reject a Number parse that changes the decimal value. */
export function parseOriginalReceiptJson(bytes:Uint8Array):unknown{
 const index=indexSourceJsonOccurrences(bytes);
 for(let i=0;i<index.occurrences.length;i++)if(index.occurrences[i]!.kind==='number'){
  const raw=new TextDecoder('utf-8',{fatal:true}).decode(originalSourceOccurrenceBytes(index,i)),number=Number(raw);
  if(!Number.isFinite(number)||Object.is(number,-0)||decimal(raw)!==decimal(JSON.stringify(number)))throw Error('Original receipt numeric meaning required');
 }
 return JSON.parse(new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes));
}
/** Validate descriptors before reading/freeze; never invoke data getters/toJSON. */
export function freezeInertReceiptJson(value:unknown):void{
 const active=new Set<object>();let visits=0;
 function visit(v:unknown,depth:number):void{
  if(++visits>100000||depth>128)throw Error('Receipt result structural capacity exceeded');
  if(v===null||typeof v==='string'||typeof v==='boolean')return;
  if(typeof v==='number'){if(!Number.isFinite(v)||Object.is(v,-0)||(Number.isInteger(v)&&!Number.isSafeInteger(v)))throw Error('Inert receipt JSON required');return}
  if(typeof v!=='object'||active.has(v)||Object.getOwnPropertySymbols(v).length)throw Error('Inert receipt JSON required');
  const array=Array.isArray(v),proto=Object.getPrototypeOf(v);if(array?proto!==Array.prototype:proto!==Object.prototype&&proto!==null)throw Error('Inert receipt JSON required');
  active.add(v);const descriptors=Object.getOwnPropertyDescriptors(v);let count=0;
  for(const [key,d] of Object.entries(descriptors)){
   if(array&&key==='length')continue;
   if(!d.enumerable||!Object.hasOwn(d,'value')||(array&&(!/^(0|[1-9][0-9]*)$/.test(key)||Number(key)>=(v as unknown[]).length)))throw Error('Inert receipt JSON required');
   count++;visit(d.value,depth+1);
  }
  if(array&&count!==(v as unknown[]).length)throw Error('Inert receipt JSON required');active.delete(v);Object.freeze(v);
 }
 visit(value,0);
}
export function sameReceiptMeaning(a:any,b:any):boolean{
 if(a===null||b===null||typeof a!=='object'||typeof b!=='object')return Object.is(a,b);
 if(Array.isArray(a)!==Array.isArray(b))return false;
 const keys=Object.keys(a);if(keys.length!==Object.keys(b).length||(Array.isArray(a)&&a.length!==b.length))return false;
 return keys.every(k=>Object.hasOwn(b,k)&&sameReceiptMeaning(a[k],b[k]));
}
