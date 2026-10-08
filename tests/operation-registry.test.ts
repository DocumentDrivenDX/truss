import {test,expect} from 'bun:test';
import {decodeOperationRegistry,OPERATION_REGISTRY_COLUMNS,type StatementResult} from '../packages/postgresql/src/index';
const values:(string|null)[]=['123','0','mutation','admitted','0',null,null,null,'61','62','63','64','65','66','67',null];
const result=(rows:(string|null)[][]):StatementResult=>({columns:OPERATION_REGISTRY_COLUMNS,rows:rows.map(row=>row.map(text=>text===null?{state:'null'}:{state:'text',text})),affectedRows:String(rows.length),command:'SELECT'});
const limits={maxRows:8,maxBytes:4096};
test('original registry row preserves exact numeric and byte carriers',()=>{
 const row=[...values];row[1]='9223372036854775807';
 expect(decodeOperationRegistry('123',result([row]),limits)[0]).toEqual(row);
 expect(Object.isFrozen(decodeOperationRegistry('123',result([row]),limits)[0])).toBe(true);
});
test('foreign/duplicate/unassigned identities and malformed phases refuse',()=>{
 expect(()=>decodeOperationRegistry(null,result([]),limits)).toThrow();
 expect(()=>decodeOperationRegistry('124',result([values]),limits)).toThrow();
 expect(()=>decodeOperationRegistry('123',result([values,values]),limits)).toThrow();
 for(const [index,text] of [[1,'9223372036854775808'],[3,'unknown'],[5,'0'],[8,''],[8,'FF'],[15,'00']] as const){const row=[...values];row[index]=text;expect(()=>decodeOperationRegistry('123',result([row]),limits)).toThrow();}
 expect(()=>decodeOperationRegistry('123',result([values]),{...limits,maxRows:0})).toThrow();
 expect(()=>decodeOperationRegistry('123',result([values]),{...limits,maxBytes:1})).toThrow();
});
