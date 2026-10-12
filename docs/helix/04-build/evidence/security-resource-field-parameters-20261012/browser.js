(() => {
  // tests/fixtures/security-resource-parameters.ts
  var ref = (elementId) => ({ documentId: "d", moduleId: "m", elementId });
  var domain = { scalarType: "boolean", nullability: "required", cardinality: "one", facets: {}, allowedValues: null };
  var request = () => ({ logicalPlan: { version: "weft.security.logical-ir/0.1.0", rules: [{ id: "active", effect: "permit", actions: ["read"], target: ref("Resource"), disclosure: [], condition: { equal: [{ field: { binding: "resource", field: ref("active"), domain } }, { constant: { field: ref("active"), domain, literal: { boolean: true } } }] } }] }, action: "read", target: ref("Resource"), subject: ref("Staff"), subjectLoginColumn: "login", resourceFieldParameters: [ref("active")], types: [{ type: ref("Resource"), keyId: "pk", keyFields: [{ ref: ref("id"), column: "id" }], fields: [{ ref: ref("id"), column: "id" }, { ref: ref("active"), column: "active" }], home: { schema: "fixture", table: "resource" } }, { type: ref("Staff"), keyId: "pk", keyFields: [{ ref: ref("staffId"), column: "id" }], fields: [{ ref: ref("staffId"), column: "id" }], home: { schema: "fixture", table: "staff" } }] });

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
  function ref2(v) {
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
    const types = new Map(input.types.map((t) => [ref2(t.type), t]));
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
    const selections = new Map(input.types.map((t) => [ref2(t.type), discriminator(t)]));
    const candidateSources = new Map;
    const relation = (t) => {
      if (Object.hasOwn(t.home, "source")) {
        const descriptors = Object.getOwnPropertyDescriptors(t.home);
        if (Reflect.ownKeys(descriptors).length !== 1 || !Object.hasOwn(descriptors.source, "value"))
          return refuse();
        const source = descriptors.source.value;
        requireCandidateGraphSource(source);
        candidateSources.set(ref2(t.type), source);
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
        const selected = group.map((t) => selections.get(ref2(t.type)) ?? refuse()), first = selected[0];
        if (selected.some((d) => d.column !== first.column || d.carrier !== first.carrier) || new Set(selected.map((d) => d.value)).size !== group.length)
          return refuse();
      }
    const resource = types.get(ref2(input.target)) ?? refuse(), subject = types.get(ref2(input.subject)) ?? refuse();
    const usedSources = new Set;
    const table = (t) => {
      const sql = relation(t), source = candidateSources.get(ref2(t.type));
      if (source)
        usedSources.add(source);
      return sql;
    };
    const selectedRow = (t, alias) => {
      const d = selections.get(ref2(t.type));
      return d ? identifier(alias) + "." + identifier(d.column) + " OPERATOR(pg_catalog.=) " + literal(d.value) + "::pg_catalog." + d.carrier : "TRUE";
    };
    const resourceSelection = selections.get(ref2(resource.type));
    if (resourceSelection ? input.resourceDiscriminatorParameter !== resource.keyFields.length + 1 : input.resourceDiscriminatorParameter !== undefined)
      return refuse();
    const resourceFields = input.resourceFieldParameters ?? [];
    if (!Array.isArray(resourceFields) || resourceFields.length > 64)
      return refuse();
    const resourcePositions = new Map;
    for (const [index, field] of resourceFields.entries()) {
      const identity = ref2(field);
      if (resourcePositions.has(identity) || resource.keyFields.some((f) => ref2(f.ref) === identity) || resource.fields.filter((f) => ref2(f.ref) === identity).length !== 1)
        return refuse();
      resourcePositions.set(identity, resource.keyFields.length + (resourceSelection ? 1 : 0) + index + 1);
    }
    const column = (t, r) => identifier(t.fields.find((f) => ref2(f.ref) === ref2(r))?.column ?? refuse());
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
        const at = b.type.keyFields.findIndex((f) => ref2(f.ref) === ref2(r));
        if (at >= 0)
          return "$" + (at + 1);
        const position = resourcePositions.get(ref2(r));
        if (position === undefined)
          return refuse();
        return "$" + position;
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
        if (ref2(i.target) !== ref2(b.type.type) || i.keyId !== b.type.keyId || !b.type.keyFields.length)
          return refuse();
        return { sql: b.type.keyFields.map((f) => scalar(b, f.ref)), identity: ref2(i.target) + ":" + JSON.stringify(i.keyId) };
      }
      if (t.endpoint) {
        const e = object(t.endpoint, ["binding", "association", "role", "target", "keyId"]), b = binding(e.binding, vars);
        const endpoint = b.type.endpoints?.find((x) => x.role === e.role), target = types.get(ref2(e.target));
        if (ref2(e.association) !== ref2(b.type.type) || !endpoint || !target || ref2(endpoint.target) !== ref2(e.target) || target.keyId !== e.keyId || endpoint.fields.length !== target.keyFields.length)
          return refuse();
        return { sql: endpoint.fields.map((f) => scalar(b, f)), identity: ref2(e.target) + ":" + JSON.stringify(e.keyId) };
      }
      if (t.field) {
        const f = object(t.field, ["binding", "field", "domain"]);
        return { sql: [scalar(binding(f.binding, vars), f.field)], domain: domain(f.domain) };
      }
      const c = object(t.constant, ["field", "domain", "literal"]);
      ref2(c.field);
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
      const type = types.get(ref2(x.association)) ?? refuse(), alias = "association_" + x.slot;
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
      if (ref2(r.target) !== ref2(input.target) || !r.actions.includes(input.action))
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

  // ../truss-resource-param-native-20261012/browser.ts
  var plain = request();
  var tagged = request();
  tagged.types[0].discriminator = { column: "type_id", carrier: "int8", value: "42" };
  tagged.resourceDiscriminatorParameter = 2;
  globalThis.results = { plain: lowerSecurityRowPredicate(plain), tagged: lowerSecurityRowPredicate(tagged) };
})();
