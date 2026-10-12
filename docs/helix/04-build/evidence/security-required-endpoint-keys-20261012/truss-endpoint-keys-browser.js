(() => {
  // packages/postgresql/src/security-candidate-endpoint.ts
  var fail = () => {
    throw Error("TRUSS_SECURITY_CANDIDATE_ENDPOINT_UNSUPPORTED");
  };
  function object(v, names) {
    if (!v || typeof v !== "object" || Array.isArray(v) || ![Object.prototype, null].includes(Object.getPrototypeOf(v)))
      return fail();
    const d = Object.getOwnPropertyDescriptors(v);
    if (Reflect.ownKeys(d).length !== names.length || names.some((n) => !Object.hasOwn(d, n) || !Object.hasOwn(d[n], "value") || !d[n].enumerable))
      return fail();
    return Object.fromEntries(names.map((n) => [n, d[n].value]));
  }
  function text(v) {
    if (typeof v !== "string" || !v || v.length > 8192)
      return fail();
    let count = 0;
    for (const c of v) {
      const cp = c.codePointAt(0);
      if (++count > 4096 || cp === 0 || cp >= 55296 && cp <= 57343)
        return fail();
    }
    return v;
  }
  function reference(v, relationship = false) {
    const names = ["documentId", "moduleId", relationship ? "relationshipId" : "elementId"];
    const r = object(v, names);
    return Object.fromEntries(names.map((n) => [n, text(r[n])]));
  }
  function association(v) {
    if (!v || typeof v !== "object")
      return fail();
    return reference(v, Object.hasOwn(v, "relationshipId"));
  }
  function array(v) {
    if (!Array.isArray(v) || Object.getPrototypeOf(v) !== Array.prototype)
      return fail();
    const length = Object.getOwnPropertyDescriptor(v, "length")?.value;
    if (!Number.isSafeInteger(length) || length < 1 || length > 256 || Reflect.ownKeys(v).length !== length + 1)
      return fail();
    return Array.from({ length }, (_, i) => {
      const d = Object.getOwnPropertyDescriptor(v, String(i));
      if (!d || !Object.hasOwn(d, "value") || !d.enumerable)
        return fail();
      return d.value;
    });
  }
  function same(a, b) {
    return JSON.stringify(a) === JSON.stringify(b);
  }
  function refs(v) {
    const r = array(v).map((x) => reference(x));
    if (new Set(r.map((x) => JSON.stringify(x))).size !== r.length)
      return fail();
    return r;
  }
  function carrier(v, graph) {
    if (graph) {
      const r = object(object(v, ["incidence"]).incidence, ["side"]);
      if (!["source", "target"].includes(r.side))
        return fail();
      return { incidence: { side: r.side } };
    }
    return { members: { fields: refs(object(object(v, ["members"]).members, ["fields"]).fields) } };
  }
  function column(v) {
    const s = text(v);
    if (new TextEncoder().encode(s).length > 63)
      return fail();
    return s;
  }
  function freeze(v) {
    if (v && typeof v === "object") {
      for (const x of Object.values(v))
        freeze(x);
      Object.freeze(v);
    }
    return v;
  }
  function bindCandidateSecurityEndpoint(term, mapping) {
    const t = object(object(term, ["endpoint"]).endpoint, ["binding", "association", "role", "target", "keyId", "carrier"]);
    const slot = object(t.binding, ["variable"]).variable;
    if (!Number.isSafeInteger(slot) || slot < 0)
      return fail();
    const a = association(t.association), graph = Object.hasOwn(a, "relationshipId");
    const target = reference(t.target), role = text(t.role), keyId = text(t.keyId), c = carrier(t.carrier, graph);
    const m = object(mapping, ["association", "role", "target", "keyId", "targetKeyFields", "carrier", "columns"]);
    const ma = association(m.association), mt = reference(m.target), mc = carrier(m.carrier, graph), keys = refs(m.targetKeyFields), columns = array(m.columns).map(column);
    if (!same(a, ma) || !same(target, mt) || role !== text(m.role) || keyId !== text(m.keyId) || !same(c, mc) || keys.length !== columns.length || new Set(columns).size !== columns.length)
      return fail();
    if ("members" in c && c.members.fields.length !== keys.length)
      return fail();
    return freeze({ binding: { variable: slot }, association: a, role, target, keyId, targetKeyFields: keys, carrier: c, columns });
  }

  // packages/postgresql/src/security-graph-source.ts
  var issued = new WeakSet;
  var sourcePopulations = new WeakMap;
  var sourceKinds = new WeakMap;
  var fail2 = () => {
    throw Error("TRUSS_SECURITY_GRAPH_SOURCE_UNSUPPORTED");
  };
  function isCandidateGraphSource(source) {
    return typeof source === "object" && source !== null && issued.has(source);
  }
  function candidateGraphSourcePopulation(source) {
    requireCandidateGraphSource(source);
    return sourcePopulations.get(source) ?? fail2();
  }
  function requireCandidateGraphSource(source) {
    if (!issued.has(source))
      return fail2();
  }

  // packages/postgresql/src/security-candidate-condition.ts
  var fail3 = () => {
    throw Error("TRUSS_SECURITY_CANDIDATE_CONDITION_UNSUPPORTED");
  };
  function object2(v, keys) {
    if (!v || typeof v !== "object" || Array.isArray(v) || ![Object.prototype, null].includes(Object.getPrototypeOf(v)))
      return fail3();
    const ds = Object.getOwnPropertyDescriptors(v);
    if (Reflect.ownKeys(ds).length !== keys.length || keys.some((k) => !Object.hasOwn(ds, k) || !Object.hasOwn(ds[k], "value") || !ds[k].enumerable))
      return fail3();
    return Object.fromEntries(keys.map((k) => [k, ds[k].value]));
  }
  function ref(v) {
    const r = object2(v, ["documentId", "moduleId", "elementId"]);
    if (Object.values(r).some((x) => typeof x !== "string" || !x || x.length > 8192 || [...x].length > 4096 || x.includes("\x00") || [...x].some((c) => {
      const p = c.codePointAt(0);
      return p >= 55296 && p <= 57343;
    })))
      return fail3();
    return JSON.stringify(r);
  }
  function assoc(v) {
    if (!v || typeof v !== "object")
      return fail3();
    if (Object.hasOwn(v, "relationshipId")) {
      const r = object2(v, ["documentId", "moduleId", "relationshipId"]);
      if (Object.values(r).some((x) => typeof x !== "string" || !x || x.length > 8192 || [...x].length > 4096 || x.includes("\x00") || [...x].some((c) => {
        const p = c.codePointAt(0);
        return p >= 55296 && p <= 57343;
      })))
        return fail3();
      return JSON.stringify(r);
    }
    return ref(v);
  }
  function quote(v) {
    if (typeof v !== "string" || !v || new TextEncoder().encode(v).length > 63 || v.includes("\x00") || [...v].some((c) => {
      const n = c.codePointAt(0);
      return n >= 55296 && n <= 57343;
    }))
      return fail3();
    return '"' + v.replaceAll('"', '""') + '"';
  }
  function candidateDomain(v) {
    const d = object2(v, ["scalarType", "nullability", "cardinality", "facets", "allowedValues"]);
    if (!["string", "boolean", "integer", "decimal", "binary"].includes(d.scalarType) || d.nullability !== "required" || d.cardinality !== "one" || d.allowedValues !== null)
      return fail3();
    if (d.scalarType === "decimal") {
      const f = object2(d.facets, ["precision", "scale"]);
      if (!Number.isSafeInteger(f.precision) || f.precision < 1 || f.precision > 1000 || !Number.isSafeInteger(f.scale) || f.scale < 0 || f.scale > f.precision)
        return fail3();
      return "decimal:" + f.precision + ":" + f.scale;
    }
    if (d.scalarType === "integer" && Object.hasOwn(d.facets ?? {}, "integerWidth")) {
      const f = object2(object2(d.facets, ["integerWidth"]).integerWidth, ["bits", "signed"]);
      if (!Number.isSafeInteger(f.bits) || f.bits < 1 || f.bits > 4096 || typeof f.signed !== "boolean")
        return fail3();
      return "integer:" + f.bits + ":" + f.signed;
    }
    object2(d.facets, []);
    return d.scalarType;
  }
  function candidateNumeric(token, d) {
    if (typeof token !== "string" || token.length > 65536)
      return fail3();
    const m = /^(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(token);
    if (!m || m[0] !== token)
      return fail3();
    const parts = d.split(":"), scale = d.startsWith("decimal:") ? Number(parts[2]) : 0, precision = d.startsWith("decimal:") ? Number(parts[1]) : 65536;
    let digits = (m[2] + (m[3] ?? "")).replace(/^0+/, "");
    if (!digits)
      return "0";
    const exponent = m[4] ?? "0";
    if (exponent.length > 32)
      return fail3();
    const shift = BigInt(exponent) - BigInt((m[3] ?? "").length) + BigInt(scale);
    if (shift < 0n) {
      const cut = -shift;
      if (cut > BigInt(digits.length))
        return fail3();
      const at = digits.length - Number(cut);
      if (!/^0*$/.test(digits.slice(at)))
        return fail3();
      digits = digits.slice(0, at);
    } else {
      if (BigInt(digits.length) + shift > BigInt(precision))
        return fail3();
      digits += "0".repeat(Number(shift));
    }
    if (digits.length > precision)
      return fail3();
    const coefficient = BigInt((m[1] ?? "") + (digits || "0"));
    if (d.startsWith("integer:")) {
      const bits = BigInt(parts[1]), signed = parts[2] === "true", limit = 1n << (signed ? bits - 1n : bits);
      if (coefficient < (signed ? -limit : 0n) || coefficient >= limit)
        return fail3();
    }
    if (!scale)
      return coefficient.toString();
    const negative = coefficient < 0n, body = (negative ? -coefficient : coefficient).toString().padStart(scale + 1, "0");
    return (negative ? "-" : "") + body.slice(0, -scale) + "." + body.slice(-scale);
  }
  function snapshot(v) {
    let nodes = 4096, text = 4000000;
    const active = new WeakSet;
    function copy(x, depth) {
      if (--nodes < 0 || depth > 32)
        return fail3();
      if (typeof x === "string") {
        text -= x.length;
        if (text < 0)
          return fail3();
        return x;
      }
      if (x === null || typeof x === "boolean" || typeof x === "number" && Number.isFinite(x))
        return x;
      if (!x || typeof x !== "object" || active.has(x))
        return fail3();
      if (isCandidateGraphSource(x)) {
        text -= x.sql.length + x.validitySql.length;
        if (text < 0)
          return fail3();
        return x;
      }
      active.add(x);
      const ds = Object.getOwnPropertyDescriptors(x);
      let result;
      if (Array.isArray(x)) {
        const length = ds.length?.value;
        if (Object.getPrototypeOf(x) !== Array.prototype || !Number.isSafeInteger(length) || length < 0 || length > 4096 || Reflect.ownKeys(ds).length !== length + 1)
          return fail3();
        result = Array.from({ length }, (_, i) => {
          const d = ds[String(i)];
          if (!d || !Object.hasOwn(d, "value") || !d.enumerable)
            return fail3();
          return copy(d.value, depth + 1);
        });
      } else {
        if (![Object.prototype, null].includes(Object.getPrototypeOf(x)) || Reflect.ownKeys(ds).length > 256)
          return fail3();
        const entries = [];
        for (const key of Reflect.ownKeys(ds)) {
          if (typeof key !== "string" || !Object.hasOwn(ds[key], "value") || !ds[key].enumerable)
            return fail3();
          text -= key.length;
          if (text < 0)
            return fail3();
          entries.push([key, copy(ds[key].value, depth + 1)]);
        }
        result = Object.fromEntries(entries);
      }
      active.delete(x);
      return result;
    }
    return copy(v, 0);
  }
  function lowerCandidateSecurityCondition(input) {
    input = snapshot(input);
    object2(input, ["condition", "scans", ...["subject", "resource", "values"].filter((k) => Object.hasOwn(input, k))]);
    if (!Array.isArray(input.scans) || input.scans.length > 64)
      return fail3();
    const scans = new Map(input.scans.map((s) => [assoc(s.association), s]));
    if (scans.size !== input.scans.length)
      return fail3();
    const keys = new Map;
    function key(target, id, fields, arity) {
      if (typeof id !== "string" || !id || id.length > 8192 || [...id].length > 4096 || id.includes("\x00") || [...id].some((c) => {
        const n = c.codePointAt(0);
        return n >= 55296 && n <= 57343;
      }) || !Array.isArray(fields) || !fields.length || fields.length > 256 || fields.length !== arity)
        return fail3();
      const ordered = fields.map(ref);
      if (new Set(ordered).size !== ordered.length)
        return fail3();
      const nominal = ref(target) + JSON.stringify(id), definition = JSON.stringify(ordered);
      if (keys.has(nominal) && keys.get(nominal) !== definition)
        return fail3();
      keys.set(nominal, definition);
      return nominal + definition;
    }
    for (const name of ["subject", "resource"])
      if (Object.hasOwn(input, name)) {
        const intrinsic = input[name] ?? fail3();
        object2(intrinsic, ["target", "keyId", "keyFields", "parameters"]);
        if (!Array.isArray(intrinsic.parameters) || intrinsic.parameters.some((p) => !Number.isSafeInteger(p) || p < 1 || p > 65535))
          return fail3();
        key(intrinsic.target, intrinsic.keyId, intrinsic.keyFields, intrinsic.parameters.length);
      }
    const sources = new Map;
    function relation(scan) {
      const source = sources.get(scan);
      if (source)
        return "(" + source.sql + ")";
      const home = scan.home;
      return quote(home.schema) + "." + quote(home.table);
    }
    for (const scan of scans.values()) {
      object2(scan, ["association", "home", "endpoints", ...scan.record ? ["record"] : [], ...Object.hasOwn(scan, "fields") ? ["fields"] : [], ...Object.hasOwn(scan, "discriminator") ? ["discriminator"] : []]);
      if (Object.hasOwn(scan.home, "source")) {
        const home = object2(scan.home, ["source"]);
        requireCandidateGraphSource(home.source);
        sources.set(scan, home.source);
      } else {
        const home = object2(scan.home, ["schema", "table"]);
        quote(home.schema);
        quote(home.table);
      }
      if (!Array.isArray(scan.endpoints) || scan.endpoints.length > 64)
        return fail3();
      const roles = new Set;
      for (const m of scan.endpoints) {
        if (roles.has(m.role) || assoc(m.association) !== assoc(scan.association))
          return fail3();
        roles.add(m.role);
        const endpoint = bindCandidateSecurityEndpoint({ endpoint: { binding: { variable: 0 }, association: m.association, role: m.role, target: m.target, keyId: m.keyId, carrier: m.carrier } }, m);
        key(endpoint.target, endpoint.keyId, endpoint.targetKeyFields, endpoint.columns.length);
      }
      if (scan.record) {
        object2(scan.record, ["owner", "keyId", "keyFields", "columns"]);
        ref(scan.record.owner);
        if (typeof scan.record.keyId !== "string" || !scan.record.keyId || !Array.isArray(scan.record.columns) || !scan.record.columns.length || scan.record.columns.length > 256 || new Set(scan.record.columns).size !== scan.record.columns.length)
          return fail3();
        scan.record.columns.forEach(quote);
        key(scan.record.owner, scan.record.keyId, scan.record.keyFields, scan.record.columns.length);
      }
    }
    const fieldDomains = new Map;
    function fieldDomain(field, value) {
      const id = ref(field), d = candidateDomain(value);
      if (fieldDomains.has(id) && fieldDomains.get(id) !== d)
        return fail3();
      fieldDomains.set(id, d);
      return d;
    }
    const fieldOwners = new Map;
    function fieldOwner(field, owner) {
      const f = ref(field), o = ref(owner);
      if (fieldOwners.has(f) && fieldOwners.get(f) !== o)
        return fail3();
      fieldOwners.set(f, o);
    }
    for (const scan of scans.values())
      if (Object.hasOwn(scan, "fields")) {
        if (!Array.isArray(scan.fields) || scan.fields.length > 256 || !scan.record)
          return fail3();
        const seen = new Set;
        for (const f of scan.fields) {
          object2(f, ["owner", "field", "domain", "column"]);
          if (ref(f.owner) !== ref(scan.record.owner) || seen.has(ref(f.field)))
            return fail3();
          seen.add(ref(f.field));
          fieldOwner(f.field, f.owner);
          fieldDomain(f.field, f.domain);
          quote(f.column);
          const at = scan.record.keyFields.findIndex((k) => ref(k) === ref(f.field));
          if (at >= 0 && scan.record.columns[at] !== f.column)
            return fail3();
          for (const endpoint of scan.endpoints) {
            const carrier = endpoint.carrier;
            if (carrier.members) {
              const member = carrier.members.fields.findIndex((k) => ref(k) === ref(f.field));
              if (member >= 0 && endpoint.columns[member] !== f.column)
                return fail3();
            }
          }
        }
      }
    const values = new Map;
    if (Object.hasOwn(input, "values")) {
      if (!Array.isArray(input.values) || input.values.length > 256)
        return fail3();
      for (const v of input.values) {
        object2(v, ["binding", "field", "domain", "parameter", ...Object.hasOwn(v, "owner") ? ["owner"] : []]);
        if (!["subject", "resource", "context"].includes(v.binding) || !Number.isSafeInteger(v.parameter) || v.parameter < 1 || v.parameter > 65535)
          return fail3();
        fieldDomain(v.field, v.domain);
        const id = JSON.stringify([v.binding, ref(v.field)]);
        if (values.has(id))
          return fail3();
        values.set(id, v);
        if (v.binding === "context") {
          if (Object.hasOwn(v, "owner"))
            return fail3();
        } else {
          const intrinsic = input[v.binding] ?? fail3();
          if (!Object.hasOwn(v, "owner") || ref(v.owner) !== ref(intrinsic.target))
            return fail3();
          fieldOwner(v.field, v.owner);
          const at = intrinsic.keyFields.findIndex((k) => ref(k) === ref(v.field));
          if (at >= 0 && intrinsic.parameters[at] !== v.parameter)
            return fail3();
        }
      }
    }
    function scalar(v, vars) {
      if (!v || typeof v !== "object" || !Object.hasOwn(v, "value"))
        return;
      const value = object2(v, ["value"]).value;
      if (!value || typeof value !== "object" || Object.hasOwn(value, "identity"))
        return;
      const names = Reflect.ownKeys(value);
      if (names.length !== 1 || !["field", "context", "constant"].includes(String(names[0])))
        return fail3();
      const kind = String(names[0]), t = object2(value, [kind])[kind], d = fieldDomain(t.field, t.domain);
      ref(t.field);
      let sql;
      if (kind === "constant") {
        object2(t, ["field", "domain", "literal"]);
        const literalKey = d.startsWith("integer") ? "integerToken" : d.startsWith("decimal:") ? "decimalToken" : d === "binary" ? "binaryHex" : d, literal = object2(t.literal, [literalKey]);
        if (d === "boolean") {
          if (typeof literal.boolean !== "boolean")
            return fail3();
          sql = literal.boolean ? "TRUE" : "FALSE";
        } else if (d.startsWith("integer") || d.startsWith("decimal:")) {
          sql = "E'" + candidateNumeric(literal[literalKey], d) + "'::pg_catalog.numeric";
        } else if (d === "binary") {
          const hex = literal.binaryHex;
          if (typeof hex !== "string" || hex.length > 65536 || hex.length % 2 || /[^0-9a-fA-F]/.test(hex))
            return fail3();
          sql = "pg_catalog.decode(E'" + hex.toLowerCase() + "'::pg_catalog.text,E'hex'::pg_catalog.text)";
        } else {
          const text = literal.string;
          if (typeof text !== "string" || text.length > 65536 || text.includes("\x00") || [...text].some((c) => {
            const n = c.codePointAt(0);
            return n >= 55296 && n <= 57343;
          }))
            return fail3();
          sql = "E'" + text.replaceAll("\\", "\\\\").replaceAll("'", "\\'") + "'::pg_catalog.text";
        }
      } else {
        object2(t, kind === "context" ? ["field", "domain"] : ["binding", "field", "domain"]);
        if (kind === "context" || t.binding === "subject" || t.binding === "resource") {
          const binding = kind === "context" ? "context" : t.binding, m = values.get(JSON.stringify([binding, ref(t.field)])) ?? fail3();
          if (candidateDomain(m.domain) !== d)
            return fail3();
          sql = "$" + m.parameter + "::pg_catalog." + (d === "string" ? "text" : d === "boolean" ? "bool" : d === "binary" ? "bytea" : "numeric");
        } else {
          const b = vars.get(object2(t.binding, ["variable"]).variable) ?? fail3(), m = b.scan.fields?.find((f) => ref(f.field) === ref(t.field)) ?? fail3();
          if (!b.scan.record || candidateDomain(m.domain) !== d)
            return fail3();
          sql = quote(b.alias) + "." + quote(m.column);
        }
      }
      return { key: "scalar:" + d, sql: [d === "string" ? "(" + sql + ' COLLATE pg_catalog."C")' : sql] };
    }
    const selectors = new Map, homes = new Map;
    for (const scan of scans.values()) {
      const source = sources.get(scan), home = source ? candidateGraphSourcePopulation(source) : relation(scan);
      homes.set(home, [...homes.get(home) ?? [], scan]);
      if (Object.hasOwn(scan, "discriminator")) {
        const d = object2(scan.discriminator, ["column", "carrier", "value"]);
        quote(d.column);
        if (!["text", "int4", "int8"].includes(d.carrier) || typeof d.value !== "string" || !d.value || d.value.length > 65536 || d.value.includes("\x00") || [...d.value].some((c) => {
          const n = c.codePointAt(0);
          return n >= 55296 && n <= 57343;
        }))
          return fail3();
        if (d.carrier !== "text") {
          if (!/^(0|-?[1-9][0-9]*)$/.test(d.value) || d.value.length > 20)
            return fail3();
          const n = BigInt(d.value), bits = d.carrier === "int4" ? 31n : 63n;
          if (n < -(1n << bits) || n >= 1n << bits)
            return fail3();
        }
        selectors.set(scan, d);
      }
    }
    for (const group of homes.values())
      if (group.length > 1) {
        const ds = group.map((s) => selectors.get(s) ?? fail3()), first = ds[0];
        if (ds.some((d) => d.column !== first.column || d.carrier !== first.carrier) || new Set(ds.map((d) => d.value)).size !== ds.length)
          return fail3();
      }
    function selected(scan, alias) {
      const d = selectors.get(scan);
      if (!d)
        return "";
      const literal = "E'" + d.value.replaceAll("\\", "\\\\").replaceAll("'", "\\'") + "'::pg_catalog." + d.carrier;
      const column = quote(alias) + "." + quote(d.column);
      return "(" + (d.carrier === "text" ? "(" + column + ' COLLATE pg_catalog."C")' : column) + " OPERATOR(pg_catalog.=) " + (d.carrier === "text" ? "(" + literal + ' COLLATE pg_catalog."C")' : literal) + ") IS TRUE AND ";
    }
    let work = 4096;
    const bounded = (sql) => {
      if (sql.length > 250000)
        return fail3();
      return sql;
    };
    function term(v, vars) {
      const scalarValue = scalar(v, vars);
      if (scalarValue)
        return scalarValue;
      if (v && typeof v === "object" && Object.hasOwn(v, "endpoint")) {
        const e = object2(object2(v, ["endpoint"]).endpoint, ["binding", "association", "role", "target", "keyId", "carrier"]), slot = object2(e.binding, ["variable"]).variable, b = vars.get(slot) ?? fail3();
        if (assoc(e.association) !== assoc(b.scan.association))
          return fail3();
        const mapping = b.scan.endpoints.find((m) => m.role === e.role) ?? fail3(), bound = bindCandidateSecurityEndpoint(v, mapping);
        return { key: key(bound.target, bound.keyId, bound.targetKeyFields, bound.columns.length), sql: bound.columns.map((c) => quote(b.alias) + "." + quote(c)) };
      }
      const value = object2(object2(v, ["value"]).value, ["identity"]), i = object2(value.identity, ["binding", "target", "keyId"]);
      let sql, fields;
      if (i.binding === "subject" || i.binding === "resource") {
        const binding = input[i.binding] ?? fail3();
        if (ref(binding.target) !== ref(i.target) || binding.keyId !== i.keyId || !binding.parameters.length || binding.parameters.length > 256 || binding.parameters.some((p) => !Number.isSafeInteger(p) || p < 1 || p > 65535))
          return fail3();
        sql = binding.parameters.map((p) => "$" + p);
        fields = binding.keyFields;
      } else {
        const b = vars.get(object2(i.binding, ["variable"]).variable) ?? fail3(), record = b.scan.record ?? fail3();
        if (ref(record.owner) !== ref(i.target) || record.keyId !== i.keyId || !record.columns.length || record.columns.length > 256)
          return fail3();
        fields = record.keyFields;
        sql = record.columns.map((c) => quote(b.alias) + "." + quote(c));
      }
      return { key: key(i.target, i.keyId, fields, sql.length), sql };
    }
    function expression(v, vars, depth) {
      if (--work < 0 || depth > 16)
        return fail3();
      if (!v || typeof v !== "object" || Reflect.ownKeys(v).length !== 1)
        return fail3();
      const op = Reflect.ownKeys(v)[0];
      if (typeof op !== "string" || !["literal", "equal", "and", "or", "not", "exists"].includes(op))
        return fail3();
      const e = object2(v, [op])[op];
      if (op === "literal") {
        if (typeof e !== "boolean")
          return fail3();
        return e ? "TRUE" : "FALSE";
      }
      if (op === "equal") {
        if (!Array.isArray(e) || e.length !== 2)
          return fail3();
        const a = term(e[0], vars), b = term(e[1], vars);
        if (a.key !== b.key || a.sql.length !== b.sql.length)
          return fail3();
        return bounded("(" + a.sql.map((s, i) => "(" + s + " OPERATOR(pg_catalog.=) " + b.sql[i] + ")").join(" AND ") + ")");
      }
      if (op === "not")
        return bounded("(NOT " + expression(e, vars, depth + 1) + ")");
      if (op === "and" || op === "or") {
        if (!Array.isArray(e) || !e.length || e.length > 4096)
          return fail3();
        return bounded("(" + e.map((x) => expression(x, vars, depth + 1)).join(op === "and" ? " AND " : " OR ") + ")");
      }
      const x = object2(e, ["slot", "association", "witness", "condition"]);
      if (!Number.isSafeInteger(x.slot) || x.slot < 0 || vars.has(x.slot))
        return fail3();
      const scan = scans.get(assoc(x.association)) ?? fail3();
      if (x.witness === "opaqueExistential") {
        if (!Object.hasOwn(scan.association, "relationshipId") || scan.record)
          return fail3();
      } else {
        const r = object2(object2(x.witness, ["recordKey"]).recordKey, ["owner", "keyId", "key"]), record = scan.record ?? fail3();
        if (ref(r.owner) !== ref(record.owner) || r.keyId !== record.keyId)
          return fail3();
        const original = object2(r.key, ["id", "name", "fields", ...Object.hasOwn(r.key ?? {}, "primary") ? ["primary"] : []]);
        if (original.id !== r.keyId || typeof original.name !== "string" || !original.name || "primary" in original && typeof original.primary !== "boolean" || !Array.isArray(original.fields))
          return fail3();
        const originalFields = original.fields.map((f) => {
          const field = object2(f, ["module", "element"]);
          return { documentId: r.owner.documentId, moduleId: field.module, elementId: field.element };
        });
        key(r.owner, r.keyId, originalFields, record.columns.length);
      }
      const alias = "candidate_" + x.slot, nested = new Map(vars);
      nested.set(x.slot, { scan, alias });
      const child = expression(x.condition, nested, depth + 1);
      const from = " FROM " + relation(scan) + " AS " + quote(alias) + " WHERE " + selected(scan, alias) + "(" + child + ")";
      return bounded("(CASE WHEN EXISTS(SELECT 1" + from + " IS TRUE) THEN TRUE WHEN EXISTS(SELECT 1" + from + " IS NULL) THEN NULL::pg_catalog.bool ELSE FALSE END)");
    }
    const condition = expression(input.condition, new Map, 0);
    function valid(sql, d) {
      const n = "(" + sql + ")", parts = d.split(":"), checks = [n + " IS NOT NULL"];
      if (d.startsWith("integer") || d.startsWith("decimal:")) {
        for (const special of ["NaN", "Infinity", "-Infinity"])
          checks.push(n + " OPERATOR(pg_catalog.<>) E'" + special + "'::pg_catalog.numeric");
        if (d.startsWith("integer")) {
          checks.push("pg_catalog.trunc(" + n + ") OPERATOR(pg_catalog.=) " + n);
          if (parts.length === 3) {
            const bits = BigInt(parts[1]), signed = parts[2] === "true", limit = 1n << (signed ? bits - 1n : bits);
            checks.push(n + " OPERATOR(pg_catalog.>=) E'" + (signed ? -limit : 0n).toString() + "'::pg_catalog.numeric", n + " OPERATOR(pg_catalog.<) E'" + limit.toString() + "'::pg_catalog.numeric");
          }
        } else {
          const precision = Number(parts[1]), scale = Number(parts[2]), factor = "E'1" + "0".repeat(scale) + "'::pg_catalog.numeric", scaled = "(" + n + " OPERATOR(pg_catalog.*) " + factor + ")";
          checks.push("pg_catalog.abs(" + n + ") OPERATOR(pg_catalog.<) E'1" + "0".repeat(precision - scale) + "'::pg_catalog.numeric");
          return "(CASE WHEN (" + checks.join(" AND ") + ") IS TRUE THEN (pg_catalog.trunc(" + scaled + ") OPERATOR(pg_catalog.=) " + scaled + ") IS TRUE ELSE FALSE END)";
        }
      }
      return "(" + checks.join(" AND ") + ")";
    }
    const guards = [...new Set(sources.values())].map((source) => "((SELECT valid FROM (" + source.validitySql + ") candidate_source_validity)::pg_catalog.bool) IS TRUE");
    for (const value of values.values()) {
      const d = candidateDomain(value.domain), carrier = d === "string" ? "text" : d === "boolean" ? "bool" : d === "binary" ? "bytea" : "numeric";
      guards.push(valid("$" + value.parameter + "::pg_catalog." + carrier, d));
    }
    let keyIndex = 0;
    for (const scan of scans.values()) {
      const columns = [...new Set([...scan.record?.columns ?? [], ...scan.endpoints.flatMap((endpoint) => endpoint.columns)])];
      if (columns.length) {
        const alias = "candidate_key_admission_" + keyIndex++;
        guards.push("(NOT EXISTS(SELECT 1 FROM " + relation(scan) + " AS " + quote(alias) + " WHERE " + selected(scan, alias) + "(" + columns.map((column) => quote(alias) + "." + quote(column) + " IS NOT NULL").join(" AND ") + ") IS NOT TRUE))");
      }
    }
    let index = 0;
    for (const scan of scans.values())
      if (scan.fields?.length) {
        const alias = "candidate_admission_" + index++, fields = scan.fields.map((f) => valid(quote(alias) + "." + quote(f.column), candidateDomain(f.domain)));
        guards.push("(NOT EXISTS(SELECT 1 FROM " + relation(scan) + " AS " + quote(alias) + " WHERE " + selected(scan, alias) + "(" + fields.join(" AND ") + ") IS NOT TRUE))");
      }
    return guards.length ? bounded("(CASE WHEN (" + guards.join(" AND ") + ") IS TRUE THEN " + condition + " ELSE NULL::pg_catalog.bool END)") : condition;
  }
  function lowerCandidateSecurityRuleFold(input) {
    input = snapshot(input);
    object2(input, ["rules", "target", "action", "scans", ...["subject", "resource", "values"].filter((k) => Object.hasOwn(input, k))]);
    const target = ref(input.target);
    ref({ documentId: "metadata", moduleId: "metadata", elementId: input.action });
    if (!Array.isArray(input.rules) || input.rules.length > 64)
      return fail3();
    const shared = { scans: input.scans, ...Object.fromEntries(["subject", "resource", "values"].filter((k) => Object.hasOwn(input, k)).map((k) => [k, input[k]])) };
    lowerCandidateSecurityCondition({ ...shared, condition: { literal: false } });
    if (input.resource && ref(input.resource.target) !== target)
      return fail3();
    const seen = new Set, selected = [];
    for (const value of input.rules) {
      const r = object2(value, ["id", "effect", "actions", "target", "condition", "disclosure"]);
      ref({ documentId: "metadata", moduleId: "metadata", elementId: r.id });
      const ruleTarget = ref(r.target), identity = JSON.stringify([r.id, ruleTarget]);
      if (seen.has(identity))
        return fail3();
      seen.add(identity);
      if (!["permit", "require", "forbid"].includes(r.effect) || !Array.isArray(r.actions) || !r.actions.length || r.actions.length > 64 || new Set(r.actions).size !== r.actions.length || !Array.isArray(r.disclosure) || r.disclosure.length)
        return fail3();
      for (const action of r.actions)
        ref({ documentId: "metadata", moduleId: "metadata", elementId: action });
      if (ruleTarget === target && r.actions.includes(input.action))
        selected.push(r);
    }
    const ruleDomains = new Map;
    function domains(node) {
      if (!node || typeof node !== "object")
        return;
      if (Array.isArray(node)) {
        node.forEach(domains);
        return;
      }
      const n = node;
      if (n.value && typeof n.value === "object") {
        for (const kind of ["field", "context", "constant"])
          if (Object.hasOwn(n.value, kind)) {
            const t = n.value[kind], id = ref(t?.field), d = candidateDomain(t?.domain);
            if (ruleDomains.has(id) && ruleDomains.get(id) !== d)
              return fail3();
            ruleDomains.set(id, d);
          }
      }
      Object.values(n).forEach(domains);
    }
    for (const r of selected)
      domains(r.condition);
    const ruleIds = Object.freeze(selected.map((r) => r.id));
    if (!selected.length) {
      const truthCte = 'candidate_rule_truths(rule_index,effect,truth) AS MATERIALIZED (SELECT NULL::pg_catalog.int4,NULL::pg_catalog.text COLLATE pg_catalog."C",NULL::pg_catalog.bool WHERE FALSE)', decisionSql = "SELECT E'deny'::pg_catalog.text AS decision";
      return Object.freeze({ sql: decisionSql, ruleIds, truthCte, decisionSql });
    }
    const tuples = selected.map((r, i) => "(" + i + "::pg_catalog.int4, E'" + r.effect + `'::pg_catalog.text COLLATE pg_catalog."C", ` + lowerCandidateSecurityCondition({ ...shared, condition: r.condition }) + ")");
    const truthCte = "candidate_rule_truths(rule_index,effect,truth) AS MATERIALIZED (VALUES " + tuples.join(", ") + ")";
    const decisionSql = `SELECT CASE WHEN EXISTS(SELECT 1 FROM candidate_rule_truths WHERE truth IS NULL) THEN E'indeterminate'::pg_catalog.text WHEN NOT EXISTS(SELECT 1 FROM candidate_rule_truths WHERE effect OPERATOR(pg_catalog.=) E'permit'::pg_catalog.text COLLATE pg_catalog."C" AND truth IS TRUE) OR EXISTS(SELECT 1 FROM candidate_rule_truths WHERE (effect OPERATOR(pg_catalog.=) E'require'::pg_catalog.text COLLATE pg_catalog."C" AND truth IS NOT TRUE) OR (effect OPERATOR(pg_catalog.=) E'forbid'::pg_catalog.text COLLATE pg_catalog."C" AND truth IS TRUE)) THEN E'deny'::pg_catalog.text ELSE E'permit'::pg_catalog.text END AS decision`;
    const sql = "WITH " + truthCte + " " + decisionSql;
    if (sql.length > 1e6)
      return fail3();
    return Object.freeze({ sql, ruleIds, truthCte, decisionSql });
  }

  // ../truss-endpoint-keys-browser.ts
  globalThis.endpointKeyFold = (input) => lowerCandidateSecurityRuleFold(input).sql;
})();
