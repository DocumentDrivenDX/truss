/** Draft request shape only. No profile/authority/revision qualification. */
import {readFileSync} from 'node:fs';
const modulePath=process.argv[2]; if(!modulePath) throw Error('Pass installed Ajv Draft 2020-12 path');
const {default:Ajv}=await import(modulePath);
const schema=JSON.parse(readFileSync(new URL('../../../02-design/contracts/catalog-view-request-v0.1.schema.json',import.meta.url),'utf8'));
const validate=new Ajv({strict:true}).compile(schema);
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const base={interfaceVersion:'truss-catalog-view-request/0.1.0',layoutProfile:pin,viewProfile:pin,selection:{kind:'current'},scope:{kind:'complete'},limits:{definitionCount:'1000',encodedBytes:'16777216'}};
const owner={documentId:'d',moduleId:'m'};
const cases:readonly [string,unknown,boolean][]=[
 ['current',base,true],['historical',{...base,selection:{kind:'historical',catalogRevision:'0'}},true],
 ['missing historical revision',{...base,selection:{kind:'historical'}},false],
 ['zero budget',{...base,limits:{...base.limits,definitionCount:'0'}},false],
 ['empty projection',{...base,scope:{kind:'authorized_projection',owners:[]}},false],
 ['duplicate owners require semantic rejection',{...base,scope:{kind:'authorized_projection',owners:[owner,owner]}},true]
];
const outcomes=cases.map(([name,input,expected])=>{const actual=Boolean(validate(input));if(actual!==expected)throw Error(name);return {name,expected,actual}});
console.log(JSON.stringify({scope:'Draft request shape only; no ownership, profile, budget maximum or revision qualification',cases:outcomes.length,outcomes},null,2));
