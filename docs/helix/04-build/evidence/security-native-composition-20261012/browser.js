(() => {
  // packages/postgresql/src/security-graph-source.ts
  var issued = new WeakSet;
  var sourcePopulations = new WeakMap;
  var sourceKinds = new WeakMap;
  var fail = () => {
    throw Error("TRUSS_SECURITY_GRAPH_SOURCE_UNSUPPORTED");
  };
  function requireCandidateGraphSource(source) {
    if (!issued.has(source))
      return fail();
  }

  // packages/postgresql/src/security-predicate.ts
  var refuse = () => {
    throw new Error("TRUSS_SECURITY_PREDICATE_UNSUPPORTED");
  };
  function object(v, keys) {
    if (!v || typeof v !== "object" || Array.isArray(v) || Object.keys(v).some((k) => !keys.includes(k)))
      return refuse();
    return v;
  }
  function text(v) {
    if (typeof v !== "string" || !v || v.includes("\x00") || new TextDecoder("utf-8", { fatal: true }).decode(new TextEncoder().encode(v)) !== v)
      return refuse();
    return v;
  }
  function ref(v) {
    const r = object(v, ["documentId", "moduleId", "elementId"]);
    return JSON.stringify([text(r.documentId), text(r.moduleId), text(r.elementId)]);
  }
  function identifier(v) {
    const value = text(v);
    if (new TextEncoder().encode(value).length > 63)
      return refuse();
    return '"' + value.replaceAll('"', '""') + '"';
  }
  function lowerSecurityRowPredicate(input) {
    const plan = object(input.logicalPlan, ["version", "rules"]);
    if (plan.version !== "weft.security.logical-ir/0.1.0" || !Array.isArray(plan.rules))
      return refuse();
    const types = new Map(input.types.map((t) => [ref(t.type), t]));
    if (types.size !== input.types.length || types.size > 64)
      return refuse();
    const literal = (value) => "E'" + text(value).replaceAll("\\", "\\\\").replaceAll("'", "\\'") + "'";
    const discriminator = (t) => {
      if (!t.discriminator)
        return;
      const d = object(t.discriminator, ["column", "carrier", "value"]);
      identifier(d.column);
      text(d.value);
      if (!["text", "int4", "int8"].includes(d.carrier) || d.value.length > 65536)
        return refuse();
      if (d.carrier !== "text") {
        if (!/^(0|-?[1-9][0-9]*)$/.test(d.value) || d.value.length > 20)
          return refuse();
        const n = BigInt(d.value), bits = d.carrier === "int4" ? 31n : 63n;
        if (n < -(1n << bits) || n >= 1n << bits)
          return refuse();
      }
      return { column: d.column, carrier: d.carrier, value: d.value };
    };
    const selections = new Map(input.types.map((t) => [ref(t.type), discriminator(t)]));
    const candidateSources = new Map;
    const relation = (t) => {
      if (Object.hasOwn(t.home, "source")) {
        const descriptors = Object.getOwnPropertyDescriptors(t.home);
        if (Reflect.ownKeys(descriptors).length !== 1 || !Object.hasOwn(descriptors.source, "value"))
          return refuse();
        const source = descriptors.source.value;
        requireCandidateGraphSource(source);
        candidateSources.set(ref(t.type), source);
        return "(" + source.sql + ")";
      }
      const home = t.home;
      return identifier(home.schema) + "." + identifier(home.table);
    };
    const homes = new Map;
    for (const t of input.types) {
      const home = relation(t);
      homes.set(home, [...homes.get(home) ?? [], t]);
    }
    for (const group of homes.values())
      if (group.length > 1) {
        const selected = group.map((t) => selections.get(ref(t.type)) ?? refuse()), first = selected[0];
        if (selected.some((d) => d.column !== first.column || d.carrier !== first.carrier) || new Set(selected.map((d) => d.value)).size !== group.length)
          return refuse();
      }
    const resource = types.get(ref(input.target)) ?? refuse(), subject = types.get(ref(input.subject)) ?? refuse();
    const usedSources = new Set;
    const table = (t) => {
      const sql = relation(t), source = candidateSources.get(ref(t.type));
      if (source)
        usedSources.add(source);
      return sql;
    };
    const selectedRow = (t, alias) => {
      const d = selections.get(ref(t.type));
      return d ? identifier(alias) + "." + identifier(d.column) + " OPERATOR(pg_catalog.=) " + literal(d.value) + "::pg_catalog." + d.carrier : "TRUE";
    };
    const resourceSelection = selections.get(ref(resource.type));
    if (resourceSelection ? input.resourceDiscriminatorParameter !== resource.keyFields.length + 1 : input.resourceDiscriminatorParameter !== undefined)
      return refuse();
    const column = (t, r) => identifier(t.fields.find((f) => ref(f.ref) === ref(r))?.column ?? refuse());
    let work = 4096;
    const bounded = (s) => {
      if (s.length > 250000 || new TextEncoder().encode(s).length > 1e6)
        return refuse();
      return s;
    };
    const binding = (v, vars) => {
      if (v === "resource")
        return { type: resource, resource: true };
      if (v === "subject")
        return { type: subject, subject: true };
      const b = object(v, ["variable"]);
      if (!Number.isSafeInteger(b.variable))
        return refuse();
      return vars.get(b.variable) ?? refuse();
    };
    const scalar = (b, r) => {
      if (b.resource) {
        const at = b.type.keyFields.findIndex((f) => ref(f.ref) === ref(r));
        if (at < 0)
          return refuse();
        return "$" + (at + 1);
      }
      if (b.subject)
        return '(SELECT "subject_row".' + column(b.type, r) + " FROM " + table(b.type) + ' AS "subject_row" WHERE "subject_row".' + identifier(input.subjectLoginColumn) + " OPERATOR(pg_catalog.=) SESSION_USER::pg_catalog.text" + (b.type.discriminator ? " AND (" + selectedRow(b.type, "subject_row") + ")" : "") + ")";
      return identifier(b.alias) + "." + column(b.type, r);
    };
    const domain = (v) => {
      const d = object(v, ["scalarType", "nullability", "cardinality", "facets", "allowedValues"]);
      if (d.allowedValues !== null || d.cardinality !== "one" || d.nullability !== "required" || Object.keys(d.facets ?? {}).length || !["string", "boolean"].includes(d.scalarType))
        return refuse();
      return d.scalarType;
    };
    const term = (v, vars) => {
      const t = object(v, ["identity", "endpoint", "field", "constant"]);
      if (Object.keys(t).length !== 1)
        return refuse();
      if (t.identity) {
        const i = object(t.identity, ["binding", "target", "keyId"]), b = binding(i.binding, vars);
        if (ref(i.target) !== ref(b.type.type) || i.keyId !== b.type.keyId || !b.type.keyFields.length)
          return refuse();
        return { sql: b.type.keyFields.map((f) => scalar(b, f.ref)), identity: ref(i.target) + ":" + JSON.stringify(i.keyId) };
      }
      if (t.endpoint) {
        const e = object(t.endpoint, ["binding", "association", "role", "target", "keyId"]), b = binding(e.binding, vars);
        const endpoint = b.type.endpoints?.find((x) => x.role === e.role), target = types.get(ref(e.target));
        if (ref(e.association) !== ref(b.type.type) || !endpoint || !target || ref(endpoint.target) !== ref(e.target) || target.keyId !== e.keyId || endpoint.fields.length !== target.keyFields.length)
          return refuse();
        return { sql: endpoint.fields.map((f) => scalar(b, f)), identity: ref(e.target) + ":" + JSON.stringify(e.keyId) };
      }
      if (t.field) {
        const f = object(t.field, ["binding", "field", "domain"]);
        return { sql: [scalar(binding(f.binding, vars), f.field)], domain: domain(f.domain) };
      }
      const c = object(t.constant, ["field", "domain", "literal"]);
      ref(c.field);
      const d = domain(c.domain);
      const literal = object(c.literal, [d]);
      if (Object.keys(literal).length !== 1)
        return refuse();
      if (d === "boolean") {
        if (typeof literal.boolean !== "boolean")
          return refuse();
        return { sql: [literal.boolean ? "TRUE" : "FALSE"], domain: d };
      }
      const value = literal.string;
      if (typeof value !== "string" || value.includes("\x00") || new TextDecoder("utf-8", { fatal: true }).decode(new TextEncoder().encode(value)) !== value || value.length > 65536)
        return refuse();
      return { sql: ["E'" + value.replaceAll("\\", "\\\\").replaceAll("'", "\\'") + "'::pg_catalog.text"], domain: d };
    };
    const expression = (v, vars, depth) => {
      if (--work < 0 || depth > 32)
        return refuse();
      const e = object(v, ["literal", "equal", "and", "or", "not", "exists"]);
      if (Object.keys(e).length !== 1)
        return refuse();
      if ("literal" in e) {
        if (typeof e.literal !== "boolean")
          return refuse();
        return e.literal ? "TRUE" : "FALSE";
      }
      if (e.equal) {
        if (!Array.isArray(e.equal) || e.equal.length !== 2)
          return refuse();
        const a = term(e.equal[0], vars), b = term(e.equal[1], vars);
        if (a.identity !== b.identity || a.domain !== b.domain || a.sql.length !== b.sql.length)
          return refuse();
        return bounded("(" + a.sql.map((value, i) => "(" + value + " OPERATOR(pg_catalog.=) " + b.sql[i] + ")").join(" AND ") + ")");
      }
      if (e.and || e.or) {
        const args = e.and ?? e.or;
        if (!Array.isArray(args) || !args.length)
          return refuse();
        const parts = args.map((a) => expression(a, vars, depth + 1));
        if (parts.reduce((n, p) => n + p.length, 0) > 250000)
          return refuse();
        return bounded("(" + parts.join(e.and ? " AND " : " OR ") + ")");
      }
      if (e.not)
        return bounded("(NOT " + expression(e.not, vars, depth + 1) + ")");
      const x = object(e.exists, ["slot", "association", "condition"]);
      if (!Number.isSafeInteger(x.slot) || x.slot < 0 || vars.has(x.slot))
        return refuse();
      const type = types.get(ref(x.association)) ?? refuse(), alias = "association_" + x.slot;
      const nested = new Map(vars);
      nested.set(x.slot, { type, alias });
      const child = expression(x.condition, nested, depth + 1);
      if (child.length > 80000)
        return refuse();
      const scan = " FROM " + table(type) + " AS " + identifier(alias) + " WHERE " + (type.discriminator ? "(" + selectedRow(type, alias) + ") AND " : "") + "(" + child + ")";
      return bounded("(CASE WHEN EXISTS(SELECT 1" + scan + " IS TRUE) THEN TRUE WHEN EXISTS(SELECT 1" + scan + " IS NULL) THEN NULL::pg_catalog.bool ELSE FALSE END)");
    };
    const effects = { permit: [], require: [], forbid: [] };
    for (const raw of plan.rules) {
      const r = object(raw, ["id", "effect", "actions", "target", "condition", "disclosure"]);
      if (!Array.isArray(r.actions) || !Array.isArray(r.disclosure) || !Object.hasOwn(effects, r.effect))
        return refuse();
      if (ref(r.target) !== ref(input.target) || !r.actions.includes(input.action))
        continue;
      effects[r.effect].push(expression(r.condition, new Map, 0));
    }
    if (!effects.permit.length)
      return "FALSE";
    const result = "(" + effects.permit.map((p) => "(" + p + ") IS TRUE").join(" OR ") + ")" + (effects.permit.length > 1 ? effects.permit.map((p) => " AND (" + p + ") IS NOT NULL").join("") : "") + effects.require.map((p) => " AND (" + p + ") IS TRUE").join("") + effects.forbid.map((p) => " AND (" + p + ") IS FALSE").join("");
    const root = resourceSelection ? "($" + input.resourceDiscriminatorParameter + " OPERATOR(pg_catalog.=) " + literal(resourceSelection.value) + "::pg_catalog." + resourceSelection.carrier + ") IS TRUE AND " : "";
    const validity = [...usedSources].map((source) => "((SELECT valid FROM (" + source.validitySql + ") candidate_validity)::pg_catalog.bool) IS TRUE AND ").join("");
    return bounded("(" + validity + root + result + ")");
  }

  // ../../../Users/erik/.codex/worktrees/security-main-integration/umf/src/model/types.ts
  class UmfError extends Error {
    code;
    path;
    constructor(code, message, path = "") {
      super(message);
      this.code = code;
      this.path = path;
      this.name = "UmfError";
    }
  }
  var pointer = (key) => key.replace(/~/g, "~0").replace(/\//g, "~1");

  // ../../../Users/erik/.codex/worktrees/security-main-integration/umf/src/model/json.ts
  var LIMITS = { maxDepth: 128, maxValues: 1e5, maxTextLength: 4000000 };
  function copyJson(input) {
    return copyJsonCharged(input);
  }
  function copyJsonCharged(input, charge) {
    const active = new Set;
    let values = 0;
    function visit(value, path, depth) {
      charge?.(1);
      if (++values > LIMITS.maxValues || depth > LIMITS.maxDepth)
        throw new UmfError("LIMIT", "JSON structural limit exceeded", path);
      if (value === null || typeof value === "string" || typeof value === "boolean")
        return value;
      if (typeof value === "number") {
        if (!Number.isFinite(value) || Object.is(value, -0) || Number.isInteger(value) && !Number.isSafeInteger(value))
          throw new UmfError("NUMBER", "Number outside the core interoperable numeric profile", path);
        return value;
      }
      if (typeof value !== "object")
        throw new UmfError("NON_JSON", "Value is not JSON-compatible", path);
      if (active.has(value))
        throw new UmfError("CYCLE", "Cyclic value", path);
      const proto = Object.getPrototypeOf(value);
      if (Array.isArray(value) ? proto !== Array.prototype : proto !== Object.prototype && proto !== null)
        throw new UmfError("NON_JSON", "Custom object prototype", path);
      if (Object.getOwnPropertySymbols(value).length)
        throw new UmfError("NON_JSON", "Symbol keys are not JSON-compatible", path);
      active.add(value);
      const descriptors = Object.getOwnPropertyDescriptors(value);
      const result = Array.isArray(value) ? [] : Object.create(null);
      for (const [key, descriptor] of Object.entries(descriptors)) {
        if (Array.isArray(value) && key === "length")
          continue;
        if (!descriptor.enumerable || !("value" in descriptor))
          throw new UmfError("NON_JSON", "Hidden fields and accessors cannot be serialized faithfully", path + "/" + pointer(key));
        if (Array.isArray(value) && (!/^(0|[1-9][0-9]*)$/.test(key) || Number(key) >= 4294967295 || Number(key) >= value.length))
          throw new UmfError("NON_JSON", "Non-index array property", path);
        const item = visit(descriptor.value, path + "/" + pointer(key), depth + 1);
        Object.defineProperty(result, key, { value: item, enumerable: true, writable: true, configurable: true });
      }
      if (Array.isArray(value) && Object.keys(value).length !== value.length)
        throw new UmfError("NON_JSON", "Sparse arrays are not JSON values", path);
      active.delete(value);
      return result;
    }
    return visit(input, "", 0);
  }

  // ../../../Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/logic.ts
  var truth = (value) => {
    if (value !== "T" && value !== "F" && value !== "U")
      throw new UmfError("SECURITY_TRUTH", "Invalid security truth");
    return value;
  };
  function object2(value) {
    if (value === null || typeof value !== "object" || Array.isArray(value))
      throw new UmfError("SECURITY_SHAPE", "Expected security object");
    return value;
  }
  function members(value, allowed) {
    if (Object.keys(value).some((key) => !allowed.includes(key)))
      throw new UmfError("SECURITY_UNKNOWN", "Uninterpreted security member");
  }
  function disposition(value) {
    const d = object2(value);
    members(d, d.kind === "transformed" ? ["kind", "type", "value"] : ["kind"]);
    if (d.kind === "original" || d.kind === "withheld")
      return { kind: d.kind };
    if (d.kind === "transformed" && d.type === "string" && typeof d.value === "string")
      return { kind: d.kind, type: d.type, value: d.value };
    if (d.kind === "transformed" && d.type === "boolean" && typeof d.value === "boolean")
      return { kind: d.kind, type: d.type, value: d.value };
    throw new UmfError("SECURITY_DISPOSITION", "Unsupported or malformed disposition");
  }
  function composeSecurityRules(input, protectedFields = []) {
    const copied = copyJson({ rules: input, protectedFields });
    if (!Array.isArray(copied.rules) || copied.rules.length > 256 || !Array.isArray(copied.protectedFields) || copied.protectedFields.length > 4096 || copied.protectedFields.some((f) => typeof f !== "string" || !f.length) || new Set(copied.protectedFields).size !== copied.protectedFields.length)
      throw new UmfError("SECURITY_BOUND", "Invalid composition bounds or protected fields");
    const rules = copied.rules.map((value) => {
      const r = object2(value);
      members(r, ["effect", "truth", "disclosure"]);
      if (!["permit", "require", "forbid"].includes(r.effect))
        throw new UmfError("SECURITY_EFFECT", "Invalid effect");
      const rule = { effect: r.effect, truth: truth(r.truth) };
      if (Object.hasOwn(r, "disclosure")) {
        if (r.effect !== "permit")
          throw new UmfError("SECURITY_DISCLOSURE", "Only permits carry disclosure");
        const entries = Object.entries(object2(r.disclosure));
        if (entries.length > 4096 || entries.some(([field]) => !field.length))
          throw new UmfError("SECURITY_BOUND", "Invalid disclosure fields");
        rule.disclosure = Object.fromEntries(entries.map(([field, d]) => [field, disposition(d)]));
      }
      return rule;
    });
    const refuse = (decision) => ({ decision, disclosure: {} });
    if (rules.some((r) => r.truth === "U"))
      return refuse("indeterminate");
    if (!rules.some((r) => r.effect === "permit" && r.truth === "T") || rules.some((r) => r.effect === "require" && r.truth !== "T") || rules.some((r) => r.effect === "forbid" && r.truth === "T"))
      return refuse("deny");
    const obligations = new Map;
    for (const r of rules)
      if (r.effect === "permit" && r.truth === "T") {
        for (const [field, d] of Object.entries(r.disclosure ?? {})) {
          const values = obligations.get(field) ?? [];
          values.push(d);
          obligations.set(field, values);
        }
      }
    if (copied.protectedFields.some((field) => !obligations.has(field)))
      return refuse("indeterminate");
    const disclosure = Object.create(null);
    for (const [field, values] of obligations) {
      if (values.some((d) => d.kind === "withheld")) {
        disclosure[field] = { kind: "withheld" };
        continue;
      }
      const transforms = values.filter((d) => d.kind === "transformed");
      if (new Set(transforms.map((d) => JSON.stringify([d.type, d.value]))).size > 1)
        return refuse("conflict");
      disclosure[field] = transforms[0] ?? { kind: "original" };
    }
    return { decision: "permit", disclosure };
  }

  // docs/helix/04-build/evidence/security-native-composition-20261012/produce.ts
  var ref2 = (elementId) => ({ documentId: "domain", moduleId: "m", elementId });
  var domain = { scalarType: "boolean", nullability: "required", cardinality: "one", facets: {}, allowedValues: null };
  var effects = ["permit", "permit", "require", "forbid"];
  var names = ["p1", "p2", "required", "forbidden"];
  var target = ref2("Resource");
  var subject = ref2("Staff");
  var sql = lowerSecurityRowPredicate({
    action: "read",
    target,
    subject,
    subjectLoginColumn: "native_login",
    types: [
      { type: target, keyId: "pk", keyFields: [{ ref: ref2("resourceId"), column: "id" }], fields: [{ ref: ref2("resourceId"), column: "id" }], home: { schema: "fixture", table: "resource" } },
      { type: subject, keyId: "pk", keyFields: [{ ref: ref2("staffId"), column: "id" }], fields: names.map((name) => ({ ref: ref2(name), column: name })), home: { schema: "fixture", table: "staff" } }
    ],
    logicalPlan: { version: "weft.security.logical-ir/0.1.0", rules: effects.map((effect, i) => ({ id: "r" + i, effect, actions: ["read"], target, disclosure: [], condition: { equal: [{ field: { binding: "subject", field: ref2(names[i]), domain } }, { constant: { field: ref2(names[i]), domain, literal: { boolean: true } } }] } })) }
  });
  var truths = ["T", "F", "U"];
  var cases = [];
  for (const a of truths)
    for (const b of truths)
      for (const c of truths)
        for (const d of truths) {
          const values = [a, b, c, d];
          const expected = !values.includes("U") && (a === "T" || b === "T") && c === "T" && d === "F";
          const decision = composeSecurityRules(values.map((truth, i) => ({ effect: effects[i], truth }))).decision;
          if (decision === "permit" !== expected)
            throw Error("Original semantic oracle differs");
          cases.push({ truths: values, expected, semanticDecision: decision });
        }
  console.log(JSON.stringify({ sql, cases }));
})();
