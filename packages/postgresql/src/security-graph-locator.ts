/** Private candidate graph projection boundary. Native rows/source custody and
 * a stable complete inventory are host premises. This neither resolves business
 * keys nor grants authorization or qualifies an installed graph. */
export interface SecurityGraphLocator { readonly id: string; readonly typeId: string }
export interface SecurityGraphEndpointProjection {
  readonly id: string;
  readonly relationshipId: string;
  readonly source: SecurityGraphLocator;
  readonly target: SecurityGraphLocator;
}
const refuse = (): never => { throw Error('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED'); };
function row(value: unknown, names: readonly string[]): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return refuse();
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) return refuse();
  const descriptors = Object.getOwnPropertyDescriptors(value);
  if (Reflect.ownKeys(descriptors).length !== names.length || names.some(name =>
    !Object.hasOwn(descriptors, name) || !Object.hasOwn(descriptors[name]!, 'value') || !descriptors[name]!.enumerable)) return refuse();
  return Object.fromEntries(names.map(name => [name, descriptors[name]!.value]));
}
function integer(value: unknown, bits: bigint): string {
  if (typeof value !== 'string' || value.length > 20 || !/^(0|-?[1-9][0-9]*)$/.test(value)) return refuse();
  const parsed = BigInt(value);
  if (parsed < -(1n << bits) || parsed >= (1n << bits)) return refuse();
  return value;
}
const identity = (locator: SecurityGraphLocator) => JSON.stringify([locator.id, locator.typeId]);
function collection(value: unknown): readonly unknown[] {
  if (!Array.isArray(value) || Object.getPrototypeOf(value) !== Array.prototype) return refuse();
  const length = Object.getOwnPropertyDescriptor(value, 'length')?.value;
  if (!Number.isSafeInteger(length) || length < 0 || length > 4096 || Reflect.ownKeys(value).length !== length + 1) return refuse();
  const snapshot: unknown[] = [];
  for (let index = 0; index < length; index++) {
    const descriptor = Object.getOwnPropertyDescriptor(value, String(index));
    if (!descriptor || !Object.hasOwn(descriptor, 'value') || !descriptor.enumerable) return refuse();
    snapshot.push(descriptor.value);
  }
  return snapshot;
}
/** Validate native bigint/int4 TEXT carriers without Number or Date conversion.
 * Every endpoint must resolve to exactly one supplied typed object. The host
 * must separately qualify relation selection, declared endpoint types and facts. */
export function projectSecurityGraphEndpoints(input: {
  objects: readonly unknown[]; edges: readonly unknown[];
}): readonly SecurityGraphEndpointProjection[] {
  const packet = row(input, ['objects', 'edges']);
  const objectRows = collection(packet.objects), edgeRows = collection(packet.edges);
  const objects = new Map<string, SecurityGraphLocator>();
  for (const raw of objectRows) {
    const value = row(raw, ['id', 'typeId']);
    const locator = Object.freeze({id: integer(value.id, 63n), typeId: integer(value.typeId, 31n)});
    const key = identity(locator);
    if (objects.has(key)) return refuse();
    objects.set(key, locator);
  }
  const result: SecurityGraphEndpointProjection[] = [];
  const seen = new Set<string>();
  for (const raw of edgeRows) {
    const value = row(raw, ['id', 'relationshipId', 'sourceId', 'sourceType', 'targetId', 'targetType']);
    const id = integer(value.id, 63n);
    const relationshipId = integer(value.relationshipId, 31n);
    const source = objects.get(identity({id: integer(value.sourceId, 63n), typeId: integer(value.sourceType, 31n)})) ?? refuse();
    const target = objects.get(identity({id: integer(value.targetId, 63n), typeId: integer(value.targetType, 31n)})) ?? refuse();
    const edgeIdentity = id;
    if (seen.has(edgeIdentity)) return refuse();
    seen.add(edgeIdentity);
    result.push(Object.freeze({id, relationshipId, source, target}));
  }
  return Object.freeze(result);
}

/** Candidate selected association projection against supplied rel_endpoint rows.
 * The original relationship allocation/declarations and their completeness must
 * be authenticated by the host; matching these rows supplies no such authority. */
export function projectDeclaredSecurityGraphEndpoints(input: {
  objects: readonly unknown[]; edges: readonly unknown[];
  declarations: readonly unknown[]; selectedRelationshipId: string;
}): readonly SecurityGraphEndpointProjection[] {
  const packet = row(input, ['objects', 'edges', 'declarations', 'selectedRelationshipId']);
  const selected = integer(packet.selectedRelationshipId, 31n);
  const declarations = collection(packet.declarations);
  const permitted = new Set<string>();
  let selectedDeclared = false;
  for (const raw of declarations) {
    const value = row(raw, ['relationshipId', 'sourceType', 'targetType']);
    const relationshipId = integer(value.relationshipId, 31n);
    const signature = JSON.stringify([relationshipId, integer(value.sourceType, 31n), integer(value.targetType, 31n)]);
    if (permitted.has(signature)) return refuse();
    permitted.add(signature);
    selectedDeclared ||= relationshipId === selected;
  }
  if (!selectedDeclared) return refuse();
  const endpoints = projectSecurityGraphEndpoints({objects: packet.objects as readonly unknown[], edges: packet.edges as readonly unknown[]});
  for (const edge of endpoints) {
    if (!permitted.has(JSON.stringify([edge.relationshipId, edge.source.typeId, edge.target.typeId]))) return refuse();
  }
  return Object.freeze(endpoints.filter(edge => edge.relationshipId === selected));
}

/** Candidate exact key-bucket lookup. expected must originate from the registered
 * UMF tuple producer and independently verified namespace selection, including
 * correspondence of its type/key-number to that namespace. Bytes or caller
 * labels alone do not authenticate this premise. No digest is semantic identity. */
export function resolveSecurityGraphKeyLocator(input: {
  objects: readonly unknown[]; buckets: readonly unknown[];
  expected: {typeId: string; keyNumber: string; namespaceHex: string; keyHex: string};
}): SecurityGraphLocator {
  const packet = row(input, ['objects', 'buckets', 'expected']);
  const objectRows = collection(packet.objects), bucketRows = collection(packet.buckets);
  const expected = row(packet.expected, ['typeId', 'keyNumber', 'namespaceHex', 'keyHex']);
  const typeId = integer(expected.typeId, 31n), keyNumber = integer(expected.keyNumber, 15n);
  let totalHexLength = 0;
  const hex = (value: unknown, maxBytes: number): string => {
    if (typeof value !== 'string' || !value.length || value.length > maxBytes * 2 || value.length % 2) return refuse();
    totalHexLength += value.length;
    if (totalHexLength > 32 * 1024 * 1024 || !/^[0-9a-f]+$/.test(value)) return refuse();
    return value;
  };
  const namespaceHex = hex(expected.namespaceHex, 65536), keyHex = hex(expected.keyHex, 1048576);
  // Validate each original row once, retaining its complete typed owner.
  const objects = new Map<string, SecurityGraphLocator>();
  for (const raw of objectRows) {
    const value = row(raw, ['id', 'typeId']);
    const locator = Object.freeze({id: integer(value.id, 63n), typeId: integer(value.typeId, 31n)});
    const key = identity(locator);
    if (objects.has(key)) return refuse();
    objects.set(key, locator);
  }
  const rows = new Set<string>(), owners = new Set<string>();
  let found: SecurityGraphLocator | undefined;
  for (const raw of bucketRows) {
    const value = row(raw, ['storageRowId', 'typeId', 'keyNumber', 'objectId', 'namespaceHex', 'keyHex']);
    const storageRowId = integer(value.storageRowId, 63n);
    if (BigInt(storageRowId) <= 0n || rows.has(storageRowId)) return refuse();
    rows.add(storageRowId);
    const nativeType = integer(value.typeId, 31n), nativeKey = integer(value.keyNumber, 15n);
    const owner = objects.get(identity({id: integer(value.objectId, 63n), typeId: nativeType})) ?? refuse();
    const ownerKey = JSON.stringify([owner.id, owner.typeId, nativeKey]);
    if (owners.has(ownerKey)) return refuse();
    owners.add(ownerKey);
    const nativeNamespace = hex(value.namespaceHex, 65536), nativeBytes = hex(value.keyHex, 1048576);
    if (nativeType === typeId && nativeKey === keyNumber && nativeNamespace === namespaceHex && nativeBytes === keyHex) {
      if (found) return refuse();
      found = owner;
    }
  }
  return found ?? refuse();
}
