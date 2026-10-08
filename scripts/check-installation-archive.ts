import {SQL} from 'bun';
const url=process.env.TRUSS_WEFT_TEST_URL;if(!url)throw Error('Fresh isolated database URL required');
const sql=new SQL(url,{max:1});
const source='docs/helix/02-design/contracts/installation-archive-insert-v0.2.proposal.sql';
const statement=await Bun.file(source).text();
const ddl=await Bun.file('docs/helix/04-build/evidence/weft-integration-layout-0.13.owner-export.sql').text();
const identity='雪\\identity',bytes='00ff80';
const identityHash=new Bun.CryptoHasher('sha256').update(identity).digest('hex');
const contentHash=new Bun.CryptoHasher('sha256').update(Buffer.from(bytes,'hex')).digest('hex');
const stop=Error('intentional original transaction rollback');let rolledBack=false,missingMarkerRefused=false;
try {
 await sql.unsafe(ddl).simple();
 try {await sql.begin(async tx=>{
  const rows=await tx.unsafe(statement,['component','input',identity,bytes]);
  if(rows.length!==1||rows[0].artifact_identity_sha256!==identityHash||rows[0].artifact_sha256!==contentHash)throw Error('Original archive digest mismatch');
  throw stop;
 })}catch(error){if(error!==stop)throw error;rolledBack=true}
 try {await sql.begin(async tx=>{await tx.unsafe(statement,['component','input',identity,bytes])})}
 catch(error){if((error as any).errno!=='23503')throw error;missingMarkerRefused=true}
 const [remaining]=await sql.unsafe('SELECT count(*)::text AS count FROM truss.installation_archive');
 if(!rolledBack||!missingMarkerRefused||remaining.count!=='0')throw Error('Archive/marker atomic boundary failed');
 const receipt={statementSha256:new Bun.CryptoHasher('sha256').update(statement).digest('hex'),identityHash,contentHash,rolledBack,missingMarkerRefused,remainingRows:remaining.count,
  qualification:'Fresh isolated native body-component evidence: exact original digests, rollback and deferred marker FK. Not complete installer/authority/resource, ready marker or populated conversion.'};
 await Bun.write('docs/helix/04-build/evidence/installation-archive-insert-v0.2.native-component.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
}finally{await sql.close()}
