/** Host-only temporary native catalog probe; transaction always rolled back. */
import {decodeNativeTriggerArguments} from '../packages/postgresql/src/index';
import {writeFile} from 'node:fs/promises';
const sql = `BEGIN;
CREATE TEMP TABLE truss_tgargs_probe (id integer);
CREATE FUNCTION pg_temp.truss_tgargs_probe_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;
CREATE TRIGGER truss_tgargs_probe BEFORE INSERT ON truss_tgargs_probe FOR EACH ROW EXECUTE FUNCTION pg_temp.truss_tgargs_probe_fn('a','','é');
SELECT json_build_object('server_version',current_setting('server_version'),'encoding',current_setting('server_encoding'),'count',tgnargs::text,'hex',encode(tgargs,'hex'),'byteLength',octet_length(tgargs)::text) FROM pg_catalog.pg_trigger WHERE tgrelid='pg_temp.truss_tgargs_probe'::regclass;
ROLLBACK;`;
const result=Bun.spawnSync(['/usr/local/bin/docker','exec','ashlar-e2e-truss-pg17','psql','-U','postgres','-d','truss_e2e','-v','ON_ERROR_STOP=1','-X','-q','-A','-t','-c',sql]);
if(result.exitCode!==0) throw Error(new TextDecoder().decode(result.stderr));
const originalStdout=new TextDecoder('utf-8',{fatal:true}).decode(result.stdout);
const row=JSON.parse(originalStdout);
if(row.encoding!=='UTF8'||!row.server_version.startsWith('17.9 ')) throw Error('Unqualified native profile');
const decoded=decodeNativeTriggerArguments(row.count,row.hex,row.byteLength,{maxBytes:4096,maxArguments:64},row.encoding);
if(JSON.stringify(decoded.arguments)!==JSON.stringify(['a','','é'])) throw Error('Original argument mismatch');
await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/native-trigger.json',import.meta.url),JSON.stringify({sql,originalStdout,decoded,
qualification:'One actual temporary pg_trigger tgargs observation on local PostgreSQL 17.9 UTF8; entire probe rolled back. No Truss trigger installation, trigger definition/WHEN/dependency admission or complete native support.'},null,2)+'\n');
console.log('Original native trigger arguments match; probe rolled back.');
