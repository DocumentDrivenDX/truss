// SPDX-License-Identifier: MIT OR Apache-2.0
// Test-only original owner oracle. This subprocess is not a Truss runtime sidecar.
const root=process.env.UMF_OWNER_ROOT??'/Users/erik/.codex/worktrees/0ede/umf';
const owner=await import(root+'/src/index.ts');
const input=JSON.parse(await Bun.stdin.text());
const preparation=owner.prepareActionPlanModel(input.pin,input.action,{registry:owner.createUmfRegistry(),models:[{pin:input.pin,artifact:input.model}],actions:[{pin:input.action,artifact:input.model}],selections:[]});
console.log(JSON.stringify(preparation));
