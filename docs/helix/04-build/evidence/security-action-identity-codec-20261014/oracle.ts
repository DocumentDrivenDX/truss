import {encodeReferenceIdentity} from '/Users/erik/.codex/worktrees/0ede/umf/scripts/actions-reference/codec.ts';
const rows=await Bun.file('/private/tmp/action-family-codec-oracle/inputs.json').json();
console.log(JSON.stringify(rows.map((pair:string[])=>({module:pair[0],action:pair[1],familyHex:Buffer.from(encodeReferenceIdentity(pair)).toString('hex'),roleHex:Buffer.from(encodeReferenceIdentity(pair[1])).toString('hex')}))));
