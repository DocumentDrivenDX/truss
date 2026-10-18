// @bun
// packages/umf-bun/src/python-preparation-core08.ts
import { resolve as resolve2 } from "path";

// packages/postgresql/src/original-byte-custody.ts
var typed = Object.getPrototypeOf(Uint8Array.prototype);
var brand = Object.getOwnPropertyDescriptor(typed, Symbol.toStringTag).get;
var length = Object.getOwnPropertyDescriptor(typed, "length").get;
var buffer = Object.getOwnPropertyDescriptor(typed, "buffer").get;
var ordinaryLength = Object.getOwnPropertyDescriptor(ArrayBuffer.prototype, "byteLength").get;
var set = Uint8Array.prototype.set;

class OriginalByteCustodyError extends Error {
  reason;
  constructor(reason) {
    super(reason);
    this.reason = reason;
  }
}
function copyOriginalByteCustody(original, ordinaryOnly = false, maxBytes = 1048576) {
  if (typeof ordinaryOnly !== "boolean" || !Number.isSafeInteger(maxBytes) || maxBytes < 0 || maxBytes > 16777216)
    throw new OriginalByteCustodyError("resource");
  if (brand.call(original) !== "Uint8Array")
    throw new OriginalByteCustodyError("carrier");
  const size = length.call(original);
  if (size > maxBytes)
    throw new OriginalByteCustodyError("resource");
  if (ordinaryOnly) {
    try {
      ordinaryLength.call(buffer.call(original));
    } catch {
      throw new OriginalByteCustodyError("carrier");
    }
  }
  const owned = new Uint8Array(size);
  try {
    set.call(owned, original);
  } catch {
    throw new OriginalByteCustodyError("carrier");
  }
  return owned;
}

// packages/postgresql/src/acceptance-json.ts
class AcceptanceJsonError extends Error {
  reason;
  constructor(reason) {
    super(reason);
    this.reason = reason;
  }
}
var MAX_DEPTH = 128;
var MAX_NODES = 1e5;
var MAX_MEMBERS = 4096;
function decodeAcceptanceJson(original) {
  return scanJson(original, false, undefined, 16777216);
}
function preflightSourceJson(original) {
  scanJson(original, true, undefined, 4194304, 1e6, 65536);
}
var originalIndexes = new WeakMap;
function scanJson(original, sourceNumbers, capture, maximumBytes = 1048576, maximumNodes = MAX_NODES, maximumMembers = MAX_MEMBERS) {
  const refuse = (reason) => {
    throw new AcceptanceJsonError(reason);
  };
  let bytes;
  try {
    bytes = copyOriginalByteCustody(original, false, maximumBytes);
  } catch (error) {
    if (error instanceof OriginalByteCustodyError)
      refuse(error.reason === "resource" ? "resource" : "grammar");
    throw error;
  }
  if (capture)
    capture.bytes = bytes;
  let index = 0, nodes = 0;
  const stack = [];
  let root;
  const take = () => bytes[index++];
  const whitespace = () => {
    while (index < bytes.length && [32, 9, 10, 13].includes(bytes[index]))
      take();
  };
  const string = () => {
    const start = index;
    if (take() !== 34)
      refuse("grammar");
    let closed = false;
    while (index < bytes.length) {
      const c = take();
      if (c === 34) {
        closed = true;
        break;
      }
      if (c < 32)
        refuse("grammar");
      if (c === 92) {
        const e = take();
        if (e === 117) {
          let code = 0;
          for (let n = 0;n < 4; n++) {
            const h = take();
            const v = h !== undefined ? parseInt(String.fromCharCode(h), 16) : NaN;
            if (!Number.isInteger(v) || !/[0-9a-fA-F]/.test(String.fromCharCode(h)))
              refuse("grammar");
            code = code * 16 + v;
          }
          if (code >= 55296 && code <= 56319) {
            if (take() !== 92 || take() !== 117)
              refuse("unicode");
            let low = 0;
            for (let n = 0;n < 4; n++) {
              const h = take();
              if (h === undefined || !/[0-9a-fA-F]/.test(String.fromCharCode(h)))
                refuse("unicode");
              low = low * 16 + parseInt(String.fromCharCode(h), 16);
            }
            if (low < 56320 || low > 57343)
              refuse("unicode");
          } else if (code >= 56320 && code <= 57343)
            refuse("unicode");
        } else if (![34, 92, 47, 98, 102, 110, 114, 116].includes(e))
          refuse("grammar");
      }
    }
    if (!closed)
      refuse("grammar");
    let text;
    try {
      text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes.subarray(start, index));
    } catch {
      refuse("unicode");
    }
    try {
      return JSON.parse(text);
    } catch {
      return refuse("grammar");
    }
  };
  const attach = (value) => {
    const parent = stack.at(-1);
    if (!parent) {
      if (root !== undefined)
        refuse("grammar");
      root = value;
      return;
    }
    if (parent.kind === "array") {
      if (parent.value.length >= maximumMembers)
        refuse("resource");
      parent.value.push(value);
      parent.state = "comma";
    } else {
      Object.defineProperty(parent.value, parent.key, { value, enumerable: true, writable: true, configurable: true });
      parent.state = "comma";
    }
  };
  const close = () => {
    take();
    const frame = stack.pop();
    if (capture && frame.occurrence !== undefined)
      capture.occurrences[frame.occurrence].end = index;
  };
  const value = () => {
    whitespace();
    const start = index, parent = stack.at(-1);
    let pointer = "";
    if (capture && parent) {
      const prefix = capture.occurrences[parent.occurrence].pointer;
      pointer = prefix + "/" + (parent.kind === "array" ? String(parent.value.length) : parent.key.replace(/~/g, "~0").replace(/\//g, "~1"));
    }
    const record = (kind) => {
      if (!capture)
        return;
      const position = capture.occurrences.length;
      capture.occurrences.push({ pointer, kind, start, end: index });
      return position;
    };
    if (++nodes > maximumNodes || stack.length > MAX_DEPTH)
      refuse("resource");
    const c = bytes[index];
    if (c === 34) {
      const text = string();
      record("string");
      attach(text);
      return;
    }
    if (c === 123 || c === 91) {
      take();
      const item = c === 123 ? Object.create(null) : [];
      const occurrence = record(c === 123 ? "object" : "array");
      attach(item);
      stack.push(c === 123 ? { kind: "object", value: item, state: "first", key: "", keys: new Set, occurrence } : { kind: "array", value: item, state: "first", occurrence });
      return;
    }
    for (const [token, result] of [["null", null], ["true", true], ["false", false]]) {
      if (c === token.charCodeAt(0)) {
        for (const ch of token)
          if (take() !== ch.charCodeAt(0))
            refuse("grammar");
        record(result === null ? "null" : "boolean");
        attach(result);
        return;
      }
    }
    if (c === 45 || c !== undefined && c >= 48 && c <= 57) {
      if (!sourceNumbers)
        refuse("numeric_node");
      const digit = () => bytes[index] !== undefined && bytes[index] >= 48 && bytes[index] <= 57;
      if (bytes[index] === 45)
        take();
      if (bytes[index] === 48)
        take();
      else {
        if (!digit() || bytes[index] === 48)
          refuse("grammar");
        while (digit())
          take();
      }
      if (bytes[index] === 46) {
        take();
        if (!digit())
          refuse("grammar");
        while (digit())
          take();
      }
      if (bytes[index] === 101 || bytes[index] === 69) {
        take();
        if (bytes[index] === 43 || bytes[index] === 45)
          take();
        if (!digit())
          refuse("grammar");
        while (digit())
          take();
      }
      record("number");
      attach(null);
      return;
    }
    refuse("grammar");
  };
  value();
  while (stack.length) {
    whitespace();
    const frame = stack.at(-1);
    const c = bytes[index];
    if (frame.kind === "array") {
      if (frame.state === "first" && c === 93) {
        close();
      } else if (frame.state === "first" || frame.state === "value")
        value();
      else if (c === 93) {
        close();
      } else if (c === 44) {
        take();
        frame.state = "value";
      } else
        refuse("grammar");
    } else {
      if (frame.state === "first" && c === 125) {
        close();
      } else if (frame.state === "first" || frame.state === "key") {
        if (c !== 34)
          refuse("grammar");
        if (frame.keys.size >= maximumMembers)
          refuse("resource");
        const key = string();
        if (frame.keys.has(key))
          refuse("duplicate_member");
        frame.keys.add(key);
        frame.key = key;
        frame.state = "colon";
      } else if (frame.state === "colon") {
        if (take() !== 58)
          refuse("grammar");
        frame.state = "value";
      } else if (frame.state === "value")
        value();
      else if (c === 125) {
        close();
      } else if (c === 44) {
        take();
        frame.state = "key";
      } else
        refuse("grammar");
    }
  }
  whitespace();
  if (index !== bytes.length || root === undefined)
    refuse("grammar");
  return root;
}

// packages/umf-bun/src/acceptance-input.ts
import { createRequire } from "module";
import { readFile } from "fs/promises";
import { createHash } from "crypto";
var SCHEMA_SHA = "0278cbbbde843091c005b688fd9c081a2fdff843b9adda006ba80fb87828d7cd";
var digest = (bytes) => createHash("sha256").update(bytes).digest("hex");

class AcceptanceInputInspectionError extends Error {
  reason;
  constructor(reason) {
    super(reason);
    this.reason = reason;
  }
}
async function createAcceptanceInputInspector(dependenciesPackage, schemaUrl = new URL("../../../docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json", import.meta.url)) {
  const schemaBytes = await readFile(schemaUrl);
  if (digest(schemaBytes) !== SCHEMA_SHA)
    throw Error("Original acceptance schema pin mismatch");
  const require2 = createRequire(dependenciesPackage);
  const Ajv = require2("ajv/dist/2020").default;
  const validate = new Ajv({ strict: true }).compile(JSON.parse(schemaBytes.toString("utf8")));
  return Object.freeze({ schemaSha256: SCHEMA_SHA, inspect(original) {
    let owned;
    try {
      owned = copyOriginalByteCustody(original, true, 16777216);
    } catch (error) {
      if (error instanceof OriginalByteCustodyError)
        throw new AcceptanceInputInspectionError(error.reason === "resource" ? "resource" : "source_custody");
      throw error;
    }
    const input = decodeAcceptanceJson(owned);
    if (!validate(input))
      throw new AcceptanceInputInspectionError("schema");
    const wire = input;
    if (wire.documents.length > 512)
      throw new AcceptanceInputInspectionError("resource");
    let totalArtifacts = 0;
    const documents = [];
    const identities = new Set;
    function artifact(value) {
      const bytes = Buffer.from(value.bytesBase64, "base64");
      if (bytes.toString("base64") !== value.bytesBase64 || digest(bytes) !== value.sha256)
        throw new AcceptanceInputInspectionError("artifact_integrity");
      totalArtifacts += bytes.length;
      if (bytes.length > 4194304 || totalArtifacts > 16777216)
        throw new AcceptanceInputInspectionError("resource");
      return bytes;
    }
    for (const document of wire.documents) {
      if (identities.has(document.documentId))
        throw new AcceptanceInputInspectionError("document_identity");
      identities.add(document.documentId);
      const bytes = artifact(document.artifact);
      let text;
      try {
        text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
      } catch {
        throw new AcceptanceInputInspectionError("document_encoding");
      }
      documents.push(Object.freeze({ documentId: document.documentId, documentRevision: document.documentRevision, originalText: text, sha256: document.artifact.sha256 }));
      if (document.ingress.kind === "converted") {
        artifact(document.ingress.source);
        artifact(document.ingress.lossReport);
      }
    }
    if (wire.binding.state === "present")
      artifact(wire.binding.artifact);
    function freeze(value) {
      if (value && typeof value === "object") {
        for (const child of Object.values(value))
          freeze(child);
        Object.freeze(value);
      }
    }
    freeze(wire);
    return Object.freeze({ input: wire, documents: Object.freeze(documents), originalUtf8Hex: Buffer.from(owned).toString("hex"), schemaSha256: SCHEMA_SHA, scope: "wire_and_artifact_inspection_only" });
  } });
}

// packages/umf-bun/src/index.ts
import { resolve } from "path";

// packages/umf-bun/src/catalog-transition-correspondence.ts
function requireUnchangedCatalogTransition(originalSourceJson, source, transition, verified, rollback) {
  const originalCandidates = [source, transition.source, verified.source, rollback.target];
  if (originalCandidates.some((value) => JSON.stringify(value) !== originalSourceJson))
    throw Error("Original transition source correspondence mismatch");
  const target = JSON.stringify(verified.target);
  if (target === undefined || JSON.stringify(transition.target) !== target || JSON.stringify(rollback.source) !== target)
    throw Error("Original transition target correspondence mismatch");
}

// packages/umf-bun/src/index.ts
var assertionOwners = new WeakMap;
function registerAssertionOwner(owner, mode) {
  assertionOwners.set(owner, mode);
  return owner;
}
var UMF_RECORD_SOURCE = "aa944733fc45c090853ca051fd79c26bd3681307";
async function loadUmfProducer(directory) {
  const { hash, captured } = await loadPinnedFunctions(directory, UMF_RECORD_SOURCE, "record", ["withCatalogResourceProfile", "readDocument", "validateDocument", "validateCoreRecordValues", "upgradeSchemaPropertiesEnvelope", "verifySchemaPropertiesUpgrade", "rollbackSchemaPropertiesEnvelope"]);
  return Object.freeze({
    sourceRevision: UMF_RECORD_SOURCE,
    bundleSha256: hash,
    inspect(originalText) {
      return captured.withCatalogResourceProfile(() => {
        if (typeof originalText !== "string" || Buffer.byteLength(originalText) > 4194304)
          throw Error("Original document bound");
        const source = captured.readDocument(originalText, "json");
        const sourceValidation = captured.validateDocument(source);
        if (!sourceValidation.valid)
          return { originalText, source, sourceValidation, transition: null, targetValidation: null };
        let transition = null, target = source;
        if (source.umf === "0.7.0") {
          const originalSourceJson = JSON.stringify(source);
          transition = captured.upgradeSchemaPropertiesEnvelope(source);
          const verified = captured.verifySchemaPropertiesUpgrade(transition);
          const restored = captured.rollbackSchemaPropertiesEnvelope(transition, transition.target);
          requireUnchangedCatalogTransition(originalSourceJson, source, transition, verified, restored);
          target = transition.target;
        } else if (source.umf !== "0.8.0")
          throw Error("Unsupported original UMF version");
        return { originalText, source, sourceValidation, transition, targetValidation: captured.validateDocument(target), target };
      });
    },
    inspectCatalog(originalText) {
      return captured.withCatalogResourceProfile(() => {
        if (typeof originalText !== "string" || Buffer.byteLength(originalText) > 4194304)
          throw Error("Original document bound");
        const source = captured.readDocument(originalText, "json");
        if (!["0.7.0", "0.8.0"].includes(source.umf))
          throw Error("Unsupported original UMF version");
        const sourceValidation = captured.validateDocument(source);
        return { originalText, source, sourceValidation, transition: null, targetValidation: sourceValidation, target: source };
      });
    },
    checkRecord(target, identity, values) {
      return captured.validateCoreRecordValues(target, identity, values);
    }
  });
}
async function loadPinnedFunctions(directory, revision, mode, names) {
  const root = resolve(directory);
  const manifest = await Bun.file(root + "/producer-manifest.json").json();
  const bytes = await Bun.file(root + "/producer.js").arrayBuffer();
  const hash = new Bun.CryptoHasher("sha256").update(bytes).digest("hex");
  if (manifest.revision !== revision || (manifest.producerMode ?? "record") !== mode || manifest.bundleSha256 !== hash)
    throw Error("Original UMF producer pin mismatch");
  const owner = await import(root + "/producer.js");
  const captured = Object.fromEntries(names.map((name) => {
    if (typeof owner[name] !== "function")
      throw Error("Missing original producer");
    return [name, owner[name].bind(owner)];
  }));
  return { hash, captured };
}
var UMF_CORE08_CATALOG_SOURCE = "aa944733fc45c090853ca051fd79c26bd3681307";
async function loadCore08CatalogOwners(directory) {
  const revision = UMF_CORE08_CATALOG_SOURCE;
  const { hash, captured } = await loadPinnedFunctions(directory, revision, "core08-catalog", [
    "withCatalogResourceProfile",
    "readDocument",
    "validateDocument",
    "inspectCoreSchemaProperties",
    "inspectCoreKeys",
    "inspectCoreRelationships",
    "inspectCoreElementKind",
    "inspectCoreNullability",
    "inspectCoreCardinality",
    "inspectCoreFacets",
    "inspectCoreScalarType",
    "inspectCoreRecordMembers",
    "inspectCoreReferenceLinks"
  ]);
  const pin = { sourceRevision: revision, bundleSha256: hash };
  const record = Object.freeze({ ...pin, inspect(originalText) {
    return captured.withCatalogResourceProfile(() => {
      if (typeof originalText !== "string" || Buffer.byteLength(originalText) > 4194304)
        throw Error("Original document bound");
      const source = captured.readDocument(originalText, "json");
      if (source.umf !== "0.8.0")
        throw Error("Unsupported original UMF version");
      const sourceValidation = captured.validateDocument(source);
      return { originalText, source, sourceValidation, transition: null, targetValidation: sourceValidation, target: source };
    });
  } });
  return Object.freeze({
    record,
    declarations: registerAssertionOwner(Object.freeze({ ...pin, inspectSchemaProperties: captured.inspectCoreSchemaProperties, inspectKeys: captured.inspectCoreKeys, inspectRelationships: captured.inspectCoreRelationships }), "declarations"),
    fields: registerAssertionOwner(Object.freeze({ ...pin, inspectKind: captured.inspectCoreElementKind, inspectNullability: captured.inspectCoreNullability, inspectCardinality: captured.inspectCoreCardinality, inspectFacets: captured.inspectCoreFacets }), "assertion-fields"),
    scalars: registerAssertionOwner(Object.freeze({ ...pin, inspectScalarType: captured.inspectCoreScalarType }), "scalar-types"),
    members: registerAssertionOwner(Object.freeze({ ...pin, inspectRecordMembers: captured.inspectCoreRecordMembers }), "record-members"),
    links: registerAssertionOwner(Object.freeze({ ...pin, inspectReferenceLinks: captured.inspectCoreReferenceLinks }), "reference-links")
  });
}

// packages/umf-bun/src/catalog-declarations.ts
function object(value) {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw Error("Original catalog object required");
  return value;
}
function array(value) {
  if (!Array.isArray(value))
    throw Error("Original catalog array required");
  return value;
}
function identity(value) {
  if (typeof value !== "string" || !value.length)
    throw Error("Original catalog identity required");
  return value;
}
function collectCatalogDeclarations(documentId, source) {
  const document = object(source);
  if (document.id !== documentId)
    throw Error("Original catalog document mismatch");
  const modules = array(document.modules).map(object);
  const moduleIndex = new Map;
  const elementIndexes = new Map;
  for (const module of modules) {
    const key = identity(module.id);
    const matches = moduleIndex.get(key) ?? [];
    matches.push(module);
    moduleIndex.set(key, matches);
    const elements = new Map;
    for (const value of array(module.elements)) {
      const element = object(value);
      const key = identity(element.id);
      const matches = elements.get(key) ?? [];
      matches.push(element);
      elements.set(key, matches);
    }
    elementIndexes.set(module, elements);
  }
  const records = [];
  const relationships = [];
  for (const module of modules) {
    const moduleId = identity(module.id);
    for (const value of array(module.elements)) {
      const declaration = object(value);
      if (declaration.kind !== "record")
        continue;
      const elementId = identity(declaration.id);
      const membership = Object.hasOwn(declaration, "members") ? "declared" : "missing";
      const fields = (membership === "declared" ? array(declaration.members) : []).map((value) => {
        const reference = object(value);
        const fieldModule = identity(reference.module);
        const fieldId = identity(reference.element);
        const declaringModules = moduleIndex.get(fieldModule) ?? [];
        if (declaringModules.length !== 1)
          throw Error("Original member module correspondence unavailable");
        const fields = elementIndexes.get(declaringModules[0]).get(fieldId) ?? [];
        if (fields.length !== 1 || fields[0].kind !== "field")
          throw Error("Original member Field correspondence unavailable");
        return Object.freeze({ fieldModule, fieldId, reference, declaration: fields[0] });
      });
      const keys = declaration.keys === undefined ? [] : array(declaration.keys).map((value) => {
        const key = object(value);
        identity(key.id);
        for (const value of array(key.fields)) {
          const reference = object(value);
          if (!fields.some((field) => field.fieldModule === reference.module && field.fieldId === reference.element))
            throw Error("Original key member correspondence unavailable");
        }
        return key;
      });
      records.push(Object.freeze({ documentId, moduleId, elementId, declaration, membership, fields: Object.freeze(fields), keys: Object.freeze(keys) }));
    }
    if (module.relationships !== undefined)
      for (const value of array(module.relationships)) {
        const declaration = object(value);
        identity(declaration.id);
        relationships.push(Object.freeze({ documentId, moduleId, declaration }));
      }
  }
  return Object.freeze({ records: Object.freeze(records), relationships: Object.freeze(relationships), scope: "original_declaration_correspondence_only" });
}

// packages/umf-bun/src/acceptance-profiles.ts
var originalResolvers = new WeakSet;

// packages/umf-bun/src/catalog-input.ts
class CatalogDocumentRejected extends Error {
  documentId;
  documentRevision;
  originalError;
  observation;
  constructor(documentId, documentRevision, originalError, observation) {
    super("invalid_document");
    this.documentId = documentId;
    this.documentRevision = documentRevision;
    this.originalError = originalError;
    this.observation = observation;
  }
}
var originalPreparations = new WeakSet;
async function createCore08CatalogInputPreparation(directory, dependenciesPackage, schemaUrl) {
  return createPreparation(directory, dependenciesPackage, undefined, true, schemaUrl);
}
async function createPreparation(directory, dependenciesPackage, profiles, current, schemaUrl) {
  const inspector = await createAcceptanceInputInspector(dependenciesPackage, schemaUrl);
  const owner = current ? (await loadCore08CatalogOwners(directory)).record : await loadUmfProducer(directory);
  const umfProfile = Object.freeze({ identity: "umf-record-interpretation", version: owner.sourceRevision, sha256: owner.bundleSha256 });
  const equal = (a, b) => a.identity === b.identity && a.version === b.version && a.sha256 === b.sha256;
  return Object.freeze({ umfProfile, prepare(original) {
    const inspected = inspector.inspect(original);
    const registeredProfiles = profiles?.resolve(inspected.input) ?? null;
    const documents = [];
    for (let i = 0;i < inspected.input.documents.length; i++) {
      const declaration = inspected.input.documents[i];
      const source = inspected.documents[i];
      if (!equal(declaration.umfProfile, umfProfile))
        throw Error("Unsupported original UMF profile");
      if (declaration.ingress.kind !== "native")
        throw Error("Original converted adapter registration unavailable");
      preflightSourceJson(new TextEncoder().encode(source.originalText));
      let observation;
      try {
        observation = "inspectCatalog" in owner ? owner.inspectCatalog(source.originalText) : owner.inspect(source.originalText);
      } catch (error) {
        throw new CatalogDocumentRejected(source.documentId, source.documentRevision, error);
      }
      if (!observation.sourceValidation.valid || !observation.targetValidation?.valid)
        throw new CatalogDocumentRejected(source.documentId, source.documentRevision, null, observation);
      if (observation.source.id !== source.documentId)
        throw Error("Original document identity mismatch");
      documents.push(Object.freeze({
        documentId: source.documentId,
        revision: source.documentRevision,
        umfVersion: observation.source.umf,
        originalText: source.originalText,
        validation: { sourceValidation: observation.sourceValidation, transition: observation.transition },
        interpretation: observation
      }));
    }
    const declarations = () => documents.map((document) => collectCatalogDeclarations(document.documentId, document.interpretation.source));
    const archiveDocuments = documents.map(({ interpretation, ...archive }) => Object.freeze(archive));
    function freeze(value) {
      if (value && typeof value === "object" && !Object.isFrozen(value)) {
        for (const child of Object.values(value))
          freeze(child);
        Object.freeze(value);
      }
    }
    freeze(documents);
    freeze(archiveDocuments);
    const prepared = Object.freeze({ original: inspected, registeredProfiles, documents: Object.freeze(documents), get declarations() {
      return Object.freeze(declarations());
    }, archiveDocuments: Object.freeze(archiveDocuments), umfProfile, scope: "original_umf_preparation_only" });
    originalPreparations.add(prepared);
    return prepared;
  } });
}

// packages/umf-bun/src/python-preparation-core08.ts
var root = resolve2(import.meta.dir);
var dependencies = resolve2(root, "../_umf/runtime/package.json");
var schemaUrl = new URL("./acceptance-input-v0.1.schema.json", import.meta.url);
var MAX_OUTPUT = 67108864;
var emit = (value) => {
  const text = JSON.stringify(value);
  console.log(Buffer.byteLength(text) + 1 <= MAX_OUTPUT ? text : JSON.stringify({ status: "refused", reason: "resource", diagnostics: [] }));
};
var diagnostics = [];
try {
  const bytes = new Uint8Array(await Bun.stdin.arrayBuffer());
  if (bytes.length > 16777216)
    throw Error("resource");
  const request = decodeAcceptanceJson(bytes);
  if (!["configurationHex,documents", "configurationHex,documents,registration"].includes(Object.keys(request).sort().join(",")) || Object.hasOwn(request, "registration") && request.registration !== true || typeof request.configurationHex !== "string" || !/^(?:[0-9a-f]{2})+$/.test(request.configurationHex) || !Array.isArray(request.documents) || request.documents.length < 1 || request.documents.length > 512)
    throw Error("invalid_input");
  const configuration = decodeAcceptanceJson(Buffer.from(request.configurationHex, "hex"));
  if (!configuration || typeof configuration !== "object" || Array.isArray(configuration) || Object.hasOwn(configuration, "documents") || Object.hasOwn(configuration, "interfaceVersion"))
    throw Error("invalid_input");
  const preparation = await createCore08CatalogInputPreparation(root, dependencies, schemaUrl);
  const current = await loadCore08CatalogOwners(root);
  const owner = current.record;
  const documents = request.documents.map((d) => {
    if (!d || Object.keys(d).sort().join(",") !== "artifact,documentId,documentRevision")
      throw Error("invalid_input");
    return { ...d, umfProfile: preparation.umfProfile, ingress: { kind: "native" } };
  });
  const input = { interfaceVersion: "truss-acceptance-input/0.1.0", ...configuration, documents };
  const original = new TextEncoder().encode(JSON.stringify(input));
  const prepared = preparation.prepare(original);
  const reportEvidence = {
    interfaceVersion: "truss-registration-preparation/2.0",
    documents: prepared.documents.map((document, index) => ({
      documentId: document.documentId,
      contentSha256: prepared.original.documents[index].sha256,
      validation: document.interpretation.sourceValidation
    }))
  };
  const descriptor = {
    ...prepared.original.input,
    interfaceVersion: "truss-acceptance-input/0.2.0",
    documents: prepared.original.input.documents.map((document) => ({
      ...document,
      artifact: { identity: document.artifact.identity, sha256: document.artifact.sha256 }
    }))
  };
  const response = {
    status: "prepared",
    input: descriptor,
    documents: prepared.documents.map((document) => ({
      documentId: document.documentId,
      revision: document.revision,
      umfVersion: document.umfVersion,
      validation: document.interpretation.sourceValidation
    })),
    reportEvidence,
    provenance: { umfProfile: prepared.umfProfile, schemaSha256: prepared.original.schemaSha256, scope: prepared.scope }
  };
  emit(response);
} catch (error) {
  if (error instanceof CatalogDocumentRejected) {
    const cause = error.originalError;
    const message = cause instanceof Error ? cause.message : "Original document refused";
    diagnostics = [{
      documentId: error.documentId,
      documentRevision: error.documentRevision,
      ...error.observation ? { observation: error.observation } : { originalError: {
        message: message.slice(0, 8192),
        truncated: message.length > 8192,
        ...typeof cause?.code === "string" ? { code: cause.code.slice(0, 256) } : {},
        ...typeof cause?.path === "string" ? { path: cause.path.slice(0, 8192) } : {}
      } }
    }];
  }
  const message = error instanceof Error ? error.message : "";
  const reason = message === "invalid_document" ? "invalid_document" : message === "resource" ? "resource" : message.includes("Unsupported") ? "unsupported_profile" : message.includes("pin mismatch") || message.includes("Missing original producer") ? "producer_unavailable" : "invalid_input";
  emit({ status: "refused", reason, diagnostics });
}
