import {test,expect} from 'bun:test';
import {loadUmfNumericProducer,UMF_NUMERIC_SOURCE} from '../packages/umf-bun/src/index';
const directory=process.env.TRUSS_UMF_NUMERIC_PRODUCER;
if(!directory)throw Error('Pinned original UMF numeric producer required');
const producer=await loadUmfNumericProducer(directory);
test('original UMF number convenience requires lossless value correspondence',()=>{
 expect(producer.sourceRevision).toBe(UMF_NUMERIC_SOURCE);
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
test('original current-core Field validation remains authoritative for numeric convenience',()=>{
 const context={document:{umf:'0.8.0',id:'truss-numeric-context',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'amount',name:'amount',kind:'field',scalarType:'decimal',nullability:'required',cardinality:'one',facets:{precision:21,scale:3},extensions:{}}]}]},field:{module:'m',element:'amount'}};
 expect(producer.exactDecimal('1.250',context)).toEqual({decimalToken:'1.250'});
 expect(producer.admitJavascriptNumber(1.25,'decimal',context)).toEqual({decimalToken:'1.25'});
 expect(()=>producer.exactDecimal('1.2345',context)).toThrow();
 expect(()=>producer.exactDecimal('1000000000000000000',context)).toThrow();
});
