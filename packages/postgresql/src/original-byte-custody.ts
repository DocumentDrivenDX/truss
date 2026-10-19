// SPDX-License-Identifier: MIT OR Apache-2.0
/** Bounded byte custody only; no JSON, semantic or native admission. */
const typed=Object.getPrototypeOf(Uint8Array.prototype);
const brand=Object.getOwnPropertyDescriptor(typed,Symbol.toStringTag)!.get!;
const length=Object.getOwnPropertyDescriptor(typed,'length')!.get!;
const buffer=Object.getOwnPropertyDescriptor(typed,'buffer')!.get!;
const ordinaryLength=Object.getOwnPropertyDescriptor(ArrayBuffer.prototype,'byteLength')!.get!;
const set=Uint8Array.prototype.set;
export class OriginalByteCustodyError extends Error{
 constructor(readonly reason:'carrier'|'resource'){super(reason)}
}
/** Never reads caller properties, iterator or species. Shared storage may be
 * copied for structural source scanning, but is not an atomic concurrent snapshot.
 * Ordinary wire handoffs require actual ArrayBuffer storage, including cross-realm buffers. */
export function copyOriginalByteCustody(original:Uint8Array,ordinaryOnly=false,maxBytes=1048576):Uint8Array{
 if(typeof ordinaryOnly!=='boolean'||!Number.isSafeInteger(maxBytes)||maxBytes<0||maxBytes>16777216)throw new OriginalByteCustodyError('resource');
 if(brand.call(original)!=='Uint8Array')throw new OriginalByteCustodyError('carrier');
 const size=length.call(original) as number;
 if(size>maxBytes)throw new OriginalByteCustodyError('resource');
 if(ordinaryOnly){try{ordinaryLength.call(buffer.call(original))}catch{throw new OriginalByteCustodyError('carrier')}}
 const owned=new Uint8Array(size);try{set.call(owned,original)}catch{throw new OriginalByteCustodyError('carrier')}return owned;
}
