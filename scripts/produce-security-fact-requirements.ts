// SPDX-License-Identifier: MIT OR Apache-2.0
/** Original UMF dependency producer fixture; no authenticated production handoff. */
import {securityPolicyDependencies} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/dependencies';
import {securityFixture} from '/Users/erik/.codex/worktrees/security-main-integration/umf/tests/security/fixture';
const fixture=securityFixture();
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const policy=JSON.stringify(fixture.policy)+'\n',resolution=JSON.stringify(fixture.resolution)+'\n';
const dependencies=securityPolicyDependencies(fixture.policy,fixture.resolution);
if(JSON.stringify(fixture.policy)+'\n'!==policy||JSON.stringify(fixture.resolution)+'\n'!==resolution)throw Error('Original semantic input changed');
const owner=Bun.spawnSync(['git','-C','/Users/erik/.codex/worktrees/security-main-integration/umf','rev-parse','HEAD']);if(owner.exitCode)throw Error('Owner unavailable');
const artifact={kind:'truss-security-fact-requirements-fixture/0.1',policySha256:hash(policy),resolutionSha256:hash(resolution),dependencies};
const base='docs/helix/04-build/evidence/security-fact-requirements';
await Bun.write(base+'/policy.json',policy);await Bun.write(base+'/resolution.json',resolution);
await Bun.write(base+'/requirements.json',JSON.stringify(artifact)+'\n');
await Bun.write(base+'/owner.json',JSON.stringify({ownerCommit:new TextDecoder().decode(owner.stdout).trim(),scope:'Actual UMF0.1 securityPolicyDependencies over original conformance fixture only. Neither authenticated issuer nor physical provider qualification.',policySha256:hash(policy),resolutionSha256:hash(resolution),requirementsSha256:hash(JSON.stringify(artifact)+'\n')},null,2)+'\n');
