/** Host-only routine carrier composition probe; complete transaction rolled back. */
import {readFile,writeFile} from 'node:fs/promises';
import {decodeNativeRoutineCarriers} from '../packages/postgresql/src/index';
const source=new URL('../docs/helix/02-design/contracts/bindings/bootstrap-routine-observation-pg17.proposal.sql',import.meta.url);
const originalQuery=await readFile(source,'utf8');
const query=originalQuery.replace('$1::pg_catalog.oid',"(SELECT oid FROM pg_catalog.pg_namespace WHERE oid=pg_my_temp_schema())").replace(/;\s*$/,'');
const sql=`BEGIN;
CREATE TEMP TABLE truss_routine_probe_marker(id integer);
CREATE FUNCTION pg_temp.truss_routine_probe(x integer,y text) RETURNS text LANGUAGE sql SET search_path='pg_catalog' AS $$ SELECT y $$;
WITH observed AS (${query}) SELECT json_agg(json_build_object(
'originalCatalogRowJson', original_catalog_row_json,
'inputCount',original_catalog_row_json::jsonb->>'pronargs',
'inputTypesText',proargtypes_native_vector_text,'inputTypesDimensions',proargtypes_native_vector_dimensions,
'names',json_build_object('text',proargnames_native_text,'dimensions',proargnames_native_dimensions,'rawJson',(original_catalog_row_json::jsonb->'proargnames')::text),
'modes',json_build_object('text',proargmodes_native_text,'dimensions',proargmodes_native_dimensions,'rawJson',(original_catalog_row_json::jsonb->'proargmodes')::text),
'settings',json_build_object('text',proconfig_native_text,'dimensions',proconfig_native_dimensions,'rawJson',(original_catalog_row_json::jsonb->'proconfig')::text))) FROM observed;
ROLLBACK;`;
const process=Bun.spawnSync(['/usr/local/bin/docker','exec','ashlar-e2e-truss-pg17','psql','-U','postgres','-d','truss_e2e','-v','ON_ERROR_STOP=1','-X','-q','-A','-t','-c',sql]);
if(process.exitCode!==0)throw Error(new TextDecoder().decode(process.stderr));
const originalStdout=new TextDecoder('utf-8',{fatal:true}).decode(process.stdout);
const rows=JSON.parse(originalStdout);
if(!Array.isArray(rows)||rows.length!==1)throw Error('Incomplete probe routine scope');
const decoded=rows.map(row=>decodeNativeRoutineCarriers(row,{maxBytes:16384,maxNodes:256,maxDepth:6,maxTokens:128}));
if(JSON.stringify(decoded[0].inputTypes.tokens)!==JSON.stringify(['23','25']) ||
 JSON.stringify(decoded[0].names.kind==='array'?decoded[0].names.elements:null)!==JSON.stringify(['x','y']))throw Error('Actual probe signature mismatch');
await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/native-routine.json',import.meta.url),JSON.stringify({
 sourceQuerySha256:new Bun.CryptoHasher('sha256').update(originalQuery).digest('hex'),sql,originalStdout,decoded,
 qualification:'Original proposal query executed for one temporary routine on local PostgreSQL 17.9. Input vector bounds/count and text names/modes/settings JSON correspond. Full raw catalog row retained opaque; other fields, authority, implicit dependencies, full collector budget/cut and Truss installation unqualified. Probe rolled back.'},null,2)+'\n');
console.log('Native routine carrier composition passes; probe rolled back.');
