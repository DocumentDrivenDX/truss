import type {AcceptanceInput, CanonicalTree, ExactArtifact} from './truss-acceptance-input-v0.1';
const pin = {identity: 'fixture', version: 'draft', sha256: '0'.repeat(64)};
const artifact: ExactArtifact = {identity: 'document', bytesBase64: 'e30=', sha256: '0'.repeat(64)};
const input: AcceptanceInput = {
  interfaceVersion: 'truss-acceptance-input/0.1.0', layoutProfile: pin,
  acceptanceProfile: pin, validatorProfile: pin, supportProfile: pin,
  documents: [{documentId: 'doc', documentRevision: 'revision', artifact, umfProfile: pin, ingress: {kind: 'native'}}],
  binding: {state: 'absent'},
  policy: {unknownEndpoint: 'reject', loss: 'strict', profile: pin}, transforms: [],
};
// @ts-expect-error Exact canonical values cannot carry rounded host numbers.
const rounded: CanonicalTree = {integer: 9007199254740993};
// @ts-expect-error Source bytes cannot be replaced with a parsed host object.
const parsedArtifact: ExactArtifact = {identity: 'document', bytesBase64: {}, sha256: '0'.repeat(64)};
// @ts-expect-error Present binding must carry complete artifact and vocabulary pins.
const incompleteBinding: AcceptanceInput = {...input, binding: {state: 'present'}};
// @ts-expect-error Attempt origin is not a compared acceptance input member.
const rewritingOrigin: AcceptanceInput = {...input, assertedOrigin: {actor: 'different'}};
void [input, rounded, parsedArtifact, incompleteBinding, rewritingOrigin];
// @ts-expect-error Converted ingress cannot omit exact source and loss report.
const missingConversion: AcceptanceInput['documents'][number]['ingress'] = {kind: 'converted', adapterProfile: pin};
void missingConversion;
