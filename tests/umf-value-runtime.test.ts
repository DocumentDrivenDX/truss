// SPDX-License-Identifier: MIT OR Apache-2.0
import {test,expect} from 'bun:test';
import {loadCurrentNumericOwner,UMF_CORE10_CATALOG_SOURCE} from '../packages/umf-bun/src/index';
const directory=process.env.TRUSS_UMF_NUMERIC_PRODUCER;
if(!directory)throw Error('Pinned current producer required');
const owner=await loadCurrentNumericOwner(directory);
const {model,identity,values,expectedHex}=await Bun.file('tests/umf-fixtures/value-key.json').json();
const validation=owner.validateSemanticTypesDocument(model);
const encode=(source:unknown,key:unknown,literals:unknown[])=>{
 const checked=owner.validateSemanticTypesDocument(source);
 if(!checked.valid)throw Error('Invalid current source');
 return owner.encodeCoreKeyTupleBody(source,key,literals,checked);
};
test('actual current source and ordered UMFK1 bytes preserve exact carriers',()=>{
 expect(owner.sourceRevision).toBe(UMF_CORE10_CATALOG_SOURCE);
 expect(validation.valid).toBe(true);expect(model.umf).toBe('0.10.0');
 const original=JSON.stringify(model),literals=JSON.stringify(values);
 const encoded=encode(model,identity,values);
 expect(encoded.profile).toBe('umf-key-tuple-v1');expect(encoded.bytesHex).toBe(expectedHex);
 expect(JSON.stringify(model)).toBe(original);expect(JSON.stringify(values)).toBe(literals);
});
test('current key primitive enforces exact field scale, precision and width',()=>{
 expect(()=>encode(model,identity,[{decimalToken:'12.3401'},values[1],values[2]])).toThrow();
 expect(()=>encode(model,identity,[{decimalToken:'1000000000000000000'},values[1],values[2]])).toThrow();
 expect(()=>encode(model,identity,[values[0],values[1],{integerToken:'18446744073709551616'}])).toThrow();
 expect(()=>encode(model,identity,[values[1],values[0],values[2]])).toThrow();
 expect(()=>encode(model,identity,values.slice(1))).toThrow();
 expect(()=>encode(model,{...identity,key:'missing'},values)).toThrow();
});
