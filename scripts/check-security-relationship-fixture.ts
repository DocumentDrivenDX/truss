// SPDX-License-Identifier: MIT OR Apache-2.0
/** Original source validation only; no native admission or installation. */
import {validateDocument} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/validation/document';
import {inspectSecurityPolicy} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/policy';
import Ajv from '/Users/erik/.codex/worktrees/security-main-integration/umf/node_modules/ajv/dist/2020.js';
import {createHash} from 'node:crypto';
const root='docs/helix/03-test/fixtures/security-public-relationship/';
const document=await Bun.file(root+'document.json').json(),policy=await Bun.file(root+'policy.json').json(),resolution=await Bun.file(root+'resolution.json').json();
const core=validateDocument(document),semantic=inspectSecurityPolicy(policy,resolution);
const schemaPath='/private/tmp/weft-b008-traversal/docs/helix/02-design/contracts/security-query-profile-v0.2-candidate.schema.json';
const schema=await Bun.file(schemaPath).json();
const validate=new Ajv({strict:false}).compile(schema);
const profile=await Bun.file(root+'query-profile-template.json').json();
if(!core.valid||!core.complete||!semantic.valid||!semantic.complete||!validate(profile))throw Error(JSON.stringify({core,semantic:semantic.diagnostics,schema:validate.errors}));
const deniedPolicy=await Bun.file(root+'policy-observation-denied.json').json();
const deniedProfile=await Bun.file(root+'query-profile-observation-denied-template.json').json();
const denied=inspectSecurityPolicy(deniedPolicy,resolution);
if(!denied.valid||!denied.complete||!validate(deniedProfile))throw Error('Denied observation sources invalid');
for(const [selected,name] of [[profile,'policy'],[deniedProfile,'policy-observation-denied']] as const){
 const policyBytes=new Uint8Array(await Bun.file(root+name+'.json').arrayBuffer());
 const ontologyBytes=new Uint8Array(await Bun.file(root+'ontology.json').arrayBuffer());
 if(selected.policySha256!==createHash('sha256').update(policyBytes).digest('hex')||selected.ontologySha256!==createHash('sha256').update(ontologyBytes).digest('hex'))throw Error('Exact selected source byte hash mismatch');
}
const modules=await Bun.file(root+'modules.json').json();
if(modules[0].documentJson!==await Bun.file(root+'document.json').text())throw Error('Selected module source bytes differ');
const original=await Bun.file('docs/helix/04-build/evidence/security-named-source-profile/policy.json').json();
if(JSON.stringify(policy.rules.slice(0,-1))!==JSON.stringify(original.rules))throw Error('Original read rules changed');
if(JSON.stringify(deniedPolicy.rules)!==JSON.stringify(original.rules))throw Error('Denied variant changed original read rules');
const fields=['policy-observation-denied','query-profile-observation-denied-template','document','modules','ontology','policy','resolution','query-profile-template','source-manifest'];
const hashes:Record<string,string>={};
for(const field of fields){const path=root+field+'.json';hashes[path]=createHash('sha256').update(new Uint8Array(await Bun.file(path).arrayBuffer())).digest('hex');}
hashes[schemaPath]=createHash('sha256').update(new Uint8Array(await Bun.file(schemaPath).arrayBuffer())).digest('hex');
console.log(JSON.stringify({status:'source-validated-uninstalled-fixture',core,policy:{valid:semantic.valid,complete:semantic.complete,diagnostics:semantic.diagnostics},profileSchema:true,originalReadRulesUnchanged:true,sourceDigests:hashes,nativeCorrespondence:null,securityReady:false}));
