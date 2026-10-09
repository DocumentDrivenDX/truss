import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
if(!process.argv[2])throw new Error('Provide the installed Ajv Draft 2020-12 module path.');
const Ajv=require(process.argv[2]).default;
const root='docs/helix/02-design/contracts/';
const ajv=new Ajv({strict:true});
for(const name of ['acceptance-input-v0.1.schema.json','conformance-case-inputs-v0.1.proposal.schema.json'])
 ajv.addSchema(JSON.parse(readFileSync(root+name,'utf8')));
const validate=ajv.compile(JSON.parse(readFileSync(root+'conformance-case-fixtures-v0.1.proposal.schema.json','utf8')));
const pin={identity:'shape-only',version:'0.1',sha256:'0'.repeat(64)};
const artifact={identity:'shape-only',bytesBase64:'',sha256:'0'.repeat(64)};
const base={interfaceVersion:'truss-conformance-case-fixtures/0.1.0',caseId:'shape',registry:artifact,grammarProfile:pin,
 profiles:{installation:pin,catalog:pin,configuration:pin,authority:pin,resource:pin,setup:pin,startingInventory:pin},
 startingInventory:artifact,steps:[]};
function check(name:string,expected:boolean,change:(x:any)=>void){const x=structuredClone(base);change(x);if(Boolean(validate(x))!==expected)throw new Error(name+': '+JSON.stringify(validate.errors));}
check('explicit no setup',true,()=>{});
check('missing setup inventory',false,x=>delete x.steps);
check('missing starting state',false,x=>delete x.startingInventory);
check('missing authority',false,x=>delete x.profiles.authority);
check('executable fixture',false,x=>x.command='SELECT 1');
check('credential member',false,x=>x.profiles.password='secret');
check('registered setup shape',true,x=>x.steps=[{label:'setup',operation:'installFresh',operationProfile:pin,input:artifact,scope:{kind:'none'},observationProfile:pin}]);
check('setup missing input',false,x=>x.steps=[{label:'setup',operation:'installFresh',operationProfile:pin,scope:{kind:'none'},observationProfile:pin}]);
console.log('8 fixture shape controls passed. Starting inventory completeness and native setup remain unqualified.');
