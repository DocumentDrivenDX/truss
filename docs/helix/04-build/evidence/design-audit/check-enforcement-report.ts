/** Wire shape only; native/database claims are deliberately unqualified fixtures. */
import {readFileSync} from 'node:fs';
const path=process.argv[2];if(!path)throw Error('Pass installed Ajv Draft 2020-12 path');
const {default:Ajv}=await import(path);
const schema=JSON.parse(readFileSync(new URL('../../../02-design/contracts/enforcement-report-v0.1.schema.json',import.meta.url),'utf8'));
const validate=new Ajv({strict:true}).compile(schema);
const sha='a'.repeat(64),pin={identity:'fixture',version:'0.1.0',sha256:sha};
const assertion={sourceKind:'umf_document',owner:{documentId:'doc',moduleId:'module'},definitionPin:'fixture',sourcePointer:'/rules/0',kind:'source',sourceIdentityProfile:pin};
const entry={assertion,source:{identity:'rule',bytesBase64:'e30=',sha256:sha},ruleName:'opaque rule',ruleNameOrigin:'profile_generated',enforcement:'none',reason:'opaque'};
const base={interfaceVersion:'truss-enforcement-report/0.1.0',catalogRevision:'1',reportProfile:pin,layoutProfile:pin,scope:{kind:'complete'},assertionInventorySha256:sha,entries:[entry]};
const {reason,...common}=entry;
const engine={...common,enforcement:'engine',validatorProfile:pin,qualificationReceiptSha256:sha};
const database={...common,enforcement:'database',procedureProfile:pin,qualificationReceiptSha256:sha,installedInventorySha256:sha,currentObservationEvidenceSha256:sha,qualifiedWritePaths:['canonical_dml']};
const cases:readonly [string,unknown,boolean][]=[
 ['storage binding assertion',{...base,entries:[{...entry,assertion:{...assertion,sourceKind:'truss_binding'}}]},true],
 ['missing source kind',{...base,entries:[{...entry,assertion:{...assertion,sourceKind:undefined}}]},false],
 ['wrong source kind needs archive admission refusal',{...base,entries:[{...entry,assertion:{...assertion,sourceKind:'truss_binding',sourcePointer:'/umf/keys/0'}}]},true],
 ['opaque source preserved',base,true],
 ['engine candidate',{...base,entries:[engine]},true],
 ['database candidate needs trusted qualification',{...base,entries:[database]},true],
 ['authored identity',{...base,entries:[{...entry,assertion:{sourceKind:'umf_document',owner:assertion.owner,definitionPin:'fixture',sourcePointer:'/rules/0',kind:'authored',authoredIdentity:'rule-id'}}]},true],
 ['projection',{...base,scope:{kind:'authorized_projection',authorizedScopeIdentity:'scope'}},true],
 ['database empty writer paths',{...base,entries:[{...database,qualifiedWritePaths:[]}]},false],
 ['none with stray qualification',{...base,entries:[{...entry,qualificationReceiptSha256:sha}]},false],
 ['missing rule name',{...base,entries:[{assertion,source:entry.source,ruleNameOrigin:'profile_generated',enforcement:'none',reason:'opaque'}]},false],
 ['unknown enforcement',{...base,entries:[{...entry,enforcement:'trigger_declared'}]},false],
 ['duplicate assertion needs semantic rejection',{...base,entries:[entry,entry]},true],
 ['unproved empty inventory',{...base,entries:[]},true],
 ['changed source digest requires semantic rejection',{...base,entries:[{...entry,source:{...entry.source,sha256:'b'.repeat(64)}}]},true]
];
const outcomes=cases.map(([name,input,expected])=>{const actual=Boolean(validate(input));if(actual!==expected)throw Error(name);return {name,expected,actual}});
console.log(JSON.stringify({scope:'Enforcement report shape only; no assertion inventory, provenance, evidence trust or native qualification',cases:outcomes.length,outcomes},null,2));
