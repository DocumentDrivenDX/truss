import {expect,test} from 'bun:test';
import {createOperationOrdinalIssuer} from '../packages/postgresql/src/operation-ordinal-issuer';
const corpus=await Bun.file('tests/fixtures/operation-ordinal-issuer.json').json();
for(const scenario of corpus.cases)test(scenario.id,()=>{
 const custody={},issuer=createOperationOrdinalIssuer(custody,BigInt(scenario.maximum)),actual:string[]=[];
 for(const event of scenario.events){
  if(event==='reserve'||event==='foreign_reserve'){
   const result=issuer.reserve(event==='reserve'?custody:{});
   actual.push(result.outcome==='issued'?result.ordinal:result.reason);
  }else if(['control_unknown','cancel','end'].includes(event))issuer.close(custody);
  else if(!['savepoint_rollback','failed_admission'].includes(event))throw Error('Unknown independent event');
 }
 expect(actual).toEqual(scenario.expected);
});
test('native maximum and exact argument types',()=>{
 const custody={};
 expect(createOperationOrdinalIssuer(custody,9223372036854775807n).reserve(custody)).toEqual({outcome:'issued',ordinal:'0'});
 for(const maximum of [-1n,9223372036854775808n,1 as any])expect(()=>createOperationOrdinalIssuer(custody,maximum)).toThrow();
});
