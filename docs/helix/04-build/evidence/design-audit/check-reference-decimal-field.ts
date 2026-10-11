import {loadUmfValueProducer} from '../../../../../packages/umf-bun/src/index';
// Original UMF Field meaning; independent of the native SQL implementation.
const owner=await loadUmfValueProducer(process.argv[2]);
const document={umf:'0.8.0',id:'truss-reference-decimal',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'amount',name:'amount',kind:'field',scalarType:'decimal',nullability:'required',cardinality:'one',facets:{precision:21,scale:3},extensions:{}}]}]};
const accepted=['9007199254740993.000','0.00','-0.01','1e2','1.2300',
 '999999999999999999.999','-999999999999999999.999','0e'+'9'.repeat(33),'-0.000e'+'9'.repeat(1000)];
const refused=['0.0001','1e18','-1e18','1e'+'0'.repeat(33),'+1','01','.1','1.','NaN','1e','1\n'];
for(const [tokens,expected] of [[accepted,true],[refused,false]] as const){
 for(const token of tokens){
  const result=owner.validateCoreFieldValue(document,{module:'m',element:'amount'},{decimalToken:token});
  if(result.valid!==expected)throw Error('Owner admission differs: '+token);
 }
}
console.log(JSON.stringify({sourceRevision:owner.sourceRevision,bundleSha256:owner.bundleSha256,
 scope:'Original UMF decimal Field precision21 scale3 admission only; no installed runtime qualification',accepted,refused},null,2));
