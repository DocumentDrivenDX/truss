// @bun
var __esm = (fn, res, err) => () => {
  if (fn)
    try {
      res = fn(fn = 0);
    } catch (e) {
      err = [e];
    }
  if (err)
    throw err[0];
  return res;
};

// packages/postgresql/src/original-byte-custody.ts
function copyOriginalByteCustody(original, ordinaryOnly = false, maxBytes = 1048576) {
  if (typeof ordinaryOnly !== "boolean" || !Number.isSafeInteger(maxBytes) || maxBytes < 0 || maxBytes > 1048576)
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
var typed, brand, length, buffer, ordinaryLength, set, OriginalByteCustodyError;
var init_original_byte_custody = __esm(() => {
  typed = Object.getPrototypeOf(Uint8Array.prototype);
  brand = Object.getOwnPropertyDescriptor(typed, Symbol.toStringTag).get;
  length = Object.getOwnPropertyDescriptor(typed, "length").get;
  buffer = Object.getOwnPropertyDescriptor(typed, "buffer").get;
  ordinaryLength = Object.getOwnPropertyDescriptor(ArrayBuffer.prototype, "byteLength").get;
  set = Uint8Array.prototype.set;
  OriginalByteCustodyError = class OriginalByteCustodyError extends Error {
    reason;
    constructor(reason) {
      super(reason);
      this.reason = reason;
    }
  };
});

// packages/postgresql/src/acceptance-json.ts
function decodeAcceptanceJson(original) {
  return scanJson(original, false);
}
function preflightSourceJson(original) {
  scanJson(original, true);
}
function scanJson(original, sourceNumbers, capture) {
  const refuse = (reason) => {
    throw new AcceptanceJsonError(reason);
  };
  let bytes;
  try {
    bytes = copyOriginalByteCustody(original);
  } catch (error) {
    if (error instanceof OriginalByteCustodyError)
      refuse(error.reason === "resource" ? "resource" : "grammar");
    throw error;
  }
  if (capture)
    capture.bytes = bytes;
  let index = 0, nodes = 0, work = bytes.length;
  const stack = [];
  let root;
  const charge = (n) => {
    if (!Number.isSafeInteger(n) || n < 0 || work > MAX_WORK - n)
      refuse("resource");
    work += n;
  };
  const take = () => {
    charge(1);
    return bytes[index++];
  };
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
    charge(2 * (index - start));
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
      if (parent.value.length >= MAX_MEMBERS)
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
      charge(2 * pointer.length);
    }
    const record = (kind) => {
      if (!capture)
        return;
      const position = capture.occurrences.length;
      capture.occurrences.push({ pointer, kind, start, end: index });
      return position;
    };
    if (++nodes > MAX_NODES || stack.length > MAX_DEPTH)
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
      stack.push(c === 123 ? { kind: "object", value: item, state: "first", key: "", keys: [], occurrence } : { kind: "array", value: item, state: "first", occurrence });
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
        if (frame.keys.length >= MAX_MEMBERS)
          refuse("resource");
        const key = string();
        for (const previous of frame.keys) {
          charge(2 * (previous.length + key.length));
          if (previous === key)
            refuse("duplicate_member");
        }
        frame.keys.push(key);
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
var AcceptanceJsonError, MAX_DEPTH = 128, MAX_NODES = 1e5, MAX_MEMBERS = 4096, MAX_WORK = 2000000, originalIndexes;
var init_acceptance_json = __esm(() => {
  init_original_byte_custody();
  AcceptanceJsonError = class AcceptanceJsonError extends Error {
    reason;
    constructor(reason) {
      super(reason);
      this.reason = reason;
    }
  };
  originalIndexes = new WeakMap;
});

// packages/umf-bun/src/acceptance-input.ts
import { createRequire } from "module";
import { readFile } from "fs/promises";
import { createHash } from "crypto";
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
      owned = copyOriginalByteCustody(original, true);
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
      if (bytes.length > 1048576 || totalArtifacts > 4194304)
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
var SCHEMA_SHA = "0278cbbbde843091c005b688fd9c081a2fdff843b9adda006ba80fb87828d7cd", digest = (bytes) => createHash("sha256").update(bytes).digest("hex"), AcceptanceInputInspectionError;
var init_acceptance_input = __esm(() => {
  init_original_byte_custody();
  init_acceptance_json();
  AcceptanceInputInspectionError = class AcceptanceInputInspectionError extends Error {
    reason;
    constructor(reason) {
      super(reason);
      this.reason = reason;
    }
  };
});

// packages/umf-bun/src/python-preparation-core08.ts
import { resolve as resolve2 } from "path";

// packages/umf-bun/src/catalog-input.ts
init_acceptance_json();
init_acceptance_input();

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
function requireLoadedUmfAssertionOwner(owner, mode) {
  if (assertionOwners.get(owner) !== mode)
    throw Error("Original loaded assertion owner required");
}
var UMF_RUNTIME_SOURCE = "c45c72a2a8a3c4fba61c40c5927dd9091acf8cc3";
async function loadUmfProducer(directory) {
  const { hash, captured } = await loadPinnedFunctions(directory, UMF_RUNTIME_SOURCE, "record", ["readDocument", "validateDocument", "validateCoreRecordValues", "upgradeSchemaPropertiesEnvelope", "verifySchemaPropertiesUpgrade", "rollbackSchemaPropertiesEnvelope"]);
  return Object.freeze({
    sourceRevision: UMF_RUNTIME_SOURCE,
    bundleSha256: hash,
    inspect(originalText) {
      if (typeof originalText !== "string" || Buffer.byteLength(originalText) > 1048576)
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
var UMF_SCALAR_TYPE_SOURCE = "94d0a99e4d1e9eb39278f38d6cd6bcba51e46db8";
var UMF_RECORD_MEMBERS_SOURCE = "5ddc656273e1965efa0187f3090d165d45225dcd";
var UMF_REFERENCE_LINKS_SOURCE = "9545b7119ceaa29ca7523e4722ec52412084d835";
var UMF_CORE08_CATALOG_SOURCE = "7c0f0c98beee2cc1a5a407992b5c53cc2616da8e";
async function loadCore08CatalogOwners(directory) {
  const revision = UMF_CORE08_CATALOG_SOURCE;
  const { hash, captured } = await loadPinnedFunctions(directory, revision, "core08-catalog", [
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
    if (typeof originalText !== "string" || Buffer.byteLength(originalText) > 1048576)
      throw Error("Original document bound");
    const source = captured.readDocument(originalText, "json");
    if (source.umf !== "0.8.0")
      throw Error("Unsupported original UMF version");
    const sourceValidation = captured.validateDocument(source);
    return { originalText, source, sourceValidation, transition: null, targetValidation: sourceValidation, target: source };
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
        const declaringModules = modules.filter((candidate) => candidate.id === fieldModule);
        if (declaringModules.length !== 1)
          throw Error("Original member module correspondence unavailable");
        const fields = array(declaringModules[0].elements).map(object).filter((candidate) => candidate.id === fieldId);
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
var originalPreparations = new WeakSet;
function requireOriginalCatalogPreparation(prepared) {
  if (!originalPreparations.has(prepared))
    throw Error("Original validated catalog preparation required");
}
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
      const observation = owner.inspect(source.originalText);
      if (!observation.sourceValidation.valid || !observation.targetValidation?.valid)
        throw Error("Original UMF validation refused");
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
    const declarations = documents.map((document) => collectCatalogDeclarations(document.documentId, document.interpretation.source));
    const archiveDocuments = documents.map(({ interpretation, ...archive }) => Object.freeze(archive));
    function freeze(value) {
      if (value && typeof value === "object") {
        for (const child of Object.values(value))
          freeze(child);
        Object.freeze(value);
      }
    }
    freeze(documents);
    freeze(archiveDocuments);
    freeze(declarations);
    const prepared = Object.freeze({ original: inspected, registeredProfiles, documents: Object.freeze(documents), declarations: Object.freeze(declarations), archiveDocuments: Object.freeze(archiveDocuments), umfProfile, scope: "original_umf_preparation_only" });
    originalPreparations.add(prepared);
    return prepared;
  } });
}

// packages/umf-bun/src/catalog-assertion-observations.ts
import { createHash as createHash2 } from "crypto";
var originalCollections = new WeakMap;
function requireOriginalCatalogObservationCollection(prepared, collection) {
  if (originalCollections.get(collection) !== prepared)
    throw Error("Original observation collection custody required");
}
function collectCatalogAssertionObservations(prepared, owner, fields, scalars, members, links) {
  requireOriginalCatalogPreparation(prepared);
  requireLoadedUmfAssertionOwner(owner, "declarations");
  if (fields)
    requireLoadedUmfAssertionOwner(fields, "assertion-fields");
  if (scalars)
    requireLoadedUmfAssertionOwner(scalars, "scalar-types");
  if (members)
    requireLoadedUmfAssertionOwner(members, "record-members");
  if (links)
    requireLoadedUmfAssertionOwner(links, "reference-links");
  if (owner.sourceRevision !== prepared.umfProfile.version)
    throw Error("Original owner observation source mismatch");
  if (fields && fields.sourceRevision !== prepared.umfProfile.version)
    throw Error("Original Field owner observation source mismatch");
  const referenceLinksProfile = links ? Object.freeze({ identity: "umf-reference-links-inspection", version: links.sourceRevision, sha256: links.bundleSha256 }) : null;
  const membersProfile = members ? Object.freeze({ identity: "umf-record-members-inspection", version: members.sourceRevision, sha256: members.bundleSha256 }) : null;
  const scalarProfile = scalars ? Object.freeze({ identity: "umf-scalar-type-inspection", version: scalars.sourceRevision, sha256: scalars.bundleSha256 }) : null;
  const fieldProfile = fields ? Object.freeze({ identity: "umf-field-assertion-inspection", version: fields.sourceRevision, sha256: fields.bundleSha256 }) : null;
  const profile = Object.freeze({ identity: "umf-declaration-inspection", version: owner.sourceRevision, sha256: owner.bundleSha256 });
  const observations = [];
  let retainedBytes = 0;
  let calls = 0;
  function capture(documentIndex, operation, identity, basis, run, observationProfile = profile) {
    if (++calls > 4096)
      throw Error("Declaration observation component call capacity exceeded");
    Object.freeze(identity);
    const document = prepared.documents[documentIndex];
    let result;
    try {
      result = { state: "observed", observation: run() };
    } catch (error) {
      result = { state: "unavailable", name: error instanceof Error ? error.name : null, code: typeof error?.code === "string" ? error.code : null, path: typeof error?.path === "string" ? error.path : null, message: error instanceof Error ? error.message : String(error) };
    }
    const bytes = Buffer.from(JSON.stringify({ profile: observationProfile, documentId: document.documentId, contentSha256: prepared.original.documents[documentIndex].sha256, basis, operation, identity, result }), "utf8");
    retainedBytes += bytes.length;
    if (retainedBytes > 4194304)
      throw Error("Declaration observation component output capacity exceeded");
    observations.push(Object.freeze({
      documentId: document.documentId,
      basis,
      operation,
      identity,
      result,
      evidence: Object.freeze({ identity: "truss.owner-declaration-observation/" + documentIndex + "/" + (calls - 1), bytesBase64: bytes.toString("base64"), sha256: createHash2("sha256").update(bytes).digest("hex") })
    }));
  }
  for (let index = 0;index < prepared.documents.length; index++) {
    const document = prepared.documents[index];
    const source = document.interpretation.source;
    const target = document.interpretation.target;
    const propertyBasis = document.interpretation.transition ? "reversible_target" : "original";
    capture(index, "schema_properties", { scope: "document" }, propertyBasis, () => owner.inspectSchemaProperties(target, { scope: "document" }));
    for (const module of source.modules) {
      const moduleIdentity = { scope: "module", module: module.id };
      capture(index, "schema_properties", moduleIdentity, propertyBasis, () => owner.inspectSchemaProperties(target, moduleIdentity));
      capture(index, "relationships", { module: module.id }, "original", () => owner.inspectRelationships(source, { module: module.id }));
      for (const element of module.elements) {
        const identity = { scope: "element", module: module.id, element: element.id };
        capture(index, "schema_properties", identity, propertyBasis, () => owner.inspectSchemaProperties(target, identity));
        if (fields) {
          const fieldIdentity = { module: module.id, element: element.id };
          for (const [operation, inspect] of [["kind", fields.inspectKind], ["nullability", fields.inspectNullability], ["cardinality", fields.inspectCardinality], ["facets", fields.inspectFacets]])
            capture(index, operation, fieldIdentity, "original", () => inspect(source, fieldIdentity), fieldProfile);
        }
        if (scalars) {
          const identity = { module: module.id, element: element.id };
          capture(index, "scalarType", identity, "original", () => scalars.inspectScalarType(source, identity), scalarProfile);
        }
        if (members) {
          const identity = { module: module.id, element: element.id };
          capture(index, "members", identity, "original", () => members.inspectRecordMembers(source, identity), membersProfile);
        }
        if (links) {
          const identity = { module: module.id, element: element.id };
          capture(index, "referenceLinks", identity, "original", () => links.inspectReferenceLinks(source, identity), referenceLinksProfile);
        }
        if (element.kind === "record")
          capture(index, "keys", { module: module.id, element: element.id }, "original", () => owner.inspectKeys(source, { module: module.id, element: element.id }));
      }
    }
  }
  function freeze(value) {
    if (value && typeof value === "object") {
      for (const child of Object.values(value))
        freeze(child);
      Object.freeze(value);
    }
  }
  freeze(observations);
  const collection = Object.freeze({ profile, fieldProfile, scalarProfile, membersProfile, referenceLinksProfile, observations: Object.freeze(observations), scope: "original_owner_assertion_observations_only" });
  originalCollections.set(collection, prepared);
  return collection;
}

// packages/umf-bun/src/catalog-observation-coverage.ts
import { createHash as createHash3 } from "crypto";
function assessCatalogObservationCoverage(prepared, collection) {
  requireOriginalCatalogObservationCollection(prepared, collection);
  const current = prepared.umfProfile.version === UMF_CORE08_CATALOG_SOURCE && prepared.documents.every((d) => d.umfVersion === "0.8.0");
  if (current) {
    for (const profile of [collection.profile, collection.fieldProfile, collection.scalarProfile, collection.membersProfile, collection.referenceLinksProfile])
      if (!profile || profile.version !== UMF_CORE08_CATALOG_SOURCE || profile.sha256 !== prepared.umfProfile.sha256)
        throw Error("Original current observation bundle required");
  }
  if (!collection.fieldProfile)
    throw Error("Complete Field observation bundle required");
  for (const [profile, identity] of [[collection.profile, "umf-declaration-inspection"], [collection.fieldProfile, "umf-field-assertion-inspection"]])
    if (profile.identity !== identity || profile.version !== prepared.umfProfile.version || !/^[0-9a-f]{64}$/.test(profile.sha256))
      throw Error("Original observation profile correspondence required");
  if (collection.scalarProfile && (collection.scalarProfile.identity !== "umf-scalar-type-inspection" || collection.scalarProfile.version !== (current ? UMF_CORE08_CATALOG_SOURCE : UMF_SCALAR_TYPE_SOURCE) || !/^[0-9a-f]{64}$/.test(collection.scalarProfile.sha256)))
    throw Error("Original scalar observation profile correspondence required");
  if (collection.membersProfile && (collection.membersProfile.identity !== "umf-record-members-inspection" || collection.membersProfile.version !== (current ? UMF_CORE08_CATALOG_SOURCE : UMF_RECORD_MEMBERS_SOURCE) || !/^[0-9a-f]{64}$/.test(collection.membersProfile.sha256)))
    throw Error("Original membership observation profile correspondence required");
  if (collection.referenceLinksProfile && (collection.referenceLinksProfile.identity !== "umf-reference-links-inspection" || collection.referenceLinksProfile.version !== (current ? UMF_CORE08_CATALOG_SOURCE : UMF_REFERENCE_LINKS_SOURCE) || !/^[0-9a-f]{64}$/.test(collection.referenceLinksProfile.sha256)))
    throw Error("Original reference-link observation profile correspondence required");
  const expected = [];
  const add = (documentIndex, operation, identity, basis, field = false) => {
    if (expected.length >= 4096)
      throw Error("Observation coverage component capacity exceeded");
    expected.push({ documentIndex, operation, identity, basis, field });
  };
  for (let i = 0;i < prepared.documents.length; i++) {
    const document = prepared.documents[i], source = document.interpretation.source, basis = document.interpretation.transition ? "reversible_target" : "original";
    add(i, "schema_properties", { scope: "document" }, basis);
    for (const module of source.modules) {
      add(i, "schema_properties", { scope: "module", module: module.id }, basis);
      add(i, "relationships", { module: module.id }, "original");
      for (const element of module.elements) {
        add(i, "schema_properties", { scope: "element", module: module.id, element: element.id }, basis);
        for (const operation of ["kind", "nullability", "cardinality", "facets"])
          add(i, operation, { module: module.id, element: element.id }, "original", true);
        if (collection.scalarProfile)
          add(i, "scalarType", { module: module.id, element: element.id }, "original");
        if (collection.membersProfile)
          add(i, "members", { module: module.id, element: element.id }, "original");
        if (collection.referenceLinksProfile)
          add(i, "referenceLinks", { module: module.id, element: element.id }, "original");
        if (element.kind === "record")
          add(i, "keys", { module: module.id, element: element.id }, "original");
      }
    }
  }
  if (collection.observations.length !== expected.length)
    throw Error("Complete original observation inventory required");
  const unavailable = [];
  let bytesRetained = 0;
  for (let index = 0;index < expected.length; index++) {
    const requirement = expected[index], observed = collection.observations[index], document = prepared.documents[requirement.documentIndex];
    if (observed.documentId !== document.documentId || observed.operation !== requirement.operation || observed.basis !== requirement.basis || JSON.stringify(observed.identity) !== JSON.stringify(requirement.identity))
      throw Error("Original ordered observation identity/basis mismatch");
    const result = observed.result;
    if (!result || !["observed", "unavailable"].includes(result.state))
      throw Error("Explicit observation availability required");
    const original = JSON.stringify({ profile: requirement.operation === "referenceLinks" ? collection.referenceLinksProfile : requirement.operation === "members" ? collection.membersProfile : requirement.operation === "scalarType" ? collection.scalarProfile : requirement.field ? collection.fieldProfile : collection.profile, documentId: document.documentId, contentSha256: prepared.original.documents[requirement.documentIndex].sha256, basis: requirement.basis, operation: requirement.operation, identity: requirement.identity, result: observed.result });
    const bytes = Buffer.from(original, "utf8");
    bytesRetained += bytes.length;
    if (bytesRetained > 4194304)
      throw Error("Observation coverage evidence capacity exceeded");
    if (observed.evidence.bytesBase64 !== bytes.toString("base64") || observed.evidence.sha256 !== createHash3("sha256").update(bytes).digest("hex") || observed.evidence.identity !== "truss.owner-declaration-observation/" + requirement.documentIndex + "/" + index)
      throw Error("Original observation evidence correspondence required");
    if (result.state === "unavailable") {
      if (!(result.code === null || typeof result.code === "string") || !(result.path === null || typeof result.path === "string"))
        throw Error("Original unavailable result required");
      unavailable.push(Object.freeze({ documentId: document.documentId, operation: requirement.operation, identity: Object.freeze(requirement.identity), code: result.code, path: result.path }));
    }
  }
  return Object.freeze({ observationsRequired: String(expected.length), observationsAvailable: String(expected.length - unavailable.length), unavailable: Object.freeze(unavailable), availability: unavailable.length ? "incomplete" : "available", scope: "original_owner_observation_correspondence_only" });
}

// packages/umf-bun/src/catalog-core-assertion-identities.ts
import { createHash as createHash4 } from "crypto";
function sameOriginalMeaning(a, b) {
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object")
    return Object.is(a, b);
  if (Array.isArray(a) !== Array.isArray(b))
    return false;
  const keys = Object.keys(a);
  if (keys.length !== Object.keys(b).length)
    return false;
  if (Array.isArray(a) && a.length !== b.length)
    return false;
  return keys.every((key) => Object.hasOwn(b, key) && sameOriginalMeaning(a[key], b[key]));
}
function collectCatalogCoreAssertionIdentities(prepared, collection) {
  requireOriginalCatalogPreparation(prepared);
  requireOriginalCatalogObservationCollection(prepared, collection);
  const current = prepared.documents.every((d) => d.umfVersion === "0.8.0");
  const identityVersion = current ? "0.7.0" : "0.6.0";
  const manifestBytes = Buffer.from(JSON.stringify({
    interfaceVersion: "truss-core-assertion-source-identity/" + identityVersion,
    producers: { fields: collection.fieldProfile, scalar: collection.scalarProfile, members: collection.membersProfile, referenceLinks: collection.referenceLinksProfile, declarations: collection.profile },
    operations: ["kind", "nullability", "cardinality", "facets", "scalarType", "members", "referenceLinks", "keys", "relationships", "schema_properties"],
    basis: "original",
    referenceLinks: "generic_core_links_not_verified_type_assertions",
    schemaPropertyAssertions: ["allowedValues", "default", "facets"],
    annotations: "retained separately; not constraint assertions",
    identity: "original document digest, qualified owner and exact owner-produced pointer",
    authored: "retain exact declaration ID with full original occurrence pointer",
    missing: "retained absence observation; no assertion invented",
    enforcement: "none/unqualified"
  }));
  const manifest = Object.freeze({ identity: "truss.core-assertion-source-identity/" + identityVersion, bytesBase64: manifestBytes.toString("base64"), sha256: createHash4("sha256").update(manifestBytes).digest("hex") });
  const profile = Object.freeze({ identity: "truss-core-assertion-source-identity", version: identityVersion, sha256: manifest.sha256 });
  const referenceLinks = [], referenceLinkDeclarations = [];
  const entries = [];
  const declarationMeanings = [];
  const membershipMeanings = [];
  const fieldMeanings = [];
  const absent = [];
  const deferred = [];
  const identities = new Set;
  for (const observed of collection.observations) {
    if (observed.basis !== "original" || !["kind", "nullability", "cardinality", "facets", "scalarType", "members", "referenceLinks", "keys", "relationships", "schema_properties"].includes(observed.operation)) {
      deferred.push(observed);
      continue;
    }
    const result = observed.result;
    if (result.state !== "observed") {
      deferred.push(observed);
      continue;
    }
    const original = result.observation, meaning = original.meaning;
    if (observed.operation === "schema_properties") {
      const di = prepared.documents.findIndex((d) => d.documentId === observed.documentId), document = prepared.documents[di], identity = observed.identity;
      if (!document || JSON.stringify(original.source) !== JSON.stringify(document.interpretation.source) || typeof original.path !== "string" || original.source.umf !== "0.8.0")
        throw Error("Original schema-property source required");
      const properties = original.properties;
      if (properties === null || typeof properties !== "object" || Array.isArray(properties))
        throw Error("Original owner property map required");
      const selected = Object.keys(properties).filter((k) => (current ? ["allowedValues", "default"] : ["allowedValues", "default", "facets"]).includes(k));
      if (Object.keys(properties).length === 0)
        absent.push(observed);
      if (Object.keys(properties).some((k) => !selected.includes(k)))
        deferred.push(observed);
      const owner = identity.scope === "document" ? Object.freeze({ scope: "document", documentId: document.documentId }) : Object.freeze({ documentId: document.documentId, moduleId: identity.module });
      if (identity.scope !== "document" && typeof identity.module !== "string")
        throw Error("Original schema-property owner required");
      const source = prepared.original.input.documents[di].artifact;
      for (const key of selected) {
        const pointer = original.path + "/" + key;
        let node = original.source;
        for (const token of pointer.slice(1).split("/")) {
          const part = token.replace(/~1/g, "/").replace(/~0/g, "~");
          if (node === null || typeof node !== "object" || !Object.hasOwn(node, part))
            throw Error("Original schema-property node absent");
          node = node[part];
        }
        if (JSON.stringify(node) !== JSON.stringify(properties[key]))
          throw Error("Original schema-property value correspondence required");
        const uniqueness = JSON.stringify([source.sha256, owner, pointer]);
        if (identities.has(uniqueness))
          throw Error("Duplicate original core assertion source identity");
        identities.add(uniqueness);
        entries.push(Object.freeze({ assertion: Object.freeze({ sourceKind: "umf_document", owner, definitionPin: source.sha256, sourcePointer: pointer, kind: "source", sourceIdentityProfile: profile }), source, ruleName: "core.schema_properties." + key, ruleNameOrigin: "profile_generated", enforcement: "none", reason: "unqualified", ownerEvidence: observed.evidence }));
      }
      continue;
    }
    if (observed.operation === "referenceLinks") {
      const di = prepared.documents.findIndex((d) => d.documentId === observed.documentId), document = prepared.documents[di], requested = observed.identity;
      if (!document || !["0.7.0", "0.8.0"].includes(document.umfVersion) || !collection.referenceLinksProfile)
        throw Error("Original referenceLinks owner context correspondence required");
      const source = document.interpretation.source, mi = source.modules.findIndex((m) => m.id === requested.module), ei = mi < 0 ? -1 : source.modules[mi].elements.findIndex((e) => e.id === requested.element);
      if (mi < 0 || ei < 0)
        throw Error("Original referenceLinks owner context correspondence required");
      const element = source.modules[mi].elements[ei], path = "/modules/" + mi + "/elements/" + ei + "/references";
      const expected = !Object.hasOwn(element, "references") ? { state: "missing" } : { state: "present", links: element.references.map((reference, index) => {
        const ti = source.modules.findIndex((m) => m.id === reference.module), te = ti < 0 ? -1 : source.modules[ti].elements.findIndex((e) => e.id === reference.element);
        if (ti < 0 || te < 0)
          throw Error("Original referenceLinks target correspondence required");
        const target = source.modules[ti].elements[te], at = path + "/" + index;
        return { index, path: at, reference, target: { identity: { module: reference.module, element: reference.element }, path: "/modules/" + ti + "/elements/" + te, ...Object.hasOwn(target, "kind") ? { kind: target.kind } : {} }, uninterpretedPaths: document.interpretation.sourceValidation.diagnostics.filter((d) => d.severity === "warning" && d.code === "UNKNOWN_CORE_FIELD" && (d.path === at || d.path.startsWith(at + "/"))).map((d) => d.path), typeAssertion: "unverified" };
      }) };
      if (!sameOriginalMeaning(original, { operation: "inspect-core-reference-links", version: document.umfVersion === "0.8.0" ? "0.2.0" : "0.1.0", source, identity: requested, path, meaning: expected, provenance: "unverified" }))
        throw Error("Original referenceLinks full result correspondence required");
      if (expected.state === "missing") {
        absent.push(observed);
        continue;
      }
      const common = { documentId: document.documentId, owner: Object.freeze({ moduleId: requested.module, elementId: requested.element }), source: prepared.original.input.documents[di].artifact, ownerProfile: collection.referenceLinksProfile, ownerEvidence: observed.evidence, typeAssertion: "unverified", meaningCorrespondence: true, interpretationQualified: false, scope: "original_direct_core_reference_links_only" };
      referenceLinkDeclarations.push(Object.freeze({ ...common, sourcePointer: path, originalMeaning: meaning }));
      for (const link of meaning.links)
        referenceLinks.push(Object.freeze({ ...common, sourcePointer: link.path, originalMeaning: link }));
      continue;
    }
    if (observed.operation === "members") {
      const di = prepared.documents.findIndex((d) => d.documentId === observed.documentId), document = prepared.documents[di], requested = observed.identity;
      if (!document || !["0.7.0", "0.8.0"].includes(document.umfVersion) || !collection.membersProfile)
        throw Error("Original members owner context correspondence required");
      const source = document.interpretation.source, mi = source.modules.findIndex((m) => m.id === requested.module), ei = mi < 0 ? -1 : source.modules[mi].elements.findIndex((e) => e.id === requested.element);
      if (mi < 0 || ei < 0)
        throw Error("Original members owner context correspondence required");
      const element = source.modules[mi].elements[ei], path = "/modules/" + mi + "/elements/" + ei + "/members";
      const uninterpretedPaths = Object.freeze(document.interpretation.sourceValidation.diagnostics.filter((d) => d.severity === "warning" && d.code === "UNKNOWN_KEY_QUALIFIER" && (d.path === path || d.path.startsWith(path + "/"))).map((d) => d.path));
      const expected = element.kind !== "record" ? { state: "inapplicable" } : !Object.hasOwn(element, "members") ? { state: "missing" } : { state: uninterpretedPaths.length ? "partial" : "known", members: element.members, uninterpretedPaths };
      if (!sameOriginalMeaning(original, { operation: "inspect-core-record-members", version: document.umfVersion === "0.8.0" ? "0.2.0" : "0.1.0", source, identity: requested, path, meaning: expected, provenance: "unverified" }))
        throw Error("Original members full result correspondence required");
      if (expected.state === "missing") {
        absent.push(observed);
        continue;
      }
      if (expected.state === "inapplicable") {
        deferred.push(observed);
        continue;
      }
      const artifact = prepared.original.input.documents[di].artifact, owner = Object.freeze({ documentId: document.documentId, moduleId: requested.module });
      const addMemberEntry = (pointer, ruleName, originalMeaning) => {
        const uniqueness = JSON.stringify([artifact.sha256, owner, pointer]);
        if (identities.has(uniqueness))
          throw Error("Duplicate original core assertion source identity");
        identities.add(uniqueness);
        const entry = Object.freeze({ assertion: Object.freeze({ sourceKind: "umf_document", owner, definitionPin: artifact.sha256, sourcePointer: pointer, kind: "source", sourceIdentityProfile: profile }), source: artifact, ruleName, ruleNameOrigin: "profile_generated", enforcement: "none", reason: "unqualified", ownerEvidence: observed.evidence });
        entries.push(entry);
        membershipMeanings.push(Object.freeze({ assertion: entry, ownerProfile: collection.membersProfile, ownerState: expected.state, originalMeaning, uninterpretedPaths, meaningCorrespondence: true, interpretationQualified: false, scope: "original_record_member_owner_meaning_only" }));
      };
      addMemberEntry(path, "core.members", meaning);
      element.members.forEach((member, index) => addMemberEntry(path + "/" + index, "core.members.member", member));
      continue;
    }
    if (observed.operation === "scalarType") {
      const document = prepared.documents.find((d) => d.documentId === observed.documentId), requested = observed.identity;
      if (!document || !["0.7.0", "0.8.0"].includes(document.umfVersion) || !collection.scalarProfile)
        throw Error("Original scalarType owner context correspondence required");
      const source = document.interpretation.source, mi = source.modules.findIndex((m) => m.id === requested.module), ei = mi < 0 ? -1 : source.modules[mi].elements.findIndex((e) => e.id === requested.element);
      if (mi < 0 || ei < 0)
        throw Error("Original scalarType owner context correspondence required");
      const element = source.modules[mi].elements[ei], present = Object.hasOwn(element, "scalarType"), value = element.scalarType;
      const known = ["boolean", "integer", "decimal", "float", "string", "binary", "date", "time", "timestamp"];
      const expected = element.kind !== "field" ? { state: "inapplicable", ...present ? { authoredScalarType: value } : {} } : !present ? { state: "missing" } : known.includes(value) ? { state: "known", scalarType: value } : { state: "unknown", value };
      if (!sameOriginalMeaning(original, { operation: "inspect-core-scalar-type", version: document.umfVersion === "0.8.0" ? "0.2.0" : "0.1.0", source, identity: requested, path: "/modules/" + mi + "/elements/" + ei + "/scalarType", meaning: expected, provenance: "unverified" }))
        throw Error("Original scalarType full result correspondence required");
    }
    if (["kind", "nullability", "cardinality", "facets"].includes(observed.operation)) {
      const document = prepared.documents.find((d) => d.documentId === observed.documentId), requested = observed.identity;
      if (document && ["0.7.0", "0.8.0"].includes(document.umfVersion)) {
        const family = observed.operation;
        const versions = document.umfVersion === "0.8.0" ? { kind: "7.0.0", nullability: "6.0.0", cardinality: "5.0.0", facets: "4.0.0" } : { kind: "6.0.0", nullability: "5.0.0", cardinality: "4.0.0", facets: "3.0.0" };
        const known = { kind: ["field", "record", "group"], nullability: ["required", "absent-allowed", "unspecified"], cardinality: ["one", "array", "map", "unspecified"], facets: [] };
        const source = document.interpretation.source, mi = source.modules.findIndex((m) => m.id === requested.module);
        const ei = mi < 0 ? -1 : source.modules[mi].elements.findIndex((e) => e.id === requested.element);
        if (!collection.fieldProfile || mi < 0 || ei < 0 || !sameOriginalMeaning(original.source, source) || !sameOriginalMeaning(original.identity, requested) || original.operation !== "inspect-core-" + family || original.version !== versions[family] || original.path !== "/modules/" + mi + "/elements/" + ei + "/" + family)
          throw Error("Original " + family + " owner context correspondence required");
        const element = source.modules[mi].elements[ei], present = Object.hasOwn(element, family), value = element[family];
        let expected = present ? known[family].includes(value) ? { state: "known", [family]: value, ...family === "cardinality" && Object.hasOwn(element, "itemType") ? { itemType: element.itemType } : {} } : { state: "unknown", value } : { state: family === "kind" ? "unspecified" : element.kind === "field" ? "missing" : "inapplicable" };
        if (family === "facets" && present) {
          const facets = value, interpreted = {};
          if (facets.length && ["unicode-scalar", "byte"].includes(facets.length.unit))
            interpreted.length = { ...facets.length.max !== undefined ? { max: facets.length.max } : {}, ...document.umfVersion === "0.8.0" && facets.length.min !== undefined ? { min: facets.length.min } : {}, unit: facets.length.unit };
          if (facets.integerWidth)
            interpreted.integerWidth = { bits: facets.integerWidth.bits, signed: facets.integerWidth.signed };
          if (facets.precision !== undefined) {
            interpreted.precision = facets.precision;
            interpreted.scale = facets.scale;
          }
          if (document.umfVersion === "0.8.0") {
            for (const group of ["collectionSize", "range"])
              if (facets[group]) {
                const selected = {};
                for (const key of group === "range" ? ["min", "max", "minInclusive", "maxInclusive"] : ["min", "max"])
                  if (Object.hasOwn(facets[group], key))
                    selected[key] = facets[group][key];
                interpreted[group] = selected;
              }
          }
          const path = "/modules/" + mi + "/elements/" + ei + "/facets";
          const uninterpretedPaths = document.interpretation.sourceValidation.diagnostics.filter((d) => d.severity === "warning" && (document.umfVersion === "0.8.0" || ["UNKNOWN_FACET", "UNKNOWN_FACET_UNIT"].includes(d.code)) && (d.path === path || d.path.startsWith(path + "/"))).map((d) => d.path);
          expected = { state: uninterpretedPaths.length ? "partial" : "known", facets, interpreted, uninterpretedPaths };
        }
        if (!sameOriginalMeaning(meaning, expected))
          throw Error("Original " + family + " meaning correspondence required");
      }
    }
    if (!["known", "partial", "missing"].includes(meaning?.state)) {
      deferred.push(observed);
      continue;
    }
    const di = prepared.documents.findIndex((d) => d.documentId === observed.documentId), document = prepared.documents[di], identity = observed.identity;
    if (!document || JSON.stringify(original.source) !== JSON.stringify(document.interpretation.source) || typeof original.path !== "string" || !original.path.startsWith("/") || typeof identity?.module !== "string")
      throw Error("Original core source/owner pointer required");
    const mi = original.source.modules.findIndex((m) => m.id === identity.module);
    const ei = mi < 0 ? -1 : original.source.modules[mi].elements.findIndex((e) => e.id === identity.element);
    const expectedPath = observed.operation === "relationships" ? "/modules/" + mi + "/relationships" : "/modules/" + mi + "/elements/" + ei + "/" + observed.operation;
    if (mi < 0 || observed.operation !== "relationships" && ei < 0 || original.path !== expectedPath)
      throw Error("Original requested owner pointer correspondence required");
    let node = original.source, present = true;
    const tokens = original.path.slice(1).split("/");
    for (let i = 0;i < tokens.length; i++) {
      const key = tokens[i].replace(/~1/g, "/").replace(/~0/g, "~");
      if (node === null || typeof node !== "object")
        throw Error("Original asserted source parent absent");
      if (!Object.hasOwn(node, key)) {
        if (i !== tokens.length - 1)
          throw Error("Original asserted source parent absent");
        present = false;
        break;
      }
      node = node[key];
    }
    if (meaning.state === "missing") {
      if (present)
        throw Error("Complete original declaration meaning correspondence required: authored value cannot be missing");
      absent.push(observed);
      continue;
    }
    if (!present)
      throw Error("Original asserted source node absent");
    const source = prepared.original.input.documents[di].artifact, owner = Object.freeze({ documentId: document.documentId, moduleId: identity.module });
    const declaration = observed.operation === "keys" || observed.operation === "relationships";
    const originalNodes = declaration ? node : [node], ownerNodes = declaration ? meaning[observed.operation] : [node];
    if (!Array.isArray(originalNodes) || !Array.isArray(ownerNodes) || originalNodes.length !== ownerNodes.length)
      throw Error("Complete original declaration occurrence correspondence required");
    if (declaration && !sameOriginalMeaning(originalNodes, ownerNodes))
      throw Error("Complete original declaration meaning correspondence required");
    if (originalNodes.length === 0) {
      absent.push(observed);
      continue;
    }
    for (let index = 0;index < originalNodes.length; index++) {
      const pointer = original.path + (declaration ? "/" + index : "");
      const uniqueness = JSON.stringify([source.sha256, owner, pointer]);
      if (identities.has(uniqueness))
        throw Error("Duplicate original core assertion source identity");
      identities.add(uniqueness);
      const authored = declaration && typeof originalNodes[index]?.id === "string" && originalNodes[index].id.length > 0;
      if (declaration && originalNodes[index]?.id !== ownerNodes[index]?.id)
        throw Error("Original authored declaration identity correspondence required");
      const identity = authored ? { kind: "authored", authoredIdentity: originalNodes[index].id } : { kind: "source", sourceIdentityProfile: profile };
      const entry = Object.freeze({
        assertion: Object.freeze({ sourceKind: "umf_document", owner, definitionPin: source.sha256, sourcePointer: pointer, ...identity }),
        source,
        ruleName: "core." + observed.operation,
        ruleNameOrigin: "profile_generated",
        enforcement: "none",
        reason: "unqualified",
        ownerEvidence: observed.evidence
      });
      entries.push(entry);
      if (["kind", "nullability", "cardinality", "facets", "scalarType"].includes(observed.operation) && ["0.7.0", "0.8.0"].includes(original.source.umf))
        fieldMeanings.push(Object.freeze({
          assertion: entry,
          ownerProfile: observed.operation === "scalarType" ? collection.scalarProfile : collection.fieldProfile,
          ownerState: meaning.state,
          originalMeaning: meaning,
          meaningCorrespondence: true,
          interpretationQualified: false,
          scope: `original_${observed.operation}_owner_meaning_only`
        }));
      if (declaration)
        declarationMeanings.push(Object.freeze({
          assertion: entry,
          ownerProfile: collection.profile,
          ownerState: meaning.state,
          originalMeaning: ownerNodes[index],
          uninterpretedPaths: meaning.uninterpretedPaths,
          meaningCorrespondence: true,
          interpretationQualified: false,
          scope: "original_declaration_owner_meaning_only"
        }));
    }
  }
  return Object.freeze({ profile, manifest, entries: Object.freeze(entries), referenceLinks: Object.freeze(referenceLinks), referenceLinkDeclarations: Object.freeze(referenceLinkDeclarations), declarationMeanings: Object.freeze(declarationMeanings), fieldMeanings: Object.freeze(fieldMeanings), membershipMeanings: Object.freeze(membershipMeanings), absent: Object.freeze(absent), deferred: Object.freeze(deferred), complete: false, scope: "original_inspected_core_source_identity_subset_only" });
}

// packages/umf-bun/src/catalog-validation-evidence.ts
import { createHash as createHash5 } from "crypto";
function collectCatalogValidationEvidence(prepared) {
  requireOriginalCatalogPreparation(prepared);
  let retained = 0, diagnosticCount = 0;
  const artifact = (identity, value) => {
    const bytes = Buffer.from(JSON.stringify(value), "utf8");
    retained += bytes.length;
    if (retained > 4194304)
      throw Error("Validation evidence component output capacity exceeded");
    return Object.freeze({ identity, bytesBase64: bytes.toString("base64"), sha256: createHash5("sha256").update(bytes).digest("hex") });
  };
  const manifest = artifact("truss.umf-validation-evidence-profile/0.1.0", { interfaceVersion: "truss-umf-validation-evidence/0.1.0", producer: prepared.umfProfile, encoding: "UTF-8 JSON native diagnostic wrapper; no code/path/severity remapping", basis: ["original", "reversible_target"], sourcePointer: "whole original document", completeness: "both source and interpretation-target owner validation complete" });
  const profile = Object.freeze({ identity: "truss-umf-validation-evidence", version: "0.1.0", sha256: manifest.sha256 });
  const diagnostics = [];
  const interpretations = prepared.documents.map((document, index) => {
    const observation = document.interpretation, source = prepared.original.input.documents[index].artifact;
    const validations = [{ basis: "original", validation: observation.sourceValidation }];
    if (observation.transition)
      validations.push({ basis: "reversible_target", validation: observation.targetValidation });
    for (const { basis, validation } of validations) {
      if (!validation || typeof validation.complete !== "boolean" || !Array.isArray(validation.diagnostics))
        throw Error("Original validation observation required");
      for (let di = 0;di < validation.diagnostics.length; di++) {
        if (++diagnosticCount > 4096)
          throw Error("Validation diagnostic component capacity exceeded");
        const diagnostic = artifact(`truss.original-umf-diagnostic/${index}/${basis}/${di}`, { profile, producer: prepared.umfProfile, documentId: document.documentId, contentSha256: source.sha256, basis, diagnostic: validation.diagnostics[di] });
        diagnostics.push(Object.freeze({ classification: "upstream_validation", source: Object.freeze({ kind: "document", artifact: source, sourcePointer: "" }), diagnosticProfile: profile, diagnostic }));
      }
    }
    if (typeof observation.targetValidation?.complete !== "boolean")
      throw Error("Original target validation required");
    const evidence = artifact("truss.original-umf-observation/" + document.documentId, { producer: prepared.umfProfile, observation });
    return Object.freeze({
      documentId: document.documentId,
      contentSha256: source.sha256,
      interpretationProfile: prepared.umfProfile,
      completeness: observation.sourceValidation.complete && observation.targetValidation.complete ? "complete" : "partial",
      evidence
    });
  });
  return Object.freeze({ profile, manifest, diagnostics: Object.freeze(diagnostics), documentInterpretations: Object.freeze(interpretations), scope: "original_producer_validation_evidence_only" });
}

// packages/umf-bun/src/catalog-extension-artifacts.ts
import { createHash as createHash6 } from "crypto";

// packages/umf-bun/src/catalog-extension-inventory.ts
function collectCatalogExtensionInventory(prepared) {
  requireOriginalCatalogPreparation(prepared);
  const entries = [];
  const pointer = (key) => key.replace(/~/g, "~0").replace(/\//g, "~1");
  for (let index = 0;index < prepared.documents.length; index++) {
    const document = prepared.documents[index], source = document.interpretation.source;
    const artifact = prepared.original.input.documents[index].artifact;
    const add = (node, path, owner, scope) => {
      for (const extensionId of Object.keys(node.extensions ?? {})) {
        if (entries.length >= 4096)
          throw Error("Original extension occurrence capacity exceeded");
        if (!Object.hasOwn(source.vocabularies, extensionId))
          throw Error("Original extension vocabulary declaration missing");
        entries.push(Object.freeze({
          owner: Object.freeze(owner),
          scope,
          sourcePointer: path + "/extensions/" + pointer(extensionId),
          extensionId,
          vocabulary: source.vocabularies[extensionId],
          payload: node.extensions[extensionId],
          source: artifact
        }));
      }
    };
    add(source, "", { scope: "document", documentId: document.documentId }, "document");
    for (let mi = 0;mi < source.modules.length; mi++) {
      const module = source.modules[mi], owner = { documentId: document.documentId, moduleId: module.id };
      add(module, `/modules/${mi}`, owner, "module");
      for (let ei = 0;ei < module.elements.length; ei++)
        add(module.elements[ei], `/modules/${mi}/elements/${ei}`, owner, "element");
    }
  }
  return Object.freeze({ entries: Object.freeze(entries), scope: "original_document_module_element_extension_occurrences_only" });
}

// packages/umf-bun/src/catalog-extension-artifacts.ts
function collectCatalogExtensionArtifacts(prepared) {
  const inventory = collectCatalogExtensionInventory(prepared);
  let retained = 0;
  const extensions = inventory.entries.map((entry, index) => {
    const bytes = Buffer.from(JSON.stringify({
      interfaceVersion: "truss-original-extension-occurrence/0.1.0",
      interpretation: "retained_uninterpreted",
      owner: entry.owner,
      scope: entry.scope,
      sourcePointer: entry.sourcePointer,
      extensionId: entry.extensionId,
      vocabulary: entry.vocabulary,
      payload: entry.payload,
      source: entry.source
    }));
    if (bytes.length > 1048576 || (retained += bytes.length) > 4194304)
      throw Error("Extension artifact output capacity exceeded");
    return Object.freeze({ identity: `truss.original-extension-occurrence/${index}`, bytesBase64: bytes.toString("base64"), sha256: createHash6("sha256").update(bytes).digest("hex") });
  });
  return Object.freeze({ extensions: Object.freeze(extensions), scope: "original_document_module_element_extension_artifacts_only" });
}

// packages/umf-bun/src/catalog-ingress-report-basis.ts
function collectCatalogIngressReportBasis(prepared) {
  requireOriginalCatalogPreparation(prepared);
  const input = prepared.original.input;
  if (input.transforms.length)
    throw Error("Complete transform report producer required");
  if (input.binding.state !== "absent")
    throw Error("Registered binding effect interpretation required");
  if (input.documents.some((document) => document.ingress.kind !== "native"))
    throw Error("Complete converted ingress loss producer required");
  return Object.freeze({
    losses: Object.freeze([]),
    transformRegistrations: Object.freeze([]),
    originalIngress: Object.freeze(input.documents.map((document, index) => Object.freeze({ documentId: document.documentId, contentSha256: document.artifact.sha256, sourcePointer: `/documents/${index}/ingress`, kind: "native" }))),
    scope: "original_native_ingress_absent_binding_and_transforms_only"
  });
}

// packages/umf-bun/src/python-preparation-core08.ts
init_acceptance_json();
var root = resolve2(import.meta.dir);
var dependencies = resolve2(root, "../_umf/runtime/package.json");
var schemaUrl = new URL("./acceptance-input-v0.1.schema.json", import.meta.url);
var MAX_OUTPUT = 16777216;
var emit = (value) => {
  const text = JSON.stringify(value);
  console.log(Buffer.byteLength(text) + 1 <= MAX_OUTPUT ? text : JSON.stringify({ status: "refused", reason: "resource", diagnostics: [] }));
};
var diagnostics = [];
try {
  const bytes = new Uint8Array(await Bun.stdin.arrayBuffer());
  if (bytes.length > 1048576)
    throw Error("resource");
  const request = decodeAcceptanceJson(bytes);
  if (Object.keys(request).sort().join(",") !== "configurationHex,documents" || typeof request.configurationHex !== "string" || !/^(?:[0-9a-f]{2})+$/.test(request.configurationHex) || !Array.isArray(request.documents) || request.documents.length < 1 || request.documents.length > 512)
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
  await Promise.resolve().then(() => init_acceptance_input());
  const inspected = (await createAcceptanceInputInspector(dependencies, schemaUrl)).inspect(original);
  for (const source of inspected.documents) {
    try {
      preflightSourceJson(new TextEncoder().encode(source.originalText));
      const observation = owner.inspect(source.originalText);
      diagnostics.push({ documentId: source.documentId, documentRevision: source.documentRevision, observation });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Original document refused";
      diagnostics.push({
        documentId: source.documentId,
        documentRevision: source.documentRevision,
        originalError: {
          message: message.slice(0, 8192),
          truncated: message.length > 8192 || typeof error?.code === "string" && error.code.length > 256 || typeof error?.path === "string" && error.path.length > 8192,
          ...typeof error?.code === "string" ? { code: error.code.slice(0, 256) } : {},
          ...typeof error?.path === "string" ? { path: error.path.slice(0, 8192) } : {}
        }
      });
    }
  }
  if (diagnostics.some((d) => d.originalError || !d.observation.sourceValidation.valid || !d.observation.targetValidation?.valid)) {
    emit({ status: "refused", reason: "invalid_document", diagnostics });
  } else {
    const prepared = preparation.prepare(original);
    let reportEvidence;
    try {
      const { declarations, fields, scalars, members, links } = current;
      const observations = collectCatalogAssertionObservations(prepared, declarations, fields, scalars, members, links);
      reportEvidence = {
        ownerObservations: observations,
        observationCoverage: assessCatalogObservationCoverage(prepared, observations),
        coreAssertionIdentities: collectCatalogCoreAssertionIdentities(prepared, observations),
        validation: collectCatalogValidationEvidence(prepared),
        retainedExtensions: collectCatalogExtensionArtifacts(prepared),
        ingress: prepared.original.input.binding.state === "absent" && !prepared.original.input.transforms.length ? { state: "available", basis: collectCatalogIngressReportBasis(prepared) } : { state: "unavailable", reason: "registered_binding_or_transform_report_producer_required" },
        scope: "original_owner_report_preparation_only"
      };
    } catch {
      reportEvidence = { scope: "original_owner_report_preparation_only", ingress: { state: "unavailable", reason: "report_evidence_unavailable" } };
    }
    const response = {
      status: "prepared",
      inputHex: prepared.original.originalUtf8Hex,
      documents: prepared.documents,
      declarations: prepared.declarations,
      archiveDocuments: prepared.archiveDocuments,
      reportEvidence,
      provenance: { umfProfile: prepared.umfProfile, schemaSha256: prepared.original.schemaSha256, scope: prepared.scope }
    };
    if (Buffer.byteLength(JSON.stringify(response)) + 1 > MAX_OUTPUT)
      response.reportEvidence = { scope: "original_owner_report_preparation_only", ingress: { state: "unavailable", reason: "report_evidence_resource" } };
    emit(response);
  }
} catch (error) {
  const message = error instanceof Error ? error.message : "";
  const reason = message === "resource" ? "resource" : message.includes("Unsupported") ? "unsupported_profile" : message.includes("pin mismatch") || message.includes("Missing original producer") ? "producer_unavailable" : "invalid_input";
  emit({ status: "refused", reason, diagnostics });
}
