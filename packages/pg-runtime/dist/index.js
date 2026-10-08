// @bun
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
  } else if (kind === "1" || kind === "2" || kind === "n") {
    if (offset !== frame.length)
      fail();
  } else if (kind === "E" || kind === "N") {
    const tags = new Set;
    let terminated = false;
    while (offset < frame.length) {
      const byte = frame[offset++];
      if (byte === 0) {
        terminated = true;
        break;
      }
      if (byte < 33 || byte > 126 || fields.length === limits.maxFields)
        fail();
      const tag = String.fromCharCode(byte);
      if (tags.has(tag))
        fail();
      tags.add(tag);
      const value = text();
      if (tag === "C" && !/^[0-9A-Z]{5}$/.test(value))
        fail();
      fields.push(Object.freeze({ tag, value }));
    }
    if (!terminated || !tags.has("C"))
      fail();
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

class ResponseIngress {
  limits;
  #header = new Uint8Array(5);
  #headerUsed = 0;
  #frame;
  #used = 0;
  #bytes = 0;
  #frames = 0;
  #failed = false;
  #columns;
  #phase = "start";
  #rowCount = 0n;
  #parsed = false;
  #bound = false;
  constructor(limits) {
    this.limits = limits;
    if (![limits.maxFrameBytes, limits.maxFields, limits.maxTotalBytes, limits.maxFrames].every((n) => Number.isSafeInteger(n) && n >= 0))
      throw Error("pg-ingress:invalid-limits");
    this.limits = Object.freeze({ ...limits });
  }
  feed(chunk, forward) {
    if (this.#failed)
      throw Error("pg-ingress:refused");
    try {
      if (this.#phase === "ended" && chunk.length)
        throw Error("pg-ingress:ended");
      if (chunk.length > this.limits.maxTotalBytes - this.#bytes)
        throw Error("pg-ingress:byte-limit");
      this.#bytes += chunk.length;
      let at = 0;
      while (at < chunk.length) {
        if (!this.#frame) {
          const take = Math.min(5 - this.#headerUsed, chunk.length - at);
          this.#header.set(chunk.subarray(at, at + take), this.#headerUsed);
          this.#headerUsed += take;
          at += take;
          if (this.#headerUsed < 5)
            continue;
          let size = 0n;
          for (let i = 1;i < 5; i++)
            size = size * 256n + BigInt(this.#header[i]);
          if (size < 4n || size + 1n > BigInt(this.limits.maxFrameBytes) || this.#frames === this.limits.maxFrames)
            throw Error("pg-ingress:frame-limit");
          if (![84, 68, 67, 90, 69, 78, 49, 50, 110].includes(this.#header[0]))
            throw Error("pg-ingress:unsupported-kind");
          this.#frame = new Uint8Array(Number(size) + 1);
          this.#frame.set(this.#header);
          this.#used = 5;
          this.#headerUsed = 0;
        }
        const take = Math.min(this.#frame.length - this.#used, chunk.length - at);
        this.#frame.set(chunk.subarray(at, at + take), this.#used);
        this.#used += take;
        at += take;
        if (this.#used === this.#frame.length) {
          const decoded = decodeResponseFrame(this.#frame, this.limits);
          if (decoded.kind === "1") {
            if (this.#phase !== "start" || this.#parsed)
              throw Error("pg-ingress:response-order");
            this.#parsed = true;
          } else if (decoded.kind === "2") {
            if (this.#phase !== "start" || !this.#parsed || this.#bound)
              throw Error("pg-ingress:response-order");
            this.#bound = true;
          } else if (decoded.kind === "n") {
            if (this.#phase !== "start" || !this.#bound)
              throw Error("pg-ingress:response-order");
            this.#phase = "rows";
          } else if (decoded.kind === "T") {
            if (this.#phase !== "start" || this.#parsed !== this.#bound)
              throw Error("pg-ingress:response-order");
            this.#phase = "rows";
            if (decoded.fields.some((field) => field.format !== "0"))
              throw Error("pg-ingress:binary-unqualified");
            this.#columns = decoded.fields.length;
          } else if (decoded.kind === "D") {
            if (this.#phase !== "rows" || this.#columns === undefined || decoded.fields.length !== this.#columns)
              throw Error("pg-ingress:row-description");
            this.#rowCount++;
            for (const field of decoded.fields) {
              if (field.hex === null)
                continue;
              const bytes = new Uint8Array(field.hex.length / 2);
              for (let i = 0;i < bytes.length; i++)
                bytes[i] = parseInt(field.hex.slice(i * 2, i * 2 + 2), 16);
              new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
            }
          } else if (decoded.kind === "C") {
            if (this.#phase !== "start" && this.#phase !== "rows")
              throw Error("pg-ingress:response-order");
            const command = decoded.fields[0].command;
            if (command?.startsWith("SELECT ") && (decoded.fields[0].affectedRows === null || BigInt(decoded.fields[0].affectedRows) !== this.#rowCount))
              throw Error("pg-ingress:row-count");
            this.#phase = "command";
          } else if (decoded.kind === "E") {
            if (this.#phase !== "start" && this.#phase !== "rows")
              throw Error("pg-ingress:response-order");
            this.#phase = "error";
          } else if (decoded.kind === "N") {
            if (this.#phase === "ended")
              throw Error("pg-ingress:response-order");
          } else if (decoded.kind === "Z") {
            if (this.#phase !== "command" && this.#phase !== "error")
              throw Error("pg-ingress:response-order");
            this.#columns = undefined;
            this.#phase = "ended";
          }
          this.#frames++;
          const original = this.#frame;
          this.#frame = undefined;
          this.#used = 0;
          forward(original);
        }
      }
    } catch (error) {
      this.#failed = true;
      throw error;
    }
  }
  finish() {
    if (this.#failed || this.#headerUsed || this.#frame || this.#phase !== "ended") {
      this.#failed = true;
      throw Error("pg-ingress:incomplete");
    }
  }
  get accounting() {
    return Object.freeze({ bytes: this.#bytes, frames: this.#frames, refused: this.#failed });
  }
}

// packages/pg-runtime/src/native-query.ts
async function originalQuery(client, text, values) {
  const connection = client.connection;
  const stream = connection?.stream;
  if (!stream)
    throw Error("Original transport unavailable");
  const handlers = stream.listeners("data");
  if (handlers.length !== 1)
    throw Error("Unsupported original parser composition");
  const originalParser = handlers[0];
  const limits = { maxFrameBytes: 1048576, maxFields: 2048, maxTotalBytes: 4194304, maxFrames: 1e4 };
  const ingress = new ResponseIngress(limits);
  const frames = [];
  let resolveReady = () => {};
  let rejectReady = () => {};
  const ready = new Promise((resolve, reject) => {
    resolveReady = resolve;
    rejectReady = reject;
  });
  const observedReady = ready.then(() => ({ ok: true }), (error) => ({ ok: false, error }));
  const timeout = setTimeout(() => {
    const error = Error("Original response deadline");
    rejectReady(error);
    stream.destroy(error);
  }, 5000);
  const guarded = (chunk) => {
    try {
      ingress.feed(chunk, (frame) => {
        const decoded = decodeResponseFrame(frame, limits);
        frames.push(decoded);
        originalParser.call(stream, Buffer.from(frame));
        if (decoded.kind === "Z")
          resolveReady();
      });
    } catch {
      const error = Error("Original response refused");
      rejectReady(error);
      stream.destroy(error);
    }
  };
  const ended = () => rejectReady(Error("Original transport ended"));
  stream.removeListener("data", originalParser);
  stream.on("data", guarded);
  stream.once("close", ended);
  let failed = false;
  let failure;
  try {
    try {
      await client.query({ text, values: values ? [...values] : undefined, rowMode: "array" });
    } catch (error) {
      failed = true;
      failure = error;
    }
    const observed = await observedReady;
    if (!observed.ok)
      throw observed.error;
    ingress.finish();
    const errors = frames.filter((frame) => frame.kind === "E");
    if (failed) {
      const code = failure && typeof failure === "object" ? Object.getOwnPropertyDescriptor(failure, "code")?.value : undefined;
      if (errors.length !== 1 || errors[0].fields.find((field) => field.tag === "C")?.value !== code)
        throw Error("Original error correspondence unavailable");
      throw failure;
    }
    if (errors.length)
      throw Error("Original error lost by driver");
    return Object.freeze(frames);
  } finally {
    clearTimeout(timeout);
    stream.off("data", guarded);
    stream.off("close", ended);
    if (!stream.destroyed)
      stream.on("data", originalParser);
  }
}
function requireOriginalCompletion(frames, status, command) {
  const ready = frames.filter((frame) => frame.kind === "Z"), commands = frames.filter((frame) => frame.kind === "C");
  if (ready.length !== 1 || ready[0].fields[0].status !== status || commands.length !== 1 || command && commands[0].fields[0].command !== command)
    throw Error("Original transaction completion mismatch");
}

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
      const frames = await originalQuery(client, sql);
      try {
        requireOriginalCompletion(frames, sql === "COMMIT" || sql === "ROLLBACK" ? "I" : "T", expected);
      } catch (error) {
        quarantine.add(client);
        throw error;
      }
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
        const frames = await originalQuery(client, statement.sql, statement.parameters.map((p) => p.carrier === "null" ? null : p.text));
        try {
          requireOriginalCompletion(frames, "T");
        } catch (error) {
          quarantine.add(client);
          throw error;
        }
        const descriptions = frames.filter((frame) => frame.kind === "T"), commands = frames.filter((frame) => frame.kind === "C");
        if (descriptions.length > 1 || commands.length !== 1)
          throw Error("Unsupported original response inventory");
        const original = commands[0].fields[0];
        const command = original.command.split(" ")[0];
        const noCount = original.affectedRows === null && ["CREATE", "DROP", "ALTER", "SET", "GRANT", "REVOKE", "COMMENT"].includes(command);
        if (original.affectedRows === null && !noCount)
          throw Error("Unknown original command count");
        const rows = frames.filter((frame) => frame.kind === "D").map((frame) => frame.fields.map((field) => {
          if (field.hex === null)
            return { state: "null" };
          return { state: "text", text: new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(Buffer.from(field.hex, "hex")) };
        }));
        return { columns: descriptions[0]?.fields.map((field) => field.name) ?? [], rows, affectedRows: noCount ? "0" : original.affectedRows, command };
      },
      async control(sql) {
        if (!/^((SAVEPOINT|RELEASE SAVEPOINT|ROLLBACK TO SAVEPOINT) truss_sp_[1-9][0-9]*)$/.test(sql))
          throw Error("Unregistered control SQL");
        await control(sql, sql.startsWith("SAVEPOINT ") ? "SAVEPOINT" : sql.startsWith("RELEASE ") ? "RELEASE" : "ROLLBACK");
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
  ResponseIngress,
  createPgConnectionSource,
  decodeResponseFrame
};
