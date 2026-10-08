import {test,expect} from 'bun:test';
import {loadUmfProducer} from '../packages/umf-bun/src/index';
const directory=process.env.TRUSS_UMF_PRODUCER;if(!directory)throw Error('Pinned UMF producer required');
const source={umf:'0.7.0',id:'native-acceptance-input',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[
 {id:'item',kind:'record',extensions:{},members:[{module:'m',element:'label'},{module:'m',element:'caption'}]},
 {id:'label',kind:'field',extensions:{},scalarType:'string',nullability:'required',cardinality:'one'},
 {id:'caption',kind:'field',extensions:{},scalarType:'string',nullability:'absent-allowed',cardinality:'one'}]}]};
test('original UMF source and verified reversible transition retained',async()=>{
 const producer=await loadUmfProducer(directory);const text=JSON.stringify(source);const inspected=producer.inspect(text);
 expect(inspected.originalText).toBe(text);expect(inspected.sourceValidation.valid).toBe(true);expect(inspected.transition?.source.umf).toBe('0.7.0');expect(inspected.target.umf).toBe('0.8.0');
 const actual=producer.checkRecord(inspected.target,{module:'m',element:'item'},[{field:{module:'m',element:'label'},state:'present',value:{string:'雪🙂'}}]);
 expect(actual.validation.valid).toBe(true);expect(actual.validation.complete).toBe(true);
 const absent=producer.checkRecord(inspected.target,{module:'m',element:'item'},[]);expect(absent.validation.valid).toBe(false);
 const wrong=producer.checkRecord(inspected.target,{module:'m',element:'item'},[{field:{module:'m',element:'label'},state:'present',value:{integerToken:'9007199254740993123'}}]);expect(wrong.validation.valid).toBe(false);
});
