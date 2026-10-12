import {test,expect} from 'bun:test';
import {lowerSecurityRowPredicate} from '../packages/postgresql/src/security-predicate';
import {request} from './fixtures/security-resource-parameters';
const ref=(elementId:string)=>({documentId:'d',moduleId:'m',elementId});
test('nonkey resource ABAC requires explicit original field parameter layout',()=>{
 const input=request();expect(lowerSecurityRowPredicate(input)).toContain('$2 OPERATOR(pg_catalog.=) TRUE');
 const missing=request();missing.resourceFieldParameters=[];expect(()=>lowerSecurityRowPredicate(missing)).toThrow();
 for(const fields of [[ref('active'),ref('active')],[ref('id')],[ref('unknown')],Array(65).fill(ref('active'))]){const bad=request();bad.resourceFieldParameters=fields;expect(()=>lowerSecurityRowPredicate(bad)).toThrow();}
});
test('resource field slots follow a separately declared row discriminator',()=>{
 const input:any=request();input.types[0].discriminator={column:'type_id',carrier:'int8',value:'42'};input.resourceDiscriminatorParameter=2;
 const sql=lowerSecurityRowPredicate(input);expect(sql).toContain('$2 OPERATOR(pg_catalog.=)');expect(sql).toContain('$3 OPERATOR(pg_catalog.=) TRUE');
});
