// C9: reading AGE property values from TypeScript/JavaScript runtimes without precision loss?
// Runs under Node 22 (pg + AGE's own pg-age driver built from PG18/v1.8.0-rc0) and under Bun.
// Usage: node c9_client.mjs | bun c9_client.mjs
import pg from './pg-age-src/node_modules/pg/lib/index.js';
import ageMod from './pg-age-src/dist/index.js';
const { setAGETypes } = ageMod.default ?? ageMod;

const runtime = typeof Bun !== 'undefined' ? `bun ${Bun.version}` : `node ${process.version}`;
const conn = { host: process.env.PGHOST, port: Number(process.env.PGPORT), user: 'postgres', database: 'postgres' };
const Q = `SELECT * FROM cypher('fid', $$
  RETURN 9223372036854775807 AS imax, 9007199254740993 AS i2p53p1,
         '12345678901234567890.123456789'::numeric AS dnum, '0.10'::numeric AS scale,
         0.1 AS flt, {nested: {big: 9223372036854775807, dec: '0.10'::numeric}} AS m
$$) AS (imax agtype, i2p53p1 agtype, dnum agtype, scale agtype, flt agtype, m agtype)`;

const show = (label, row) => {
  const out = {};
  for (const [k, v] of Object.entries(row)) {
    const val = v instanceof Map ? Object.fromEntries([...v].map(([a, b]) => [a, b instanceof Map ? Object.fromEntries(b) : b])) : v;
    out[k] = { type: typeof v === 'object' && v !== null ? v.constructor.name : typeof v, value: val };
  }
  console.log(label, JSON.stringify(out, (_, x) => (typeof x === 'bigint' ? `${x}n` : x)));
};

async function main() {
  console.log('runtime:', runtime);
  // 1. plain pg, no AGE type parser: agtype has no built-in parser, so values arrive as text
  const c1 = new pg.Client(conn); await c1.connect();
  await c1.query(`LOAD 'age'; SET search_path = ag_catalog, "$user", public;`);
  const r1 = await c1.query(Q);
  show('[pg default]', r1.rows[0]);
  // the obvious next step an application takes on text agtype: JSON.parse
  const jp = {};
  for (const [k, v] of Object.entries(r1.rows[0])) { try { jp[k] = JSON.parse(v); } catch (e) { jp[k] = `JSON.parse error: ${e.message}`; } }
  console.log('[pg default + JSON.parse]', JSON.stringify(jp));
  await c1.end();

  // 2. AGE's own Node driver (pg-age) type parser
  const c2 = new pg.Client(conn); await c2.connect();
  await c2.query(`LOAD 'age'; SET search_path = ag_catalog, "$user", public;`);
  await setAGETypes(c2, pg.types);
  const r2 = await c2.query(Q);
  show('[pg-age driver]', r2.rows[0]);
  // 3. writing a big integer and an exact decimal back through a parameter map
  const params = `{"big": 9223372036854775807, "dec": 12345678901234567890.123456789, "decAnnotated": 12345678901234567890.123456789::numeric}`;
  const r3 = await c2.query(`SELECT * FROM cypher('fid', $$ RETURN $big, $dec, $decAnnotated $$, $1) AS (big agtype, dec agtype, deca agtype)`, [params]);
  show('[pg-age write via param map]', r3.rows[0]);
  let jsonStringifyBigInt;
  try { JSON.stringify({ big: 9223372036854775807n }); jsonStringifyBigInt = 'ok'; } catch (e) { jsonStringifyBigInt = `error: ${e.message}`; }
  console.log('[JSON.stringify of a BigInt param]', jsonStringifyBigInt);
  await c2.end();
}
main().catch((e) => { console.error('FAILED', e); process.exit(1); });
