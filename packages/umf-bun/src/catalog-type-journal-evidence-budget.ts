// SPDX-License-Identifier: MIT OR Apache-2.0
/** Private retained-byte ledger only; not a shared operation heap/text/CPU budget. */
export function createTypeJournalEvidenceBudget(){
 let retained=0;
 return Object.freeze({charge(bytes:number):void{
  if(!Number.isSafeInteger(bytes)||bytes<0||bytes>4194304-retained)throw Error('Type journal ingress evidence capacity exceeded');
  retained+=bytes;
 },total():number{return retained}});
}
