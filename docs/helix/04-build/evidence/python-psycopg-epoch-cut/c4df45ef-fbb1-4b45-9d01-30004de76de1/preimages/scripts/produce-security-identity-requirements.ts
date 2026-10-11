/** Original owner identity/endpoint fixture closure; no issuer authority. */
import {securityIdentityTransportDependencies} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/dependencies';
import {securityFixture} from '/Users/erik/.codex/worktrees/security-main-integration/umf/tests/security/fixture';
const f=securityFixture();const policy=JSON.stringify(f.policy)+'\n',resolution=JSON.stringify(f.resolution)+'\n';
const transport=securityIdentityTransportDependencies(f.policy,f.resolution);
if(JSON.stringify(f.policy)+'\n'!==policy||JSON.stringify(f.resolution)+'\n'!==resolution)throw Error('Original identity input changed');
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const artifact={kind:'truss-security-fact-requirements-fixture/0.1',policySha256:hash(policy),resolutionSha256:hash(resolution),dependencies:{fields:transport.fields,associations:transport.associations}};
const base='docs/helix/04-build/evidence/security-identity-requirements';
for(const [name,value] of [['policy',policy],['resolution',resolution],['requirements',JSON.stringify(artifact)+'\n'],['transport',JSON.stringify(transport)+'\n']] as const)await Bun.write(base+'/'+name+'.json',value);
const owner=Bun.spawnSync(['git','-C','/Users/erik/.codex/worktrees/security-main-integration/umf','rev-parse','HEAD']);if(owner.exitCode)throw Error('Original owner unavailable');
await Bun.write(base+'/owner.json',JSON.stringify({ownerCommit:new TextDecoder().decode(owner.stdout).trim(),producer:'securityIdentityTransportDependencies',policySha256:hash(policy),resolutionSha256:hash(resolution),requirementsSha256:hash(JSON.stringify(artifact)+'\n'),transportSha256:hash(JSON.stringify(transport)+'\n'),scope:'Original security0.1/core0.8 fixture identity/endpoint closure. Not authenticated issuer or physical mapping qualification.'},null,2)+'\n');
