// packages/postgresql/src/index.ts
var INERT_ASSEMBLY_PROFILE = Object.freeze({
  identity: "truss-reference-assembly-inert",
  version: "0.1.0",
  sha256: "3cca9dddd4b39f0325392acae67832137a9f3d6ddc2824e344f6f1a182742d09"
});
var families = new Set([
  "catalog",
  "mutation",
  "group",
  "import",
  "direct_read",
  "history",
  "feed",
  "weft_execution",
  "bootstrap",
  "physical_optimization",
  "conformance"
]);
function record(value) {
  if (!value || typeof value !== "object" || Array.isArray(value))
    return;
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null)
    return;
  const descriptors = Object.getOwnPropertyDescriptors(value);
  if (Reflect.ownKeys(value).some((key) => typeof key !== "string" || !("value" in descriptors[key])))
    return;
  const result = Object.create(null);
  for (const [key, descriptor] of Object.entries(descriptors))
    result[key] = descriptor.value;
  return result;
}
function own(value, key) {
  if (!value || typeof value !== "object")
    return;
  const descriptor = Object.getOwnPropertyDescriptor(value, key);
  return descriptor && "value" in descriptor ? descriptor.value : undefined;
}
function exact(value, required, optional = []) {
  return required.every((key) => Object.hasOwn(value, key)) && Object.keys(value).every((key) => required.includes(key) || optional.includes(key));
}
function text(value) {
  return typeof value === "string" && value.length > 0 && value.length <= 1024 && !value.includes("\x00");
}
function pin(value) {
  const data = record(value);
  if (!data || !exact(data, ["identity", "version", "sha256"]) || !text(data.identity) || !text(data.version) || typeof data.sha256 !== "string" || !/^[0-9a-f]{64}$/.test(data.sha256))
    return;
  return Object.freeze({ identity: data.identity, version: data.version, sha256: data.sha256 });
}
function same(left, right) {
  return left.identity === right.identity && left.version === right.version && left.sha256 === right.sha256;
}
function selection(value) {
  const data = record(value);
  const keys = ["capabilityProfile", "layoutProfile", "adapterProfile", "valueProfile", "policyProfile"];
  if (!data || !exact(data, ["family", ...keys]) || typeof data.family !== "string" || !families.has(data.family))
    return;
  const profiles = keys.map((key) => pin(data[key]));
  if (profiles.some((value) => value === undefined))
    return;
  return Object.freeze({
    family: data.family,
    capabilityProfile: profiles[0],
    layoutProfile: profiles[1],
    adapterProfile: profiles[2],
    valueProfile: profiles[3],
    policyProfile: profiles[4]
  });
}
function selectionKey(value) {
  return JSON.stringify([value.family, ...[
    value.capabilityProfile,
    value.layoutProfile,
    value.adapterProfile,
    value.valueProfile,
    value.policyProfile
  ].map((p) => [p.identity, p.version, p.sha256])]);
}
function createReferenceAssembly(input, executor, services) {
  const error = (code, path) => Object.freeze({ status: "error", code, ...path ? { path } : {}, diagnosticProfile: INERT_ASSEMBLY_PROFILE });
  const data = record(input);
  if (!data || !exact(data, ["interfaceVersion", "assemblyId", "assemblyProfile", "recovery", "databaseIdentity", "schema", "capabilities"], ["requestReplay"]) || data.interfaceVersion !== "truss-reference-assembly/0.1.0" || !text(data.assemblyId) || !text(data.databaseIdentity) || !text(data.schema) || !executor || typeof executor !== "object")
    return error("invalid_configuration");
  const assemblyProfile = pin(data.assemblyProfile);
  if (!assemblyProfile || !same(assemblyProfile, INERT_ASSEMBLY_PROFILE))
    return error("unsupported_profile", "assemblyProfile");
  const recovery = record(data.recovery);
  const registryProfile = recovery && pin(recovery.registryProfile);
  if (!recovery || !exact(recovery, ["registryProfile", "retention"]) || !registryProfile || recovery.retention !== "process_lifetime" && recovery.retention !== "restart_durable")
    return error("invalid_configuration", "recovery");
  const registry = own(services, "recoveryRegistry");
  const actualRegistryProfile = pin(own(registry, "profile"));
  if (!actualRegistryProfile || !same(registryProfile, actualRegistryProfile) || own(registry, "retention") !== recovery.retention)
    return error("incompatible_selection", "recovery");
  let requestReplay;
  if (Object.hasOwn(data, "requestReplay")) {
    const replay = record(data.requestReplay);
    const profile = replay && pin(replay.namespaceAuthorityProfile);
    const authority = own(services, "requestNamespaceAuthority");
    const actual = pin(own(authority, "profile"));
    if (!replay || !exact(replay, ["namespaceAuthorityProfile"]) || !profile || !actual || !same(profile, actual))
      return error("incompatible_selection", "requestReplay");
    requestReplay = Object.freeze({ namespaceAuthorityProfile: profile });
  }
  if (!Array.isArray(data.capabilities) || data.capabilities.length < 1 || data.capabilities.length > 128)
    return error("invalid_configuration", "capabilities");
  if (Reflect.ownKeys(data.capabilities).some((key) => typeof key !== "string" || key !== "length" && !/^(0|[1-9][0-9]*)$/.test(key)))
    return error("invalid_configuration", "capabilities");
  const capabilities = [];
  const keys = new Set;
  for (let index = 0;index < data.capabilities.length; index++) {
    const value = selection(own(data.capabilities, String(index)));
    if (!value || keys.has(selectionKey(value)))
      return error("incompatible_selection", "capabilities");
    keys.add(selectionKey(value));
    capabilities.push(value);
  }
  const configuration = Object.freeze({
    interfaceVersion: "truss-reference-assembly/0.1.0",
    assemblyId: data.assemblyId,
    assemblyProfile,
    recovery: Object.freeze({ registryProfile, retention: recovery.retention }),
    databaseIdentity: data.databaseIdentity,
    schema: data.schema,
    capabilities: Object.freeze(capabilities),
    ...requestReplay ? { requestReplay } : {}
  });
  let disposed = false;
  const unavailable = () => ({ status: "unavailable", reason: disposed ? "disposed" : "selection" });
  const disposal = Object.freeze({ state: "disposed", ownedResourcesReleased: true });
  const assembly = Object.freeze({
    configuration,
    directReads: unavailable,
    catalog: unavailable,
    groups: unavailable,
    mutations: unavailable,
    imports: unavailable,
    history: unavailable,
    feed: unavailable,
    compiledExecution: unavailable,
    async observeReadiness(request) {
      const value = selection(request);
      if (disposed || !value || !keys.has(selectionKey(value)))
        return { status: "error", error: {
          code: "execution_obligation",
          retryScope: "none",
          message: disposed ? "Assembly disposed" : "Selection not configured"
        } };
      return { status: "ok", value: Object.freeze({ interfaceVersion: "truss-capability-readiness/0.1.0", selection: value, state: "unverified" }) };
    },
    async dispose() {
      disposed = true;
      return disposal;
    }
  });
  return Object.freeze({ status: "ok", value: assembly });
}

class NativeVectorError extends Error {
  code;
  constructor(code) {
    super(code);
    this.code = code;
    this.name = "NativeVectorError";
  }
}
function decodeNativeVector(family, text, limits, declaredCount) {
  if (family !== "oidvector" && family !== "int2vector")
    throw new NativeVectorError("output-grammar");
  if (typeof text !== "string")
    throw new NativeVectorError("output-grammar");
  if (!Number.isSafeInteger(limits.maxBytes) || limits.maxBytes < 0 || !Number.isSafeInteger(limits.maxTokens) || limits.maxTokens < 0 || text.length > limits.maxBytes)
    throw new NativeVectorError("resource-limit");
  if (declaredCount !== undefined && (typeof declaredCount !== "string" || !/^(0|[1-9][0-9]*)$/.test(declaredCount)))
    throw new NativeVectorError("count-correspondence");
  if (declaredCount !== undefined && (declaredCount.length > String(limits.maxTokens).length || BigInt(declaredCount) > BigInt(limits.maxTokens)))
    throw new NativeVectorError("resource-limit");
  const tokens = [];
  let start = 0;
  for (let end = 0;end <= text.length; end++) {
    if (end < text.length && text.charCodeAt(end) !== 32)
      continue;
    if (text.length === 0)
      break;
    if (tokens.length === limits.maxTokens)
      throw new NativeVectorError("resource-limit");
    const token = text.slice(start, end);
    const grammar = family === "oidvector" ? /^(0|[1-9][0-9]*)$/ : /^(0|-?[1-9][0-9]*)$/;
    if (!grammar.test(token))
      throw new NativeVectorError("output-grammar");
    if (token.length > (family === "oidvector" ? 10 : 6))
      throw new NativeVectorError("native-domain");
    const value = BigInt(token);
    if (family === "oidvector" ? value > 4294967295n : value < -32768n || value > 32767n)
      throw new NativeVectorError("native-domain");
    tokens.push(token);
    start = end + 1;
  }
  if (declaredCount !== undefined && BigInt(declaredCount) !== BigInt(tokens.length))
    throw new NativeVectorError("count-correspondence");
  return Object.freeze({ family, originalText: text, tokens: Object.freeze(tokens) });
}
export {
  INERT_ASSEMBLY_PROFILE,
  NativeVectorError,
  createReferenceAssembly,
  decodeNativeVector
};
