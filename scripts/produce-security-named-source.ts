/** Exact shared named source packet; source correspondence, not issuer authority. */
import {namedSecurityFixture} from './security-named-source-fixture';
import {securityIdentityTransportDependencies} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/dependencies';
const model=namedSecurityFixture();
const policy=JSON.stringify(model.policy)+'\n',resolution=JSON.stringify(model.resolution)+'\n';
const document=JSON.stringify(model.resolution.documents[0]!.document)+'\n';
const transport=securityIdentityTransportDependencies(model.policy,model.resolution);
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const requirements={kind:'truss-security-fact-requirements-fixture/0.1',policySha256:hash(policy),resolutionSha256:hash(resolution),dependencies:{fields:transport.fields,associations:transport.associations}};
const request=await Bun.file('packages/python/tests/fixtures/security-mapping-request.json').json();
request.modules[0].documentJson=document;
request.modules[0].pin={...request.modules[0].pin,revision:'named-schema-1',sha256:hash(document)};
request.policyJson=policy;request.ontologyJson=JSON.stringify(model.resolution.ontology)+'\n';
const profile=JSON.parse(request.queryProfileJson);
request.sql='SELECT r.resourceId FROM Resource r';
profile.bindings=[];
profile.modelPins=[request.modules[0].pin];profile.policySha256=hash(policy);profile.ontologySha256=hash(request.ontologyJson);
request.queryProfileJson=JSON.stringify(profile);
const base='docs/helix/04-build/evidence/security-named-source-profile';
for(const [name,value] of [['document',document],['policy',policy],['resolution',resolution],['transport',JSON.stringify(transport)+'\n'],['requirements',JSON.stringify(requirements)+'\n'],['mapping-request',JSON.stringify(request)+'\n']] as const)
 await Bun.write(base+'/'+name+'.json',value);
console.log(JSON.stringify({scope:'Separately authored shared named fixture source; no native admission',documentSha256:hash(document),policySha256:hash(policy),resolutionSha256:hash(resolution)}));
