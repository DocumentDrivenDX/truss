// SPDX-License-Identifier: MIT OR Apache-2.0
import {test,expect} from 'bun:test';
import {loadCurrentNumericOwner,UMF_CORE10_CATALOG_SOURCE} from '../packages/umf-bun/src/index';
const directory=process.env.TRUSS_UMF_NUMERIC_PRODUCER;
if(!directory)throw Error('Pinned original UMF numeric producer required');
const producer=await loadCurrentNumericOwner(directory);
test('original UMF number convenience requires lossless value correspondence',()=>{
 expect(producer.sourceRevision).toBe(UMF_CORE10_CATALOG_SOURCE);
 expect(producer.admitJavascriptNumber(123,'integer')).toEqual({integerToken:'123'});
 expect(producer.admitJavascriptNumber(0.5,'decimal')).toEqual({decimalToken:'0.5'});
 expect(()=>producer.admitJavascriptNumber(0.1,'decimal')).toThrow();
 expect(()=>producer.admitJavascriptNumber(9007199254740992,'integer')).toThrow();
 expect(()=>producer.admitJavascriptNumber(-0,'decimal')).toThrow();
 expect(()=>producer.admitJavascriptNumber(Infinity,'decimal')).toThrow();
});
test('original UMF exact carriers retain spelling and require exact output conversion',()=>{
 const decimal=producer.exactDecimal('0.500');
 expect(decimal).toEqual({decimalToken:'0.500'});
 expect(producer.numericToNumberLossless(decimal)).toBe(0.5);
 expect(decimal.decimalToken).toBe('0.500');
 const tenth=producer.exactDecimal('0.1');expect(tenth).toEqual({decimalToken:'0.1'});
 expect(()=>producer.numericToNumberLossless(tenth)).toThrow();
 const integer=producer.integerFromBigInt(9007199254740993n);
 expect(integer).toEqual({integerToken:'9007199254740993'});
 expect(producer.integerToBigInt(integer)).toBe(9007199254740993n);
 expect(()=>producer.numericToNumberLossless(integer)).toThrow();
 expect(()=>producer.integerToBigInt({integerToken:'-0'})).toThrow();
});
test('numeric loader refuses a catalog-only owner bundle',async()=>{
 const catalog=process.env.TRUSS_UMF_PRODUCER;
 if(!catalog)throw Error('Current core10 catalog producer required');
 await expect(loadCurrentNumericOwner(catalog)).rejects.toThrow('Original UMF producer pin mismatch');
});
