// SPDX-License-Identifier: MIT OR Apache-2.0
/** Private adjunct SQL retention, not core layout or installed authority. */
import {backend} from '/Users/erik/.codex/worktrees/security-main-integration/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/adapters/postgresql';
const source=await Bun.file('packages/postgresql/native/source-epoch-authority-reason-storage.sql').text();
const model=await importPostgresqlSql(source,backend,{id:'truss-authority-epoch-reason-adjunct-candidate'});
const serialized=JSON.stringify(model)+'\n';const ddl=await exportPostgresqlSql(model,backend);
if(await exportPostgresqlSql(readDocument(serialized,'json'),backend)!==ddl)throw Error('Reload/export mismatch');
await Bun.write('docs/helix/02-design/contracts/authority-epoch-reason-v0.1.proposal.umf.json',serialized);
await Bun.write('docs/helix/04-build/evidence/authority-epoch-reason.owner-export.sql',ddl);
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const owner=Bun.spawnSync(['git','-C','/Users/erik/.codex/worktrees/security-main-integration/umf','rev-parse','HEAD']);if(owner.exitCode)throw Error('Original owner revision unavailable');
await Bun.write('docs/helix/04-build/evidence/design-audit/authority-epoch-reason-owner.json',JSON.stringify({ownerCommit:new TextDecoder().decode(owner.stdout).trim(),scope:'Original owner SQL import and exact saved-model reload/export only; no core layout/installed authority/profile qualification',sourceSha256:hash(source),modelSha256:hash(serialized),ddlSha256:hash(ddl),reloadExact:true},null,2)+'\n');
