// C9 addendum: Bun's built-in PostgreSQL client (Bun.sql) reading agtype with default parsing.
import { SQL } from "bun";
const sql = new SQL({ hostname: "127.0.0.1", port: Number(process.env.PGPORT), max: 1, username: "postgres", database: "postgres" });
await sql.unsafe(`LOAD 'age'`);
await sql.unsafe(`SET search_path = ag_catalog, "$user", public`);
const rows = await sql.unsafe(`SELECT * FROM cypher('fid', $$ RETURN 9223372036854775807 AS imax, '0.10'::numeric AS scale, {big: 9223372036854775807} AS m $$) AS (imax agtype, scale agtype, m agtype)`);
for (const [k, v] of Object.entries(rows[0])) console.log(`[Bun.sql ${Bun.version}] ${k}: typeof=${typeof v} value=${String(v)}`);
await sql.close();
