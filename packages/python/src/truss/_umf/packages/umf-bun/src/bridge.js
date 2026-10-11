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

// packages/postgresql/src/acceptance-json.ts
function decodeAcceptanceJson(original) {
  return scanJson(original, false);
}
function preflightSourceJson(original) {
  scanJson(original, true);
}
function scanJson(original, sourceNumbers) {
  const refuse = (reason) => {
    throw new AcceptanceJsonError(reason);
  };
  if (original.length > MAX_BYTES)
    refuse("resource");
  const bytes = original.slice();
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
  const value = () => {
    whitespace();
    if (++nodes > MAX_NODES || stack.length > MAX_DEPTH)
      refuse("resource");
    const c = bytes[index];
    if (c === 34) {
      attach(string());
      return;
    }
    if (c === 123 || c === 91) {
      take();
      const item = c === 123 ? Object.create(null) : [];
      attach(item);
      stack.push(c === 123 ? { kind: "object", value: item, state: "first", key: "", keys: [] } : { kind: "array", value: item, state: "first" });
      return;
    }
    for (const [token, result] of [["null", null], ["true", true], ["false", false]]) {
      if (c === token.charCodeAt(0)) {
        for (const ch of token)
          if (take() !== ch.charCodeAt(0))
            refuse("grammar");
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
        take();
        stack.pop();
      } else if (frame.state === "first" || frame.state === "value")
        value();
      else if (c === 93) {
        take();
        stack.pop();
      } else if (c === 44) {
        take();
        frame.state = "value";
      } else
        refuse("grammar");
    } else {
      if (frame.state === "first" && c === 125) {
        take();
        stack.pop();
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
        take();
        stack.pop();
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
var AcceptanceJsonError, MAX_BYTES = 1048576, MAX_DEPTH = 128, MAX_NODES = 1e5, MAX_MEMBERS = 4096, MAX_WORK = 2000000;
var init_acceptance_json = __esm(() => {
  AcceptanceJsonError = class AcceptanceJsonError extends Error {
    reason;
    constructor(reason) {
      super(reason);
      this.reason = reason;
    }
  };
});

// packages/umf-bun/src/acceptance-input.ts
import { createRequire } from "module";
import { readFile } from "fs/promises";
import { createHash } from "crypto";
async function createAcceptanceInputInspector(dependenciesPackage) {
  const schemaBytes = await readFile(new URL("../../../docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json", import.meta.url));
  if (digest(schemaBytes) !== SCHEMA_SHA)
    throw Error("Original acceptance schema pin mismatch");
  const require2 = createRequire(dependenciesPackage);
  const Ajv = require2("ajv/dist/2020").default;
  const validate = new Ajv({ strict: true }).compile(JSON.parse(schemaBytes.toString("utf8")));
  return Object.freeze({ schemaSha256: SCHEMA_SHA, inspect(original) {
    if (!(original.buffer instanceof ArrayBuffer))
      throw new AcceptanceInputInspectionError("source_custody");
    if (original.length > 1048576)
      throw new AcceptanceInputInspectionError("resource");
    const owned = original.slice();
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
  init_acceptance_json();
  AcceptanceInputInspectionError = class AcceptanceInputInspectionError extends Error {
    reason;
    constructor(reason) {
      super(reason);
      this.reason = reason;
    }
  };
});

// packages/umf-bun/src/python-preparation.ts
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
      const fields = array(declaration.members).map((value) => {
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
      records.push(Object.freeze({ documentId, moduleId, elementId, declaration, fields: Object.freeze(fields), keys: Object.freeze(keys) }));
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
function requireOriginalAcceptanceProfileResolver(resolver) {
  if (!originalResolvers.has(resolver))
    throw Error("Original profile byte-custody resolver required");
}

// packages/umf-bun/src/catalog-input.ts
var originalPreparations = new WeakSet;
function requireOriginalCatalogPreparation(prepared) {
  if (!originalPreparations.has(prepared))
    throw Error("Original validated catalog preparation required");
}
async function createCatalogInputPreparation(directory, dependenciesPackage, profiles) {
  if (profiles !== undefined)
    requireOriginalAcceptanceProfileResolver(profiles);
  const inspector = await createAcceptanceInputInspector(dependenciesPackage);
  const owner = await loadUmfProducer(directory);
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

// packages/umf-bun/src/catalog-validation-evidence.ts
import { createHash as createHash2 } from "crypto";
function collectCatalogValidationEvidence(prepared) {
  requireOriginalCatalogPreparation(prepared);
  let retained = 0, diagnosticCount = 0;
  const artifact = (identity, value) => {
    const bytes = Buffer.from(JSON.stringify(value), "utf8");
    retained += bytes.length;
    if (retained > 4194304)
      throw Error("Validation evidence component output capacity exceeded");
    return Object.freeze({ identity, bytesBase64: bytes.toString("base64"), sha256: createHash2("sha256").update(bytes).digest("hex") });
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
import { createHash as createHash3 } from "crypto";

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
    return Object.freeze({ identity: `truss.original-extension-occurrence/${index}`, bytesBase64: bytes.toString("base64"), sha256: createHash3("sha256").update(bytes).digest("hex") });
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

// packages/umf-bun/src/python-preparation.ts
init_acceptance_json();
var root = resolve2(import.meta.dir, "../../..");
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
  const preparation = await createCatalogInputPreparation(root + "/owner", root + "/runtime/package.json");
  const owner = await loadUmfProducer(root + "/owner");
  const documents = request.documents.map((d) => {
    if (!d || Object.keys(d).sort().join(",") !== "artifact,documentId,documentRevision")
      throw Error("invalid_input");
    return { ...d, umfProfile: preparation.umfProfile, ingress: { kind: "native" } };
  });
  const input = { interfaceVersion: "truss-acceptance-input/0.1.0", ...configuration, documents };
  const original = new TextEncoder().encode(JSON.stringify(input));
  await Promise.resolve().then(() => init_acceptance_input());
  const inspected = (await createAcceptanceInputInspector(root + "/runtime/package.json")).inspect(original);
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
      reportEvidence = {
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
