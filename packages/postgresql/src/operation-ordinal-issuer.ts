/** Private counter component. Construction is not original transaction admission.
 * Bind one instance to the qualified shared physical-connection/epoch issuer.
 * Reserve control/account permits before reserve; submit savepoint only afterward.
 */
export function createOperationOrdinalIssuer(custody:object, maximum:bigint=9223372036854775807n){
 if(!custody||typeof custody!=='object'||typeof maximum!=='bigint'||maximum<0n||maximum>9223372036854775807n)throw Error('Invalid original issuer component');
 let next=0n,closed=false;
 return Object.freeze({
  reserve(original:object):{outcome:'issued';ordinal:string}|{outcome:'refused';reason:'custody'|'closed'|'exhausted'}{
   if(original!==custody)return Object.freeze({outcome:'refused',reason:'custody'});
   if(closed)return Object.freeze({outcome:'refused',reason:'closed'});
   if(next>maximum)return Object.freeze({outcome:'refused',reason:'exhausted'});
   const ordinal=(next++).toString();return Object.freeze({outcome:'issued',ordinal});
  },
  close(original:object):void{
   if(original!==custody)throw Error('Original issuer custody required');
   closed=true;
  },
 });
}
