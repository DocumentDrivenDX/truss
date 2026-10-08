// @bun
// packages/pg-runtime/src/index.ts
import { Pool, DatabaseError } from "pg";

// packages/pg-runtime/src/wire.ts
function decodeResponseFrame(frame, limits) {
  const fail = () => {
    throw Error("pg-wire:unsupported-or-malformed");
  };
  if (![limits.maxFrameBytes, limits.maxFields].every((n) => Number.isSafeInteger(n) && n >= 0) || frame.length > limits.maxFrameBytes || frame.length < 5)
    fail();
  let offset = 1;
  const uint = (bytes) => {
    if (offset + bytes > frame.length)
      fail();
    let n = 0n;
    for (let i = 0;i < bytes; i++)
      n = n * 256n + BigInt(frame[offset++]);
    return n;
  };
  const length = uint(4);
  if (length < 4n || length + 1n !== BigInt(frame.length))
    fail();
  const text = () => {
    const start = offset;
    while (offset < frame.length && frame[offset] !== 0)
      offset++;
    if (offset === frame.length)
      fail();
    let value;
    try {
      value = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(frame.subarray(start, offset));
    } catch {
      return fail();
    }
    offset++;
    return value;
  };
  const signed = (n, bits) => n >= 1n << bits - 1n ? n - (1n << bits) : n;
  const hex = (bytes) => {
    let value = "";
    for (const byte of bytes)
      value += byte.toString(16).padStart(2, "0");
    return value;
  };
  const kind = String.fromCharCode(frame[0]);
  const fields = [];
  if (kind === "T") {
    const count = uint(2);
    if (count > BigInt(limits.maxFields) || count > 32767n)
      fail();
    for (let i = 0n;i < count; i++)
      fields.push(Object.freeze({ name: text(), tableOid: uint(4).toString(), attribute: signed(uint(2), 16n).toString(), typeOid: uint(4).toString(), typeSize: signed(uint(2), 16n).toString(), typeModifier: signed(uint(4), 32n).toString(), format: uint(2).toString() }));
    if (fields.some((field) => field.format !== "0" && field.format !== "1"))
      fail();
  } else if (kind === "D") {
    const count = uint(2);
    if (count > BigInt(limits.maxFields) || count > 32767n)
      fail();
    for (let i = 0n;i < count; i++) {
      const size = signed(uint(4), 32n);
      if (size === -1n) {
        fields.push(Object.freeze({ hex: null }));
        continue;
      }
      if (size < 0n || size > BigInt(frame.length - offset))
        fail();
      const end = offset + Number(size);
      fields.push(Object.freeze({ hex: hex(frame.subarray(offset, end)) }));
      offset = end;
    }
  } else if (kind === "C") {
    const command = text();
    const match = /^(SELECT|UPDATE|DELETE|MOVE|FETCH|COPY) (0|[1-9][0-9]*)$/.exec(command) || /^INSERT (?:0|[1-9][0-9]*) (0|[1-9][0-9]*)$/.exec(command);
    fields.push(Object.freeze({ command, affectedRows: match ? match[2] ?? match[1] : null }));
    if (command.startsWith("INSERT ")) {
      const parts = command.split(" ");
      if (parts.length !== 3 || !parts.every((p, i) => i === 0 || /^(0|[1-9][0-9]*)$/.test(p)))
        fail();
      fields[0] = Object.freeze({ command, affectedRows: parts[2] });
    }
  } else if (kind === "Z") {
    if (offset + 1 !== frame.length)
      fail();
    const status = String.fromCharCode(frame[offset++]);
    if (!["I", "T", "E"].includes(status))
      fail();
    fields.push(Object.freeze({ status }));
  } else
    fail();
  if (offset !== frame.length)
    fail();
  return Object.freeze({ kind, originalHex: hex(frame), fields: Object.freeze(fields) });
}

// packages/pg-runtime/src/index.ts
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
  createPgConnectionSource,
  decodeResponseFrame
};
