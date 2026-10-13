import {createOrdinarySubjectKeyBinding} from '/private/tmp/truss-security-main-integration/packages/pg-runtime/src/subject-key.ts';
import * as owner from '/private/tmp/truss-security-main-integration/packages/python/src/truss/_umf_keys08/producer.js';
const base=JSON.parse(JSON.parse(await Bun.file('/private/tmp/truss-security-main-integration/packages/python/tests/fixtures/security-mapping-request.json').text()).modules[0].documentJson);
base.modules[0].elements[0].name='SENTINEL';
const observation=Object.freeze({version:'truss.native.subject-observation/0.1' as const,principal:'alice',keyColumns:Object.freeze(['id']),keyValues:Object.freeze(['alice']),keyHex:Object.freeze(['616c696365'])});
const output=[];
for(const scalar of ['\ud800','\udfff','\ufffd']){
 const sourceText=JSON.stringify(base).replace('SENTINEL',scalar);
 try{const r=createOrdinarySubjectKeyBinding({host:{observeOrdinarySubject(){return observation;}},owner,sourceText,identity:{module:'m',element:'Staff',key:'pk'},keyColumns:['id'],encodings:['string']}).encode({} as any);output.push({scalarCode:scalar.charCodeAt(0),status:'accepted',sourceSha256:r.sourceSha256,retainedScalarCode:JSON.parse(r.originalReceiptText).source.modules[0].elements[0].name.charCodeAt(0)});}catch(e){output.push({scalarCode:scalar.charCodeAt(0),status:'refused',error:String(e)});}
}
console.log(JSON.stringify(output,null,2));
