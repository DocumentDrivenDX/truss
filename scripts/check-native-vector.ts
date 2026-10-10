/** Host-only narrow read-only PostgreSQL 17 vector-output probe. */
import {decodeNativeVector} from '../packages/postgresql/src/index';
import {mkdir, writeFile} from 'node:fs/promises';
const sql = `SELECT json_build_object('server_version',current_setting('server_version'),'oid_empty', ''::oidvector::text,'oid_empty_dims', array_dims(''::oidvector),'oid_extremes','0 4294967295'::oidvector::text,'oid_dims',array_dims('0 4294967295'::oidvector),'int2_extremes','-32768 0 32767'::int2vector::text,'int2_dims',array_dims('-32768 0 32767'::int2vector));`;
const process = Bun.spawnSync(['/usr/local/bin/docker', 'exec', 'ashlar-e2e-truss-pg17', 'psql', '-U', 'postgres', '-d', 'truss_e2e', '-X', '-A', '-t', '-c', sql]);
if (process.exitCode !== 0) throw Error(new TextDecoder().decode(process.stderr));
const originalStdout = new TextDecoder('utf-8', {fatal: true}).decode(process.stdout);
const row = JSON.parse(originalStdout);
if (!row.server_version.startsWith('17.9 ') || row.oid_empty_dims !== '[0:-1]' ||
    row.oid_dims !== '[0:1]' || row.int2_dims !== '[0:2]') throw Error('Unqualified native output/dimensions');
const limits = {maxBytes: 1024, maxTokens: 64};
const decoded = [decodeNativeVector('oidvector', row.oid_empty, limits, '0'),
  decodeNativeVector('oidvector', row.oid_extremes, limits, '2'),
  decodeNativeVector('int2vector', row.int2_extremes, limits, '3')];
if (JSON.stringify(decoded.map(x => x.tokens)) !== JSON.stringify([[], ['0','4294967295'], ['-32768','0','32767']]))
  throw Error('Native value correspondence failed');
const output = new URL('../docs/helix/04-build/evidence/inert-assembly/native-vector.json', import.meta.url);
await mkdir(new URL('.', output), {recursive: true});
await writeFile(output, JSON.stringify({profile: 'truss-bootstrap-native-vector-decoder/0.1.0', sql, originalStdout, decoded,
  qualification: 'Three read-only constant vector observations on existing local PostgreSQL 17.9. No layout installation, catalog signature/index field semantics, complete native collector or database support qualification.'}, null, 2) + '\n');
console.log('Three native vector observations decoded; no mutations.');
