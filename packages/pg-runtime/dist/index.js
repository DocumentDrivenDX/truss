// @bun
// packages/pg-runtime/src/index.ts
import { Pool, DatabaseError } from "pg";
function createPgConnectionSource(config) {
  const pool = new Pool({ ...config, types: { getTypeParser(_oid, format) {
    if (format === "binary")
      throw Error("Binary native carriers unsupported");
    return (text) => text;
  } } });
  const quarantine = new Set;
  const source = { async acquire() {
    const client = await pool.connect();
    let ended = false;
    let started = false;
    const alive = () => {
      if (ended || quarantine.has(client))
        throw Error("Original native connection unavailable");
    };
    const onError = () => {
      quarantine.add(client);
    };
    client.on("error", onError);
    const control = async (sql, expected) => {
      alive();
      const result = await client.query({ text: sql, rowMode: "array" });
      if (Array.isArray(result) || expected && result.command !== expected)
        throw Error("Native command correspondence");
    };
    const connection = {
      async begin(options) {
        alive();
        if (started)
          throw Error("Already begun");
        const isolation = { read_committed: "READ COMMITTED", repeatable_read: "REPEATABLE READ", serializable: "SERIALIZABLE" }[options.isolation];
        const mode = { read_only: "READ ONLY", read_write: "READ WRITE" }[options.accessMode];
        if (!isolation || !mode || options.cancellation)
          throw Error("Unsupported transaction options");
        await control("BEGIN ISOLATION LEVEL " + isolation + " " + mode, "BEGIN");
        started = true;
      },
      async execute(statement) {
        alive();
        if (!started)
          throw Error("Not begun");
        const result = await client.query({ text: statement.sql, values: statement.parameters.map((p) => p.carrier === "null" ? null : p.text), rowMode: "array" });
        if (Array.isArray(result))
          throw Error("Multiple native results unsupported");
        const noCount = result.rowCount === null && result.rows.length === 0 && ["CREATE", "DROP", "ALTER", "SET", "GRANT", "REVOKE", "COMMENT"].includes(result.command);
        if (!noCount && (result.rowCount === null || !Number.isSafeInteger(result.rowCount) || result.rowCount < 0))
          throw Error("Unsupported native count/result");
        const rows = result.rows.map((row) => row.map((value) => {
          if (value === null)
            return { state: "null" };
          if (typeof value !== "string")
            throw Error("Non-text native cell");
          return { state: "text", text: value };
        }));
        return { columns: result.fields.map((field) => field.name), rows, affectedRows: noCount ? "0" : String(result.rowCount), command: result.command };
      },
      async control(sql) {
        if (!/^((SAVEPOINT|RELEASE SAVEPOINT|ROLLBACK TO SAVEPOINT) truss_sp_[1-9][0-9]*)$/.test(sql))
          throw Error("Unregistered control SQL");
        await control(sql);
      },
      async commit() {
        try {
          await control("COMMIT", "COMMIT");
          started = false;
          return "committed";
        } catch (error) {
          if (!(error instanceof DatabaseError) || !error.code || !/^(23|40)[0-9A-Z]{3}$/.test(error.code))
            throw error;
          await control("ROLLBACK", "ROLLBACK");
          started = false;
          return { status: "rejected", sqlState: error.code };
        }
      },
      async rollback() {
        await control("ROLLBACK", "ROLLBACK");
        started = false;
        return "rolled_back";
      },
      async release() {
        alive();
        if (started)
          throw Error("Active connection cannot release");
        ended = true;
        client.off("error", onError);
        client.release();
      },
      async quarantine() {
        quarantine.add(client);
      }
    };
    return connection;
  } };
  return { source, quarantinedCount: () => quarantine.size, async close() {
    if (quarantine.size)
      throw Error("Original quarantined custody needs explicit settlement");
    await pool.end();
  } };
}
export {
  createPgConnectionSource
};
