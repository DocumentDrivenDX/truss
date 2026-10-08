import {test,expect} from 'bun:test';
import {loadUmfValueProducer,UMF_VALUE_SOURCE} from '../packages/umf-bun/src/index';
const directory=process.env.TRUSS_UMF_VALUE_PRODUCER;if(!directory)throw Error('Pinned original UMF value producer required');
const producer=await loadUmfValueProducer(directory);
const {model,identity,values,expectedHex}=await Bun.file('tests/umf-fixtures/value-key.json').json();
test('original current-core Field producer retains exact validity and completeness',()=>{
 expect(producer.sourceRevision).toBe(UMF_VALUE_SOURCE);
 const decimal=producer.validateCoreFieldValue(model,{module:'m',element:'amount'},values[0]);
 expect(decimal.valid).toBe(true);expect(decimal.complete).toBe(true);
 expect(producer.validateCoreFieldValue(model,{module:'m',element:'amount'},{decimalToken:'12.3401'}).valid).toBe(false);
 expect(producer.validateCoreFieldValue(model,{module:'m',element:'count'},values[2]).valid).toBe(true);
 expect(producer.validateCoreFieldValue(model,{module:'m',element:'count'},{integerToken:'18446744073709551616'}).valid).toBe(false);
 expect(producer.validateCoreFieldValue(model,{module:'m',element:'amount'},{string:'12.340'}).valid).toBe(false);
});
test('original current-core tuple encoder preserves ordered exact source and mathematical encoding',()=>{
 const receipt=producer.encodeCoreKeyTuple(model,identity,values);
 expect(receipt.version).toBe('3.0.0');expect(receipt.profile).toBe('umf-key-tuple-v1');
 // Independently specified UMFK1 count/tag/length, scale/coefficient, UTF-8 and integer bytes.
 expect(receipt.bytesHex).toBe(expectedHex);
 expect(receipt.values).toEqual(values);expect(receipt.source).toEqual(model);
 expect(producer.verifyCoreKeyTuple(receipt,model)).toEqual(receipt);
 expect(()=>producer.verifyCoreKeyTuple({...receipt,bytesHex:'00'},model)).toThrow();
 expect(()=>producer.verifyCoreKeyTuple(receipt,{...model,id:'changed'})).toThrow();
 expect(()=>producer.encodeCoreKeyTuple(model,identity,[values[1],values[0],values[2]])).toThrow();
 expect(()=>producer.encodeCoreKeyTuple(model,identity,[values[0],values[1],{integerToken:'18446744073709551616'}])).toThrow();
});
