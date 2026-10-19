// SPDX-License-Identifier: MIT OR Apache-2.0
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

test('selected resource layouts reject null and malformed native mapping',()=>{
 const nil:any=request();nil.resourceFieldParameters=null;nil.logicalPlan.rules[0].condition={literal:true};expect(()=>lowerSecurityRowPredicate(nil)).toThrow();
 for(const column of ['', 'bad\0column', 'x'.repeat(64)]){const bad=request();bad.types[0]!.fields[1]!.column=column;expect(()=>lowerSecurityRowPredicate(bad)).toThrow();}
 const duplicate=request();duplicate.types[0]!.fields.push({...duplicate.types[0]!.fields[1]!});expect(()=>lowerSecurityRowPredicate(duplicate)).toThrow();
});
test('resource argument order is explicit and cannot be inferred from field mapping order',()=>{
 const input=request();input.types[0]!.fields.push({ref:ref('other'),column:'other'});input.resourceFieldParameters=[ref('other'),ref('active')];expect(lowerSecurityRowPredicate(input)).toContain('$3 OPERATOR(pg_catalog.=) TRUE');
 input.resourceFieldParameters.reverse();expect(lowerSecurityRowPredicate(input)).toContain('$2 OPERATOR(pg_catalog.=) TRUE');
});
